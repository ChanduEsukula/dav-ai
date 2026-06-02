from app.analytics.saved_monitor_review_priority import (
    SavedMonitorReviewPriorityInput,
    evaluate_saved_monitor_review_priority,
)


def test_stable_monitor_is_routine():
    result = evaluate_saved_monitor_review_priority(
        SavedMonitorReviewPriorityInput(
            module="recalls",
            current_record_count=10,
            previous_record_count=10,
            payload_changed=False,
            source_freshness_status="fresh",
            upstream_status="ok",
        )
    )

    assert result.priority_label == "routine"
    assert result.priority_score < 35
    assert result.is_production_ml is False
    assert any("stable" in reason.lower() for reason in result.reasons)


def test_moderate_count_increase_is_watch():
    result = evaluate_saved_monitor_review_priority(
        SavedMonitorReviewPriorityInput(
            module="drug_events",
            current_record_count=13,
            previous_record_count=10,
            payload_changed=False,
            source_freshness_status="fresh",
            upstream_status="ok",
        )
    )

    assert result.priority_label == "watch"
    assert 35 <= result.priority_score < 70
    assert any("increased" in reason.lower() for reason in result.reasons)


def test_large_count_increase_and_payload_change_is_review():
    result = evaluate_saved_monitor_review_priority(
        SavedMonitorReviewPriorityInput(
            module="recalls",
            current_record_count=25,
            previous_record_count=10,
            payload_changed=True,
            source_freshness_status="fresh",
            upstream_status="ok",
        )
    )

    assert result.priority_label == "review"
    assert result.priority_score >= 70
    assert any("payload hash changed" in reason.lower() for reason in result.reasons)


def test_upstream_failure_is_review():
    result = evaluate_saved_monitor_review_priority(
        SavedMonitorReviewPriorityInput(
            module="recalls",
            current_record_count=0,
            previous_record_count=5,
            payload_changed=False,
            source_freshness_status="fresh",
            upstream_status="error",
        )
    )

    assert result.priority_label == "review"
    assert any("upstream" in reason.lower() for reason in result.reasons)


def test_insufficient_history_includes_limitation():
    result = evaluate_saved_monitor_review_priority(
        SavedMonitorReviewPriorityInput(
            module="regional_health",
            current_record_count=4,
            previous_record_count=None,
            payload_changed=False,
            source_freshness_status="fresh",
            upstream_status="ok",
            insufficient_history=True,
        )
    )

    assert result.is_production_ml is False
    assert any("not enough prior run history" in reason.lower() for reason in result.reasons)
    assert any("additional saved-monitor runs" in limitation.lower() for limitation in result.limitations)


def test_response_never_contains_unsafe_clinical_risk_wording():
    result = evaluate_saved_monitor_review_priority(
        SavedMonitorReviewPriorityInput(
            module="drug_events",
            current_record_count=100,
            previous_record_count=10,
            payload_changed=True,
            source_freshness_status="stale",
            upstream_status="ok",
        )
    )

    combined = " ".join(
        [
            result.priority_label,
            *result.reasons,
            *result.limitations,
            result.preview_version,
            str(result.is_production_ml),
        ]
    ).lower()

    unsafe_terms = [
        "patient risk",
        "diagnosis",
        "treatment guidance",
        "caused by",
        "outbreak detected",
        "medical urgency",
        "stop taking",
        "change medication",
    ]

    for term in unsafe_terms:
        assert term not in combined
