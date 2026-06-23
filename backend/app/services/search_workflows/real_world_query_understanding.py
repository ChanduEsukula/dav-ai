from __future__ import annotations

import re
from dataclasses import asdict, dataclass


TYPO_CORRECTIONS = {
    "tylonal": "tylenol",
    "tylenall": "tylenol",
    "acetominophen": "acetaminophen",
    "acetaminophin": "acetaminophen",
    "ibuprophen": "ibuprofen",
    "ibuprofin": "ibuprofen",
    "ibruprofen": "ibuprofen",
    "benedryl": "benadryl",
    "bendryl": "benadryl",
    "loratidine": "loratadine",
    "metforman": "metformin",
    "metforimn": "metformin",
    "albuteral": "albuterol",
    "segwey": "segway",
    "listerea": "listeria",
}

PHRASE_REPLACEMENTS = {
    "airfryer": "air fryer",
    "air-fryer": "air fryer",
    "powerbank": "power bank",
    "power-bank": "power bank",
    "carseat": "car seat",
    "car-seat": "car seat",
    "babycarseat": "baby car seat",
    "glucose monitor": "glucose meter",
    "blood sugar monitor": "glucose meter",
    "blood sugar meter": "glucose meter",
    "cpap machine": "cpap",
    "sleep apnea machine": "cpap",
    "e scooter": "electric scooter",
    "e-scooter": "electric scooter",
    "eye drop": "eye drops",
}

BRAND_GENERIC_EXPANSIONS = {
    "tylenol": ["acetaminophen"],
    "advil": ["ibuprofen"],
    "motrin": ["ibuprofen"],
    "benadryl": ["diphenhydramine"],
    "claritin": ["loratadine"],
    "zyrtec": ["cetirizine"],
    "prilosec": ["omeprazole"],
    "ventolin": ["albuterol"],
    "glucophage": ["metformin"],
    "epipen": ["epinephrine"],
    "ozempic": ["semaglutide"],
}

DRUG_TERMS = {
    "tylenol",
    "acetaminophen",
    "advil",
    "motrin",
    "ibuprofen",
    "benadryl",
    "diphenhydramine",
    "claritin",
    "loratadine",
    "zyrtec",
    "cetirizine",
    "metformin",
    "albuterol",
    "ndc",
}

FOOD_TERMS = {
    "food",
    "chicken",
    "beef",
    "poultry",
    "meat",
    "fsis",
    "salmonella",
    "listeria",
    "nuggets",
}

DEVICE_TERMS = {
    "glucose meter",
    "insulin pump",
    "cpap",
    "medical device",
}

CONSUMER_PRODUCT_TERMS = {
    "air fryer",
    "power bank",
    "car seat",
    "stroller",
    "crib",
    "scooter",
    "electric scooter",
    "battery",
}

VEHICLE_TERMS = {
    "vin",
    "vehicle",
    "honda",
    "toyota",
    "ford",
    "tesla",
    "truck",
}


@dataclass(frozen=True)
class RealWorldQueryUnderstanding:
    original_query: str
    normalized_query: str
    search_query: str
    corrections_applied: list[str]
    expanded_terms: list[str]
    expansion_search_terms_used: list[str]
    detected_identifiers: dict[str, str | None]
    query_type_hints: list[str]

    def as_response_dict(self) -> dict[str, object]:
        return asdict(self)


def _compact(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _append_unique(values: list[str], value: str) -> None:
    if value and value not in values:
        values.append(value)


def _apply_phrase_replacements(query: str, corrections: list[str]) -> str:
    normalized = query
    for source, replacement in PHRASE_REPLACEMENTS.items():
        pattern = r"(?<![a-z0-9])" + re.escape(source) + r"(?![a-z0-9])"
        updated = re.sub(pattern, replacement, normalized)
        if updated != normalized:
            normalized = updated
            _append_unique(corrections, f"{source} → {replacement}")
    return normalized


def _apply_token_corrections(query: str, corrections: list[str]) -> str:
    tokens = query.split()
    corrected_tokens: list[str] = []

    for token in tokens:
        stripped = token.strip(".,;:!?()[]{}")
        replacement = TYPO_CORRECTIONS.get(stripped, stripped)
        if replacement != stripped:
            _append_unique(corrections, f"{stripped} → {replacement}")
        corrected_tokens.append(replacement)

    return " ".join(corrected_tokens)


def _expanded_terms(normalized_query: str) -> list[str]:
    expansions: list[str] = []
    tokens = set(normalized_query.split())

    for brand, generics in BRAND_GENERIC_EXPANSIONS.items():
        if brand in tokens or brand in normalized_query:
            for generic in generics:
                _append_unique(expansions, generic)

    return expansions


def _detect_vin(original_query: str) -> str | None:
    compact = re.sub(r"[^A-Za-z0-9]", "", original_query).upper()
    if len(compact) == 17 and not any(character in compact for character in "IOQ"):
        return compact
    return None


def _detect_ndc(original_query: str) -> str | None:
    lower = original_query.lower()
    compact = re.sub(r"\s+", "", original_query)
    digits = re.sub(r"\D", "", original_query)

    if "ndc" in lower and 9 <= len(digits) <= 11:
        return digits
    if "-" in compact and 9 <= len(digits) <= 11:
        return digits
    return None


def _detect_upc(original_query: str) -> str | None:
    if "ndc" in original_query.lower():
        return None

    digits = re.sub(r"\D", "", original_query)
    if len(digits) in {12, 13, 14}:
        return digits
    return None


def _query_type_hints(
    *,
    normalized_query: str,
    expanded_terms: list[str],
    detected_identifiers: dict[str, str | None],
) -> list[str]:
    text = " ".join([normalized_query, *expanded_terms])
    hints: list[str] = []

    if detected_identifiers.get("vin"):
        _append_unique(hints, "vehicle")
    if detected_identifiers.get("ndc"):
        _append_unique(hints, "drug")
    if detected_identifiers.get("upc"):
        _append_unique(hints, "consumer_product")

    if any(term in text for term in DRUG_TERMS):
        _append_unique(hints, "drug")
    if any(term in text for term in FOOD_TERMS):
        _append_unique(hints, "food")
    if any(term in text for term in DEVICE_TERMS):
        _append_unique(hints, "medical_device")
    if any(term in text for term in CONSUMER_PRODUCT_TERMS):
        _append_unique(hints, "consumer_product")
    if any(term in text for term in VEHICLE_TERMS):
        _append_unique(hints, "vehicle")

    return hints or ["unknown"]


def understand_real_world_safety_query(raw_query: str) -> RealWorldQueryUnderstanding:
    corrections: list[str] = []
    normalized = _compact(raw_query)
    normalized = _apply_phrase_replacements(normalized, corrections)
    normalized = _apply_token_corrections(normalized, corrections)
    normalized = _compact(normalized)

    expanded = _expanded_terms(normalized)
    detected_identifiers = {
        "vin": _detect_vin(raw_query),
        "ndc": _detect_ndc(raw_query),
        "upc": _detect_upc(raw_query),
    }

    # V1 uses the corrected/normalized query for retrieval.
    # Expanded terms are exposed to the response for UI/fusion use but are not allowed to create records.
    search_query = normalized

    return RealWorldQueryUnderstanding(
        original_query=raw_query,
        normalized_query=normalized,
        search_query=search_query,
        corrections_applied=corrections,
        expanded_terms=expanded,
        expansion_search_terms_used=[],
        detected_identifiers=detected_identifiers,
        query_type_hints=_query_type_hints(
            normalized_query=normalized,
            expanded_terms=expanded,
            detected_identifiers=detected_identifiers,
        ),
    )
