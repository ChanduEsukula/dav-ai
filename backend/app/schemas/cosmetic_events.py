from pydantic import BaseModel

from app.schemas.audit import AuditSummary


class CosmeticProduct(BaseModel):
    brand_name: str | None = None
    name_brand: str | None = None
    industry_code: str | None = None
    industry_name: str | None = None


class CosmeticEventRecord(BaseModel):
    report_number: str | None = None
    report_date: str | None = None
    serious: str | None = None
    outcomes: list[str]
    reactions: list[str]
    products: list[CosmeticProduct]



class CosmeticRecallNotice(BaseModel):
    title: str | None = None
    product_name: str | None = None
    brand_name: str | None = None
    company_name: str | None = None
    category: str | None = None
    reason: str | None = None
    published_date: str | None = None
    record_url: str | None = None
    source_name: str


class CosmeticReaction(BaseModel):
    reaction: str
    count: int


class CosmeticSignalScore(BaseModel):
    score: int
    label: str
    data_confidence: str
    top_reaction_concentration: float
    review_priority: str
    score_version: str
    limitations: list[str]


class CosmeticEventSearchResponse(BaseModel):
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
    medical_disclaimer: str
    cosmetic_disclaimer: str
    audit: AuditSummary
    signal_score: CosmeticSignalScore
    top_reactions: list[CosmeticReaction]
    records: list[CosmeticEventRecord]
    recall_count: int = 0
    recall_source_name: str | None = None
    recall_source_status: str | None = None
    recall_source_error: str | None = None
    recall_notices: list[CosmeticRecallNotice] = []
