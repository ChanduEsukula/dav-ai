from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.audit import AuditSummary
from app.schemas.recalls import RecallRiskScore


EverydaySafetyCategory = Literal["food_supplement"]
EverydaySafetySourceType = Literal[
    "FDA_FOOD_ENFORCEMENT",
    "USDA_FSIS_RECALL",
    "FDA_PUBLIC_NOTICE",
    "FDA_NORMALIZED_PUBLIC_NOTICE",
]
EverydaySafetySourceKind = Literal[
    "structured_api",
    "public_notice",
    "normalized_public_notice",
]


class EverydaySafetySource(BaseModel):
    name: str
    endpoint: str
    retrieval_timestamp: str
    source_kind: EverydaySafetySourceKind = "structured_api"
    source_type: str = "official API record"


class EverydaySafetyCheckedSource(BaseModel):
    source_id: str
    source_name: str
    source_type: EverydaySafetySourceType
    endpoint: str
    source_kind: EverydaySafetySourceKind = "structured_api"
    record_type: str = "official API record"
    upstream_status: str
    record_count: int


class EverydaySafetyRecord(BaseModel):
    record_id: str | None = None
    recall_number: str | None = None
    product_description: str | None = None
    reason_for_recall: str | None = None
    classification: str | None = None
    status: str | None = None
    recall_initiation_date: str | None = None
    report_date: str | None = None
    distribution_pattern: str | None = None
    recalling_firm: str | None = None
    product_quantity: str | None = None
    code_info: str | None = None
    source_type: EverydaySafetySourceType
    source_kind: EverydaySafetySourceKind = "structured_api"
    source_record_type: str = "official API record"
    title: str | None = None
    product_name: str | None = None
    brand_name: str | None = None
    company_name: str | None = None
    remedy: str | None = None
    official_url: str | None = None
    affected_models: list[str] = Field(default_factory=list)
    affected_lots: list[str] = Field(default_factory=list)
    extraction_confidence: str | None = None
    source_text_excerpt: str | None = None
    search_strategy_used: str
    risk_score: RecallRiskScore
    source: EverydaySafetySource


class EverydaySafetySearchResponse(BaseModel):
    query: str
    raw_query: str
    normalized_query: str
    correction_applied: bool
    suggestion_message: str | None = None
    category: EverydaySafetyCategory
    category_label: str
    count: int
    limit: int
    source_name: str
    endpoint: str
    retrieval_timestamp: str
    score_version: str
    search_strategy_used: str
    sources_checked: list[EverydaySafetyCheckedSource]
    public_data_disclaimer: str
    limitations: list[str]
    audit: AuditSummary
    results: list[EverydaySafetyRecord]
