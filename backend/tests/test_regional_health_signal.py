from app.scoring.regional_health_signal import calculate_regional_health_signal


def test_regional_health_signal_labels_increasing_public_data():
    signal = calculate_regional_health_signal(
        previous_value=32,
        latest_value=46,
        record_count=2,
    )

    assert signal["trend_label"] == "Increasing"
    assert signal["review_priority"] == "Watch"
    assert signal["confidence"] == "Moderate"
    assert signal["change_percent"] == 43.75
    assert signal["signal_version"] == "regional-health-signal-v0.1"
    assert "not medical advice" in signal["limitations"][0]


def test_regional_health_signal_labels_stable_public_data():
    signal = calculate_regional_health_signal(
        previous_value=41,
        latest_value=43,
        record_count=2,
    )

    assert signal["trend_label"] == "Stable"
    assert signal["review_priority"] == "Low"


def test_regional_health_signal_handles_insufficient_data():
    signal = calculate_regional_health_signal(
        previous_value=None,
        latest_value=None,
        record_count=0,
    )

    assert signal["trend_label"] == "Insufficient data"
    assert signal["confidence"] == "Limited"
    assert signal["change_percent"] is None
