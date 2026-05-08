from app.scoring.reaction_classifier import classify_reaction, classify_reactions


def test_classify_reaction_maps_known_categories():
    assert classify_reaction("Gait disturbance") == "Neurological"
    assert classify_reaction("Nausea") == "Gastrointestinal"
    assert classify_reaction("Dyspnoea") == "Respiratory"
    assert classify_reaction("Hypertension") == "Cardiovascular"
    assert classify_reaction("Rash") == "Skin / allergy"
    assert classify_reaction("Sepsis") == "Infection / immune"
    assert classify_reaction("Weight increased") == "Metabolic"


def test_classify_reaction_uses_general_other_fallback():
    assert classify_reaction("Unevaluable event") == "General / other"


def test_classify_reactions_groups_counts_and_reaction_names():
    categories = classify_reactions(
        [
            {"reaction": "Gait disturbance", "count": 2},
            {"reaction": "Balance disorder", "count": 1},
            {"reaction": "Dyspnoea", "count": 1},
            {"reaction": "Sepsis", "count": 1},
            {"reaction": "Unevaluable event", "count": 2},
        ]
    )

    assert categories[0] == {
        "category": "Neurological",
        "count": 3,
        "reactions": ["Balance disorder", "Gait disturbance"],
    }

    assert {
        "category": "General / other",
        "count": 2,
        "reactions": ["Unevaluable event"],
    } in categories

    assert {
        "category": "Respiratory",
        "count": 1,
        "reactions": ["Dyspnoea"],
    } in categories
