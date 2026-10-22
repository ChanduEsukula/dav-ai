"""Read-only pharmaceutical tools for Dav AI's research agent."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any

from app.db.pharma.release_repository import FrozenPharmaReleaseRepository


STRENGTH_QUERY = re.compile(
    r"^(?P<name>.+?)\s+(?P<amount>(?:\d+(?:\.\d*)?|\.\d+))\s*mg$",
    re.IGNORECASE,
)


def _requested_strength(query: str) -> tuple[str, Decimal | None]:
    match = STRENGTH_QUERY.fullmatch(query.strip())

    if not match:
        return query.strip(), None

    return match.group("name").strip(), Decimal(match.group("amount"))


def _matches_strength(product: dict[str, Any], requested: Decimal) -> bool:
    strength = str(product.get("strength") or "")
    if len(product.get("active_ingredients", [])) != 1 or ";" in strength:
        return False
    match = re.fullmatch(r"\s*(?P<amount>(?:\d+(?:\.\d*)?|\.\d+))\s*mg(?:/1)?\s*", strength, re.IGNORECASE)

    if not match:
        return False

    try:
        return Decimal(match.group("amount")) == requested
    except InvalidOperation:
        return False


def _project_product(product: dict[str, Any]) -> dict[str, Any]:
    return {
        "product_id": product["product_id"],
        "brand_names": product.get("brand_names", []),
        "generic_name": product.get("generic_name"),
        "strength": product.get("strength"),
        "dosage_form": product.get("dosage_form"),
        "formulation_id": product.get("formulation_id"),
        "routes": product.get("routes", []),
        "provenance": product.get("provenance"),
        "product_ndcs": product.get("product_ndcs", []),
        "package_ndcs": product.get("package_ndcs", []),
        "active_ingredients": product.get("active_ingredients", []),
    }


def resolve_drug_product(
    query: str,
    repository: FrozenPharmaReleaseRepository | None = None,
) -> dict[str, Any]:
    """Find actual products without inventing IDs or selecting ambiguous matches."""

    if not isinstance(query, str) or not query.strip():
        return {
            "status": "invalid_query",
            "candidates": [],
        }

    if len(query) > 200:
        return {
            "status": "invalid_query",
            "candidates": [],
        }

    name, requested_strength = _requested_strength(query)
    repo = repository or FrozenPharmaReleaseRepository()

    products = repo.search(name, limit=100)

    search_was_limited = len(products) >= 100

    if requested_strength is not None:
        products = [
            product
            for product in products
            if _matches_strength(product, requested_strength)
        ]

    candidates = [_project_product(product) for product in products]

    if not candidates:
        status = "not_found"
    elif len(candidates) == 1 and not search_was_limited:
        status = "resolved"
    else:
        status = "needs_clarification"

    return {
        "status": status,
        "query": query,
        "candidates": candidates,
        "result_limit": 100,
        "results_may_be_incomplete": search_was_limited,
    }


def search_historical_recalls(
    product_id: str,
    repository: FrozenPharmaReleaseRepository | None = None,
) -> dict[str, Any]:
    """Retrieve historical recall evidence for an exact database product ID."""

    if (
        not isinstance(product_id, str)
        or not product_id.strip()
        or len(product_id) > 300
    ):
        return {"status": "invalid_product_id", "records": []}

    repo = repository or FrozenPharmaReleaseRepository()
    product = repo.find_by_id(product_id)

    if product is None:
        return {"status": "product_not_found", "records": []}

    safety = repo.safety(product_id)
    if safety is None or not isinstance(safety.get("recalls"), dict):
        return {
            "status": "evidence_unavailable",
            "product_id": product_id,
            "records": [],
        }

    recall_data = safety["recalls"]
    records = recall_data.get("records", [])

    if not isinstance(records, list):
        return {
            "status": "evidence_unavailable",
            "product_id": product_id,
            "records": [],
        }

    output = []

    for record in records[:10]:
        if not isinstance(record, dict):
            return {
                "status": "evidence_unavailable",
                "product_id": product_id,
                "records": [],
            }

        output.append({
            key: record.get(key)
            for key in (
                "id",
                "recall_number",
                "classification",
                "reported_status",
                "reason_for_recall",
                "recalling_firm",
                "recall_initiation_date",
                "report_date",
                "lot_information",
                "lot_scope",
                "applicability_class",
                "match_method",
                "matched_value",
                "source_record_id",
                "source_url",
            )
        })

    return {
        "status": "found" if records else "no_linked_recalls",
        "product_id": product_id,
        "product_ndcs": product.get("product_ndcs", []),
        "package_ndcs": product.get("package_ndcs", []),
        "coverage": recall_data.get("coverage"),
        "source_snapshot_date": (recall_data.get("coverage") or {}).get("source_date"),
        "record_count": len(records),
        "returned_count": len(output),
        "results_truncated": len(records) > len(output),
        "records": output,
        "limitation": (
            "These are historical recall records linked to this product. "
            "Lot and package applicability must be evaluated separately. "
            "No linked records does not prove that the product was never recalled."
        ),
    }
