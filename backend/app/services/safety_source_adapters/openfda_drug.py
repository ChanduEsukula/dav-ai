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
from app.sources.registry import OPENFDA_DRUG_ENFORCEMENT

logger = logging.getLogger("dav_ai.real_world_safety.openfda_drug")

REPO_ROOT = Path(__file__).resolve().parents[4]
CURATED_RECORDS_PATH = REPO_ROOT / "data" / "safety_sources" / "drug" / "openfda_drug_curated_records.json"


class OpenFDADrugEnforcementAdapter:
    def __init__(self):
        self.source = OPENFDA_DRUG_ENFORCEMENT
        self.endpoint = "local:data/safety_sources/drug/openfda_drug_curated_records.json"

    async def search(
        self,
        *,
        query: str,
        limit: int,
        request_id: str | None = None,
    ) -> SourceAdapterResult:
        retrieved_at = utc_now_iso()

        try:
            curated_records = _load_curated_records()
            records: list[NormalizedSafetyRecord] = []

            query_text = query.lower().strip()
            query_terms = [term for term in query_text.split() if term]

            for source_record in curated_records:
                search_blob = json.dumps(source_record, ensure_ascii=False).lower()
                is_match = query_text in search_blob or all(term in search_blob for term in query_terms)

                if not is_match:
                    continue

                normalized = _normalize_openfda_drug_record(
                    record=source_record,
                    retrieved_at=retrieved_at,
                    source_name=self.source["source_name"],
                    source_url=self.source["endpoint"],
                )

                if record_matches_query(normalized, query) or is_match:
                    records.append(normalized)

            records = dedupe_records(records)[:limit]

            return SourceAdapterResult(
                source_id=self.source["source_id"],
                source_name=self.source["source_name"],
                source_type="local curated official snapshot",
                source_url=self.endpoint,
                source_kind="structured_api",
                retrieved_at=retrieved_at,
                records=records,
                raw_payload={
                    "mode": "local_curated_official_snapshot",
                    "path": str(CURATED_RECORDS_PATH.relative_to(REPO_ROOT)),
                    "records_loaded": len(curated_records),
                    "query": query,
                },
                upstream_status="success" if records else "empty",
            )

        except FileNotFoundError as exc:
            message = f"openFDA drug curated snapshot file not found: {CURATED_RECORDS_PATH}"
            raise SafetySourceAdapterError(message, error_type="missing_snapshot") from exc
        except Exception as exc:
            logger.exception("openfda_drug_curated_snapshot_search_failed")
            raise SafetySourceAdapterError(str(exc), error_type="adapter_error") from exc


def _load_curated_records() -> list[dict[str, Any]]:
    with CURATED_RECORDS_PATH.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    if not isinstance(payload, list):
        return []

    return [item for item in payload if isinstance(item, dict)]


def _normalize_openfda_drug_record(
    *,
    record: dict[str, Any],
    retrieved_at: str,
    source_name: str,
    source_url: str,
) -> NormalizedSafetyRecord:
    product_description = first_text(record.get("product_description"))
    recalling_firm = first_text(record.get("recalling_firm"))
    reason = first_text(record.get("reason_for_recall"))
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

    reason_parts = [
        reason,
        f"Classification: {classification}" if classification else None,
        f"Status: {status}" if status else None,
        f"Distribution: {distribution}" if distribution else None,
        f"Quantity: {product_quantity}" if product_quantity else None,
    ]

    remedy_parts = [
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
        source_type="local curated official snapshot",
        source_url=source_url,
        source_kind="structured_api",
        category="Drug recall",
        product_name=product_description,
        brand_name=None,
        company_name=recalling_firm,
        title=title,
        reason=" ".join(part for part in reason_parts if part) or reason,
        hazard_type=first_text(classification, status, reason),
        remedy=" ".join(part for part in remedy_parts if part) or distribution,
        published_date=recall_date,
        recall_number=first_text(record.get("recall_number")),
        affected_models=[],
        affected_lots=affected_lots,
        raw_payload_hash=stable_payload_hash(record),
        retrieved_at=retrieved_at,
        record_url=source_url,
    )
