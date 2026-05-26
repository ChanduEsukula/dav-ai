from datetime import datetime, timezone

from app.scoring.regional_health_signal import (
    PUBLIC_HEALTH_LIMITATION,
    calculate_regional_health_signal,
)
from app.schemas.regional_health import RegionalHealthSearchResponse


SOURCE_ID = "regional_health_pulse_demo"
SOURCE_NAME = "Regional Health Pulse MVP scaffold"
ENDPOINT = "https://healthdata.gov/"
DISCLAIMER = PUBLIC_HEALTH_LIMITATION


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

    return RegionalHealthSearchResponse(
        region=region.strip(),
        category=category.strip(),
        source_id=SOURCE_ID,
        source_name=SOURCE_NAME,
        endpoint=ENDPOINT,
        query=f"region={region.strip()} category={category.strip()}",
        retrieval_timestamp=datetime.now(timezone.utc).isoformat(),
        record_count=len(records),
        latest_period=str(latest_record["period"]) if latest_record else None,
        latest_value=latest_value,
        previous_period=str(previous_record["period"]) if previous_record else None,
        previous_value=previous_value,
        signal=signal,
        records=records,
        disclaimer=DISCLAIMER,
    )
