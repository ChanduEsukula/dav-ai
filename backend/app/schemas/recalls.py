from pydantic import BaseModel


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


class RecallResult(BaseModel):
    recall_number: str | None
    product_description: str | None
    reason_for_recall: str | None
    classification: str | None
    status: str | None
    recall_initiation_date: str | None
    distribution_pattern: str | None
    recalling_firm: str | None
    risk_score: RecallRiskScore
    source: RecallSource


class RecallSearchResponse(BaseModel):
    query: str
    count: int
    limit: int
    source_name: str
    retrieval_timestamp: str
    medical_disclaimer: str
    results: list[RecallResult]