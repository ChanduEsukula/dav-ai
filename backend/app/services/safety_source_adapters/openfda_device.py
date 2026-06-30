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
from app.sources.registry import OPENFDA_DEVICE_ENFORCEMENT

logger = logging.getLogger("dav_ai.real_world_safety.openfda_device")

REPO_ROOT = Path(__file__).resolve().parents[4]
CURATED_RECORDS_PATH = REPO_ROOT / "data" / "safety_sources" / "device" / "openfda_device_enforcement_curated_records.json"


class OpenFDADeviceEnforcementAdapter:
    def __init__(self):
        self.source = OPENFDA_DEVICE_ENFORCEMENT
        self.endpoint = "local:data/safety_sources/device/openfda_device_enforcement_curated_records.json"

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

                normalized = _normalize_device_record(
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
                    "endpoint": self.source["endpoint"],
                },
                upstream_status="success" if records else "empty",
            )

        except FileNotFoundError as exc:
            message = f"openFDA Device Enforcement curated snapshot file not found: {CURATED_RECORDS_PATH}"
            raise SafetySourceAdapterError(message, error_type="missing_snapshot") from exc
        except Exception as exc:
            logger.exception("openfda_device_curated_snapshot_search_failed")
            raise SafetySourceAdapterError(str(exc), error_type="adapter_error") from exc


def _load_curated_records() -> list[dict[str, Any]]:
    with CURATED_RECORDS_PATH.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    if not isinstance(payload, list):
        return []

    return [item for item in payload if isinstance(item, dict)]


def _normalize_device_record(
    *,
    record: dict[str, Any],
    retrieved_at: str,
    source_name: str,
    source_url: str,
) -> NormalizedSafetyRecord:
    product_name = first_text(record.get("product_description"))
    firm = first_text(record.get("recalling_firm"))
    reason = first_text(record.get("reason_for_recall"))
    recall_number = first_text(record.get("recall_number"))
    status = first_text(record.get("status"))
    classification = first_text(record.get("classification"))
    event_id = first_text(record.get("event_id"))
    code_info = first_text(record.get("code_info"))
    more_code_info = first_text(record.get("more_code_info"))
    distribution = first_text(record.get("distribution_pattern"))
    product_quantity = first_text(record.get("product_quantity"))
    notification = first_text(record.get("initial_firm_notification"))
    voluntary_mandated = first_text(record.get("voluntary_mandated"))

    title = first_text(
        f"{firm} recalls {product_name}" if firm and product_name else None,
        product_name,
        recall_number,
    )

    reason_parts = [
        reason,
        f"Classification: {classification}" if classification else None,
        f"Status: {status}" if status else None,
        f"Distribution: {distribution}" if distribution else None,
        f"Quantity: {product_quantity}" if product_quantity else None,
    ]

    remedy = first_text(
        code_info,
        more_code_info,
        distribution,
        f"Firm notification: {notification}" if notification else None,
        f"Recall type: {voluntary_mandated}" if voluntary_mandated else None,
        "Review FDA device enforcement details for affected products, lots, and firm instructions.",
    )

    return NormalizedSafetyRecord(
        source_name=source_name,
        source_type="local curated official snapshot",
        source_url=source_url,
        source_kind="structured_api",
        category="Medical device recall",
        product_name=product_name,
        brand_name=None,
        company_name=firm,
        title=title,
        reason=" ".join(part for part in reason_parts if part) or reason,
        hazard_type=first_text(classification, "Device enforcement recall"),
        remedy=remedy,
        published_date=first_text(record.get("recall_initiation_date"), record.get("report_date")),
        recall_number=recall_number,
        affected_models=[],
        affected_lots=[
            value
            for value in [
                code_info,
                more_code_info,
                product_quantity,
                distribution,
                first_text(record.get("product_code")),
                first_text(record.get("product_type")),
                first_text(record.get("k_numbers")),
                status,
                event_id,
            ]
            if value
        ],
        raw_payload_hash=stable_payload_hash(record),
        retrieved_at=retrieved_at,
        record_url=source_url,
    )
