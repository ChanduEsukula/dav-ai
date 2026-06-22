from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

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

logger = logging.getLogger("medtrek.real_world_safety.openfda_food")

REPO_ROOT = Path(__file__).resolve().parents[4]
DEMO_RECORDS_PATH = REPO_ROOT / "data" / "safety_sources" / "food" / "openfda_food_curated_records.json"


class OpenFDAFoodEnforcementAdapter:
    def __init__(self):
        self.source = OPENFDA_FOOD_ENFORCEMENT
        self.endpoint = "local:data/safety_sources/food/openfda_food_curated_records.json"

    async def search(
        self,
        *,
        query: str,
        limit: int,
        request_id: str | None = None,
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
                    source_url=first_text(demo_record.get("source_url"), self.endpoint),
                )

                if record_matches_query(normalized, query) or is_match:
                    records.append(normalized)

            records = dedupe_records(records)[:limit]

            return SourceAdapterResult(
                source_id=self.source["source_id"],
                source_name=self.source["source_name"],
                source_type="local official snapshot",
                source_url=self.endpoint,
                source_kind="structured_api",
                retrieved_at=retrieved_at,
                records=records,
                raw_payload={
                    "mode": "local_curated_official_snapshot",
                    "path": str(DEMO_RECORDS_PATH.relative_to(REPO_ROOT)),
                    "records_loaded": len(demo_records),
                    "query": query,
                },
                upstream_status="success" if records else "empty",
            )

        except FileNotFoundError as exc:
            message = f"openFDA food demo snapshot file not found: {DEMO_RECORDS_PATH}"
            logger.warning(
                "openfda_food_demo_snapshot_missing",
                extra={
                    "event": "openfda_food_demo_snapshot_missing",
                    "request_id": request_id,
                    "source_id": self.source["source_id"],
                    "query": query,
                },
            )
            raise SafetySourceAdapterError(message, error_type="missing_snapshot") from exc
        except Exception as exc:
            logger.exception(
                "openfda_food_demo_snapshot_search_failed",
                extra={
                    "event": "openfda_food_demo_snapshot_search_failed",
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
) -> NormalizedSafetyRecord:
    product_description = first_text(record.get("product_description"), record.get("product_name"))
    recalling_firm = first_text(record.get("recalling_firm"), record.get("company_name"))
    reason = first_text(record.get("reason_for_recall"), record.get("reason"))
    classification = first_text(record.get("classification"))
    status = first_text(record.get("status"))
    code_info = first_text(record.get("code_info"))
    distribution = first_text(record.get("distribution_pattern"))
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

    return NormalizedSafetyRecord(
        source_name=source_name,
        source_type="local official snapshot",
        source_url=source_url,
        source_kind="structured_api",
        category=first_text(record.get("category"), "Food recall"),
        product_name=product_description,
        brand_name=first_text(record.get("brand_name")),
        company_name=recalling_firm,
        title=title,
        reason=reason,
        hazard_type=hazard_text,
        remedy=first_text(record.get("remedy"), distribution),
        published_date=recall_date,
        recall_number=first_text(record.get("recall_number"), record.get("id")),
        affected_models=[],
        affected_lots=[value for value in [code_info] if value],
        raw_payload_hash=stable_payload_hash(record),
        retrieved_at=retrieved_at,
        record_url=source_url,
    )
