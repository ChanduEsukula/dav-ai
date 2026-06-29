from __future__ import annotations

import re
from dataclasses import asdict, dataclass

from app.sources.registry import (
    CPSC_RECALLS_API,
    CDC_FOODBORNE_OUTBREAKS,
    CDC_VAERS,
    DAILYMED_SPL_API,
    FDA_RECALLS_MARKET_WITHDRAWALS_SAFETY_ALERTS,
    FDA_SAFETY_COMMUNICATIONS,
    NHTSA_RECALLS_API_DATASETS,
    NHTSA_VPIC_VIN_DECODER_API,
    OPENFDA_DEVICE_ENFORCEMENT,
    OPENFDA_DEVICE_EVENT,
    OPENFDA_DRUG_ENFORCEMENT,
    OPENFDA_DRUG_LABEL,
    OPENFDA_FOOD_ENFORCEMENT,
    OPENFDA_NDC_DIRECTORY,
    OPENFDA_UDI_DIRECTORY,
    RXNORM_RXNAV_API,
    USDA_FSIS_RECALL,
)


CATEGORIES = {
    "food",
    "drug",
    "medical_device",
    "vehicle",
    "consumer_product",
    "cosmetic",
    "vaccine",
    "unknown",
}


def _source_id(source: dict[str, str]) -> str:
    return source["source_id"]


FDA_PUBLIC_SOURCE_ID = _source_id(FDA_RECALLS_MARKET_WITHDRAWALS_SAFETY_ALERTS)
CPSC_SOURCE_ID = _source_id(CPSC_RECALLS_API)
OPENFDA_FOOD_SOURCE_ID = _source_id(OPENFDA_FOOD_ENFORCEMENT)
OPENFDA_DRUG_SOURCE_ID = _source_id(OPENFDA_DRUG_ENFORCEMENT)
OPENFDA_DEVICE_SOURCE_ID = _source_id(OPENFDA_DEVICE_ENFORCEMENT)

BROAD_PUBLIC_FALLBACK_SOURCE_IDS = [
    FDA_PUBLIC_SOURCE_ID,
    CPSC_SOURCE_ID,
    OPENFDA_FOOD_SOURCE_ID,
    OPENFDA_DRUG_SOURCE_ID,
    OPENFDA_DEVICE_SOURCE_ID,
]

FOOD_SOURCE_IDS = [
    OPENFDA_FOOD_SOURCE_ID,
    FDA_PUBLIC_SOURCE_ID,
    _source_id(CDC_FOODBORNE_OUTBREAKS),
]

FOOD_FSIS_SOURCE_IDS = [
    OPENFDA_FOOD_SOURCE_ID,
    _source_id(USDA_FSIS_RECALL),
    FDA_PUBLIC_SOURCE_ID,
    _source_id(CDC_FOODBORNE_OUTBREAKS),
]

DRUG_SOURCE_IDS = [
    OPENFDA_DRUG_SOURCE_ID,
    FDA_PUBLIC_SOURCE_ID,
    _source_id(RXNORM_RXNAV_API),
    _source_id(DAILYMED_SPL_API),
    _source_id(OPENFDA_DRUG_LABEL),
    _source_id(OPENFDA_NDC_DIRECTORY),
]

MEDICAL_DEVICE_SOURCE_IDS = [
    OPENFDA_DEVICE_SOURCE_ID,
    _source_id(OPENFDA_DEVICE_EVENT),
    _source_id(OPENFDA_UDI_DIRECTORY),
    _source_id(FDA_SAFETY_COMMUNICATIONS),
]

VEHICLE_SOURCE_IDS = [
    _source_id(NHTSA_VPIC_VIN_DECODER_API),
    _source_id(NHTSA_RECALLS_API_DATASETS),
]

CONSUMER_PRODUCT_SOURCE_IDS = [
    CPSC_SOURCE_ID,
    FDA_PUBLIC_SOURCE_ID,
]

VACCINE_SOURCE_IDS = [
    _source_id(CDC_VAERS),
]

COSMETIC_SUPPORTED_SOURCE_IDS = [
    FDA_PUBLIC_SOURCE_ID,
]

FOOD_TERMS = {
    "baby formula",
    "beef",
    "broth",
    "chicken",
    "chicken broth",
    "e. coli",
    "ecoli",
    "food",
    "foodborne",
    "formula recall",
    "frozen chicken",
    "infant formula",
    "listeria",
    "meat",
    "meatloaf",
    "milk",
    "nuggets",
    "outbreak",
    "peanut butter",
    "poultry",
    "protein bar",
    "salmonella",
    "undeclared milk",
}

FSIS_TERMS = {
    "beef",
    "broth",
    "chicken",
    "chicken broth",
    "egg product",
    "frozen chicken",
    "meat",
    "meatloaf",
    "pork",
    "poultry",
    "turkey",
}

ALLERGEN_TERMS = {
    "allergen",
    "almond",
    "cashew",
    "egg",
    "milk",
    "peanut",
    "peanut butter",
    "sesame",
    "soy",
    "tree nut",
    "undeclared",
    "walnut",
    "wheat",
}

DRUG_TERMS = {
    "acetaminophen",
    "advil",
    "albuterol",
    "aspirin",
    "benadryl",
    "cetirizine",
    "claritin",
    "diphenhydramine",
    "drug",
    "eye drops",
    "ibuprofen",
    "loratadine",
    "metformin",
    "motrin",
    "ndc",
    "omeprazole",
    "sunscreen",
    "tylenol",
    "zyrtec",
}

OTC_DRUG_TERMS = {
    "acetaminophen",
    "advil",
    "aspirin",
    "eye drops",
    "ibuprofen",
    "motrin",
    "sunscreen",
    "tylenol",
}

MEDICAL_DEVICE_TERMS = {
    "blood glucose",
    "blood sugar monitor",
    "cpap",
    "device advisory",
    "fda safety communication",
    "glucose meter",
    "insulin pump",
    "medical device",
    "medical device safety",
    "pacemaker",
    "safety communication",
    "safety communications",
    "udi",
    "ventilator",
}

VEHICLE_TERMS = {
    "bmw",
    "camry",
    "ford",
    "honda",
    "nhtsa",
    "tesla",
    "toyota",
    "truck",
    "vehicle",
    "vin",
    "x3",
}

CONSUMER_PRODUCT_TERMS = {
    "air fryer",
    "appliance",
    "battery",
    "bicycle helmet",
    "car seat",
    "crib",
    "electric scooter",
    "heater",
    "helmet",
    "microwave",
    "microwave oven",
    "power bank",
    "scooter",
    "segway",
    "stroller",
    "toaster",
    "toy",
    "washing machine",
}

COSMETIC_TERMS = {
    "conditioner",
    "cosmetic",
    "cream",
    "deodorant",
    "fragrance",
    "hair dye",
    "lotion",
    "makeup",
    "mascara",
    "shampoo",
    "skin care",
    "sunscreen",
}

VACCINE_TERMS = {
    "covid vaccine",
    "covid-19 vaccine",
    "flu shot",
    "immunization",
    "influenza vaccine",
    "mmr",
    "vaers",
    "vaccination",
    "vaccine",
}


@dataclass(frozen=True)
class ProductCategoryClassification:
    primary_category: str
    secondary_categories: list[str]
    confidence: str
    matched_terms: list[str]
    reason: str
    suggested_source_ids: list[str]
    flags: dict[str, bool]

    def as_response_dict(self) -> dict[str, object]:
        return asdict(self)


def _compact(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _append_unique(values: list[str], value: str) -> None:
    if value and value not in values:
        values.append(value)


def _contains_term(text: str, term: str) -> bool:
    if " " in term or "." in term or "-" in term:
        return term in text
    return re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", text) is not None


def _matched_terms(text: str, terms: set[str]) -> list[str]:
    return sorted(term for term in terms if _contains_term(text, term))


def _confidence_for_score(score: int, category_count: int) -> str:
    if score >= 4:
        return "high"
    if score >= 2 or category_count > 1:
        return "medium"
    return "low"


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    for value in values:
        _append_unique(deduped, value)
    return deduped


def _suggested_sources(
    *,
    primary_category: str,
    secondary_categories: list[str],
    flags: dict[str, bool],
) -> list[str]:
    if primary_category == "food":
        return FOOD_FSIS_SOURCE_IDS if flags["fsis_relevant"] else FOOD_SOURCE_IDS

    if primary_category == "drug":
        sources = list(DRUG_SOURCE_IDS)
        if "cosmetic" in secondary_categories:
            sources.extend(COSMETIC_SUPPORTED_SOURCE_IDS)
        return _dedupe(sources)

    if primary_category == "medical_device":
        return MEDICAL_DEVICE_SOURCE_IDS

    if primary_category == "vehicle":
        return VEHICLE_SOURCE_IDS

    if primary_category == "consumer_product":
        return CONSUMER_PRODUCT_SOURCE_IDS

    if primary_category == "vaccine":
        return VACCINE_SOURCE_IDS

    if primary_category == "cosmetic":
        return COSMETIC_SUPPORTED_SOURCE_IDS

    broad_sources = list(BROAD_PUBLIC_FALLBACK_SOURCE_IDS)
    if flags["vehicle_like"]:
        broad_sources.extend(VEHICLE_SOURCE_IDS)
    return _dedupe(broad_sources)


def classify_product_category(
    query: str,
    *,
    detected_identifiers: dict[str, str | None] | None = None,
) -> ProductCategoryClassification:
    normalized = _compact(query)
    identifiers = detected_identifiers or {}
    text = normalized

    matched_by_category = {
        "food": _matched_terms(text, FOOD_TERMS),
        "drug": _matched_terms(text, DRUG_TERMS),
        "medical_device": _matched_terms(text, MEDICAL_DEVICE_TERMS),
        "vehicle": _matched_terms(text, VEHICLE_TERMS),
        "consumer_product": _matched_terms(text, CONSUMER_PRODUCT_TERMS),
        "cosmetic": _matched_terms(text, COSMETIC_TERMS),
        "vaccine": _matched_terms(text, VACCINE_TERMS),
    }

    scores: dict[str, int] = {}
    for category, terms in matched_by_category.items():
        if terms:
            scores[category] = sum(3 if " " in term else 2 for term in terms)

    if identifiers.get("vin"):
        scores["vehicle"] = scores.get("vehicle", 0) + 5
        _append_unique(matched_by_category["vehicle"], "vin")
    if identifiers.get("ndc"):
        scores["drug"] = scores.get("drug", 0) + 5
        _append_unique(matched_by_category["drug"], "ndc")
    if identifiers.get("udi"):
        scores["medical_device"] = scores.get("medical_device", 0) + 5
        _append_unique(matched_by_category["medical_device"], "udi")
    if identifiers.get("upc"):
        scores["consumer_product"] = scores.get("consumer_product", 0) + 2

    fsis_relevant = bool(_matched_terms(text, FSIS_TERMS))
    allergen_relevant = bool(_matched_terms(text, ALLERGEN_TERMS))
    otc_drug_possible = bool(_matched_terms(text, OTC_DRUG_TERMS))
    cosmetic_possible = bool(matched_by_category["cosmetic"])
    vehicle_like = bool(matched_by_category["vehicle"] or identifiers.get("vin"))
    medical_device_like = bool(matched_by_category["medical_device"] or identifiers.get("udi"))

    if "sunscreen" in matched_by_category["drug"]:
        scores["drug"] = scores.get("drug", 0) + 1
        scores["cosmetic"] = scores.get("cosmetic", 0) + 1

    if not scores:
        flags = {
            "fsis_relevant": fsis_relevant,
            "allergen_relevant": allergen_relevant,
            "otc_drug_possible": otc_drug_possible,
            "cosmetic_possible": cosmetic_possible,
            "vehicle_like": vehicle_like,
            "medical_device_like": medical_device_like,
        }
        return ProductCategoryClassification(
            primary_category="unknown",
            secondary_categories=[],
            confidence="low",
            matched_terms=[],
            reason=(
                "No deterministic product-category terms were matched, so Dav AI uses a broad "
                "public-source fallback without assuming a specific domain."
            ),
            suggested_source_ids=_suggested_sources(
                primary_category="unknown",
                secondary_categories=[],
                flags=flags,
            ),
            flags=flags,
        )

    priority = [
        "medical_device",
        "vehicle",
        "vaccine",
        "drug",
        "food",
        "consumer_product",
        "cosmetic",
    ]
    sorted_categories = sorted(
        scores,
        key=lambda category: (scores[category], -priority.index(category)),
        reverse=True,
    )

    primary_category = sorted_categories[0]
    if "sunscreen" in text:
        primary_category = "drug"

    secondary_categories: list[str] = []
    for category in sorted_categories:
        if category != primary_category:
            _append_unique(secondary_categories, category)

    if primary_category == "drug" and cosmetic_possible:
        _append_unique(secondary_categories, "cosmetic")

    matched_terms: list[str] = []
    for category in [primary_category, *secondary_categories]:
        for term in matched_by_category.get(category, []):
            _append_unique(matched_terms, term)

    flags = {
        "fsis_relevant": fsis_relevant,
        "allergen_relevant": allergen_relevant,
        "otc_drug_possible": otc_drug_possible,
        "cosmetic_possible": cosmetic_possible,
        "vehicle_like": vehicle_like,
        "medical_device_like": medical_device_like,
    }
    confidence = _confidence_for_score(
        scores.get(primary_category, 0),
        len([category for category, score in scores.items() if score > 0]),
    )

    if secondary_categories:
        reason = (
            f"Matched {primary_category} terms with related "
            f"{', '.join(secondary_categories)} context."
        )
    else:
        reason = f"Matched deterministic {primary_category} terms in the query."

    return ProductCategoryClassification(
        primary_category=primary_category,
        secondary_categories=secondary_categories,
        confidence=confidence,
        matched_terms=matched_terms,
        reason=reason,
        suggested_source_ids=_suggested_sources(
            primary_category=primary_category,
            secondary_categories=secondary_categories,
            flags=flags,
        ),
        flags=flags,
    )
