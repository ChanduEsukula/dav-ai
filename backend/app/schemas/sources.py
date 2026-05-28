from pydantic import BaseModel


class SourceRecord(BaseModel):
    source_id: str
    source_name: str
    endpoint: str
    module: str
    description: str
    update_cadence: str
    freshness_status: str = "unknown"
    freshness_label: str = "Unknown"
    freshness_days_since_last_success: int | None = None
    last_successful_retrieval_at: str | None = None
    last_attempted_retrieval_at: str | None = None
    last_record_count: int | None = None
    last_error_message: str | None = None
    freshness_reason: str = "No audit history found for this source yet."
    freshness_safety_note: str = (
        "Source freshness is an operational review signal based on Dav AI audit "
        "history. It does not prove source correctness, medical risk, clinical "
        "urgency, product danger, causation, or outbreak activity."
    )


class SourceRegistryResponse(BaseModel):
    count: int
    sources: list[SourceRecord]