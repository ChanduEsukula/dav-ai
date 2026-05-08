from collections import defaultdict
from typing import TypedDict


REACTION_CLASSIFIER_VERSION = "reaction-classifier-v0.1"


class ReactionCategory(TypedDict):
    category: str
    count: int
    reactions: list[str]


CATEGORY_KEYWORDS = {
    "Neurological": [
        "headache",
        "dizziness",
        "gait",
        "balance",
        "seizure",
        "tremor",
        "syncope",
        "neuropathy",
        "disturbance",
    ],
    "Gastrointestinal": [
        "nausea",
        "vomiting",
        "diarrhoea",
        "diarrhea",
        "abdominal",
        "constipation",
        "gastrointestinal",
    ],
    "Respiratory": [
        "dyspnoea",
        "dyspnea",
        "cough",
        "wheezing",
        "respiratory",
        "breathing",
    ],
    "Cardiovascular": [
        "chest pain",
        "hypertension",
        "hypotension",
        "tachycardia",
        "arrhythmia",
        "cardiac",
        "palpitation",
    ],
    "Skin / allergy": [
        "rash",
        "pruritus",
        "urticaria",
        "allergy",
        "hypersensitivity",
        "swelling",
        "oedema",
        "edema",
    ],
    "Infection / immune": [
        "sepsis",
        "infection",
        "cellulitis",
        "erysipelas",
        "immune",
        "osteomyelitis",
    ],
    "Metabolic": [
        "weight",
        "glucose",
        "hypoglycaemia",
        "hypoglycemia",
        "hyperglycaemia",
        "hyperglycemia",
        "acidosis",
        "metabolic",
    ],
}


def classify_reaction(reaction_name: str) -> str:
    normalized = reaction_name.strip().lower()

    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return category

    return "General / other"


def classify_reactions(
    top_reactions: list[dict[str, int | str]],
) -> list[ReactionCategory]:
    category_counts: dict[str, int] = defaultdict(int)
    category_reactions: dict[str, set[str]] = defaultdict(set)

    for item in top_reactions:
        reaction = str(item.get("reaction", "")).strip()
        count = int(item.get("count", 0))

        if not reaction:
            continue

        category = classify_reaction(reaction)
        category_counts[category] += count
        category_reactions[category].add(reaction)

    return [
        {
            "category": category,
            "count": count,
            "reactions": sorted(category_reactions[category]),
        }
        for category, count in sorted(
            category_counts.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    ]
