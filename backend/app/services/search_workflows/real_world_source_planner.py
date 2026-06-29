from __future__ import annotations

from dataclasses import asdict, dataclass

from app.services.search_workflows.real_world_query_understanding import RealWorldQueryUnderstanding
from app.services.search_workflows.product_category_classifier import (
    BROAD_PUBLIC_FALLBACK_SOURCE_IDS,
)
from app.sources.registry import (
    CPSC_RECALLS_API,
    CDC_FOODBORNE_OUTBREAKS,
    CDC_VAERS,
    FDA_RECALLS_MARKET_WITHDRAWALS_SAFETY_ALERTS,
    FDA_SAFETY_COMMUNICATIONS,
    OPENFDA_DRUG_ENFORCEMENT,
    OPENFDA_DRUG_LABEL,
    OPENFDA_NDC_DIRECTORY,
    OPENFDA_DEVICE_ENFORCEMENT,
    OPENFDA_DEVICE_EVENT,
    OPENFDA_UDI_DIRECTORY,
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
    _source_id(CDC_FOODBORNE_OUTBREAKS),
    _source_id(FDA_RECALLS_MARKET_WITHDRAWALS_SAFETY_ALERTS),
]

MEDICAL_DEVICE_SOURCES = [
    _source_id(OPENFDA_DEVICE_ENFORCEMENT),
    _source_id(OPENFDA_DEVICE_EVENT),
    _source_id(OPENFDA_UDI_DIRECTORY),
    _source_id(FDA_SAFETY_COMMUNICATIONS),
]

VEHICLE_SOURCES = [
    _source_id(NHTSA_VPIC_VIN_DECODER_API),
    _source_id(NHTSA_RECALLS_API_DATASETS),
]

VACCINE_SOURCES = [
    _source_id(CDC_VAERS),
]


def _first_supported_hint(hints: list[str]) -> str:
    priority = ["vehicle", "medical_device", "vaccine", "drug", "food", "consumer_product"]
    for hint in priority:
        if hint in hints:
            return hint
    return "unknown"


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    for value in values:
        if value and value not in deduped:
            deduped.append(value)
    return deduped


def _split_source_priority(intent: str, source_ids: list[str]) -> tuple[list[str], list[str]]:
    source_ids = _dedupe(source_ids)

    if intent == "consumer_product":
        primary = [_source_id(CPSC_RECALLS_API)]
        return primary, [source_id for source_id in source_ids if source_id not in primary]

    if intent == "drug":
        primary = [
            _source_id(OPENFDA_DRUG_ENFORCEMENT),
            _source_id(RXNORM_RXNAV_API),
            _source_id(OPENFDA_NDC_DIRECTORY),
        ]
        primary = [source_id for source_id in primary if source_id in source_ids]
        return primary, [source_id for source_id in source_ids if source_id not in primary]

    if intent == "food":
        primary = [
            _source_id(OPENFDA_FOOD_ENFORCEMENT),
            _source_id(USDA_FSIS_RECALL),
        ]
        primary = [source_id for source_id in primary if source_id in source_ids]
        return primary, [source_id for source_id in source_ids if source_id not in primary]

    if intent == "medical_device":
        primary = [_source_id(OPENFDA_DEVICE_ENFORCEMENT)]
        return primary, [source_id for source_id in source_ids if source_id not in primary]

    if intent == "vaccine":
        primary = [_source_id(CDC_VAERS)]
        return primary, [source_id for source_id in source_ids if source_id not in primary]

    if intent == "vehicle":
        primary = [_source_id(NHTSA_RECALLS_API_DATASETS)]
        primary = [source_id for source_id in primary if source_id in source_ids]
        return primary, [source_id for source_id in source_ids if source_id not in primary]

    if intent == "cosmetic":
        primary = [_source_id(FDA_RECALLS_MARKET_WITHDRAWALS_SAFETY_ALERTS)]
        return primary, [source_id for source_id in source_ids if source_id not in primary]

    primary = [
        _source_id(FDA_RECALLS_MARKET_WITHDRAWALS_SAFETY_ALERTS),
        _source_id(CPSC_RECALLS_API),
    ]
    primary = [source_id for source_id in primary if source_id in source_ids]
    return primary, [source_id for source_id in source_ids if source_id not in primary]


def plan_real_world_safety_sources(
    query_understanding: RealWorldQueryUnderstanding,
) -> RealWorldSourcePlan:
    hints = query_understanding.query_type_hints
    classification = query_understanding.category_classification
    intent = classification.primary_category
    if intent == "unknown":
        intent = _first_supported_hint(hints)

    classifier_source_ids = _dedupe(classification.suggested_source_ids)
    if classifier_source_ids:
        primary_source_ids, secondary_source_ids = _split_source_priority(intent, classifier_source_ids)
        return RealWorldSourcePlan(
            intent=intent,
            confidence=classification.confidence,
            reason=classification.reason,
            primary_source_ids=primary_source_ids,
            secondary_source_ids=secondary_source_ids,
            sources_to_check=classifier_source_ids,
        )

    if intent == "consumer_product":
        return RealWorldSourcePlan(
            intent="consumer_product",
            confidence="high",
            reason="The query appears to describe a consumer product, so Dav AI checks consumer-product recall sources first.",
            primary_source_ids=[_source_id(CPSC_RECALLS_API)],
            secondary_source_ids=[
                _source_id(CDC_FOODBORNE_OUTBREAKS),
                _source_id(FDA_RECALLS_MARKET_WITHDRAWALS_SAFETY_ALERTS),
            ],
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
            secondary_source_ids=[
                _source_id(CDC_FOODBORNE_OUTBREAKS),
                _source_id(FDA_RECALLS_MARKET_WITHDRAWALS_SAFETY_ALERTS),
            ],
            sources_to_check=FOOD_SOURCES,
        )

    if intent == "medical_device":
        return RealWorldSourcePlan(
            intent="medical_device",
            confidence="high",
            reason="The query appears to describe a medical device, so Dav AI checks device enforcement and signal-report sources.",
            primary_source_ids=[_source_id(OPENFDA_DEVICE_ENFORCEMENT)],
            secondary_source_ids=[
                _source_id(OPENFDA_DEVICE_EVENT),
                _source_id(OPENFDA_UDI_DIRECTORY),
                _source_id(FDA_SAFETY_COMMUNICATIONS),
            ],
            sources_to_check=MEDICAL_DEVICE_SOURCES,
        )

    if intent == "vaccine":
        return RealWorldSourcePlan(
            intent="vaccine",
            confidence="high",
            reason="The query appears to describe a vaccine or vaccine adverse-event signal, so Dav AI checks VAERS signal-report data.",
            primary_source_ids=[_source_id(CDC_VAERS)],
            secondary_source_ids=[],
            sources_to_check=VACCINE_SOURCES,
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
        reason="The query type is unclear, so Dav AI uses a broad public-source fallback without assuming a single domain.",
        primary_source_ids=[
            _source_id(FDA_RECALLS_MARKET_WITHDRAWALS_SAFETY_ALERTS),
            _source_id(CPSC_RECALLS_API),
        ],
        secondary_source_ids=[
            source_id
            for source_id in BROAD_PUBLIC_FALLBACK_SOURCE_IDS
            if source_id
            not in {
                _source_id(FDA_RECALLS_MARKET_WITHDRAWALS_SAFETY_ALERTS),
                _source_id(CPSC_RECALLS_API),
            }
        ],
        sources_to_check=BROAD_PUBLIC_FALLBACK_SOURCE_IDS,
    )
