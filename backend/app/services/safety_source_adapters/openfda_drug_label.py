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
from app.sources.registry import OPENFDA_DRUG_LABEL

logger = logging.getLogger("dav_ai.real_world_safety.openfda_drug_label")

REPO_ROOT = Path(__file__).resolve().parents[4]
CURATED_RECORDS_PATH = REPO_ROOT / "data" / "safety_sources" / "drug" / "openfda_drug_label_curated_records.json"


class OpenFDADrugLabelAdapter:
    def __init__(self):
        self.source = OPENFDA_DRUG_LABEL
        self.endpoint = "local:data/safety_sources/drug/openfda_drug_label_curated_records.json"

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

                normalized = _normalize_openfda_drug_label_record(
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
                    "note": "openFDA Drug Label provides official label sections, not recall enforcement records.",
                },
                upstream_status="success" if records else "empty",
            )

        except FileNotFoundError as exc:
            message = f"openFDA Drug Label curated snapshot file not found: {CURATED_RECORDS_PATH}"
            raise SafetySourceAdapterError(message, error_type="missing_snapshot") from exc
        except Exception as exc:
            logger.exception("openfda_drug_label_curated_snapshot_search_failed")
            raise SafetySourceAdapterError(str(exc), error_type="adapter_error") from exc


def _load_curated_records() -> list[dict[str, Any]]:
    with CURATED_RECORDS_PATH.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    if not isinstance(payload, list):
        return []

    return [item for item in payload if isinstance(item, dict)]


def _openfda_first(record: dict[str, Any], key: str) -> str | None:
    openfda = record.get("openfda") or {}
    return first_text(openfda.get(key))


def _section(record: dict[str, Any], *keys: str) -> str | None:
    return first_text(*(record.get(key) for key in keys))


def _normalize_openfda_drug_label_record(
    *,
    record: dict[str, Any],
    retrieved_at: str,
    source_name: str,
    source_url: str,
) -> NormalizedSafetyRecord:
    brand_name = _openfda_first(record, "brand_name")
    generic_name = _openfda_first(record, "generic_name")
    manufacturer = _openfda_first(record, "manufacturer_name")

    active_ingredient = _section(record, "active_ingredient", "spl_product_data_elements")
    purpose = _section(record, "purpose", "indications_and_usage")
    warnings = _section(record, "warnings", "boxed_warning")
    dosage = _section(record, "dosage_and_administration", "dosage")
    do_not_use = _section(record, "do_not_use")
    ask_doctor = _section(record, "ask_doctor", "ask_doctor_or_pharmacist")
    stop_use = _section(record, "stop_use")

    safety_sections = [
        f"Active ingredient: {active_ingredient}" if active_ingredient else None,
        f"Purpose/uses: {purpose}" if purpose else None,
        f"Warnings: {warnings}" if warnings else None,
        f"Do not use: {do_not_use}" if do_not_use else None,
        f"Ask doctor/pharmacist: {ask_doctor}" if ask_doctor else None,
        f"Stop use: {stop_use}" if stop_use else None,
        f"Dosage: {dosage}" if dosage else None,
    ]

    reason = " ".join(section for section in safety_sections if section)

    product_name = first_text(brand_name, generic_name, record.get("_dav_query"))

    return NormalizedSafetyRecord(
        source_name=source_name,
        source_type="local curated official snapshot",
        source_url=source_url,
        source_kind="structured_api",
        category="Drug label",
        product_name=product_name,
        brand_name=brand_name,
        company_name=manufacturer or "FDA / openFDA Drug Label",
        title=first_text(
            f"openFDA official drug label: {brand_name} ({generic_name})" if brand_name and generic_name else None,
            f"openFDA official drug label: {product_name}" if product_name else None,
        ),
        reason=reason or "Official openFDA drug label sections for warnings, ingredients, dosage, and usage.",
        hazard_type="Official drug label warnings / directions",
        remedy="Review official label sections for active ingredients, warnings, do-not-use directions, ask-doctor guidance, and dosage.",
        published_date=first_text(record.get("effective_time")),
        recall_number=first_text(record.get("id"), record.get("set_id")),
        affected_models=[],
        affected_lots=[
            value
            for value in [
                active_ingredient,
                do_not_use,
                ask_doctor,
                stop_use,
                dosage,
            ]
            if value
        ][:5],
        raw_payload_hash=stable_payload_hash(record),
        retrieved_at=retrieved_at,
        record_url=source_url,
    )
