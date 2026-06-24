from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.audit import AuditSummary


RecallSourceKind = Literal[
    "structured_api",
    "public_notice",
    "normalized_public_notice",
]


class RecallScoreComponents(BaseModel):
    classification_score: int
    status_score: int
    recency_score: int
    scope_score: int


class RecallRiskScore(BaseModel):
    score: int
    label: str
    components: RecallScoreComponents
    score_version: str


class RecallSource(BaseModel):
    name: str
    endpoint: str
    retrieval_timestamp: str
    source_kind: RecallSourceKind = "structured_api"
    source_type: str = "official API record"


class RecallCheckedSource(BaseModel):
    source_id: str
    source_name: str
    source_type: str
    endpoint: str
    source_kind: RecallSourceKind
    record_type: str
    upstream_status: str
    record_count: int
    error: str | None = None


class RecallResult(BaseModel):
    recall_number: str | None
    product_description: str | None
    reason_for_recall: str | None
    classification: str | None
    status: str | None
    recall_initiation_date: str | None
    distribution_pattern: str | None
    recalling_firm: str | None
    source_type: str = "OPENFDA_DRUG_ENFORCEMENT"
    source_kind: RecallSourceKind = "structured_api"
    source_record_type: str = "official API record"
    title: str | None = None
    product_name: str | None = None
    brand_name: str | None = None
    company_name: str | None = None
    remedy: str | None = None
    record_url: str | None = None
    extraction_confidence: str | None = None
    source_text_excerpt: str | None = None
    risk_score: RecallRiskScore
    source: RecallSource


class RecallSemanticMatch(BaseModel):
    record_id: str
    text: str
    similarity_score: float
    explanation: str
    source_name: str | None = None


class RecallSemanticPreview(BaseModel):
    query_text: str
    matches: list[RecallSemanticMatch]
    limitations: list[str]
    preview_version: str
    is_production_ml: bool


class RecallSearchResponse(BaseModel):
    query: str
    raw_query: str
    normalized_query: str
    correction_applied: bool
    suggestion_message: str | None = None
    count: int
    limit: int
    source_name: str
    endpoint: str
    retrieval_timestamp: str
    score_version: str
    medical_disclaimer: str
    sources_checked: list[RecallCheckedSource] = Field(default_factory=list)
    audit: AuditSummary
    semantic_preview: RecallSemanticPreview | None = None
    results: list[RecallResult]
