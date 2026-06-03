from typing import Literal

from pydantic import BaseModel

from app.schemas.audit import AuditSummary
from app.schemas.recalls import RecallRiskScore


EverydaySafetyCategory = Literal["food_supplement"]


class EverydaySafetySource(BaseModel):
    name: str
    endpoint: str
    retrieval_timestamp: str


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
    public_data_disclaimer: str
    limitations: list[str]
    audit: AuditSummary
    results: list[EverydaySafetyRecord]
