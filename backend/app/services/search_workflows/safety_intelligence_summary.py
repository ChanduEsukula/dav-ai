from __future__ import annotations

from typing import Any

from app.services.safety_source_adapters.base import NormalizedSafetyRecord


RECALL_ENFORCEMENT_SOURCES = {
    "CPSC Recalls API",
    "FDA Recalls, Market Withdrawals & Safety Alerts",
    "openFDA Food Enforcement API",
    "USDA FSIS Recall API",
    "openFDA Drug Enforcement API",
    "openFDA Device Enforcement API",
    "NHTSA Recalls API / datasets",
}

REFERENCE_IDENTITY_SOURCES = {
    "RxNorm/RxNav API",
    "openFDA NDC Directory API",
    "NHTSA vPIC VIN Decoder API",
}

LABEL_REFERENCE_SOURCES = {
    "DailyMed SPL API",
    "openFDA Drug Label API",
}

SIGNAL_SOURCES = {
    "openFDA Device Event API",
    "CDC/VAERS Vaccine Adverse Event Reports",
}

OUTBREAK_CONTEXT_SOURCES = {
    "CDC/FDA Foodborne Outbreak Investigation Context",
}

ROLE_ORDER = [
    "recall_enforcement",
    "reference_identity",
    "label_reference",
    "signal_report",
    "outbreak_context",
    "other",
]


def _source_role(source_name: str) -> str:
    if source_name in RECALL_ENFORCEMENT_SOURCES:
        return "recall_enforcement"
    if source_name in REFERENCE_IDENTITY_SOURCES:
        return "reference_identity"
    if source_name in LABEL_REFERENCE_SOURCES:
        return "label_reference"
    if source_name in SIGNAL_SOURCES:
        return "signal_report"
    if source_name in OUTBREAK_CONTEXT_SOURCES:
        return "outbreak_context"
    return "other"


def _append_unique(values: list[str], value: str | None) -> None:
    if value and value not in values:
        values.append(value)


def _empty_role_map() -> dict[str, list[str]]:
    return {role: [] for role in ROLE_ORDER}


def _infer_query_type(query: str, records: list[NormalizedSafetyRecord]) -> str:
    text = " ".join(
        [
            query,
            *[record.category or "" for record in records],
            *[record.source_name for record in records],
            *[record.product_name or "" for record in records],
            *[record.brand_name or "" for record in records],
            *[record.title or "" for record in records],
        ]
    ).lower()

    # Prefer specific source/category evidence over broad keyword guessing.
    if any(
        term in text
        for term in [
            "drug reference",
            "drug label",
            "ndc",
            "rxnorm",
            "dailymed",
            "tylenol",
            "acetaminophen",
            "ibuprofen",
            "metformin",
            "albuterol",
        ]
    ):
        return "drug"

    if any(
        term in text
        for term in [
            "medical device",
            "glucose meter",
            "insulin pump",
            "cpap",
            "openfda device",
        ]
    ):
        return "medical_device"

    if any(
        term in text
        for term in [
            "vaers",
            "vaccine",
            "vaccination",
            "mmr",
            "influenza vaccine",
            "covid-19 vaccine",
        ]
    ):
        return "vaccine"

    if any(
        term in text
        for term in [
            "food recall",
            "meat/poultry",
            "chicken",
            "beef",
            "poultry",
            "fsis",
            "fda food",
            "salmonella",
            "listeria",
            "outbreak",
            "foodborne",
            "e. coli",
            "ecoli",
        ]
    ):
        return "food"

    if any(
        term in text
        for term in [
            "nhtsa",
            "vin",
            "vehicle recall",
            "honda",
            "toyota",
            "ford",
            "tesla",
            "truck",
        ]
    ):
        return "vehicle"

    if any(
        term in text
        for term in [
            "cpsc",
            "consumer product",
            "scooter",
            "air fryer",
            "battery",
            "toy",
            "crib",
            "stroller",
        ]
    ):
        return "consumer_product"

    return "unknown"


def build_safety_intelligence_summary(
    *,
    query: str,
    records: list[NormalizedSafetyRecord],
    ranked_records: list[NormalizedSafetyRecord],
    sources_checked: list[dict[str, Any]],
    sources_failed: list[dict[str, Any]],
    expansion_search_terms_used: list[str] | None = None,
    query_type_hint: str | None = None,
) -> dict[str, Any]:
    matched_sources_by_role = _empty_role_map()
    checked_sources_by_role = _empty_role_map()

    for record in records:
        _append_unique(matched_sources_by_role[_source_role(record.source_name)], record.source_name)

    for source in sources_checked:
        source_name = str(source.get("source_name") or "")
        _append_unique(checked_sources_by_role[_source_role(source_name)], source_name)

    recall_or_enforcement_found = bool(matched_sources_by_role["recall_enforcement"])
    reference_or_label_found = bool(
        matched_sources_by_role["reference_identity"] or matched_sources_by_role["label_reference"]
    )
    signal_report_found = bool(matched_sources_by_role["signal_report"])
    outbreak_context_found = bool(matched_sources_by_role["outbreak_context"])

    query_type = _infer_query_type(query, records)
    if query_type == "unknown" and query_type_hint and query_type_hint != "unknown":
        query_type = query_type_hint

    top_titles: list[str] = []
    for record in ranked_records[:3]:
        _append_unique(top_titles, record.title or record.product_name or record.brand_name)

    expansion_terms = expansion_search_terms_used or []
    expansion_explanations: list[str] = [
        f'Dav AI also checked "{term}" because it is a known related search term for the original query.'
        for term in expansion_terms
    ]

    if recall_or_enforcement_found and reference_or_label_found:
        plain_language_summary = (
            "Dav AI found official recall/enforcement records and official identity or label reference records "
            "for this query. Review the recall result details first, then use the reference records to confirm the exact "
            "product, ingredient, model, NDC, UPC, or package information."
        )
    elif recall_or_enforcement_found:
        plain_language_summary = (
            "Dav AI found official recall/enforcement records for this query. Review the affected products, lots, models, "
            "hazard, remedy, and official source links before taking action."
        )
    elif reference_or_label_found:
        plain_language_summary = (
            "No matching recall/enforcement record was found in the returned results, but Dav AI found official identity "
            "or label reference records. This can help confirm the product, active ingredient, dosage form, route, NDC, "
            "or label information before checking official recall pages."
        )
    elif signal_report_found:
        plain_language_summary = (
            "No matching recall/enforcement record was found in the returned results, but Dav AI found public signal-report "
            "records. Signal reports are not recalls and do not prove causation; verify details against official sources."
        )
    elif outbreak_context_found:
        plain_language_summary = (
            "No matching recall/enforcement record was found in the returned results, but Dav AI found public foodborne "
            "outbreak or investigation context. Investigation context is not automatically a recall or proof that a specific "
            "product caused illness."
        )
    else:
        plain_language_summary = (
            "No matching public record was found in the returned results from the checked sources. This does not certify "
            "that the product is safe; it only means Dav AI did not find a matching public record in this search."
        )

    suggested_next_steps: list[str] = []

    if expansion_explanations:
        suggested_next_steps.extend(expansion_explanations)

    if recall_or_enforcement_found:
        suggested_next_steps.extend(
            [
                "Compare the official recall details against your exact product name, model, lot, UPC, NDC, VIN, or package code.",
                "Open the official source URL before following any recall remedy or disposal instruction.",
            ]
        )

    if reference_or_label_found and not recall_or_enforcement_found:
        suggested_next_steps.extend(
            [
                "Use the reference records to confirm exact product identity before searching official recall pages again.",
                "For drugs, compare active ingredient, NDC, labeler, dosage form, and route against the product package.",
            ]
        )

    if sources_failed:
        suggested_next_steps.append(
            "Some sources failed or timed out, so recheck later or verify directly with official source pages."
        )

    return {
        "query_type": query_type,
        "recall_or_enforcement_found": recall_or_enforcement_found,
        "reference_or_label_found": reference_or_label_found,
        "signal_report_found": signal_report_found,
        "outbreak_context_found": outbreak_context_found,
        "matched_sources_by_role": matched_sources_by_role,
        "checked_sources_by_role": checked_sources_by_role,
        "top_result_titles": top_titles,
        "expansion_explanations": expansion_explanations,
        "plain_language_summary": plain_language_summary,
        "suggested_next_steps": suggested_next_steps,
        "caveat": (
            "This summary is generated only from returned official/public records. It does not invent missing recalls, "
            "certify safety, or provide medical/legal advice."
        ),
    }