from __future__ import annotations

from pydantic import BaseModel, Field


class SemanticSimilarityCandidateRequest(BaseModel):
    record_id: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)
    source_name: str | None = None


class SemanticSimilarityPreviewRequest(BaseModel):
    query_text: str = Field(..., min_length=0)
    candidates: list[SemanticSimilarityCandidateRequest] = Field(default_factory=list)
    max_matches: int = Field(default=5, ge=1, le=20)


class SemanticSimilarityMatchResponse(BaseModel):
    record_id: str
    text: str
    similarity_score: float
    explanation: str
    source_name: str | None = None


class SemanticSimilarityPreviewResponse(BaseModel):
    query_text: str
    matches: list[SemanticSimilarityMatchResponse]
    limitations: list[str]
    preview_version: str
    is_production_ml: bool
