from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AuditHistoryItem(BaseModel):
    audit_id: UUID
    module: str
    source_id: str
    source_name: str
    endpoint: str
    query: str
    query_params: dict[str, Any] = Field(default_factory=dict)
    retrieval_timestamp: datetime
    upstream_status: str
    record_count: int
    transform_version: str
    score_version: str | None = None
    disclaimer_version: str | None = None
    error_message: str | None = None
    created_at: datetime


class AuditHistoryListResponse(BaseModel):
    status: str
    persistence_available: bool
    count: int
    items: list[AuditHistoryItem]


class AuditHistoryDetailResponse(BaseModel):
    status: str
    persistence_available: bool
    item: AuditHistoryItem | None = None
    message: str | None = None
