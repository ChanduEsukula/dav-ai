import pytest

from app.services.semantic_similarity_service import (
    SemanticSimilarityServiceRecord,
    run_semantic_similarity_preview,
)


def test_service_returns_semantic_similarity_matches():
    result = run_semantic_similarity_preview(
        "eye drops contamination recall",
        [
            SemanticSimilarityServiceRecord(
                record_id="recall-1",
                text="eye drops contamination public recall record",
                source_name="openFDA Drug Enforcement API",
            ),
            SemanticSimilarityServiceRecord(
                record_id="recall-2",
                text="tablet packaging label update",
                source_name="openFDA Drug Enforcement API",
            ),
        ],
    )

    assert result.preview_version == "semantic-similarity-preview-v0.1"
    assert result.is_production_ml is False
    assert result.matches[0].record_id == "recall-1"
    assert result.matches[0].source_name == "openFDA Drug Enforcement API"


def test_service_limits_max_matches():
    records = [
        SemanticSimilarityServiceRecord(
            record_id=f"record-{index}",
            text="aspirin recall public data record",
        )
        for index in range(8)
    ]

    result = run_semantic_similarity_preview(
        "aspirin recall",
        records,
        max_matches=3,
    )

    assert len(result.matches) == 3


def test_service_preserves_empty_result_for_empty_query():
    result = run_semantic_similarity_preview(
        "",
        [
            SemanticSimilarityServiceRecord(
                record_id="record-1",
                text="metformin public reaction report",
            )
        ],
    )

    assert result.matches == []
    assert "A query is required before similarity can be evaluated." in result.limitations


def test_service_rejects_unsafe_candidate_text():
    with pytest.raises(ValueError):
        run_semantic_similarity_preview(
            "public recall",
            [
                SemanticSimilarityServiceRecord(
                    record_id="bad-record",
                    text="this is safe for you",
                )
            ],
        )


def test_service_rejects_unsafe_query_text():
    with pytest.raises(ValueError):
        run_semantic_similarity_preview(
            "stop taking this medicine",
            [
                SemanticSimilarityServiceRecord(
                    record_id="record-1",
                    text="public recall record",
                )
            ],
        )


def test_service_output_keeps_safety_boundaries():
    result = run_semantic_similarity_preview(
        "public recall review",
        [
            SemanticSimilarityServiceRecord(
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
