from datetime import datetime, timedelta

from app.scoring.recall_score import calculate_recall_risk_score


def test_high_risk_ongoing_class_i_nationwide_recent_recall():
    recent_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y%m%d")

    record = {
        "classification": "Class I",
        "status": "Ongoing",
        "recall_initiation_date": recent_date,
        "distribution_pattern": "Nationwide distribution across the United States",
    }

    result = calculate_recall_risk_score(record)

    assert result["score"] == 100
    assert result["label"] == "Critical"
    assert result["score_version"] == "recall-risk-v0.1"
    assert result["components"]["classification_score"] == 40
    assert result["components"]["status_score"] == 20
    assert result["components"]["recency_score"] == 20
    assert result["components"]["scope_score"] == 20


def test_low_risk_completed_class_iii_old_local_recall():
    old_date = (datetime.utcnow() - timedelta(days=1500)).strftime("%Y%m%d")

    record = {
        "classification": "Class III",
        "status": "Completed",
        "recall_initiation_date": old_date,
        "distribution_pattern": "Local distribution only",
    }

    result = calculate_recall_risk_score(record)

    assert result["score"] == 22
    assert result["label"] == "Low"
    assert result["components"]["classification_score"] == 10
    assert result["components"]["status_score"] == 5
    assert result["components"]["recency_score"] == 2
    assert result["components"]["scope_score"] == 5


def test_missing_fields_use_safe_default_scores():
    record = {}

    result = calculate_recall_risk_score(record)

    assert result["score"] == 20
    assert result["label"] == "Low"
    assert result["components"]["classification_score"] == 5
    assert result["components"]["status_score"] == 5
    assert result["components"]["recency_score"] == 5
    assert result["components"]["scope_score"] == 5


def test_invalid_date_uses_default_recency_score():
    record = {
        "classification": "Class II",
        "status": "Ongoing",
        "recall_initiation_date": "not-a-date",
        "distribution_pattern": "multiple states",
    }

    result = calculate_recall_risk_score(record)

    assert result["score"] == 62
    assert result["label"] == "High"
    assert result["components"]["recency_score"] == 5