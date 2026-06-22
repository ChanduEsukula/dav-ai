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
from app.sources.registry import CPSC_RECALLS_API

logger = logging.getLogger("medtrek.real_world_safety.cpsc")

REPO_ROOT = Path(__file__).resolve().parents[4]
DAILY_RECORDS_PATH = REPO_ROOT / "data" / "safety_sources" / "cpsc" / "cpsc_daily_products_curated_records.json"
DEMO_RECORDS_PATH = REPO_ROOT / "data" / "safety_sources" / "cpsc" / "cpsc_demo_records.json"


class CPSCRecallsAdapter:
    def __init__(self, timeout_seconds: float = 5.0):
        self.timeout_seconds = timeout_seconds
        self.source = CPSC_RECALLS_API
        self.endpoint = "local:data/safety_sources/cpsc/cpsc_daily_products_curated_records.json"

    async def search(
        self,
        *,
        query: str,
        limit: int,
        request_id: str | None = None,
    ) -> SourceAdapterResult:
        retrieved_at = utc_now_iso()

        try:
            cpsc_records = _load_cpsc_records()
            records: list[NormalizedSafetyRecord] = []

            for demo_record in cpsc_records:
                search_blob = json.dumps(demo_record, ensure_ascii=False).lower()
                query_text = query.lower().strip()
                query_terms = [term for term in query_text.split() if term]

                is_match = query_text in search_blob or all(term in search_blob for term in query_terms)
                if not is_match:
                    continue

                raw_record = demo_record.get("raw_record") or demo_record

                normalized = _normalize_cpsc_record(
                    record=raw_record,
                    retrieved_at=retrieved_at,
                    source_name=self.source["source_name"],
                    source_url=first_text(demo_record.get("source_url"), raw_record.get("URL"), self.endpoint),
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
                    "mode": "local_curated_official_snapshot",
                    "path": str(DAILY_RECORDS_PATH.relative_to(REPO_ROOT)),
                    "fallback_path": str(DEMO_RECORDS_PATH.relative_to(REPO_ROOT)),
                    "records_loaded": len(cpsc_records),
                    "query": query,
                },
                upstream_status="success" if records else "empty",
            )

        except FileNotFoundError as exc:
            message = f"CPSC curated snapshot file not found: {DAILY_RECORDS_PATH}"
            logger.warning(
                "cpsc_curated_snapshot_missing",
                extra={
                    "event": "cpsc_curated_snapshot_missing",
                    "request_id": request_id,
                    "source_id": self.source["source_id"],
                    "query": query,
                },
            )
            raise SafetySourceAdapterError(message, error_type="missing_snapshot") from exc
        except Exception as exc:
            logger.exception(
                "cpsc_curated_snapshot_search_failed",
                extra={
                    "event": "cpsc_curated_snapshot_search_failed",
                    "request_id": request_id,
                    "source_id": self.source["source_id"],
                    "query": query,
                },
            )
            raise SafetySourceAdapterError(str(exc), error_type="adapter_error") from exc


def _load_cpsc_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    for path in (DAILY_RECORDS_PATH, DEMO_RECORDS_PATH):
        if not path.exists():
            continue

        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)

        if isinstance(payload, list):
            records.extend(item for item in payload if isinstance(item, dict))

    if not records:
        raise FileNotFoundError(str(DAILY_RECORDS_PATH))

    return records


def _normalize_cpsc_record(
    *,
    record: dict[str, Any],
    retrieved_at: str,
    source_name: str,
    source_url: str,
) -> NormalizedSafetyRecord:
    products = record.get("Products") or record.get("products") or []
    hazards = record.get("Hazards") or record.get("hazards") or []
    remedies = record.get("Remedies") or record.get("remedies") or []
    manufacturers = record.get("Manufacturers") or record.get("manufacturers") or []
    importers = record.get("Importers") or record.get("importers") or []

    product_names = list_text(products, "Name", "name", "Description", "description")
    model_names = list_text(products, "Model", "model", "ModelNumber", "modelNumber")
    hazard_names = list_text(hazards, "Name", "name", "Hazard", "hazard")
    remedy_names = list_text(remedies, "Name", "name", "Remedy", "remedy")
    manufacturer_names = list_text(manufacturers, "Name", "name")
    importer_names = list_text(importers, "Name", "name")

    title = first_text(record.get("Title"), record.get("title"))
    description = first_text(record.get("Description"), record.get("description"))
    product_name = first_text("; ".join(product_names), description, title)
    company_name = first_text(
        "; ".join(manufacturer_names),
        "; ".join(importer_names),
        record.get("Manufacturer"),
        record.get("manufacturer"),
    )

    return NormalizedSafetyRecord(
        source_name=source_name,
        source_type="local official snapshot",
        source_url=source_url,
        source_kind="structured_api",
        category=first_text(record.get("ProductType"), record.get("Category"), "Consumer product"),
        product_name=product_name,
        brand_name=first_text(record.get("Brand"), record.get("brand")),
        company_name=company_name,
        title=title,
        reason=description,
        hazard_type=first_text("; ".join(hazard_names)),
        remedy=first_text("; ".join(remedy_names), record.get("Remedy")),
        published_date=first_text(record.get("RecallDate"), record.get("recallDate")),
        recall_number=first_text(record.get("RecallNumber"), record.get("recallNumber")),
        affected_models=model_names,
        affected_lots=[],
        raw_payload_hash=stable_payload_hash(record),
        retrieved_at=retrieved_at,
        record_url=first_text(record.get("URL"), record.get("url"), source_url),
    )
