from pydantic import BaseModel


class DatabaseStatus(BaseModel):
    configured: bool
    audit_readable: bool


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
