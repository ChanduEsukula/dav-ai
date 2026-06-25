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
from app.sources.registry import CDC_FOODBORNE_OUTBREAKS

logger = logging.getLogger("dav_ai.real_world_safety.cdc_foodborne_outbreaks")

REPO_ROOT = Path(__file__).resolve().parents[4]
CURATED_RECORDS_PATH = REPO_ROOT / "data" / "safety_sources" / "food" / "cdc_foodborne_outbreaks_curated_records.json"


class CDCFoodborneOutbreaksAdapter:
    def __init__(self):
        self.source = CDC_FOODBORNE_OUTBREAKS
        self.endpoint = "local:data/safety_sources/food/cdc_foodborne_outbreaks_curated_records.json"

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

                normalized = _normalize_outbreak_record(
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
                    "note": "Foodborne outbreak investigation records provide public-health context and are not automatically formal recalls or proof that a specific product caused illness.",
                },
                upstream_status="success" if records else "empty",
            )

        except FileNotFoundError as exc:
            message = f"CDC foodborne outbreaks curated snapshot file not found: {CURATED_RECORDS_PATH}"
            raise SafetySourceAdapterError(message, error_type="missing_snapshot") from exc
        except Exception as exc:
            logger.exception("cdc_foodborne_outbreaks_curated_snapshot_search_failed")
            raise SafetySourceAdapterError(str(exc), error_type="adapter_error") from exc


def _load_curated_records() -> list[dict[str, Any]]:
    with CURATED_RECORDS_PATH.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    if not isinstance(payload, list):
        return []

    return [item for item in payload if isinstance(item, dict)]


def _list_text(value: Any) -> str | None:
    if isinstance(value, list):
        return "; ".join(str(item) for item in value if item)
    return first_text(value)


def _normalize_outbreak_record(
    *,
    record: dict[str, Any],
    retrieved_at: str,
    source_name: str,
    source_url: str,
) -> NormalizedSafetyRecord:
    title = first_text(record.get("title"))
    investigation_id = first_text(record.get("investigation_id"))
    pathogen = first_text(record.get("pathogen"))
    food_vehicle = first_text(record.get("food_vehicle"))
    agency = first_text(record.get("agency"))
    status = first_text(record.get("status"))
    states = _list_text(record.get("states"))
    summary = first_text(record.get("summary"))
    source_record_url = first_text(record.get("source_url"), source_url)

    illness_count = record.get("illness_count")
    hospitalization_count = record.get("hospitalization_count")
    death_count = record.get("death_count")

    reason_parts = [
        "Public foodborne outbreak investigation context. This is not automatically a formal recall and does not prove that a specific product caused illness.",
        f"Pathogen: {pathogen}" if pathogen else None,
        f"Food vehicle: {food_vehicle}" if food_vehicle else None,
        f"Status: {status}" if status else None,
        f"States: {states}" if states else None,
        f"Illnesses: {illness_count}" if illness_count is not None else None,
        f"Hospitalizations: {hospitalization_count}" if hospitalization_count is not None else None,
        f"Deaths: {death_count}" if death_count is not None else None,
        summary,
    ]

    return NormalizedSafetyRecord(
        source_name=source_name,
        source_type="local curated official snapshot",
        source_url=source_url,
        source_kind="structured_api",
        category="Foodborne outbreak / investigation context",
        product_name=first_text(food_vehicle, pathogen),
        brand_name=None,
        company_name=first_text(agency, "CDC/FDA public health investigation"),
        title=title,
        reason=" ".join(part for part in reason_parts if part),
        hazard_type=first_text(pathogen, "Foodborne outbreak investigation context"),
        remedy="Use this as public-health investigation context only. Check official CDC/FDA pages and recall sources before assuming a specific product is recalled or caused illness.",
        published_date=first_text(record.get("last_update_date"), record.get("investigation_start_date")),
        recall_number=investigation_id,
        affected_models=[],
        affected_lots=[value for value in [food_vehicle, pathogen, states, status] if value],
        raw_payload_hash=stable_payload_hash(record),
        retrieved_at=retrieved_at,
        record_url=source_record_url,
    )
