from typing import Literal

from pydantic import BaseModel, Field


RealWorldSafetySourceKind = Literal["structured_api", "public_notice"]


class RealWorldSafetyRecord(BaseModel):
    source_name: str
    source_type: str
    source_url: str
    source_kind: RealWorldSafetySourceKind
    category: str | None = None
    product_name: str | None = None
    brand_name: str | None = None
    company_name: str | None = None
    title: str | None = None
    reason: str | None = None
    hazard_type: str | None = None
    remedy: str | None = None
    published_date: str | None = None
    recall_number: str | None = None
    affected_models: list[str] = Field(default_factory=list)
    affected_lots: list[str] = Field(default_factory=list)
    raw_payload_hash: str
    retrieved_at: str
    record_url: str | None = None


class RealWorldSafetyCheckedSource(BaseModel):
    source_id: str
    source_name: str
    source_type: str
    source_url: str
    source_kind: RealWorldSafetySourceKind
    upstream_status: str
    record_count: int


class RealWorldSafetyFailedSource(BaseModel):
    source_id: str
    source_name: str
    source_type: str
    source_url: str
    source_kind: RealWorldSafetySourceKind
    error_type: str
    reason: str


class RealWorldSafetyAuditSummary(BaseModel):
    audit_id: str
    source_id: str
    source_name: str
    module: str
    upstream_status: str
    record_count: int
    transform_version: str
    source_snapshot_status: str | None = None
    source_pull_id: str | None = None
    source_payload_hash: str | None = None


class RealWorldSafetySearchResponse(BaseModel):
    query: str
    raw_query: str
    count: int
    limit: int
    retrieval_timestamp: str
    sources_checked: list[RealWorldSafetyCheckedSource]
    sources_failed: list[RealWorldSafetyFailedSource]
    records_per_source: dict[str, int]
    structured_api_matches: int
    public_notice_matches: int
    total_matches: int
    no_match_explanation: str | None = None
    public_data_disclaimer: str
    limitations: list[str]
    source_audits: list[RealWorldSafetyAuditSummary]
    results: list[RealWorldSafetyRecord]
