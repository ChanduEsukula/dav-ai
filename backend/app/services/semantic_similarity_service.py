from __future__ import annotations

from dataclasses import dataclass

from app.nlp.semantic_similarity_preview import (
    SemanticSimilarityCandidate,
    SemanticSimilarityPreviewResult,
    evaluate_semantic_similarity_preview,
)


@dataclass(frozen=True)
class SemanticSimilarityServiceRecord:
    record_id: str
    text: str
    source_name: str | None = None


def run_semantic_similarity_preview(
    query_text: str,
    records: list[SemanticSimilarityServiceRecord],
    *,
    max_matches: int = 5,
) -> SemanticSimilarityPreviewResult:
    """
    Service-layer wrapper for the backend-only semantic similarity preview.

    This keeps the NLP preview reusable by future backend workflows without
    exposing it as production ML, RAG, LLM output, clinical decision support,
    alerting, or frontend UI.
    """

    candidates = [
        SemanticSimilarityCandidate(
            record_id=record.record_id,
            text=record.text,
            source_name=record.source_name,
        )
        for record in records
    ]

    return evaluate_semantic_similarity_preview(
        query_text=query_text,
        candidates=candidates,
        max_matches=max_matches,
    )
