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
    top_reactions: list[DrugEventReaction]