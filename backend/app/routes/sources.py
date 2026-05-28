from datetime import datetime, timezone

from fastapi import APIRouter, Request

from app.db.audit_repository import get_latest_audit_event_for_source
from app.schemas.sources import SourceRegistryResponse
from app.scoring.source_freshness import (
    FreshnessLabel,
    SOURCE_FRESHNESS_SAFETY_NOTE,
    classify_source_freshness,
)
from app.sources.registry import REGISTERED_SOURCES

router = APIRouter()


def _as_utc_datetime(value) -> datetime | None:
    if value is None:
        return None

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return None

        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    return None


def _iso_or_none(value) -> str | None:
    parsed = _as_utc_datetime(value)
    if parsed is None:
        return None
    return parsed.isoformat()


def _source_freshness_label(label: FreshnessLabel) -> str:
    labels = {
        FreshnessLabel.FRESH: "Fresh",
        FreshnessLabel.AGING: "Aging",
        FreshnessLabel.STALE: "Stale",
        FreshnessLabel.UNKNOWN: "Unknown",
        FreshnessLabel.SOURCE_ERROR: "Source Error",
    }
    return labels[label]


def _build_freshness(source: dict, latest_event: dict | None, repository_status: str) -> dict:
    if repository_status == "skipped":
        freshness = classify_source_freshness(
            latest_success_at=None,
            latest_upstream_status=None,
        )
        return {
            **source,
            "freshness_status": freshness.label.value,
            "freshness_label": _source_freshness_label(freshness.label),
            "freshness_days_since_last_success": freshness.days_since_last_success,
            "last_successful_retrieval_at": None,
            "last_attempted_retrieval_at": None,
            "last_record_count": None,
            "last_error_message": None,
            "freshness_reason": "Database is not configured, so audit history is not available for freshness checks.",
            "freshness_safety_note": freshness.safety_note,
        }

    if repository_status == "error":
        freshness = classify_source_freshness(
            latest_success_at=None,
            latest_upstream_status="error",
        )
        return {
            **source,
            "freshness_status": freshness.label.value,
            "freshness_label": _source_freshness_label(freshness.label),
            "freshness_days_since_last_success": freshness.days_since_last_success,
            "last_successful_retrieval_at": None,
            "last_attempted_retrieval_at": None,
            "last_record_count": None,
            "last_error_message": "Could not read latest audit event for this source.",
            "freshness_reason": "Audit history lookup failed, so source freshness could not be calculated.",
            "freshness_safety_note": freshness.safety_note,
        }

    if latest_event is None:
        freshness = classify_source_freshness(
            latest_success_at=None,
            latest_upstream_status=None,
        )
        return {
            **source,
            "freshness_status": freshness.label.value,
            "freshness_label": _source_freshness_label(freshness.label),
            "freshness_days_since_last_success": freshness.days_since_last_success,
            "last_successful_retrieval_at": None,
            "last_attempted_retrieval_at": None,
            "last_record_count": None,
            "last_error_message": None,
            "freshness_reason": "No audit history found for this source yet.",
            "freshness_safety_note": freshness.safety_note,
        }

    upstream_status = latest_event.get("upstream_status")
    retrieval_timestamp = latest_event.get("retrieval_timestamp")
    created_at = latest_event.get("created_at")
    attempted_at = _iso_or_none(retrieval_timestamp or created_at)

    latest_success_at = None if upstream_status == "error" else retrieval_timestamp or created_at

    freshness = classify_source_freshness(
        latest_success_at=latest_success_at,
        latest_upstream_status=upstream_status,
    )

    last_successful_retrieval_at = None
    if freshness.label not in {FreshnessLabel.UNKNOWN, FreshnessLabel.SOURCE_ERROR}:
        last_successful_retrieval_at = _iso_or_none(latest_success_at)

    last_error_message = latest_event.get("error_message")
    if freshness.label == FreshnessLabel.SOURCE_ERROR and not last_error_message:
        last_error_message = "Latest upstream retrieval failed."

    return {
        **source,
        "freshness_status": freshness.label.value,
        "freshness_label": _source_freshness_label(freshness.label),
        "freshness_days_since_last_success": freshness.days_since_last_success,
        "last_successful_retrieval_at": last_successful_retrieval_at,
        "last_attempted_retrieval_at": attempted_at,
        "last_record_count": latest_event.get("record_count"),
        "last_error_message": last_error_message,
        "freshness_reason": freshness.reason,
        "freshness_safety_note": freshness.safety_note or SOURCE_FRESHNESS_SAFETY_NOTE,
    }


@router.get("", response_model=SourceRegistryResponse)
async def list_sources(request: Request):
    request_id = getattr(request.state, "request_id", None)

    sources = []

    for source in REGISTERED_SOURCES:
        repository_status, latest_event = get_latest_audit_event_for_source(
            source_id=source["source_id"],
            request_id=request_id,
        )
        sources.append(_build_freshness(source, latest_event, repository_status))

    return {
        "count": len(sources),
        "sources": sources,
    }