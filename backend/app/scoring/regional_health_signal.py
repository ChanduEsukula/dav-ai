from typing import Literal, TypedDict


REGIONAL_HEALTH_SIGNAL_VERSION = "regional-health-signal-v0.1"

PUBLIC_HEALTH_LIMITATION = (
    "Regional Health Pulse uses public-data signals only. It is not medical advice, "
    "diagnosis, treatment guidance, emergency guidance, clinical decision support, "
    "or a personal disease-risk prediction."
)


class RegionalHealthSignal(TypedDict):
    trend_label: Literal["Increasing", "Stable", "Decreasing", "Insufficient data"]
    review_priority: Literal["Low", "Watch", "Review"]
    confidence: Literal["Limited", "Moderate"]
    change_percent: float | None
    signal_version: str
    limitations: list[str]


def _trend_label(previous_value: int | None, latest_value: int | None) -> str:
    if previous_value is None or latest_value is None:
        return "Insufficient data"

    if previous_value == 0 and latest_value == 0:
        return "Stable"

    if previous_value == 0:
        return "Increasing"

    change_percent = ((latest_value - previous_value) / previous_value) * 100

    if change_percent >= 20:
        return "Increasing"
    if change_percent <= -20:
        return "Decreasing"
    return "Stable"


def _change_percent(previous_value: int | None, latest_value: int | None) -> float | None:
    if previous_value is None or latest_value is None or previous_value == 0:
        return None

    return round(((latest_value - previous_value) / previous_value) * 100, 2)


def _review_priority(trend_label: str, latest_value: int | None) -> str:
    if latest_value is None:
        return "Low"

    if trend_label == "Increasing" and latest_value >= 50:
        return "Review"

    if trend_label == "Increasing":
        return "Watch"

    return "Low"


def calculate_regional_health_signal(
    *,
    previous_value: int | None,
    latest_value: int | None,
    record_count: int,
) -> RegionalHealthSignal:
    trend_label = _trend_label(previous_value, latest_value)

    return {
        "trend_label": trend_label,
        "review_priority": _review_priority(trend_label, latest_value),
        "confidence": "Moderate" if record_count >= 2 else "Limited",
        "change_percent": _change_percent(previous_value, latest_value),
        "signal_version": REGIONAL_HEALTH_SIGNAL_VERSION,
        "limitations": [
            PUBLIC_HEALTH_LIMITATION,
            "Trend labels are based on returned public-data records in this MVP scaffold, not complete real-time disease surveillance.",
            "Users should verify current guidance with official public-health authorities.",
        ],
    }
