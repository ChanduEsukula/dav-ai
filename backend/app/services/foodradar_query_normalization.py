from dataclasses import dataclass
import re
import string


@dataclass(frozen=True)
class FoodRadarQueryNormalization:
    raw_query: str
    normalized_query: str
    correction_applied: bool
    suggestion_message: str | None


_EXACT_CORRECTIONS = {
    "chiken": "chicken",
    "protien powder": "protein powder",
    "proteinpowder": "protein powder",
    "protein-powder": "protein powder",
    "e coli": "e. coli",
    "e-coli": "e. coli",
    "e.coli": "e. coli",
    "ecoli": "e. coli",
    "vitamins": "vitamin",
    "multivitamin": "vitamin",
    "preworkout": "pre workout",
    "pre-workout": "pre workout",
}


_HYPHEN_TO_SPACE = {
    "protein-powder",
    "pre-workout",
    "peanut-butter",
}


def _strip_surrounding_punctuation(value: str) -> str:
    removable = string.punctuation.replace(".", "").replace("-", "")
    return value.strip(removable)


def normalize_foodradar_query(raw_query: str) -> FoodRadarQueryNormalization:
    raw = raw_query
    normalized = " ".join(raw_query.strip().lower().split())
    normalized = _strip_surrounding_punctuation(normalized)
    normalized = " ".join(normalized.split())

    if normalized in _HYPHEN_TO_SPACE:
        normalized = normalized.replace("-", " ")

    normalized = re.sub(r"\s+", " ", normalized).strip()

    corrected = _EXACT_CORRECTIONS.get(normalized, normalized)

    correction_applied = corrected != " ".join(raw_query.strip().lower().split())
    suggestion_message = None
    if correction_applied:
        suggestion_message = f"Showing results for {corrected}."

    return FoodRadarQueryNormalization(
        raw_query=raw,
        normalized_query=corrected,
        correction_applied=correction_applied,
        suggestion_message=suggestion_message,
    )
