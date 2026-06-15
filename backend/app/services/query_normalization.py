from dataclasses import dataclass
import re
import string
from typing import Literal


SafetyQueryArea = Literal["pharmacy", "food", "cosmetic"]


@dataclass(frozen=True)
class QueryNormalization:
    raw_query: str
    normalized_query: str
    correction_applied: bool
    suggestion_message: str | None


ALIASES_BY_AREA: dict[SafetyQueryArea, dict[str, str]] = {
    "food": {
        "strawberries": "strawberry",
        "berries": "berry",
        "eggs": "egg",
        "vitamins": "vitamin",
        "multivitamin": "vitamin",
        "cookies": "cookie",
        "tomatoes": "tomato",
        "potatoes": "potato",
        "proteinpowder": "protein powder",
        "protein-powder": "protein powder",
        "protien powder": "protein powder",
        "peanutbutter": "peanut butter",
        "peanutbutters": "peanut butter",
        "peanut-butter": "peanut butter",
        "chickenbreast": "chicken breast",
        "chiken": "chicken",
        "e coli": "e. coli",
        "e-coli": "e. coli",
        "e.coli": "e. coli",
        "ecoli": "e. coli",
        "preworkout": "pre workout",
        "pre-workout": "pre workout",
    },
    "cosmetic": {
        "hairdye": "hair dye",
        "hairdyes": "hair dye",
        "sunscrean": "sunscreen",
        "sun screen": "sunscreen",
        "sunscreens": "sunscreen",
        "moisturizers": "moisturizer",
        "lipsticks": "lipstick",
        "shampoos": "shampoo",
        "conditioners": "conditioner",
    },
    "pharmacy": {
        "xanex": "xanax",
        "metforimn": "metformin",
        "metfromin": "metformin",
        "metformins": "metformin",
        "ibruprofen": "ibuprofen",
        "ibuprofin": "ibuprofen",
        "ibuprofens": "ibuprofen",
        "amoxycillin": "amoxicillin",
        "acetaminophin": "acetaminophen",
        "aspirins": "aspirin",
    },
}


def _compact_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def _strip_surrounding_punctuation(value: str) -> str:
    removable = string.punctuation.replace(".", "").replace("-", "")
    return value.strip(removable)


def normalize_safety_query(
    raw_query: str,
    area: SafetyQueryArea,
) -> QueryNormalization:
    raw = raw_query
    compact_query = _compact_whitespace(raw_query)
    cleaned_query = _strip_surrounding_punctuation(compact_query)
    lookup_key = cleaned_query.lower()
    normalized_query = ALIASES_BY_AREA[area].get(lookup_key, lookup_key)
    correction_applied = bool(compact_query) and lookup_key != normalized_query.lower()
    suggestion_message = None

    if correction_applied:
        suggestion_message = (
            f"Showing results for '{normalized_query}' based on your search "
            f"'{compact_query}'."
        )

    return QueryNormalization(
        raw_query=raw,
        normalized_query=normalized_query,
        correction_applied=correction_applied,
        suggestion_message=suggestion_message,
    )
