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
from app.sources.registry import OPENFDA_NDC_DIRECTORY

logger = logging.getLogger("dav_ai.real_world_safety.openfda_ndc")

REPO_ROOT = Path(__file__).resolve().parents[4]
CURATED_RECORDS_PATH = REPO_ROOT / "data" / "safety_sources" / "drug" / "openfda_ndc_curated_records.json"


class OpenFDANDCDirectoryAdapter:
    def __init__(self):
        self.source = OPENFDA_NDC_DIRECTORY
        self.endpoint = "local:data/safety_sources/drug/openfda_ndc_curated_records.json"

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

                normalized = _normalize_openfda_ndc_record(
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
                    "note": "openFDA NDC Directory provides official drug listing/reference records, not recall enforcement records.",
                },
                upstream_status="success" if records else "empty",
            )

        except FileNotFoundError as exc:
            message = f"openFDA NDC curated snapshot file not found: {CURATED_RECORDS_PATH}"
            raise SafetySourceAdapterError(message, error_type="missing_snapshot") from exc
        except Exception as exc:
            logger.exception("openfda_ndc_curated_snapshot_search_failed")
            raise SafetySourceAdapterError(str(exc), error_type="adapter_error") from exc


def _load_curated_records() -> list[dict[str, Any]]:
    with CURATED_RECORDS_PATH.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    if not isinstance(payload, list):
        return []

    return [item for item in payload if isinstance(item, dict)]


def _normalize_openfda_ndc_record(
    *,
    record: dict[str, Any],
    retrieved_at: str,
    source_name: str,
    source_url: str,
) -> NormalizedSafetyRecord:
    brand_name = first_text(record.get("brand_name"), record.get("brand_name_base"))
    generic_name = first_text(record.get("generic_name"))
    labeler = first_text(record.get("labeler_name"))
    product_ndc = first_text(record.get("product_ndc"))
    product_id = first_text(record.get("product_id"))
    dosage_form = first_text(record.get("dosage_form"))
    product_type = first_text(record.get("product_type"))
    marketing_category = first_text(record.get("marketing_category"))
    listing_expiration_date = first_text(record.get("listing_expiration_date"))
    routes = record.get("route") or []
    route_text = first_text("; ".join(str(route) for route in routes)) if isinstance(routes, list) else first_text(routes)

    active_ingredients = record.get("active_ingredients") or []
    packaging = record.get("packaging") or []

    ingredient_names = list_text(active_ingredients, "name", "Name")
    ingredient_strengths = list_text(active_ingredients, "strength", "Strength")
    package_ndcs = list_text(packaging, "package_ndc", "packageNdc")
    package_descriptions = list_text(packaging, "description", "Description")

    ingredient_text = first_text(
        "; ".join(
            " ".join(part for part in [name, strength] if part)
            for name, strength in zip(ingredient_names, ingredient_strengths, strict=False)
        ),
        "; ".join(ingredient_names),
    )
    package_text = first_text("; ".join(package_ndcs), "; ".join(package_descriptions))

    reason_parts = [
        "Official openFDA NDC Directory drug listing/reference record.",
        f"Generic name: {generic_name}" if generic_name else None,
        f"Active ingredient: {ingredient_text}" if ingredient_text else None,
        f"Dosage form: {dosage_form}" if dosage_form else None,
        f"Route: {route_text}" if route_text else None,
        f"Marketing category: {marketing_category}" if marketing_category else None,
        f"Product type: {product_type}" if product_type else None,
        f"Listing expiration: {listing_expiration_date}" if listing_expiration_date else None,
    ]

    return NormalizedSafetyRecord(
        source_name=source_name,
        source_type="local curated official snapshot",
        source_url=source_url,
        source_kind="structured_api",
        category="Drug reference / NDC directory",
        product_name=first_text(brand_name, generic_name, record.get("_dav_query")),
        brand_name=brand_name,
        company_name=labeler or "FDA / openFDA NDC Directory",
        title=first_text(
            f"openFDA NDC listing: {brand_name} ({generic_name})" if brand_name and generic_name else None,
            f"openFDA NDC listing: {brand_name}" if brand_name else None,
            f"openFDA NDC listing: {generic_name}" if generic_name else None,
        ),
        reason=" ".join(part for part in reason_parts if part),
        hazard_type="Reference record, not a recall",
        remedy="Use this record to identify the drug product, NDC, active ingredient, dosage form, route, labeler, and package listing before comparing against recall/enforcement sources.",
        published_date=first_text(record.get("marketing_start_date")),
        recall_number=first_text(product_ndc, product_id),
        affected_models=[
            value
            for value in [product_ndc, product_id, dosage_form, route_text, marketing_category]
            if value
        ],
        affected_lots=[
            value
            for value in [package_text, ingredient_text, listing_expiration_date]
            if value
        ][:5],
        raw_payload_hash=stable_payload_hash(record),
        retrieved_at=retrieved_at,
        record_url=source_url,
    )
