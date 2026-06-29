from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.services.openfda_food_enforcement_client import OpenFDAFoodEnforcementClient
from app.services.safety_source_adapters.base import (
    NormalizedSafetyRecord,
    SafetySourceAdapterError,
    SourceAdapterResult,
    dedupe_records,
    first_text,
    record_matches_query,
    stable_payload_hash,
    utc_now_iso,
)
from app.sources.registry import OPENFDA_FOOD_ENFORCEMENT

logger = logging.getLogger("dav_ai.real_world_safety.openfda_food")

REPO_ROOT = Path(__file__).resolve().parents[4]
DEMO_RECORDS_PATH = REPO_ROOT / "data" / "safety_sources" / "food" / "openfda_food_curated_records.json"


class OpenFDAFoodEnforcementAdapter:
    def __init__(self):
        self.source = OPENFDA_FOOD_ENFORCEMENT
        self.endpoint = self.source["endpoint"]
        self.snapshot_endpoint = "local:data/safety_sources/food/openfda_food_curated_records.json"
        self.live_client = OpenFDAFoodEnforcementClient(timeout_seconds=4.5)

    async def search(
        self,
        *,
        query: str,
        limit: int,
        request_id: str | None = None,
    ) -> SourceAdapterResult:
        try:
            return await self._search_live(
                query=query,
                limit=limit,
                request_id=request_id,
            )
        except Exception as exc:
            logger.warning(
                "openfda_food_live_search_failed_using_snapshot_fallback",
                extra={
                    "event": "openfda_food_live_search_failed_using_snapshot_fallback",
                    "request_id": request_id,
                    "source_id": self.source["source_id"],
                    "query": query,
                    "error_type": exc.__class__.__name__,
                },
            )
            return await self._search_snapshot_fallback(
                query=query,
                limit=limit,
                request_id=request_id,
                fallback_reason=str(exc) or exc.__class__.__name__,
            )

    async def _search_live(
        self,
        *,
        query: str,
        limit: int,
        request_id: str | None = None,
    ) -> SourceAdapterResult:
        payload = await self.live_client.search_food_recalls(
            query=query,
            limit=limit,
            request_id=request_id,
        )

        retrieved_at = payload["retrieval_timestamp"]
        raw_results = payload.get("raw", {}).get("results", [])

        records: list[NormalizedSafetyRecord] = []
        for raw_record in raw_results:
            if not isinstance(raw_record, dict):
                continue

            normalized = _normalize_openfda_food_record(
                record=raw_record,
                retrieved_at=retrieved_at,
                source_name=self.source["source_name"],
                source_url=self.source["endpoint"],
                source_type="live public API request",
            )

            if record_matches_query(normalized, query):
                records.append(normalized)

        records = dedupe_records(records)[:limit]

        return SourceAdapterResult(
            source_id=self.source["source_id"],
            source_name=self.source["source_name"],
            source_type="live public API request",
            source_url=self.source["endpoint"],
            source_kind="structured_api",
            retrieved_at=retrieved_at,
            records=records,
            raw_payload={
                "mode": "live_public_api_request",
                "endpoint": self.source["endpoint"],
                "query": query,
                "raw": payload.get("raw", {}),
            },
            upstream_status="success" if records else "empty",
            context={
                "fallback_used": False,
            },
        )

    async def _search_snapshot_fallback(
        self,
        *,
        query: str,
        limit: int,
        request_id: str | None = None,
        fallback_reason: str | None = None,
    ) -> SourceAdapterResult:
        retrieved_at = utc_now_iso()

        try:
            demo_records = _load_demo_records()
            records: list[NormalizedSafetyRecord] = []

            query_text = query.lower().strip()
            query_terms = [term for term in query_text.split() if term]

            for demo_record in demo_records:
                search_blob = json.dumps(demo_record, ensure_ascii=False).lower()
                is_match = query_text in search_blob or all(term in search_blob for term in query_terms)

                if not is_match:
                    continue

                normalized = _normalize_openfda_food_record(
                    record=demo_record,
                    retrieved_at=retrieved_at,
                    source_name=self.source["source_name"],
                    source_url=self.source["endpoint"],
                    source_type="local curated official snapshot",
                )

                if record_matches_query(normalized, query) or is_match:
                    records.append(normalized)

            records = dedupe_records(records)[:limit]

            return SourceAdapterResult(
                source_id=self.source["source_id"],
                source_name=self.source["source_name"],
                source_type="local curated official snapshot",
                source_url=self.snapshot_endpoint,
                source_kind="structured_api",
                retrieved_at=retrieved_at,
                records=records,
                raw_payload={
                    "mode": "curated_official_source_snapshot_fallback",
                    "path": str(DEMO_RECORDS_PATH.relative_to(REPO_ROOT)),
                    "records_loaded": len(demo_records),
                    "query": query,
                    "fallback_reason": fallback_reason,
                },
                upstream_status="success" if records else "empty",
                context={
                    "fallback_used": True,
                    "fallback_reason": fallback_reason,
                    "live_endpoint": self.source["endpoint"],
                },
            )

        except FileNotFoundError as exc:
            message = f"openFDA food curated snapshot file not found: {DEMO_RECORDS_PATH}"
            logger.warning(
                "openfda_food_snapshot_fallback_missing",
                extra={
                    "event": "openfda_food_snapshot_fallback_missing",
                    "request_id": request_id,
                    "source_id": self.source["source_id"],
                    "query": query,
                },
            )
            raise SafetySourceAdapterError(message, error_type="missing_snapshot") from exc
        except Exception as exc:
            logger.exception(
                "openfda_food_snapshot_fallback_search_failed",
                extra={
                    "event": "openfda_food_snapshot_fallback_search_failed",
                    "request_id": request_id,
                    "source_id": self.source["source_id"],
                    "query": query,
                },
            )
            raise SafetySourceAdapterError(str(exc), error_type="adapter_error") from exc


def _load_demo_records() -> list[dict[str, Any]]:
    with DEMO_RECORDS_PATH.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    if not isinstance(payload, list):
        return []

    return [item for item in payload if isinstance(item, dict)]


def _normalize_openfda_food_record(
    *,
    record: dict[str, Any],
    retrieved_at: str,
    source_name: str,
    source_url: str,
    source_type: str,
) -> NormalizedSafetyRecord:
    product_description = first_text(record.get("product_description"), record.get("product_name"))
    recalling_firm = first_text(record.get("recalling_firm"), record.get("company_name"))
    reason = first_text(record.get("reason_for_recall"), record.get("reason"))
    classification = first_text(record.get("classification"))
    status = first_text(record.get("status"))
    code_info = first_text(record.get("code_info"))
    more_code_info = first_text(record.get("more_code_info"))
    distribution = first_text(record.get("distribution_pattern"))
    product_quantity = first_text(record.get("product_quantity"))
    notification = first_text(record.get("initial_firm_notification"))
    termination_date = first_text(record.get("termination_date"))
    voluntary_mandated = first_text(record.get("voluntary_mandated"))
    recall_date = first_text(record.get("recall_initiation_date"), record.get("report_date"))

    title = first_text(
        record.get("title"),
        f"{recalling_firm} recalls {product_description}" if recalling_firm and product_description else None,
        product_description,
    )

    hazard_text = first_text(
        classification,
        status,
        reason,
    )

    reason_parts = [
        reason,
        f"Classification: {classification}" if classification else None,
        f"Status: {status}" if status else None,
        f"Distribution: {distribution}" if distribution else None,
        f"Quantity: {product_quantity}" if product_quantity else None,
    ]

    remedy_parts = [
        first_text(record.get("remedy")),
        f"Firm notification: {notification}" if notification else None,
        f"Termination date: {termination_date}" if termination_date else None,
        f"Recall type: {voluntary_mandated}" if voluntary_mandated else None,
        f"Distribution: {distribution}" if distribution else None,
    ]

    affected_lots = [
        value
        for value in [code_info, more_code_info, product_quantity, distribution, status]
        if value
    ]

    return NormalizedSafetyRecord(
        source_name=source_name,
        source_type=source_type,
        source_url=source_url,
        source_kind="structured_api",
        category=first_text(record.get("category"), "Food recall"),
        product_name=product_description,
        brand_name=first_text(record.get("brand_name")),
        company_name=recalling_firm,
        title=title,
        reason=" ".join(part for part in reason_parts if part) or reason,
        hazard_type=hazard_text,
        remedy=" ".join(part for part in remedy_parts if part) or None,
        published_date=recall_date,
        recall_number=first_text(record.get("recall_number"), record.get("id")),
        affected_models=[],
        affected_lots=affected_lots,
        raw_payload_hash=stable_payload_hash(record),
        retrieved_at=retrieved_at,
        record_url=source_url,
    )