from app.scoring.drug_signal_score import calculate_drug_signal_intelligence_score


def test_drug_signal_score_returns_low_for_empty_results():
    score = calculate_drug_signal_intelligence_score(record_count=0, top_reactions=[])

    assert score["score"] == 0
    assert score["label"] == "Low"
    assert score["data_confidence"] == "Limited"
    assert score["top_reaction_concentration"] == 0.0
    assert score["review_priority"] == "Low"
    assert score["score_version"] == "drug-signal-intelligence-v0.1"
    assert "do not prove causation" in score["limitations"][0]


def test_drug_signal_score_returns_moderate_for_small_concentrated_results():
    score = calculate_drug_signal_intelligence_score(
        record_count=2,
        top_reactions=[
            {"reaction": "Nausea", "count": 2},
            {"reaction": "Headache", "count": 1},
        ],
    )

    assert score["score"] == 57
    assert score["label"] == "Moderate"
    assert score["data_confidence"] == "Limited"
    assert score["top_reaction_concentration"] == 66.67
    assert score["review_priority"] == "Watch"


def test_drug_signal_score_returns_high_for_large_diverse_results():
    score = calculate_drug_signal_intelligence_score(
        record_count=25,
        top_reactions=[
            {"reaction": "Nausea", "count": 30},
            {"reaction": "Headache", "count": 20},
            {"reaction": "Fatigue", "count": 15},
            {"reaction": "Dizziness", "count": 10},
            {"reaction": "Vomiting", "count": 5},
        ],
    )

    assert score["score"] >= 61
    assert score["label"] == "High"
    assert score["data_confidence"] == "Strong"
    assert score["review_priority"] == "Review"
