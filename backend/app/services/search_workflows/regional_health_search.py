from datetime import datetime, timezone
from typing import Any

from app.audit.audit_event import build_audit_event
from app.db.audit_repository import save_audit_event
from app.db.source_pull_repository import save_source_pull_with_snapshot
from app.scoring.regional_health_signal import (
    PUBLIC_HEALTH_LIMITATION,
    calculate_regional_health_signal,
)
from app.schemas.regional_health import RegionalHealthSearchResponse


SOURCE_ID = "regional_health_pulse_demo"
SOURCE_NAME = "Regional Health Pulse MVP scaffold"
ENDPOINT = "https://healthdata.gov/"
DISCLAIMER = PUBLIC_HEALTH_LIMITATION

TRANSFORM_VERSION = "regional-health-transform-v0.1"
SOURCE_UPDATE_CADENCE = "MVP scaffold data; live CDC/HHS update cadence is not configured yet."
SOURCE_FRESHNESS = {
    "freshness_status": "scaffold",
    "freshness_label": "Scaffold data",
    "source_update_cadence": SOURCE_UPDATE_CADENCE,
    "freshness_message": (
        "Regional Health Pulse is using MVP scaffold data. Live CDC/HHS freshness "
        "checks are not configured yet."
    ),
}


def _save_audit_event_with_request_id(audit_event: dict[str, Any], request_id: str | None):
    try:
        return save_audit_event(audit_event, request_id=request_id)
    except TypeError as exc:
        if "request_id" not in str(exc):
            raise
        return save_audit_event(audit_event)


def _save_source_pull_with_request_id(
    *,
    audit_event: dict[str, Any],
    raw_payload: dict[str, Any],
    request_id: str | None,
):
    try:
        return save_source_pull_with_snapshot(
            audit_event=audit_event,
            raw_payload=raw_payload,
            request_id=request_id,
        )
    except TypeError as exc:
        if "request_id" not in str(exc):
            raise
        return save_source_pull_with_snapshot(
            audit_event=audit_event,
            raw_payload=raw_payload,
        )


_SAMPLE_DATA = {
    ("mn", "respiratory"): [
        {"period": "2026-W18", "value": 32, "label": "Respiratory public-data signal"},
        {"period": "2026-W19", "value": 46, "label": "Respiratory public-data signal"},
    ],
    ("ca", "respiratory"): [
        {"period": "2026-W18", "value": 80, "label": "Respiratory public-data signal"},
        {"period": "2026-W19", "value": 64, "label": "Respiratory public-data signal"},
    ],
    ("mn", "hospital_pressure"): [
        {"period": "2026-W18", "value": 41, "label": "Hospital pressure public-data signal"},
        {"period": "2026-W19", "value": 43, "label": "Hospital pressure public-data signal"},
    ],
}


def _normalize(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


def execute_regional_health_search(
    *,
    region: str,
    category: str,
    request_id: str | None,
) -> RegionalHealthSearchResponse:
    normalized_region = _normalize(region)
    normalized_category = _normalize(category)
    records = _SAMPLE_DATA.get((normalized_region, normalized_category), [])

    previous_record = records[-2] if len(records) >= 2 else None
    latest_record = records[-1] if records else None

    previous_value = int(previous_record["value"]) if previous_record else None
    latest_value = int(latest_record["value"]) if latest_record else None

    signal = calculate_regional_health_signal(
        previous_value=previous_value,
        latest_value=latest_value,
        record_count=len(records),
    )

    query = f"region={region.strip()} category={category.strip()}"
    retrieval_timestamp = datetime.now(timezone.utc).isoformat()
    upstream_status = "empty" if not records else "success"

    audit_event = build_audit_event(
        module="RegionalHealthPulse",
        source_id=SOURCE_ID,
        source_name=SOURCE_NAME,
        endpoint=ENDPOINT,
        query=query,
        query_params={
            "region": region.strip(),
            "category": category.strip(),
        },
        retrieval_timestamp=retrieval_timestamp,
        upstream_status=upstream_status,
        record_count=len(records),
        transform_version=TRANSFORM_VERSION,
        score_version=signal["signal_version"],
    )

    _save_audit_event_with_request_id(audit_event, request_id=request_id)

    raw_payload = {
        "source": SOURCE_NAME,
        "endpoint": ENDPOINT,
        "region": region.strip(),
        "category": category.strip(),
        "records": records,
        "signal": signal,
        "disclaimer": DISCLAIMER,
    }

    source_pull_result = _save_source_pull_with_request_id(
        audit_event=audit_event,
        raw_payload=raw_payload,
        request_id=request_id,
    )

    return RegionalHealthSearchResponse(
        region=region.strip(),
        category=category.strip(),
        source_id=SOURCE_ID,
        source_name=SOURCE_NAME,
        endpoint=ENDPOINT,
        query=query,
        retrieval_timestamp=retrieval_timestamp,
        record_count=len(records),
        source_freshness=SOURCE_FRESHNESS,
        latest_period=str(latest_record["period"]) if latest_record else None,
        latest_value=latest_value,
        previous_period=str(previous_record["period"]) if previous_record else None,
        previous_value=previous_value,
        signal=signal,
        records=records,
        disclaimer=DISCLAIMER,
        audit={
            "audit_id": audit_event["audit_id"],
            "source_id": audit_event["source_id"],
            "module": audit_event["module"],
            "upstream_status": audit_event["upstream_status"],
            "record_count": audit_event["record_count"],
            "transform_version": audit_event["transform_version"],
            "source_snapshot_status": source_pull_result["status"],
            "source_pull_id": source_pull_result["pull_id"],
            "source_payload_hash": source_pull_result["payload_hash"],
        },
    )
