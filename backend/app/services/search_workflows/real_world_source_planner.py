from __future__ import annotations

from dataclasses import asdict, dataclass

from app.services.search_workflows.real_world_query_understanding import RealWorldQueryUnderstanding
from app.sources.registry import (
    CPSC_RECALLS_API,
    FDA_RECALLS_MARKET_WITHDRAWALS_SAFETY_ALERTS,
    OPENFDA_DRUG_ENFORCEMENT,
    OPENFDA_DRUG_LABEL,
    OPENFDA_NDC_DIRECTORY,
    OPENFDA_DEVICE_ENFORCEMENT,
    OPENFDA_DEVICE_EVENT,
    OPENFDA_FOOD_ENFORCEMENT,
    RXNORM_RXNAV_API,
    USDA_FSIS_RECALL,
    DAILYMED_SPL_API,
    NHTSA_RECALLS_API_DATASETS,
    NHTSA_VPIC_VIN_DECODER_API,
)


@dataclass(frozen=True)
class RealWorldSourcePlan:
    intent: str
    confidence: str
    reason: str
    primary_source_ids: list[str]
    secondary_source_ids: list[str]
    sources_to_check: list[str]
    clarification_required: bool = False

    def as_response_dict(self) -> dict[str, object]:
        return asdict(self)


def _source_id(source: dict[str, str]) -> str:
    return source["source_id"]


CONSUMER_PRODUCT_SOURCES = [
    _source_id(CPSC_RECALLS_API),
    _source_id(FDA_RECALLS_MARKET_WITHDRAWALS_SAFETY_ALERTS),
]

DRUG_SOURCES = [
    _source_id(OPENFDA_DRUG_ENFORCEMENT),
    _source_id(RXNORM_RXNAV_API),
    _source_id(DAILYMED_SPL_API),
    _source_id(OPENFDA_DRUG_LABEL),
    _source_id(OPENFDA_NDC_DIRECTORY),
]

FOOD_SOURCES = [
    _source_id(OPENFDA_FOOD_ENFORCEMENT),
    _source_id(USDA_FSIS_RECALL),
    _source_id(FDA_RECALLS_MARKET_WITHDRAWALS_SAFETY_ALERTS),
]

MEDICAL_DEVICE_SOURCES = [
    _source_id(OPENFDA_DEVICE_ENFORCEMENT),
    _source_id(OPENFDA_DEVICE_EVENT),
]

VEHICLE_SOURCES = [
    _source_id(NHTSA_VPIC_VIN_DECODER_API),
    _source_id(NHTSA_RECALLS_API_DATASETS),
]

AMBIGUOUS_TERMS = {
    "sunscreen",
    "cream",
    "gel",
    "spray",
}


def _has_ambiguous_term(query: str) -> bool:
    return any(term in query for term in AMBIGUOUS_TERMS)


def _first_supported_hint(hints: list[str]) -> str:
    priority = ["vehicle", "medical_device", "drug", "food", "consumer_product"]
    for hint in priority:
        if hint in hints:
            return hint
    return "unknown"


def plan_real_world_safety_sources(
    query_understanding: RealWorldQueryUnderstanding,
) -> RealWorldSourcePlan:
    normalized_query = query_understanding.normalized_query
    hints = query_understanding.query_type_hints
    intent = _first_supported_hint(hints)

    if _has_ambiguous_term(normalized_query) and intent == "unknown":
        return RealWorldSourcePlan(
            intent="ambiguous",
            confidence="low",
            reason="The query could refer to more than one safety area. Ask for category context before running a broad source sweep.",
            primary_source_ids=[],
            secondary_source_ids=[],
            sources_to_check=[],
            clarification_required=True,
        )

    if intent == "consumer_product":
        return RealWorldSourcePlan(
            intent="consumer_product",
            confidence="high",
            reason="The query appears to describe a consumer product, so Dav AI checks consumer-product recall sources first.",
            primary_source_ids=[_source_id(CPSC_RECALLS_API)],
            secondary_source_ids=[_source_id(FDA_RECALLS_MARKET_WITHDRAWALS_SAFETY_ALERTS)],
            sources_to_check=CONSUMER_PRODUCT_SOURCES,
        )

    if intent == "drug":
        return RealWorldSourcePlan(
            intent="drug",
            confidence="high",
            reason="The query appears to describe a drug, brand, generic ingredient, or NDC identifier.",
            primary_source_ids=[
                _source_id(OPENFDA_DRUG_ENFORCEMENT),
                _source_id(RXNORM_RXNAV_API),
                _source_id(OPENFDA_NDC_DIRECTORY),
            ],
            secondary_source_ids=[
                _source_id(DAILYMED_SPL_API),
                _source_id(OPENFDA_DRUG_LABEL),
            ],
            sources_to_check=DRUG_SOURCES,
        )

    if intent == "food":
        return RealWorldSourcePlan(
            intent="food",
            confidence="high",
            reason="The query appears to describe food, meat, poultry, egg products, or foodborne recall language.",
            primary_source_ids=[
                _source_id(OPENFDA_FOOD_ENFORCEMENT),
                _source_id(USDA_FSIS_RECALL),
            ],
            secondary_source_ids=[_source_id(FDA_RECALLS_MARKET_WITHDRAWALS_SAFETY_ALERTS)],
            sources_to_check=FOOD_SOURCES,
        )

    if intent == "medical_device":
        return RealWorldSourcePlan(
            intent="medical_device",
            confidence="high",
            reason="The query appears to describe a medical device, so Dav AI checks device enforcement and signal-report sources.",
            primary_source_ids=[_source_id(OPENFDA_DEVICE_ENFORCEMENT)],
            secondary_source_ids=[_source_id(OPENFDA_DEVICE_EVENT)],
            sources_to_check=MEDICAL_DEVICE_SOURCES,
        )

    if intent == "vehicle":
        return RealWorldSourcePlan(
            intent="vehicle",
            confidence="high",
            reason="The query appears to describe a vehicle or VIN, so Dav AI checks NHTSA vehicle sources.",
            primary_source_ids=[_source_id(NHTSA_RECALLS_API_DATASETS)],
            secondary_source_ids=[_source_id(NHTSA_VPIC_VIN_DECODER_API)],
            sources_to_check=VEHICLE_SOURCES,
        )

    return RealWorldSourcePlan(
        intent="unknown",
        confidence="low",
        reason="The query type is unclear, so Dav AI uses a limited recall-oriented fallback instead of checking every source.",
        primary_source_ids=[_source_id(CPSC_RECALLS_API)],
        secondary_source_ids=[_source_id(FDA_RECALLS_MARKET_WITHDRAWALS_SAFETY_ALERTS)],
        sources_to_check=CONSUMER_PRODUCT_SOURCES,
    )
