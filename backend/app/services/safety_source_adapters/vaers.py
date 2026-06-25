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
from app.sources.registry import CDC_VAERS

logger = logging.getLogger("dav_ai.real_world_safety.vaers")

REPO_ROOT = Path(__file__).resolve().parents[4]
CURATED_RECORDS_PATH = REPO_ROOT / "data" / "safety_sources" / "vaccine" / "vaers_curated_records.json"


class VAERSVaccineSignalAdapter:
    def __init__(self):
        self.source = CDC_VAERS
        self.endpoint = "local:data/safety_sources/vaccine/vaers_curated_records.json"

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

                normalized = _normalize_vaers_record(
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
                    "note": "VAERS reports are public adverse-event reports and do not prove a vaccine caused an event.",
                },
                upstream_status="success" if records else "empty",
            )

        except FileNotFoundError as exc:
            message = f"VAERS curated snapshot file not found: {CURATED_RECORDS_PATH}"
            raise SafetySourceAdapterError(message, error_type="missing_snapshot") from exc
        except Exception as exc:
            logger.exception("vaers_curated_snapshot_search_failed")
            raise SafetySourceAdapterError(str(exc), error_type="adapter_error") from exc


def _load_curated_records() -> list[dict[str, Any]]:
    with CURATED_RECORDS_PATH.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    if not isinstance(payload, list):
        return []

    return [item for item in payload if isinstance(item, dict)]


def _normalize_vaers_record(
    *,
    record: dict[str, Any],
    retrieved_at: str,
    source_name: str,
    source_url: str,
) -> NormalizedSafetyRecord:
    vaccine_name = first_text(record.get("vaccine_name"), record.get("vaccine_type"))
    manufacturer = first_text(record.get("manufacturer"))
    vaers_id = first_text(record.get("vaers_id"))
    report_date = first_text(record.get("report_date"))
    outcome = first_text(record.get("outcome"))
    serious = record.get("serious")
    narrative = first_text(record.get("narrative"))
    symptoms = record.get("symptoms") or []
    symptom_text = "; ".join(str(symptom) for symptom in symptoms) if isinstance(symptoms, list) else first_text(symptoms)
    demographic_parts = [
        f"Age: {record.get('age_years')}" if record.get("age_years") is not None else None,
        f"Sex: {record.get('sex')}" if record.get("sex") else None,
        f"State: {record.get('state')}" if record.get("state") else None,
    ]

    reason_parts = [
        "VAERS public adverse-event report signal; this is not a recall and does not prove causation.",
        f"Reported vaccine: {vaccine_name}" if vaccine_name else None,
        f"Reported symptoms: {symptom_text}" if symptom_text else None,
        f"Outcome: {outcome}" if outcome else None,
        f"Serious report: {serious}" if serious is not None else None,
        " ".join(part for part in demographic_parts if part) or None,
        narrative,
    ]

    return NormalizedSafetyRecord(
        source_name=source_name,
        source_type="local curated official snapshot",
        source_url=source_url,
        source_kind="structured_api",
        category="Vaccine adverse-event signal report",
        product_name=vaccine_name,
        brand_name=None,
        company_name=manufacturer,
        title=first_text(
            f"VAERS signal report: {vaccine_name}" if vaccine_name else None,
            vaers_id,
        ),
        reason=" ".join(part for part in reason_parts if part),
        hazard_type="Reported adverse-event signal, not proof of causation",
        remedy="VAERS reports are public signal reports only. Do not use them as proof that a vaccine caused an event; review CDC/FDA context and contact a qualified healthcare professional for medical decisions.",
        published_date=report_date,
        recall_number=vaers_id,
        affected_models=[value for value in [first_text(record.get("vaccine_type")), manufacturer] if value],
        affected_lots=[value for value in [symptom_text, outcome, first_text(record.get("state"))] if value],
        raw_payload_hash=stable_payload_hash(record),
        retrieved_at=retrieved_at,
        record_url=source_url,
    )
