import pytest

from app.nlp.semantic_similarity_preview import (
    SemanticSimilarityCandidate,
    evaluate_semantic_similarity_preview,
)


def test_returns_highest_score_for_most_similar_text():
    result = evaluate_semantic_similarity_preview(
        "eye drops contamination recall",
        [
            SemanticSimilarityCandidate(
                record_id="recall-1",
                text="eye drops recalled because of contamination risk in public recall data",
                source_name="openFDA Drug Enforcement API",
            ),
            SemanticSimilarityCandidate(
                record_id="recall-2",
                text="tablet packaging label update",
                source_name="openFDA Drug Enforcement API",
            ),
        ],
    )

    assert result.matches
    assert result.matches[0].record_id == "recall-1"
    assert result.matches[0].similarity_score > 0
    assert result.preview_version == "semantic-similarity-preview-v0.1"
    assert result.is_production_ml is False


def test_empty_candidates_return_no_matches():
    result = evaluate_semantic_similarity_preview("metformin reaction reports", [])

    assert result.matches == []
    assert result.is_production_ml is False


def test_empty_query_returns_limitation_and_no_matches():
    result = evaluate_semantic_similarity_preview(
        "",
        [
            SemanticSimilarityCandidate(
                record_id="record-1",
                text="metformin reaction report",
            )
        ],
    )

    assert result.matches == []
    assert any("query is required" in item.lower() for item in result.limitations)


def test_limits_max_matches():
    candidates = [
        SemanticSimilarityCandidate(
            record_id=f"record-{index}",
            text="aspirin tablet recall public record",
        )
        for index in range(10)
    ]

    result = evaluate_semantic_similarity_preview(
        "aspirin recall",
        candidates,
        max_matches=3,
    )

    assert len(result.matches) == 3


def test_similarity_scores_are_normalized_between_zero_and_one():
    result = evaluate_semantic_similarity_preview(
        "insulin recall",
        [
            SemanticSimilarityCandidate(
                record_id="record-1",
                text="insulin recall",
            )
        ],
    )

    assert result.matches
    assert 0 <= result.matches[0].similarity_score <= 1


def test_output_never_contains_unsafe_clinical_wording():
    result = evaluate_semantic_similarity_preview(
        "public recall review",
        [
            SemanticSimilarityCandidate(
                record_id="record-1",
                text="public recall review",
            )
        ],
    )

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

    unsafe_terms = [
        "stop taking",
        "safe for you",
        "caused by",
        "diagnosis",
        "treatment guidance",
        "patient risk",
        "medical urgency",
        "outbreak detected",
    ]

    for term in unsafe_terms:
        assert term not in combined


def test_raises_if_candidate_text_contains_unsafe_wording():
    with pytest.raises(ValueError):
        evaluate_semantic_similarity_preview(
            "public recall",
            [
                SemanticSimilarityCandidate(
                    record_id="bad-record",
                    text="this is safe for you",
                )
            ],
        )
