from ml_experiments.saved_monitor_anomaly import (
    RuleBasedSavedMonitorAnomalyClassifier,
    SavedMonitorAnomalySafetyDisclaimer,
    accuracy_score,
    encode_categorical_features,
    evaluate_classifier,
    macro_f1_score,
    standardize_numeric_features,
)
from ml_experiments.saved_monitor_anomaly_dataset import (
    ALLOWED_MONITOR_ANOMALY_LABELS,
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    build_feature_rows,
    build_labels,
    build_saved_monitor_anomaly_examples,
)


def test_saved_monitor_anomaly_dataset_includes_all_three_public_data_workflows():
    examples = build_saved_monitor_anomaly_examples()

    modules = {example.module for example in examples}
    source_ids = {example.source_id for example in examples}

    assert modules == {
        "RecallRadar",
        "DrugSignal",
        "RegionalHealthPulse",
    }
    assert source_ids == {
        "openfda_drug_enforcement",
        "openfda_drug_event",
        "regional_health_pulse_demo",
    }


def test_saved_monitor_anomaly_dataset_includes_all_allowed_labels():
    labels = set(build_labels())

    assert labels == ALLOWED_MONITOR_ANOMALY_LABELS
    assert labels == {
        "insufficient_history",
        "stable",
        "increased",
        "decreased",
        "notable_increase",
        "notable_decrease",
        "source_warning",
    }


def test_saved_monitor_feature_rows_include_expected_predictors():
    rows = build_feature_rows()

    assert rows

    first_row = rows[0]

    for feature in CATEGORICAL_FEATURES:
        assert feature in first_row

    for feature in NUMERIC_FEATURES:
        assert feature in first_row

    assert "source_pull_present" in first_row
    assert "payload_hash_present" in first_row
    assert "payload_hash_changed" in first_row
    assert "refresh_enabled" in first_row


def test_saved_monitor_categorical_features_are_one_hot_encoded():
    rows = build_feature_rows()

    encoded_rows = encode_categorical_features(rows)

    assert len(encoded_rows) == len(rows)
    assert encoded_rows

    first_encoded = encoded_rows[0]

    assert "module__RecallRadar" in first_encoded
    assert "module__DrugSignal" in first_encoded
    assert "module__RegionalHealthPulse" in first_encoded
    assert set(first_encoded.values()).issubset({0, 1})


def test_saved_monitor_numeric_features_are_standardized_without_dummy_columns():
    rows = build_feature_rows()

    standardized_rows = standardize_numeric_features(rows)

    assert len(standardized_rows) == len(rows)
    assert standardized_rows

    first_standardized = standardized_rows[0]

    for feature in NUMERIC_FEATURES:
        assert feature in first_standardized
        assert isinstance(first_standardized[feature], float)

    assert not any(key.startswith("module__") for key in first_standardized)


def test_saved_monitor_anomaly_classifier_trains_and_predicts_allowed_labels():
    rows = build_feature_rows()
    labels = build_labels()

    classifier = RuleBasedSavedMonitorAnomalyClassifier().fit(rows, labels)
    predictions = classifier.predict(rows)

    predicted_labels = {prediction.label for prediction in predictions}

    assert predicted_labels.issubset(ALLOWED_MONITOR_ANOMALY_LABELS)
    assert predicted_labels
    assert all(prediction.reasons for prediction in predictions)
    assert all(
        prediction.safety_disclaimer == SavedMonitorAnomalySafetyDisclaimer
        for prediction in predictions
    )


def test_saved_monitor_anomaly_classifier_predicts_source_warning_for_error_state():
    classifier = RuleBasedSavedMonitorAnomalyClassifier()

    prediction = classifier.predict_one(
        {
            "module": "RegionalHealthPulse",
            "source_id": "regional_health_pulse_demo",
            "upstream_status": "error",
            "freshness_status": "error",
            "provenance_state": "missing_source_pull",
            "last_scheduled_status": "error",
            "latest_record_count": 0,
            "previous_record_count": 8,
            "record_count_delta": -8,
            "record_count_pct_change": -100.0,
            "latest_score": 0,
            "previous_score": 40,
            "score_delta": -40,
            "run_count": 3,
            "days_since_last_run": 1,
            "source_pull_present": False,
            "payload_hash_present": False,
            "payload_hash_changed": False,
            "refresh_enabled": True,
        }
    )

    assert prediction.label == "source_warning"
    assert "source" in prediction.reasons[0]


def test_saved_monitor_anomaly_classifier_predicts_insufficient_history():
    classifier = RuleBasedSavedMonitorAnomalyClassifier()

    prediction = classifier.predict_one(
        {
            "module": "RecallRadar",
            "source_id": "openfda_drug_enforcement",
            "upstream_status": "success",
            "freshness_status": "fresh",
            "provenance_state": "complete",
            "last_scheduled_status": "success",
            "latest_record_count": 5,
            "previous_record_count": 0,
            "record_count_delta": 5,
            "record_count_pct_change": 100.0,
            "latest_score": 22,
            "previous_score": 0,
            "score_delta": 22,
            "run_count": 1,
            "days_since_last_run": 0,
            "source_pull_present": True,
            "payload_hash_present": True,
            "payload_hash_changed": False,
            "refresh_enabled": False,
        }
    )

    assert prediction.label == "insufficient_history"
    assert "insufficient" in prediction.reasons[0]


def test_saved_monitor_anomaly_classifier_predicts_notable_increase():
    classifier = RuleBasedSavedMonitorAnomalyClassifier()

    prediction = classifier.predict_one(
        {
            "module": "DrugSignal",
            "source_id": "openfda_drug_event",
            "upstream_status": "success",
            "freshness_status": "fresh",
            "provenance_state": "complete",
            "last_scheduled_status": "success",
            "latest_record_count": 50,
            "previous_record_count": 20,
            "record_count_delta": 30,
            "record_count_pct_change": 150.0,
            "latest_score": 85,
            "previous_score": 55,
            "score_delta": 30,
            "run_count": 5,
            "days_since_last_run": 1,
            "source_pull_present": True,
            "payload_hash_present": True,
            "payload_hash_changed": True,
            "refresh_enabled": True,
        }
    )

    assert prediction.label == "notable_increase"
    assert "notable increase" in prediction.reasons[0]


def test_saved_monitor_anomaly_classifier_predicts_stable_activity():
    classifier = RuleBasedSavedMonitorAnomalyClassifier()

    prediction = classifier.predict_one(
        {
            "module": "RecallRadar",
            "source_id": "openfda_drug_enforcement",
            "upstream_status": "success",
            "freshness_status": "fresh",
            "provenance_state": "complete",
            "last_scheduled_status": "success",
            "latest_record_count": 10,
            "previous_record_count": 10,
            "record_count_delta": 0,
            "record_count_pct_change": 0.0,
            "latest_score": 42,
            "previous_score": 42,
            "score_delta": 0,
            "run_count": 5,
            "days_since_last_run": 1,
            "source_pull_present": True,
            "payload_hash_present": True,
            "payload_hash_changed": False,
            "refresh_enabled": True,
        }
    )

    assert prediction.label == "stable"
    assert "stable" in prediction.reasons[0]


def test_saved_monitor_anomaly_metrics_include_expected_outputs():
    true_labels = [
        "stable",
        "increased",
        "notable_increase",
        "source_warning",
    ]
    predicted_labels = [
        "stable",
        "increased",
        "increased",
        "source_warning",
    ]

    metrics = evaluate_classifier(true_labels, predicted_labels)

    assert metrics["accuracy"] == accuracy_score(true_labels, predicted_labels)
    assert metrics["macro_f1"] == macro_f1_score(true_labels, predicted_labels)
    assert "confusion_matrix" in metrics
    assert "prediction_counts" in metrics
    assert metrics["safety_disclaimer"] == SavedMonitorAnomalySafetyDisclaimer


def test_saved_monitor_anomaly_safety_disclaimer_blocks_unsafe_framing():
    lowered = SavedMonitorAnomalySafetyDisclaimer.lower()

    assert "public-data saved-monitor change state only" in lowered
    assert "not medical advice" in lowered
    assert "diagnosis" in lowered
    assert "treatment guidance" in lowered
    assert "patient risk prediction" in lowered
    assert "clinical decision support" in lowered
    assert "outbreak prediction" in lowered
    assert "proof of causation" in lowered