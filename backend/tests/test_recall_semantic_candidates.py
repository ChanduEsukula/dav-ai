import pytest

from app.services.recall_semantic_candidates import build_recall_semantic_candidates


def test_builds_semantic_candidates_from_recall_results():
    candidates = build_recall_semantic_candidates(
        [
            {
                "recall_number": "D-1234-2026",
                "product_description": "Example eye drops",
                "reason_for_recall": "Example recall reason",
                "classification": "Class II",
                "status": "Ongoing",
                "recall_initiation_date": "20260401",
                "distribution_pattern": "Nationwide",
                "recalling_firm": "Example Pharma",
                "source": {
                    "name": "openFDA Drug Enforcement API",
                },
            }
        ]
    )

    assert len(candidates) == 1

    candidate = candidates[0]
    assert candidate.record_id == "D-1234-2026"
    assert candidate.source_name == "openFDA Drug Enforcement API"
    assert "Example eye drops" in candidate.text
    assert "Example recall reason" in candidate.text
    assert "Class II" in candidate.text
    assert "Ongoing" in candidate.text
    assert "Nationwide" in candidate.text
    assert "Example Pharma" in candidate.text


def test_skips_recall_results_without_public_text():
    candidates = build_recall_semantic_candidates(
        [
            {
                "recall_number": "D-empty",
                "product_description": None,
                "reason_for_recall": None,
                "classification": None,
                "status": None,
                "recall_initiation_date": None,
                "distribution_pattern": None,
                "recalling_firm": None,
            }
        ]
    )

    assert candidates == []


def test_uses_fallback_record_id_when_recall_number_missing():
    candidates = build_recall_semantic_candidates(
        [
            {
                "product_description": "Example product",
                "reason_for_recall": "Example public recall reason",
            }
        ]
    )

    assert len(candidates) == 1
    assert candidates[0].record_id == "recall-1"


def test_candidate_text_avoids_unsafe_clinical_claim_words():
    candidates = build_recall_semantic_candidates(
        [
            {
                "recall_number": "D-1234-2026",
                "product_description": "Example eye drops",
                "reason_for_recall": "Example public recall reason",
                "classification": "Class II",
                "status": "Ongoing",
            }
        ]
    )

    combined = " ".join(candidate.text for candidate in candidates).lower()

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
