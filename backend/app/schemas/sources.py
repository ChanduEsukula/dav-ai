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
    last_successful_retrieval_at: str | None = None
    last_attempted_retrieval_at: str | None = None
    last_record_count: int | None = None
    last_error_message: str | None = None
    freshness_reason: str = "No audit history found for this source yet."


class SourceRegistryResponse(BaseModel):
    count: int
    sources: list[SourceRecord]
