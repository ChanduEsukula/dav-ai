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
