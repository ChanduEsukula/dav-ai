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
from app.sources.registry import OPENFDA_DEVICE_EVENT

logger = logging.getLogger("dav_ai.real_world_safety.openfda_device_event")

REPO_ROOT = Path(__file__).resolve().parents[4]
CURATED_RECORDS_PATH = REPO_ROOT / "data" / "safety_sources" / "device" / "openfda_device_event_curated_records.json"


class OpenFDADeviceEventAdapter:
    def __init__(self):
        self.source = OPENFDA_DEVICE_EVENT
        self.endpoint = "local:data/safety_sources/device/openfda_device_event_curated_records.json"

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

                normalized = _normalize_device_event_record(
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
                    "note": "openFDA Device Event records are adverse-event reports and are not recalls or proof of causation.",
                },
                upstream_status="success" if records else "empty",
            )

        except FileNotFoundError as exc:
            message = f"openFDA Device Event curated snapshot file not found: {CURATED_RECORDS_PATH}"
            raise SafetySourceAdapterError(message, error_type="missing_snapshot") from exc
        except Exception as exc:
            logger.exception("openfda_device_event_curated_snapshot_search_failed")
            raise SafetySourceAdapterError(str(exc), error_type="adapter_error") from exc


def _load_curated_records() -> list[dict[str, Any]]:
    with CURATED_RECORDS_PATH.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    if not isinstance(payload, list):
        return []

    return [item for item in payload if isinstance(item, dict)]


def _first_device(record: dict[str, Any]) -> dict[str, Any]:
    devices = record.get("device") or []
    if devices and isinstance(devices[0], dict):
        return devices[0]
    return {}


def _first_text_summary(record: dict[str, Any]) -> str | None:
    texts = record.get("mdr_text") or []
    for item in texts:
        if isinstance(item, dict):
            value = first_text(item.get("text"))
            if value:
                return value
    return None


def _normalize_device_event_record(
    *,
    record: dict[str, Any],
    retrieved_at: str,
    source_name: str,
    source_url: str,
) -> NormalizedSafetyRecord:
    device = _first_device(record)

    generic_name = first_text(device.get("generic_name"))
    brand_name = first_text(device.get("brand_name"))
    manufacturer = first_text(device.get("manufacturer_d_name"))
    event_type = first_text(record.get("event_type"))
    report_number = first_text(record.get("report_number"))
    mdr_report_key = first_text(record.get("mdr_report_key"))
    text_summary = _first_text_summary(record)

    product_name = first_text(brand_name, generic_name)
    title = first_text(
        f"openFDA device event report: {product_name} ({event_type})" if product_name and event_type else None,
        product_name,
        report_number,
    )

    reason = first_text(
        text_summary,
        f"Device adverse-event report. Event type: {event_type}. Report number: {report_number}.",
    )

    return NormalizedSafetyRecord(
        source_name=source_name,
        source_type="local curated official snapshot",
        source_url=source_url,
        source_kind="structured_api",
        category="Medical device adverse-event report",
        product_name=product_name,
        brand_name=brand_name,
        company_name=manufacturer,
        title=title,
        reason=reason,
        hazard_type=first_text(event_type, "Device adverse-event signal"),
        remedy="Adverse-event reports are signals, not recalls or proof of causation. Review official FDA context before acting.",
        published_date=first_text(record.get("date_received"), record.get("date_report")),
        recall_number=first_text(report_number, mdr_report_key),
        affected_models=[
            value
            for value in [
                first_text(device.get("model_number")),
                first_text(device.get("catalog_number")),
            ]
            if value
        ],
        affected_lots=[
            value
            for value in [
                first_text(device.get("lot_number")),
                first_text(device.get("device_report_product_code")),
                mdr_report_key,
            ]
            if value
        ],
        raw_payload_hash=stable_payload_hash(record),
        retrieved_at=retrieved_at,
        record_url=source_url,
    )
