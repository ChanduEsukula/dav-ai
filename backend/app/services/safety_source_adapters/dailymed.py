from __future__ import annotations

import json
import logging
import re
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
from app.sources.registry import DAILYMED_SPL_API

logger = logging.getLogger("medtrek.real_world_safety.dailymed")

REPO_ROOT = Path(__file__).resolve().parents[4]
CURATED_RECORDS_PATH = REPO_ROOT / "data" / "safety_sources" / "drug" / "dailymed_curated_records.json"


class DailyMedSPLAdapter:
    def __init__(self):
        self.source = DAILYMED_SPL_API
        self.endpoint = "local:data/safety_sources/drug/dailymed_curated_records.json"

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

                normalized = _normalize_dailymed_record(
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
                    "note": "DailyMed provides official SPL drug label references, not recall enforcement records.",
                },
                upstream_status="success" if records else "empty",
            )

        except FileNotFoundError as exc:
            message = f"DailyMed curated snapshot file not found: {CURATED_RECORDS_PATH}"
            raise SafetySourceAdapterError(message, error_type="missing_snapshot") from exc
        except Exception as exc:
            logger.exception("dailymed_curated_snapshot_search_failed")
            raise SafetySourceAdapterError(str(exc), error_type="adapter_error") from exc


def _load_curated_records() -> list[dict[str, Any]]:
    with CURATED_RECORDS_PATH.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    if not isinstance(payload, list):
        return []

    return [item for item in payload if isinstance(item, dict)]


def _company_from_title(title: str | None) -> str | None:
    if not title:
        return None

    match = re.search(r"\[([^\]]+)\]\s*$", title)
    if match:
        return match.group(1).strip()

    return None


def _normalize_dailymed_record(
    *,
    record: dict[str, Any],
    retrieved_at: str,
    source_name: str,
    source_url: str,
) -> NormalizedSafetyRecord:
    title = first_text(record.get("title"))
    query = first_text(record.get("query"))
    setid = first_text(record.get("setid"))
    published_date = first_text(record.get("published_date"))
    company_name = _company_from_title(title)

    product_name = first_text(title, query)

    return NormalizedSafetyRecord(
        source_name=source_name,
        source_type="local curated official snapshot",
        source_url=source_url,
        source_kind="structured_api",
        category="Drug label",
        product_name=product_name,
        brand_name=query,
        company_name=company_name or "DailyMed / U.S. National Library of Medicine",
        title=first_text(f"DailyMed official label: {title}" if title else None, query),
        reason=first_text(
            f"Official DailyMed SPL label reference. Set ID: {setid}. Published: {published_date}.",
            f"Official DailyMed SPL label reference. Set ID: {setid}.",
        ),
        hazard_type="Official drug label / SPL reference",
        remedy="Review the official DailyMed label for warnings, dosage, active ingredients, and package details.",
        published_date=published_date,
        recall_number=setid,
        affected_models=[],
        affected_lots=[],
        raw_payload_hash=stable_payload_hash(record),
        retrieved_at=retrieved_at,
        record_url=first_text(record.get("source_url"), source_url),
    )
