from typing import Literal, TypedDict

from app.scoring import DRUG_SIGNAL_SCORE_VERSION

FAERS_CAUSATION_LIMITATION = (
    "FAERS adverse-event reports are safety signals only and do not prove causation."
)


class DrugSignalIntelligenceScore(TypedDict):
    score: int
    label: Literal["Low", "Moderate", "High"]
    data_confidence: Literal["Limited", "Moderate", "Strong"]
    top_reaction_concentration: float
    review_priority: Literal["Low", "Watch", "Review"]
    score_version: str
    limitations: list[str]


def _record_count_component(record_count: int) -> int:
    if record_count <= 0:
        return 0
    if record_count <= 2:
        return 15
    if record_count <= 9:
        return 25
    return 35


def _concentration_component(concentration: float) -> int:
    if concentration >= 60:
        return 25
    if concentration >= 40:
        return 18
    if concentration >= 20:
        return 10
    return 5


def _reaction_diversity_component(reaction_count: int) -> int:
    if reaction_count <= 0:
        return 0
    if reaction_count == 1:
        return 5
    if reaction_count <= 4:
        return 12
    return 20


def _data_confidence(record_count: int) -> Literal["Limited", "Moderate", "Strong"]:
    if record_count <= 2:
        return "Limited"
    if record_count <= 9:
        return "Moderate"
    return "Strong"


def _data_confidence_component(confidence: str) -> int:
    if confidence == "Strong":
        return 20
    if confidence == "Moderate":
        return 12
    return 5


def _label(score: int) -> Literal["Low", "Moderate", "High"]:
    if score <= 30:
        return "Low"
    if score <= 60:
        return "Moderate"
    return "High"


def _review_priority(label: str) -> Literal["Low", "Watch", "Review"]:
    if label == "High":
        return "Review"
    if label == "Moderate":
        return "Watch"
    return "Low"


def calculate_drug_signal_intelligence_score(
    record_count: int,
    top_reactions: list[dict[str, int | str]],
) -> DrugSignalIntelligenceScore:
    if record_count <= 0:
        return {
            "score": 0,
            "label": "Low",
            "data_confidence": "Limited",
            "top_reaction_concentration": 0.0,
            "review_priority": "Low",
            "score_version": DRUG_SIGNAL_SCORE_VERSION,
            "limitations": [
                FAERS_CAUSATION_LIMITATION,
                "No score or confidence assessment should be displayed when no public records are returned.",
            ],
        }

    total_reaction_mentions = sum(int(item.get("count", 0)) for item in top_reactions)
    top_reaction_count = int(top_reactions[0].get("count", 0)) if top_reactions else 0

    top_reaction_concentration = (
        round((top_reaction_count / total_reaction_mentions) * 100, 2)
        if total_reaction_mentions > 0
        else 0.0
    )

    confidence = _data_confidence(record_count)

    score = min(
        100,
        _record_count_component(record_count)
        + _concentration_component(top_reaction_concentration)
        + _reaction_diversity_component(len(top_reactions))
        + _data_confidence_component(confidence),
    )

    label = _label(score)

    return {
        "score": score,
        "label": label,
        "data_confidence": confidence,
        "top_reaction_concentration": top_reaction_concentration,
        "review_priority": _review_priority(label),
        "score_version": DRUG_SIGNAL_SCORE_VERSION,
        "limitations": [
            FAERS_CAUSATION_LIMITATION,
            "Scores are based on returned public openFDA records and reaction counts, not clinical incidence rates.",
        ],
    }
