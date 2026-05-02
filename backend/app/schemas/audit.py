from pydantic import BaseModel


class AuditSummary(BaseModel):
    audit_id: str
    source_id: str
    module: str
    upstream_status: str
    record_count: int
    transform_version: str