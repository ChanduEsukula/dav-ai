from app.trends.drug_signal_trend import build_drug_signal_trend_snapshot


def test_trend_snapshot_returns_insufficient_history_without_previous_event():
    snapshot = build_drug_signal_trend_snapshot(
        current_record_count=10,
        previous_event=None,
    )

    assert snapshot["label"] == "Insufficient history"
    assert snapshot["current_record_count"] == 10
    assert snapshot["previous_record_count"] is None
    assert snapshot["previous_audit_id"] is None
    assert "No previous stored DrugSignal audit event" in snapshot["explanation"]
    assert snapshot["trend_version"] == "drug-signal-trend-v0.1"


def test_trend_snapshot_returns_stable_when_counts_match():
    snapshot = build_drug_signal_trend_snapshot(
        current_record_count=10,
        previous_event={
            "audit_id": "11111111-1111-4111-8111-111111111111",
            "record_count": 10,
            "created_at": "2026-05-08T18:00:00Z",
        },
    )

    assert snapshot["label"] == "Stable"
    assert snapshot["previous_record_count"] == 10
    assert snapshot["previous_audit_id"] == "11111111-1111-4111-8111-111111111111"
    assert snapshot["previous_created_at"] == "2026-05-08T18:00:00Z"


def test_trend_snapshot_returns_increased_or_decreased():
    increased = build_drug_signal_trend_snapshot(
        current_record_count=12,
        previous_event={"audit_id": "a", "record_count": 10, "created_at": "2026-05-08T18:00:00Z"},
    )
    decreased = build_drug_signal_trend_snapshot(
        current_record_count=8,
        previous_event={"audit_id": "b", "record_count": 10, "created_at": "2026-05-08T18:00:00Z"},
    )

    assert increased["label"] == "Increased"
    assert decreased["label"] == "Decreased"
