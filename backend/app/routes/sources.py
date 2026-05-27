from datetime import datetime, timezone

from fastapi import APIRouter, Request

from app.db.audit_repository import get_latest_audit_event_for_source
from app.schemas.sources import SourceRegistryResponse
from app.sources.registry import REGISTERED_SOURCES

router = APIRouter()

FRESHNESS_WINDOW_DAYS = 14


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


def _build_freshness(source: dict, latest_event: dict | None, repository_status: str) -> dict:
    if repository_status == "skipped":
        return {
            **source,
            "freshness_status": "unknown",
            "freshness_label": "Unknown",
            "last_successful_retrieval_at": None,
            "last_attempted_retrieval_at": None,
            "last_record_count": None,
            "last_error_message": None,
            "freshness_reason": "Database is not configured, so audit history is not available for freshness checks.",
        }

    if repository_status == "error":
        return {
            **source,
            "freshness_status": "error",
            "freshness_label": "Error",
            "last_successful_retrieval_at": None,
            "last_attempted_retrieval_at": None,
            "last_record_count": None,
            "last_error_message": "Could not read latest audit event for this source.",
            "freshness_reason": "Audit history lookup failed, so source freshness could not be calculated.",
        }

    if latest_event is None:
        return {
            **source,
            "freshness_status": "unknown",
            "freshness_label": "Unknown",
            "last_successful_retrieval_at": None,
            "last_attempted_retrieval_at": None,
            "last_record_count": None,
            "last_error_message": None,
            "freshness_reason": "No audit history found for this source yet.",
        }

    upstream_status = latest_event.get("upstream_status")
    retrieval_timestamp = latest_event.get("retrieval_timestamp")
    created_at = latest_event.get("created_at")
    attempted_at = _iso_or_none(retrieval_timestamp or created_at)

    if upstream_status == "error":
        return {
            **source,
            "freshness_status": "error",
            "freshness_label": "Error",
            "last_successful_retrieval_at": None,
            "last_attempted_retrieval_at": attempted_at,
            "last_record_count": latest_event.get("record_count"),
            "last_error_message": latest_event.get("error_message") or "Latest upstream retrieval failed.",
            "freshness_reason": "The latest audit event for this source recorded an upstream error.",
        }

    successful_at = _as_utc_datetime(retrieval_timestamp or created_at)

    if successful_at is None:
        return {
            **source,
            "freshness_status": "unknown",
            "freshness_label": "Unknown",
            "last_successful_retrieval_at": None,
            "last_attempted_retrieval_at": attempted_at,
            "last_record_count": latest_event.get("record_count"),
            "last_error_message": latest_event.get("error_message"),
            "freshness_reason": "The latest audit event did not include a usable retrieval timestamp.",
        }

    age_days = (datetime.now(timezone.utc) - successful_at).days

    if age_days <= FRESHNESS_WINDOW_DAYS:
        freshness_status = "fresh"
        freshness_label = "Fresh"
        freshness_reason = (
            f"Last successful retrieval was {age_days} day(s) ago, within the "
            f"{FRESHNESS_WINDOW_DAYS}-day MVP freshness window."
        )
    else:
        freshness_status = "delayed"
        freshness_label = "Delayed"
        freshness_reason = (
            f"Last successful retrieval was {age_days} day(s) ago, outside the "
            f"{FRESHNESS_WINDOW_DAYS}-day MVP freshness window."
        )

    return {
        **source,
        "freshness_status": freshness_status,
        "freshness_label": freshness_label,
        "last_successful_retrieval_at": successful_at.isoformat(),
        "last_attempted_retrieval_at": attempted_at,
        "last_record_count": latest_event.get("record_count"),
        "last_error_message": latest_event.get("error_message"),
        "freshness_reason": freshness_reason,
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