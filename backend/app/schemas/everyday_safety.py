from typing import Literal

from pydantic import BaseModel

from app.schemas.audit import AuditSummary
from app.schemas.recalls import RecallRiskScore


EverydaySafetyCategory = Literal["food_supplement"]
EverydaySafetySourceType = Literal["FDA_FOOD_ENFORCEMENT", "USDA_FSIS_RECALL"]


class EverydaySafetySource(BaseModel):
    name: str
    endpoint: str
    retrieval_timestamp: str


class EverydaySafetyCheckedSource(BaseModel):
    source_id: str
    source_name: str
    source_type: EverydaySafetySourceType
    endpoint: str
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
    search_strategy_used: str
    risk_score: RecallRiskScore
    source: EverydaySafetySource


class EverydaySafetySearchResponse(BaseModel):
    query: str
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
