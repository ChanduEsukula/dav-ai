from typing import Literal

from pydantic import BaseModel, Field


RealWorldSafetySourceKind = Literal["structured_api", "public_notice", "normalized_public_notice"]


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
    extraction_confidence: str | None = None
    source_text_excerpt: str | None = None


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


class RealWorldSafetySourceFreshness(BaseModel):
    source_id: str
    source_name: str
    source_type: str
    source_kind: RealWorldSafetySourceKind
    upstream_status: str
    record_count: int
    freshness_status: str
    user_label: str
    explanation: str
    source_snapshot_status: str | None = None
    source_pull_id: str | None = None
    source_payload_hash: str | None = None
    checked_at: str


class RealWorldSafetyQueryUnderstanding(BaseModel):
    original_query: str
    normalized_query: str
    search_query: str
    corrections_applied: list[str] = Field(default_factory=list)
    expanded_terms: list[str] = Field(default_factory=list)
    expansion_search_terms_used: list[str] = Field(default_factory=list)
    detected_identifiers: dict[str, str | None]
    query_type_hints: list[str] = Field(default_factory=list)


class RealWorldSafetySearchPlan(BaseModel):
    intent: str
    confidence: str
    reason: str
    primary_source_ids: list[str] = Field(default_factory=list)
    secondary_source_ids: list[str] = Field(default_factory=list)
    sources_to_check: list[str] = Field(default_factory=list)
    clarification_required: bool = False


class RealWorldSafetyIntelligenceSummary(BaseModel):
    query_type: str
    recall_or_enforcement_found: bool
    reference_or_label_found: bool
    signal_report_found: bool
    outbreak_context_found: bool = False
    matched_sources_by_role: dict[str, list[str]]
    checked_sources_by_role: dict[str, list[str]]
    top_result_titles: list[str] = Field(default_factory=list)
    expansion_explanations: list[str] = Field(default_factory=list)
    plain_language_summary: str
    suggested_next_steps: list[str] = Field(default_factory=list)
    caveat: str


class RealWorldSafetyIdentifierCheckItem(BaseModel):
    type: str
    label: str
    value: str | None = None
    source: str
    reason: str


class RealWorldSafetyIdentifierCheck(BaseModel):
    detected: list[RealWorldSafetyIdentifierCheckItem] = Field(default_factory=list)
    to_verify: list[RealWorldSafetyIdentifierCheckItem] = Field(default_factory=list)
    user_message: str


class RealWorldSafetySearchResponse(BaseModel):
    query: str
    raw_query: str
    query_understanding: RealWorldSafetyQueryUnderstanding
    search_plan: RealWorldSafetySearchPlan
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
    safety_intelligence_summary: RealWorldSafetyIntelligenceSummary
    identifier_check: RealWorldSafetyIdentifierCheck
    public_data_disclaimer: str
    limitations: list[str]
    source_audits: list[RealWorldSafetyAuditSummary]
    source_freshness: list[RealWorldSafetySourceFreshness]
    results: list[RealWorldSafetyRecord]
