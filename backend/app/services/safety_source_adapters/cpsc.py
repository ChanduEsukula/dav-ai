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

logger = logging.getLogger("dav_ai.real_world_safety.cpsc")

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
                source_type="local curated official snapshot",
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
    distributors = record.get("Distributors") or record.get("distributors") or []
    retailers = record.get("Retailers") or record.get("retailers") or []
    product_upcs = record.get("ProductUPCs") or record.get("productUPCs") or []
    remedy_options = record.get("RemedyOptions") or record.get("remedyOptions") or []
    images = record.get("Images") or record.get("images") or []

    product_names = list_text(products, "Name", "name", "Description", "description")
    model_names = list_text(products, "Model", "model", "ModelNumber", "modelNumber")
    unit_counts = list_text(products, "NumberOfUnits", "numberOfUnits")
    upc_values = list_text(product_upcs, "UPC", "upc")
    hazard_names = list_text(hazards, "Name", "name", "Hazard", "hazard")
    remedy_names = list_text(remedies, "Name", "name", "Remedy", "remedy")
    remedy_option_names = list_text(remedy_options, "Option", "option", "Name", "name")
    manufacturer_names = list_text(manufacturers, "Name", "name")
    importer_names = list_text(importers, "Name", "name")
    distributor_names = list_text(distributors, "Name", "name")
    retailer_names = list_text(retailers, "Name", "name")
    image_urls = list_text(images, "URL", "url")

    title = first_text(record.get("Title"), record.get("title"))
    description = first_text(record.get("Description"), record.get("description"))
    product_name = first_text("; ".join(product_names), description, title)
    company_name = first_text(
        "; ".join(manufacturer_names),
        "; ".join(importer_names),
        "; ".join(distributor_names),
        record.get("Manufacturer"),
        record.get("manufacturer"),
    )

    sold_at = first_text(record.get("SoldAtLabel"), record.get("soldAtLabel"), "; ".join(retailer_names))
    hazard_text = first_text("; ".join(hazard_names))
    retailer_text = first_text("; ".join(retailer_names))
    upc_text = first_text("; ".join(upc_values))
    image_text = first_text("; ".join(image_urls))

    reason_parts = [
        description,
        f"Hazard: {hazard_text}" if hazard_text else None,
        f"Sold at: {sold_at}" if sold_at else None,
        f"Retailers: {retailer_text}" if retailer_text and retailer_text != sold_at else None,
        f"UPC: {upc_text}" if upc_text else None,
        f"Image: {image_text}" if image_text else None,
    ]

    remedy_parts = [
        first_text("; ".join(remedy_names), record.get("Remedy")),
        f"Remedy option: {'; '.join(remedy_option_names)}" if remedy_option_names else None,
    ]

    affected_models = [
        value
        for value in [*product_names, *model_names, *unit_counts]
        if value
    ]
    affected_lots = [
        value
        for value in [*upc_values, sold_at, retailer_text]
        if value
    ]

    return NormalizedSafetyRecord(
        source_name=source_name,
        source_type="local curated official snapshot",
        source_url=source_url,
        source_kind="structured_api",
        category=first_text(record.get("ProductType"), record.get("Category"), "Consumer product"),
        product_name=product_name,
        brand_name=first_text(record.get("Brand"), record.get("brand")),
        company_name=company_name,
        title=title,
        reason=" ".join(part for part in reason_parts if part) or description,
        hazard_type=hazard_text,
        remedy=" ".join(part for part in remedy_parts if part) or None,
        published_date=first_text(record.get("RecallDate"), record.get("recallDate")),
        recall_number=first_text(record.get("RecallNumber"), record.get("recallNumber")),
        affected_models=affected_models,
        affected_lots=affected_lots,
        raw_payload_hash=stable_payload_hash(record),
        retrieved_at=retrieved_at,
        record_url=first_text(record.get("URL"), record.get("url"), source_url),
    )
