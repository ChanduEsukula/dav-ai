from datetime import datetime, timezone

from app.scoring.source_freshness import (
    FreshnessLabel,
    PayloadChangeLabel,
    classify_payload_change,
    classify_source_freshness,
    freshness_result_to_dict,
    payload_change_result_to_dict,
)


NOW = datetime(2026, 5, 28, 12, 0, 0, tzinfo=timezone.utc)


def test_classifies_fresh_source_when_recent_success():
    result = classify_source_freshness(
        latest_success_at="2026-05-27T12:00:00Z",
        latest_upstream_status="success",
        now=NOW,
    )

    assert result.label == FreshnessLabel.FRESH
    assert result.days_since_last_success == 1
    assert "fresh threshold" in result.reason
    assert "operational review signal" in result.safety_note
    assert "clinical urgency" in result.safety_note


def test_classifies_aging_source_between_fresh_and_stale_thresholds():
    result = classify_source_freshness(
        latest_success_at="2026-05-20T12:00:00Z",
        latest_upstream_status="success",
        now=NOW,
    )

    assert result.label == FreshnessLabel.AGING
    assert result.days_since_last_success == 8


def test_classifies_stale_source_when_older_than_threshold():
    result = classify_source_freshness(
        latest_success_at="2026-05-01T12:00:00Z",
        latest_upstream_status="success",
        now=NOW,
    )

    assert result.label == FreshnessLabel.STALE
    assert result.days_since_last_success == 27
    assert "stale threshold" in result.reason


def test_classifies_unknown_when_timestamp_missing():
    result = classify_source_freshness(
        latest_success_at=None,
        latest_upstream_status="success",
        now=NOW,
    )

    assert result.label == FreshnessLabel.UNKNOWN
    assert result.days_since_last_success is None
    assert "No usable" in result.reason


def test_classifies_unknown_when_timestamp_invalid():
    result = classify_source_freshness(
        latest_success_at="not-a-date",
        latest_upstream_status="success",
        now=NOW,
    )

    assert result.label == FreshnessLabel.UNKNOWN
    assert result.days_since_last_success is None


def test_classifies_source_error_from_upstream_status():
    result = classify_source_freshness(
        latest_success_at="2026-05-27T12:00:00Z",
        latest_upstream_status="error",
        now=NOW,
    )

    assert result.label == FreshnessLabel.SOURCE_ERROR
    assert result.days_since_last_success is None
    assert "error" in result.reason.lower()


def test_source_freshness_result_dict_uses_serializable_label():
    result = classify_source_freshness(
        latest_success_at="2026-05-27T12:00:00Z",
        latest_upstream_status="success",
        now=NOW,
    )

    payload = freshness_result_to_dict(result)

    assert payload == {
        "label": "fresh",
        "days_since_last_success": 1,
        "reason": "Latest successful retrieval is within the fresh threshold.",
        "safety_note": result.safety_note,
    }


def test_payload_change_first_seen_without_previous_hash():
    result = classify_payload_change(
        latest_payload_hash="abc123",
        previous_payload_hash=None,
    )

    assert result.label == PayloadChangeLabel.FIRST_SEEN
    assert result.latest_hash == "abc123"
    assert result.previous_hash is None
    assert "No previous" in result.reason
    assert "operational public-data review signal" in result.safety_note


def test_payload_change_unchanged_when_hashes_match():
    result = classify_payload_change(
        latest_payload_hash="abc123",
        previous_payload_hash="abc123",
    )

    assert result.label == PayloadChangeLabel.UNCHANGED
    assert result.latest_hash == "abc123"
    assert result.previous_hash == "abc123"


def test_payload_change_changed_when_hashes_differ():
    result = classify_payload_change(
        latest_payload_hash="def456",
        previous_payload_hash="abc123",
    )

    assert result.label == PayloadChangeLabel.CHANGED
    assert result.latest_hash == "def456"
    assert result.previous_hash == "abc123"
    assert "differs" in result.reason


def test_payload_change_unknown_when_latest_hash_missing():
    result = classify_payload_change(
        latest_payload_hash=None,
        previous_payload_hash="abc123",
    )

    assert result.label == PayloadChangeLabel.UNKNOWN
    assert result.latest_hash is None
    assert result.previous_hash == "abc123"


def test_payload_change_unavailable_when_latest_source_unavailable():
    result = classify_payload_change(
        latest_payload_hash=None,
        previous_payload_hash="abc123",
        latest_available=False,
    )

    assert result.label == PayloadChangeLabel.UNAVAILABLE
    assert result.latest_hash is None
    assert result.previous_hash == "abc123"
    assert "unavailable" in result.reason.lower()


def test_payload_change_result_dict_uses_serializable_label():
    result = classify_payload_change(
        latest_payload_hash="def456",
        previous_payload_hash="abc123",
    )

    payload = payload_change_result_to_dict(result)

    assert payload == {
        "label": "changed",
        "previous_hash": "abc123",
        "latest_hash": "def456",
        "reason": "Latest payload hash differs from the previous payload hash.",
        "safety_note": result.safety_note,
    }