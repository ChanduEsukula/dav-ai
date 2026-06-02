from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.schemas.semantic_similarity import (
    SemanticSimilarityMatchResponse,
    SemanticSimilarityPreviewRequest,
    SemanticSimilarityPreviewResponse,
)
from app.services.semantic_similarity_service import (
    SemanticSimilarityServiceRecord,
    run_semantic_similarity_preview,
)


router = APIRouter()


@router.post("/preview", response_model=SemanticSimilarityPreviewResponse)
def preview_semantic_similarity(
    request: SemanticSimilarityPreviewRequest,
) -> SemanticSimilarityPreviewResponse:
    try:
        result = run_semantic_similarity_preview(
            query_text=request.query_text,
            records=[
                SemanticSimilarityServiceRecord(
                    record_id=candidate.record_id,
                    text=candidate.text,
                    source_name=candidate.source_name,
                )
                for candidate in request.candidates
            ],
            max_matches=request.max_matches,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return SemanticSimilarityPreviewResponse(
        query_text=result.query_text,
        matches=[
            SemanticSimilarityMatchResponse(
                record_id=match.record_id,
                text=match.text,
                similarity_score=match.similarity_score,
                explanation=match.explanation,
                source_name=match.source_name,
            )
            for match in result.matches
        ],
        limitations=result.limitations,
        preview_version=result.preview_version,
        is_production_ml=result.is_production_ml,
    )
