"""Deterministic source freshness and payload-change helpers.

These helpers produce operational review signals from Dav AI audit/source-pull
metadata. They are not clinical risk models, not source-of-truth guarantees,
and not medical safety determinations.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class FreshnessLabel(str, Enum):
    FRESH = "fresh"
    AGING = "aging"
    STALE = "stale"
    UNKNOWN = "unknown"
    SOURCE_ERROR = "source_error"


class PayloadChangeLabel(str, Enum):
    FIRST_SEEN = "first_seen"
    UNCHANGED = "unchanged"
    CHANGED = "changed"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class SourceFreshnessResult:
    label: FreshnessLabel
    days_since_last_success: int | None
    reason: str
    safety_note: str


@dataclass(frozen=True)
class PayloadChangeResult:
    label: PayloadChangeLabel
    previous_hash: str | None
    latest_hash: str | None
    reason: str
    safety_note: str


SOURCE_FRESHNESS_SAFETY_NOTE = (
    "Source freshness is an operational review signal based on Dav AI audit "
    "history. It does not prove source correctness, medical risk, clinical "
    "urgency, product danger, causation, or outbreak activity."
)

PAYLOAD_CHANGE_SAFETY_NOTE = (
    "Payload-change status is an operational public-data review signal based "
    "on stored payload hashes. It does not prove medical risk, clinical "
    "urgency, product danger, causation, or source correctness."
)


def _coerce_datetime(value: datetime | str | None) -> datetime | None:
    """Convert a datetime-like value to an aware UTC datetime when possible."""

    if value is None:
        return None

    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return None
    else:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def classify_source_freshness(
    *,
    latest_success_at: datetime | str | None,
    latest_upstream_status: str | None = None,
    now: datetime | str | None = None,
    fresh_after_days: int = 2,
    stale_after_days: int = 14,
) -> SourceFreshnessResult:
    """Classify source freshness from latest successful audit/source-pull metadata.

    The labels are intentionally conservative:
    - source_error: latest upstream status indicates an error.
    - unknown: no usable timestamp exists.
    - fresh: latest success is recent.
    - aging: latest success exists but is not very recent.
    - stale: latest success is older than the stale threshold.
    """

    status = (latest_upstream_status or "").strip().lower()
    if status in {"error", "failed", "failure", "timeout", "unavailable"}:
        return SourceFreshnessResult(
            label=FreshnessLabel.SOURCE_ERROR,
            days_since_last_success=None,
            reason="Latest upstream status indicates a source or retrieval error.",
            safety_note=SOURCE_FRESHNESS_SAFETY_NOTE,
        )

    parsed_success_at = _coerce_datetime(latest_success_at)
    parsed_now = _coerce_datetime(now) or datetime.now(timezone.utc)

    if parsed_success_at is None:
        return SourceFreshnessResult(
            label=FreshnessLabel.UNKNOWN,
            days_since_last_success=None,
            reason="No usable latest successful retrieval timestamp is available.",
            safety_note=SOURCE_FRESHNESS_SAFETY_NOTE,
        )

    delta = parsed_now - parsed_success_at
    days_since = max(delta.days, 0)

    if days_since <= fresh_after_days:
        return SourceFreshnessResult(
            label=FreshnessLabel.FRESH,
            days_since_last_success=days_since,
            reason="Latest successful retrieval is within the fresh threshold.",
            safety_note=SOURCE_FRESHNESS_SAFETY_NOTE,
        )

    if days_since >= stale_after_days:
        return SourceFreshnessResult(
            label=FreshnessLabel.STALE,
            days_since_last_success=days_since,
            reason="Latest successful retrieval is older than the stale threshold.",
            safety_note=SOURCE_FRESHNESS_SAFETY_NOTE,
        )

    return SourceFreshnessResult(
        label=FreshnessLabel.AGING,
        days_since_last_success=days_since,
        reason="Latest successful retrieval is available but no longer fresh.",
        safety_note=SOURCE_FRESHNESS_SAFETY_NOTE,
    )


def classify_payload_change(
    *,
    latest_payload_hash: str | None,
    previous_payload_hash: str | None,
    latest_available: bool = True,
) -> PayloadChangeResult:
    """Classify payload-level change using stable payload hashes."""

    latest = (latest_payload_hash or "").strip() or None
    previous = (previous_payload_hash or "").strip() or None

    if not latest_available:
        return PayloadChangeResult(
            label=PayloadChangeLabel.UNAVAILABLE,
            previous_hash=previous,
            latest_hash=latest,
            reason="Latest payload hash is unavailable because the source response was unavailable.",
            safety_note=PAYLOAD_CHANGE_SAFETY_NOTE,
        )

    if latest is None:
        return PayloadChangeResult(
            label=PayloadChangeLabel.UNKNOWN,
            previous_hash=previous,
            latest_hash=None,
            reason="Latest payload hash is missing.",
            safety_note=PAYLOAD_CHANGE_SAFETY_NOTE,
        )

    if previous is None:
        return PayloadChangeResult(
            label=PayloadChangeLabel.FIRST_SEEN,
            previous_hash=None,
            latest_hash=latest,
            reason="No previous payload hash is available for comparison.",
            safety_note=PAYLOAD_CHANGE_SAFETY_NOTE,
        )

    if latest == previous:
        return PayloadChangeResult(
            label=PayloadChangeLabel.UNCHANGED,
            previous_hash=previous,
            latest_hash=latest,
            reason="Latest payload hash matches the previous payload hash.",
            safety_note=PAYLOAD_CHANGE_SAFETY_NOTE,
        )

    return PayloadChangeResult(
        label=PayloadChangeLabel.CHANGED,
        previous_hash=previous,
        latest_hash=latest,
        reason="Latest payload hash differs from the previous payload hash.",
        safety_note=PAYLOAD_CHANGE_SAFETY_NOTE,
    )


def freshness_result_to_dict(result: SourceFreshnessResult) -> dict[str, Any]:
    return {
        "label": result.label.value,
        "days_since_last_success": result.days_since_last_success,
        "reason": result.reason,
        "safety_note": result.safety_note,
    }


def payload_change_result_to_dict(result: PayloadChangeResult) -> dict[str, Any]:
    return {
        "label": result.label.value,
        "previous_hash": result.previous_hash,
        "latest_hash": result.latest_hash,
        "reason": result.reason,
        "safety_note": result.safety_note,
    }