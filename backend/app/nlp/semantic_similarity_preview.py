from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Literal


SimilarityPreviewVersion = Literal["semantic-similarity-preview-v0.1"]

UNSAFE_CLINICAL_TERMS = [
    "stop taking",
    "safe for you",
    "caused by",
    "diagnosis",
    "treatment guidance",
    "patient risk",
    "medical urgency",
    "outbreak detected",
]


@dataclass(frozen=True)
class SemanticSimilarityCandidate:
    record_id: str
    text: str
    source_name: str | None = None


@dataclass(frozen=True)
class SemanticSimilarityMatch:
    record_id: str
    text: str
    similarity_score: float
    explanation: str
    source_name: str | None = None


@dataclass(frozen=True)
class SemanticSimilarityPreviewResult:
    query_text: str
    matches: list[SemanticSimilarityMatch]
    limitations: list[str]
    preview_version: SimilarityPreviewVersion = "semantic-similarity-preview-v0.1"
    is_production_ml: bool = False


def evaluate_semantic_similarity_preview(
    query_text: str,
    candidates: list[SemanticSimilarityCandidate],
    *,
    max_matches: int = 5,
) -> SemanticSimilarityPreviewResult:
    normalized_query = query_text.strip()

    _assert_no_unsafe_input_text(normalized_query)

    for candidate in candidates:
        _assert_no_unsafe_input_text(candidate.text)

    safe_max_matches = max(1, min(max_matches, 20))

    limitations = [
        "This preview compares public-data text similarity only.",
        "Similarity does not imply cause-and-effect relationships, clinical urgency, product danger, or personal risk.",
        "This is not medical advice, diagnostic output, care guidance, clinical decision support, or production ML.",
    ]

    if not normalized_query:
        result = SemanticSimilarityPreviewResult(
            query_text=normalized_query,
            matches=[],
            limitations=[
                "A query is required before similarity can be evaluated.",
                *limitations,
            ],
        )
        _assert_no_unsafe_clinical_language(result)
        return result

    query_vector = _tf_vector(normalized_query)
    matches: list[SemanticSimilarityMatch] = []

    for candidate in candidates:
        candidate_text = candidate.text.strip()
        if not candidate_text:
            continue

        score = _cosine_similarity(query_vector, _tf_vector(candidate_text))
        if score <= 0:
            continue

        matches.append(
            SemanticSimilarityMatch(
                record_id=candidate.record_id,
                text=candidate_text,
                similarity_score=round(score, 4),
                explanation="Matched shared public-data terms. This is text similarity only.",
                source_name=candidate.source_name,
            )
        )

    matches = sorted(
        matches,
        key=lambda match: match.similarity_score,
        reverse=True,
    )[:safe_max_matches]

    result = SemanticSimilarityPreviewResult(
        query_text=normalized_query,
        matches=matches,
        limitations=limitations,
    )
    _assert_no_unsafe_clinical_language(result)
    return result


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _tf_vector(text: str) -> Counter[str]:
    return Counter(_tokenize(text))


def _cosine_similarity(left: Counter[str], right: Counter[str]) -> float:
    if not left or not right:
        return 0.0

    shared_terms = set(left) & set(right)
    numerator = sum(left[term] * right[term] for term in shared_terms)

    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))

    if left_norm == 0 or right_norm == 0:
        return 0.0

    return numerator / (left_norm * right_norm)


def _assert_no_unsafe_input_text(text: str) -> None:
    normalized = text.lower()

    for term in UNSAFE_CLINICAL_TERMS:
        if term in normalized:
            raise ValueError(
                f"Semantic similarity preview input used unsafe wording: {term}"
            )


def _assert_no_unsafe_clinical_language(
    result: SemanticSimilarityPreviewResult,
) -> None:
    combined = " ".join(
        [
            result.query_text,
            result.preview_version,
            str(result.is_production_ml),
            *result.limitations,
            *[
                " ".join(
                    [
                        match.record_id,
                        match.text,
                        match.explanation,
                        str(match.similarity_score),
                        match.source_name or "",
                    ]
                )
                for match in result.matches
            ],
        ]
    ).lower()

    for term in UNSAFE_CLINICAL_TERMS:
        if term in combined:
            raise ValueError(
                f"Semantic similarity preview used unsafe wording: {term}"
            )
