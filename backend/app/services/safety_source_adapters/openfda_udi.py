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
    list_text,
    record_matches_query,
    stable_payload_hash,
    utc_now_iso,
)
from app.sources.registry import OPENFDA_UDI_DIRECTORY

logger = logging.getLogger("dav_ai.real_world_safety.openfda_udi")

REPO_ROOT = Path(__file__).resolve().parents[4]
CURATED_RECORDS_PATH = REPO_ROOT / "data" / "safety_sources" / "device" / "openfda_udi_curated_records.json"


class OpenFDAUDIDirectoryAdapter:
    def __init__(self):
        self.source = OPENFDA_UDI_DIRECTORY
        self.endpoint = "local:data/safety_sources/device/openfda_udi_curated_records.json"

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

                normalized = _normalize_openfda_udi_record(
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
                    "note": "openFDA UDI Directory provides medical-device identity/reference records, not recalls or proof of device safety.",
                },
                upstream_status="success" if records else "empty",
            )

        except FileNotFoundError as exc:
            message = f"openFDA UDI curated snapshot file not found: {CURATED_RECORDS_PATH}"
            raise SafetySourceAdapterError(message, error_type="missing_snapshot") from exc
        except Exception as exc:
            logger.exception("openfda_udi_curated_snapshot_search_failed")
            raise SafetySourceAdapterError(str(exc), error_type="adapter_error") from exc


def _load_curated_records() -> list[dict[str, Any]]:
    with CURATED_RECORDS_PATH.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    if not isinstance(payload, list):
        return []

    return [item for item in payload if isinstance(item, dict)]


def _identifier_values(record: dict[str, Any]) -> list[str]:
    identifiers = record.get("identifiers") or []
    values: list[str] = []

    if isinstance(identifiers, list):
        for item in identifiers:
            if isinstance(item, dict):
                value = first_text(item.get("id"), item.get("device_identifier"))
                if value:
                    values.append(value)

    return values


def _gmdn_text(record: dict[str, Any]) -> str | None:
    gmdn_terms = record.get("gmdn_terms") or []
    if not isinstance(gmdn_terms, list):
        return None

    names = list_text(gmdn_terms, "name")
    definitions = list_text(gmdn_terms, "definition")
    return first_text(
        "; ".join(
            " - ".join(part for part in [name, definition] if part)
            for name, definition in zip(names, definitions, strict=False)
        ),
        "; ".join(names),
    )


def _normalize_openfda_udi_record(
    *,
    record: dict[str, Any],
    retrieved_at: str,
    source_name: str,
    source_url: str,
) -> NormalizedSafetyRecord:
    brand_name = first_text(record.get("brand_name"), record.get("device_name"))
    model_number = first_text(record.get("version_or_model_number"), record.get("model_number"))
    company_name = first_text(record.get("company_name"), record.get("labeler_duns_number"))
    description = first_text(record.get("device_description"), record.get("description"))
    commercial_status = first_text(record.get("commercial_distribution_status"))
    package_count = first_text(record.get("device_count_in_base_package"))
    public_key = first_text(record.get("public_device_record_key"))
    product_codes = record.get("product_codes") or []
    product_code_text = first_text("; ".join(str(code) for code in product_codes)) if isinstance(product_codes, list) else first_text(product_codes)
    udi_values = _identifier_values(record)
    primary_di = first_text(*udi_values)
    gmdn_text = _gmdn_text(record)

    reason_parts = [
        "Official openFDA UDI Directory medical-device identity/reference record.",
        f"Device description: {description}" if description else None,
        f"GMDN: {gmdn_text}" if gmdn_text else None,
        f"Commercial distribution status: {commercial_status}" if commercial_status else None,
        f"Product code: {product_code_text}" if product_code_text else None,
        f"Base package count: {package_count}" if package_count else None,
    ]

    return NormalizedSafetyRecord(
        source_name=source_name,
        source_type="local curated official snapshot",
        source_url=source_url,
        source_kind="structured_api",
        category="Medical device reference / UDI directory",
        product_name=first_text(brand_name, description, public_key),
        brand_name=brand_name,
        company_name=company_name or "FDA / openFDA UDI Directory",
        title=first_text(
            f"openFDA UDI listing: {brand_name}" if brand_name else None,
            f"openFDA UDI listing: {description}" if description else None,
            public_key,
        ),
        reason=" ".join(part for part in reason_parts if part),
        hazard_type="Reference record, not a recall",
        remedy="Use this UDI/device identity record to verify the exact device, model, manufacturer, GMDN term, and device identifier before comparing against recall or adverse-event sources.",
        published_date=first_text(record.get("publish_date"), record.get("public_version_date")),
        recall_number=first_text(primary_di, public_key),
        affected_models=[
            value
            for value in [model_number, brand_name, product_code_text, gmdn_text]
            if value
        ],
        affected_lots=[
            value
            for value in [primary_di, *udi_values[1:], commercial_status, package_count]
            if value
        ][:6],
        raw_payload_hash=stable_payload_hash(record),
        retrieved_at=retrieved_at,
        record_url=source_url,
    )
