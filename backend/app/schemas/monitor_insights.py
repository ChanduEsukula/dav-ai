"""Schemas for deterministic AI Monitor Insights v1."""

from pydantic import BaseModel


class MonitorInsightResponse(BaseModel):
    monitor_id: str
    label: str
    headline: str
    explanation: str
    latest_run_id: str | None = None
    previous_run_id: str | None = None
    latest_record_count: int | None = None
    previous_record_count: int | None = None
    record_count_delta: int | None = None
    percent_change: float | None = None
    latest_score: int | None = None
    previous_score: int | None = None
    score_delta: int | None = None
    confidence: str
    insight_version: str
    limitation: str
