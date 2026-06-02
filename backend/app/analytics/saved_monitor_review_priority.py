"""Explainable saved-monitor review-priority preview.

This module is intentionally backend-only and safety-bounded.

It does not predict clinical risk, product danger, outbreak activity, causality,
or patient-level outcomes. It provides an operational public-data review-priority
preview for saved-monitor runs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


PriorityLabel = Literal["routine", "watch", "review"]

PREVIEW_VERSION = "saved-monitor-review-priority-preview-v0.1"

UNSAFE_CLINICAL_TERMS = (
    "clinical risk",
    "patient risk",
    "diagnosis",
    "treatment",
    "caused by",
    "causation",
    "outbreak detected",
    "medical urgency",
    "stop taking",
    "start taking",
    "change medication",
)


@dataclass(frozen=True)
class SavedMonitorReviewPriorityInput:
    """Inputs for saved-monitor public-data review-priority scoring."""

    module: str
    current_record_count: int | None = None
    previous_record_count: int | None = None
    payload_changed: bool | None = None
    source_freshness_status: str | None = None
    upstream_status: str | None = None
    insufficient_history: bool = False


@dataclass(frozen=True)
class SavedMonitorReviewPriorityResult:
    priority_label: PriorityLabel
    priority_score: int
    reasons: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    preview_version: str = PREVIEW_VERSION
    is_production_ml: bool = False


def evaluate_saved_monitor_review_priority(
    review_input: SavedMonitorReviewPriorityInput,
) -> SavedMonitorReviewPriorityResult:
    """Return an explainable public-data review-priority preview.

    The scoring is deterministic and intentionally conservative. It is a preview
    baseline, not production ML.
    """

    score = 10
    reasons: list[str] = []
    limitations: list[str] = [
        "This is an operational public-data review-priority preview only.",
        "This is not medical advice or production ML.",
        "This preview does not infer cause-and-effect relationships, product danger, personal risk, public-health event activity, or urgency.",
    ]

    current_count = _safe_nonnegative_count(review_input.current_record_count)
    previous_count = _safe_nonnegative_count(review_input.previous_record_count)
    upstream_status = (review_input.upstream_status or "").strip().lower()
    freshness_status = (review_input.source_freshness_status or "").strip().lower()
    payload_changed = bool(review_input.payload_changed)

    if review_input.insufficient_history or previous_count is None:
        score += 10
        reasons.append("There is not enough prior run history to compare this monitor confidently.")
        limitations.append("Additional saved-monitor runs are needed before trend-style review signals become meaningful.")
    else:
        delta = (current_count or 0) - previous_count
        percent_change = _percent_change(current_count or 0, previous_count)

        if delta == 0 and not payload_changed:
            reasons.append("Record count and payload state appear stable compared with the previous run.")
        elif delta > 0:
            reasons.append(f"Record count increased by {delta} compared with the previous run.")
            if percent_change is not None:
                reasons.append(f"Record count changed by approximately {percent_change:.1f}% from the previous run.")

            if percent_change is not None and percent_change >= 100:
                score += 45
            elif percent_change is not None and percent_change >= 25:
                score += 25
            else:
                score += 15
        elif delta < 0:
            reasons.append(f"Record count decreased by {abs(delta)} compared with the previous run.")
            score += 10

    if payload_changed:
        score += 25
        reasons.append("Source payload hash changed compared with the prior run.")

    if upstream_status and upstream_status not in {"ok", "success", "available"}:
        score += 50
        reasons.append("Upstream source retrieval did not complete successfully and should be reviewed.")

    if freshness_status in {"stale", "warning", "unknown", "error"}:
        score += 20
        reasons.append("Source freshness status indicates the data may need review.")

    if not reasons:
        reasons.append("No notable public-data review signal was detected from the available monitor metadata.")

    score = max(0, min(100, score))
    label = _label_for_score(score)

    result = SavedMonitorReviewPriorityResult(
        priority_label=label,
        priority_score=score,
        reasons=reasons,
        limitations=limitations,
    )

    _assert_no_unsafe_clinical_language(result)
    return result


def _safe_nonnegative_count(value: int | None) -> int | None:
    if value is None:
        return None
    return max(0, int(value))


def _percent_change(current_count: int, previous_count: int | None) -> float | None:
    if previous_count is None or previous_count <= 0:
        return None
    return ((current_count - previous_count) / previous_count) * 100


def _label_for_score(score: int) -> PriorityLabel:
    if score >= 70:
        return "review"
    if score >= 35:
        return "watch"
    return "routine"


def _assert_no_unsafe_clinical_language(
    result: SavedMonitorReviewPriorityResult,
) -> None:
    combined = " ".join(
        [result.priority_label, *result.reasons, *result.limitations]
    ).lower()

    for term in UNSAFE_CLINICAL_TERMS:
        if term in combined:
            raise ValueError(
                f"Saved-monitor review-priority preview used unsafe wording: {term}"
            )
