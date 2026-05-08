from typing import Any


DRUG_SIGNAL_TREND_VERSION = "drug-signal-trend-v0.1"
TREND_LIMITATION = (
    "Trend is based only on stored public-data searches in MedTrek AI, not all FDA activity."
)


def _trend_label(current_count: int, previous_count: int | None) -> str:
    if previous_count is None:
        return "Insufficient history"

    if current_count > previous_count:
        return "Increased"

    if current_count < previous_count:
        return "Decreased"

    return "Stable"


def build_drug_signal_trend_snapshot(
    current_record_count: int,
    previous_event: dict[str, Any] | None,
) -> dict[str, Any]:
    previous_record_count = (
        int(previous_event["record_count"])
        if previous_event and previous_event.get("record_count") is not None
        else None
    )

    label = _trend_label(current_record_count, previous_record_count)

    if previous_event:
        explanation = (
            "Compared with the most recent stored DrugSignal audit event for this query."
        )
    else:
        explanation = (
            "No previous stored DrugSignal audit event was available for this query."
        )

    return {
        "label": label,
        "current_record_count": current_record_count,
        "previous_record_count": previous_record_count,
        "previous_audit_id": str(previous_event["audit_id"]) if previous_event else None,
        "previous_created_at": previous_event.get("created_at") if previous_event else None,
        "explanation": explanation,
        "limitation": TREND_LIMITATION,
        "trend_version": DRUG_SIGNAL_TREND_VERSION,
    }
