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
from app.sources.registry import RXNORM_RXNAV_API

logger = logging.getLogger("dav_ai.real_world_safety.rxnorm")

REPO_ROOT = Path(__file__).resolve().parents[4]
CURATED_RECORDS_PATH = REPO_ROOT / "data" / "safety_sources" / "drug" / "rxnorm_curated_records.json"


class RxNormDrugReferenceAdapter:
    def __init__(self):
        self.source = RXNORM_RXNAV_API
        self.endpoint = "local:data/safety_sources/drug/rxnorm_curated_records.json"

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

                normalized = _normalize_rxnorm_record(
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
                    "note": "RxNorm is a drug reference and name-normalization source, not a recall source.",
                },
                upstream_status="success" if records else "empty",
            )

        except FileNotFoundError as exc:
            message = f"RxNorm curated snapshot file not found: {CURATED_RECORDS_PATH}"
            raise SafetySourceAdapterError(message, error_type="missing_snapshot") from exc
        except Exception as exc:
            logger.exception("rxnorm_curated_snapshot_search_failed")
            raise SafetySourceAdapterError(str(exc), error_type="adapter_error") from exc


def _load_curated_records() -> list[dict[str, Any]]:
    with CURATED_RECORDS_PATH.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    if not isinstance(payload, list):
        return []

    return [item for item in payload if isinstance(item, dict)]


def _normalize_rxnorm_record(
    *,
    record: dict[str, Any],
    retrieved_at: str,
    source_name: str,
    source_url: str,
) -> NormalizedSafetyRecord:
    drug_name = first_text(record.get("name"), record.get("query"))
    rxcui = first_text(record.get("rxcui"))
    tty = first_text(record.get("tty"))
    synonym = first_text(record.get("synonym"))

    title = first_text(
        f"RxNorm drug reference: {drug_name} ({tty}, RXCUI {rxcui})" if drug_name and rxcui else None,
        drug_name,
    )

    reason = first_text(
        f"RxNorm normalized drug concept. Term type: {tty}. RXCUI: {rxcui}.",
        synonym,
    )

    return NormalizedSafetyRecord(
        source_name=source_name,
        source_type="local curated official snapshot",
        source_url=source_url,
        source_kind="structured_api",
        category="Drug reference",
        product_name=drug_name,
        brand_name=drug_name if tty == "BN" else None,
        company_name="U.S. National Library of Medicine",
        title=title,
        reason=reason,
        hazard_type="Drug reference / name normalization",
        remedy="Use this reference to normalize drug names before checking labels or recalls.",
        published_date=None,
        recall_number=rxcui,
        affected_models=[],
        affected_lots=[value for value in [synonym] if value],
        raw_payload_hash=stable_payload_hash(record),
        retrieved_at=retrieved_at,
        record_url=first_text(record.get("source_url"), source_url),
    )
