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
from app.sources.registry import USDA_FSIS_RECALL

logger = logging.getLogger("medtrek.real_world_safety.usda_fsis")

REPO_ROOT = Path(__file__).resolve().parents[4]
DEMO_RECORDS_PATH = REPO_ROOT / "data" / "safety_sources" / "food" / "usda_fsis_demo_records.json"


class USDAFSISRecallAdapter:
    def __init__(self):
        self.source = USDA_FSIS_RECALL
        self.endpoint = "local:data/safety_sources/food/usda_fsis_demo_records.json"

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

                normalized = _normalize_fsis_record(
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
                    "mode": "local_demo_snapshot",
                    "path": str(DEMO_RECORDS_PATH.relative_to(REPO_ROOT)),
                    "records_loaded": len(demo_records),
                    "query": query,
                },
                upstream_status="success" if records else "empty",
            )

        except FileNotFoundError as exc:
            message = f"USDA FSIS demo snapshot file not found: {DEMO_RECORDS_PATH}"
            logger.warning(
                "usda_fsis_demo_snapshot_missing",
                extra={
                    "event": "usda_fsis_demo_snapshot_missing",
                    "request_id": request_id,
                    "source_id": self.source["source_id"],
                    "query": query,
                },
            )
            raise SafetySourceAdapterError(message, error_type="missing_snapshot") from exc
        except Exception as exc:
            logger.exception(
                "usda_fsis_demo_snapshot_search_failed",
                extra={
                    "event": "usda_fsis_demo_snapshot_search_failed",
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


def _normalize_fsis_record(
    *,
    record: dict[str, Any],
    retrieved_at: str,
    source_name: str,
    source_url: str,
) -> NormalizedSafetyRecord:
    product_name = first_text(record.get("product_name"), record.get("product"))
    recalling_firm = first_text(record.get("recalling_firm"), record.get("firm"))
    reason = first_text(record.get("reason_for_recall"), record.get("reason"))
    classification = first_text(record.get("classification"))
    recall_date = first_text(record.get("recall_date"), record.get("published_date"))
    affected_states = record.get("affected_states") or []

    if not isinstance(affected_states, list):
        affected_states = [str(affected_states)]

    state_text = ", ".join(str(state) for state in affected_states if state)

    title = first_text(
        record.get("title"),
        f"{recalling_firm} recalls {product_name}" if recalling_firm and product_name else None,
        product_name,
    )

    return NormalizedSafetyRecord(
        source_name=source_name,
        source_type="local official snapshot",
        source_url=source_url,
        source_kind="structured_api",
        category=first_text(record.get("category"), "Meat/poultry/egg recall"),
        product_name=product_name,
        brand_name=first_text(record.get("brand_name")),
        company_name=recalling_firm,
        title=title,
        reason=reason,
        hazard_type=first_text(classification, reason),
        remedy=first_text(record.get("remedy"), f"Affected states: {state_text}" if state_text else None),
        published_date=recall_date,
        recall_number=first_text(record.get("recall_number"), record.get("id")),
        affected_models=[],
        affected_lots=[value for value in [record.get("code_info"), state_text] if value],
        raw_payload_hash=stable_payload_hash(record),
        retrieved_at=retrieved_at,
        record_url=source_url,
    )
