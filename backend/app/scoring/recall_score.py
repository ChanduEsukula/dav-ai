from datetime import datetime, timezone

from app.scoring import RECALL_REVIEW_SCORE_VERSION


CLASSIFICATION_WEIGHTS = {
    "Class I": 40,
    "Class II": 25,
    "Class III": 10,
}

STATUS_WEIGHTS = {
    "Ongoing": 20,
    "Completed": 5,
    "Terminated": 0,
}


def calculate_recall_risk_score(record: dict) -> dict:
    """Calculate a deterministic RecallRadar review-priority signal.

    The function name is kept for compatibility with existing routes, schemas,
    frontend types, and tests that still expect a `risk_score` field.

    This score is an operational review-priority signal over public recall
    records. It is not a medical-risk score, personal safety score, product
    danger score, or clinical urgency estimate.
    """
    classification = record.get("classification", "")
    status = record.get("status", "")

    classification_score = CLASSIFICATION_WEIGHTS.get(classification, 5)
    status_score = STATUS_WEIGHTS.get(status, 5)
    recency_score = _recency_score(record.get("recall_initiation_date"))
    scope_score = _scope_score(record.get("distribution_pattern", ""))

    total = classification_score + status_score + recency_score + scope_score
    total = max(0, min(total, 100))

    return {
        "score": total,
        "label": _score_label(total),
        "components": {
            "classification_score": classification_score,
            "status_score": status_score,
            "recency_score": recency_score,
            "scope_score": scope_score,
        },
        "score_version": RECALL_REVIEW_SCORE_VERSION,
    }


def _recency_score(date_string: str | None) -> int:
    if not date_string:
        return 5

    try:
        recall_date = datetime.strptime(date_string, "%Y%m%d").replace(tzinfo=timezone.utc)
        days_old = (datetime.now(timezone.utc) - recall_date).days

        if days_old <= 90:
            return 20
        if days_old <= 365:
            return 12
        if days_old <= 1095:
            return 6
        return 2
    except ValueError:
        return 5


def _scope_score(distribution_pattern: str) -> int:
    text = distribution_pattern.lower()

    if "nationwide" in text or "nation wide" in text:
        return 20
    if "multiple states" in text or "statewide" in text:
        return 12
    if len(text) > 120:
        return 10
    return 5


def _score_label(score: int) -> str:
    if score >= 81:
        return "High Attention"
    if score >= 61:
        return "High"
    if score >= 31:
        return "Moderate"
    return "Low"
