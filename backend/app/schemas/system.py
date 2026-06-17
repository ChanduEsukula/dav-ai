from typing import Literal

from pydantic import BaseModel

PersistenceMode = Literal["database", "memory_fallback"]


class DatabaseStatus(BaseModel):
    configured: bool
    audit_readable: bool
    persistence_mode: PersistenceMode
    durable_persistence: bool
    warning: str | None = None


class SourceStatus(BaseModel):
    registered_count: int
    available: bool


class SystemStatusResponse(BaseModel):
    status: str
    app: str
    version: str
    database: DatabaseStatus
    sources: SourceStatus
    modules: list[str]


class AuditStatusCounts(BaseModel):
    success: int
    empty: int
    error: int


class LatestAuditEventSummary(BaseModel):
    exists: bool
    audit_id: str | None = None
    module: str | None = None
    query: str | None = None
    upstream_status: str | None = None
    record_count: int | None = None
    created_at: str | None = None


class DataQualityResponse(BaseModel):
    status: str
    database_configured: bool
    audit_readable: bool
    persistence_mode: PersistenceMode
    durable_persistence: bool
    warning: str | None = None
    source_registry_count: int
    recent_audit_count: int
    upstream_status_counts: AuditStatusCounts
    latest_audit_event: LatestAuditEventSummary
