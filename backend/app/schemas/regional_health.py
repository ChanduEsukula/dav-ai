from pydantic import BaseModel, Field


class RegionalHealthPoint(BaseModel):
    period: str
    value: int
    label: str


class RegionalHealthSignalSummary(BaseModel):
    trend_label: str
    review_priority: str
    confidence: str
    change_percent: float | None = None
    signal_version: str
    limitations: list[str]


class RegionalHealthSearchResponse(BaseModel):
    module: str = "RegionalHealthPulse"
    region: str
    category: str
    source_id: str
    source_name: str
    endpoint: str
    query: str
    retrieval_timestamp: str
    record_count: int
    latest_period: str | None = None
    latest_value: int | None = None
    previous_period: str | None = None
    previous_value: int | None = None
    signal: RegionalHealthSignalSummary
    records: list[RegionalHealthPoint] = Field(default_factory=list)
    disclaimer: str
