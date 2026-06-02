from pydantic import BaseModel

from app.schemas.audit import AuditSummary


class DrugEventReaction(BaseModel):
    reaction: str
    count: int


class DrugSignalIntelligenceScore(BaseModel):
    score: int
    label: str
    data_confidence: str
    top_reaction_concentration: float
    review_priority: str
    score_version: str
    limitations: list[str]


class DrugReactionCategory(BaseModel):
    category: str
    count: int
    reactions: list[str]


class DrugSignalTrendSnapshot(BaseModel):
    label: str
    current_record_count: int
    previous_record_count: int | None = None
    previous_audit_id: str | None = None
    previous_created_at: str | None = None
    explanation: str
    limitation: str
    trend_version: str

class DrugSignalSemanticMatch(BaseModel):
    record_id: str
    text: str
    similarity_score: float
    explanation: str
    source_name: str | None = None


class DrugSignalSemanticPreview(BaseModel):
    query_text: str
    matches: list[DrugSignalSemanticMatch]
    limitations: list[str]
    preview_version: str
    is_production_ml: bool


class DrugEventSearchResponse(BaseModel):
    query: str
    count: int
    limit: int
    source_name: str
    endpoint: str
    retrieval_timestamp: str
    medical_disclaimer: str
    faers_disclaimer: str
    audit: AuditSummary
    intelligence_score: DrugSignalIntelligenceScore
    reaction_categories: list[DrugReactionCategory]
    reaction_classifier_version: str
    trend_snapshot: DrugSignalTrendSnapshot
    top_reactions: list[DrugEventReaction]