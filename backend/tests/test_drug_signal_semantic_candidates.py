from app.services.drug_signal_semantic_candidates import build_drug_signal_semantic_candidates


def test_builds_candidates_from_top_reactions():
    candidates = build_drug_signal_semantic_candidates(
        query="metformin",
        top_reactions=[
            {"reaction": "Nausea", "count": 2},
            {"reaction": "Headache", "count": 1},
        ],
        reaction_categories=[],
        source_name="openFDA Drug Event API",
    )

    assert len(candidates) == 2
    assert candidates[0].record_id == "reaction-1-nausea"
    assert "DrugSignal query: metformin" in candidates[0].text
    assert "Reported reaction term: Nausea" in candidates[0].text
    assert "Public report count: 2" in candidates[0].text
    assert "do not prove causality" in candidates[0].text
    assert candidates[0].source_name == "openFDA Drug Event API"


def test_builds_candidates_from_reaction_categories():
    candidates = build_drug_signal_semantic_candidates(
        query="metformin",
        top_reactions=[],
        reaction_categories=[
            {
                "category": "Gastrointestinal",
                "count": 2,
                "reactions": ["Nausea"],
            }
        ],
        source_name="openFDA Drug Event API",
    )

    assert len(candidates) == 1
    assert candidates[0].record_id == "category-1-gastrointestinal"
    assert "Reaction category: Gastrointestinal" in candidates[0].text
    assert "Category public report count: 2" in candidates[0].text
    assert "Included reaction terms: Nausea" in candidates[0].text
    assert "deterministic public-data organization only" in candidates[0].text


def test_skips_blank_reaction_and_category_names():
    candidates = build_drug_signal_semantic_candidates(
        query="metformin",
        top_reactions=[
            {"reaction": "", "count": 2},
            {"reaction": None, "count": 1},
        ],
        reaction_categories=[
            {"category": "", "count": 2, "reactions": ["Nausea"]},
            {"category": None, "count": 1, "reactions": ["Headache"]},
        ],
    )

    assert candidates == []


def test_candidate_text_avoids_unsafe_clinical_wording():
    candidates = build_drug_signal_semantic_candidates(
        query="metformin",
        top_reactions=[
            {"reaction": "Nausea", "count": 2},
        ],
        reaction_categories=[
            {
                "category": "Gastrointestinal",
                "count": 2,
                "reactions": ["Nausea"],
            }
        ],
        source_name="openFDA Drug Event API",
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
