import math
import re
from dataclasses import dataclass
from typing import Protocol, Sequence

from app.db.documentation_chunks_repository import (
    DocumentationChunkSemanticCandidate,
    DocumentationChunksRepository,
)
from app.schemas.docs import StaticDocsSemanticPreviewResult
from app.services.static_docs_embeddings import (
    DEFAULT_EMBEDDING_PREVIEW_VALUES,
    DeterministicFakeEmbeddingProvider,
    EmbeddingProvider,
)


DOCS_SEMANTIC_PREVIEW_LIMITATIONS = [
    "Deterministic semantic retrieval preview only. This is not production semantic search.",
    "No pgvector, vector column, vector index, real embedding API, OpenAI call, or LLM call is used.",
    "No generated answers are produced.",
    "Not safety advice and not a safety determination for any product, drug, food, supplement, or cosmetic.",
    "Official FDA/USDA/source workflows remain authoritative.",
]

DEFAULT_SEMANTIC_PREVIEW_CANDIDATE_LIMIT = 200
DEFAULT_SNIPPET_CHARACTERS = 320


class SemanticPreviewCandidateRepository(Protocol):
    def list_semantic_preview_candidates(
        self,
        *,
        limit: int = DEFAULT_SEMANTIC_PREVIEW_CANDIDATE_LIMIT,
    ) -> list[DocumentationChunkSemanticCandidate]:
        """Return stored documentation chunks with deterministic preview embeddings."""


@dataclass(frozen=True)
class RankedSemanticPreviewResult:
    result: StaticDocsSemanticPreviewResult
    sort_score: float


def _cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    shared_length = min(len(left), len(right))
    if shared_length == 0:
        return 0.0

    left_values = list(left[:shared_length])
    right_values = list(right[:shared_length])
    dot_product = sum(left_value * right_value for left_value, right_value in zip(left_values, right_values))
    left_norm = math.sqrt(sum(value * value for value in left_values))
    right_norm = math.sqrt(sum(value * value for value in right_values))

    if left_norm == 0 or right_norm == 0:
        return 0.0

    return dot_product / (left_norm * right_norm)


def _snippet(text: str, max_characters: int = DEFAULT_SNIPPET_CHARACTERS) -> str:
    normalized_text = re.sub(r"\s+", " ", text).strip()
    if len(normalized_text) <= max_characters:
        return normalized_text

    return f"{normalized_text[:max_characters].rstrip()}..."


def semantic_preview_search(
    query: str,
    *,
    max_results: int = 8,
    repository: SemanticPreviewCandidateRepository | None = None,
    provider: EmbeddingProvider | None = None,
) -> list[StaticDocsSemanticPreviewResult]:
    clean_query = query.strip()
    if not clean_query:
        return []

    embedding_provider = provider or DeterministicFakeEmbeddingProvider()
    query_vector = embedding_provider.embed_text(clean_query)[:DEFAULT_EMBEDDING_PREVIEW_VALUES]
    storage = repository or DocumentationChunksRepository()

    try:
        candidates = storage.list_semantic_preview_candidates(
            limit=DEFAULT_SEMANTIC_PREVIEW_CANDIDATE_LIMIT,
        )
    except Exception:
        return []

    ranked_results: list[RankedSemanticPreviewResult] = []

    for candidate in candidates:
        similarity = _cosine_similarity(query_vector, candidate.embedding_preview)
        rounded_similarity = round(similarity, 6)
        ranked_results.append(
            RankedSemanticPreviewResult(
                result=StaticDocsSemanticPreviewResult(
                    chunk_id=candidate.chunk_id,
                    source_path=candidate.source_path,
                    title=candidate.title,
                    section_heading=candidate.section_heading,
                    snippet=_snippet(candidate.text),
                    line_start=candidate.line_start,
                    line_end=candidate.line_end,
                    content_hash=candidate.content_hash,
                    similarity_score=rounded_similarity,
                    embedding_provider=candidate.embedding_provider,
                    embedding_model=candidate.embedding_model,
                ),
                sort_score=similarity,
            )
        )

    ranked_results.sort(
        key=lambda ranked: (
            -ranked.sort_score,
            ranked.result.source_path,
            ranked.result.line_start,
            ranked.result.chunk_id,
        )
    )

    bounded_limit = max(1, min(max_results, 20))
    return [ranked.result for ranked in ranked_results[:bounded_limit]]
