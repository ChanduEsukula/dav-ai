from ml_experiments.review_priority_classifier import (
    PredictionSafetyDisclaimer,
    RuleBasedReviewPriorityClassifier,
    accuracy_score,
    encode_categorical_features,
    evaluate_classifier,
    macro_f1_score,
    standardize_numeric_features,
    train_test_split,
)
from ml_experiments.review_priority_dataset import (
    ALLOWED_REVIEW_PRIORITY_LABELS,
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    build_feature_rows,
    build_labels,
    build_review_priority_examples,
)


def test_review_priority_dataset_includes_all_three_public_data_workflows():
    examples = build_review_priority_examples()

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


def test_review_priority_dataset_includes_all_allowed_labels():
    labels = set(build_labels())

    assert labels == ALLOWED_REVIEW_PRIORITY_LABELS
    assert labels == {"routine", "watch", "elevated"}


def test_feature_rows_include_expected_predictors():
    rows = build_feature_rows()

    assert rows

    first_row = rows[0]

    for feature in CATEGORICAL_FEATURES:
        assert feature in first_row

    for feature in NUMERIC_FEATURES:
        assert feature in first_row

    assert "source_pull_present" in first_row
    assert "payload_hash_present" in first_row
    assert "query_length" in first_row
    assert "query_word_count" in first_row


def test_categorical_features_are_one_hot_encoded_without_ordinal_values():
    rows = build_feature_rows()

    encoded_rows = encode_categorical_features(rows)

    assert len(encoded_rows) == len(rows)
    assert encoded_rows

    first_encoded = encoded_rows[0]

    assert "module__RecallRadar" in first_encoded
    assert "module__DrugSignal" in first_encoded
    assert "module__RegionalHealthPulse" in first_encoded
    assert set(first_encoded.values()).issubset({0, 1})


def test_numeric_features_are_standardized_separately_from_categorical_dummies():
    rows = build_feature_rows()

    standardized_rows = standardize_numeric_features(rows)

    assert len(standardized_rows) == len(rows)
    assert standardized_rows

    first_standardized = standardized_rows[0]

    for feature in NUMERIC_FEATURES:
      assert feature in first_standardized
      assert isinstance(first_standardized[feature], float)

    assert not any(key.startswith("module__") for key in first_standardized)


def test_train_test_split_returns_non_empty_train_and_test_sets():
    rows = build_feature_rows()
    labels = build_labels()

    train_rows, train_labels, test_rows, test_labels = train_test_split(rows, labels)

    assert train_rows
    assert train_labels
    assert test_rows
    assert test_labels
    assert len(train_rows) == len(train_labels)
    assert len(test_rows) == len(test_labels)


def test_rule_based_classifier_trains_and_predicts_allowed_labels():
    rows = build_feature_rows()
    labels = build_labels()

    classifier = RuleBasedReviewPriorityClassifier().fit(rows, labels)
    predictions = classifier.predict(rows)

    predicted_labels = {prediction.label for prediction in predictions}

    assert predicted_labels.issubset(ALLOWED_REVIEW_PRIORITY_LABELS)
    assert predicted_labels
    assert all(prediction.reasons for prediction in predictions)
    assert all(
        prediction.safety_disclaimer == PredictionSafetyDisclaimer
        for prediction in predictions
    )


def test_rule_based_classifier_predicts_elevated_for_high_score_public_signal():
    classifier = RuleBasedReviewPriorityClassifier()

    prediction = classifier.predict_one(
        {
            "module": "RecallRadar",
            "source_id": "openfda_drug_enforcement",
            "upstream_status": "success",
            "record_count": 12,
            "score": 91,
            "score_label": "high",
            "source_pull_present": True,
            "payload_hash_present": True,
            "freshness_status": "fresh",
            "provenance_state": "complete",
            "record_count_delta": 3,
            "record_count_pct_change": 10.0,
            "score_delta": 4,
        }
    )

    assert prediction.label == "elevated"
    assert "high score" in prediction.reasons[0]


def test_rule_based_classifier_predicts_watch_for_missing_provenance():
    classifier = RuleBasedReviewPriorityClassifier()

    prediction = classifier.predict_one(
        {
            "module": "DrugSignal",
            "source_id": "openfda_drug_event",
            "upstream_status": "success",
            "record_count": 3,
            "score": 12,
            "score_label": "low",
            "source_pull_present": False,
            "payload_hash_present": False,
            "freshness_status": "fresh",
            "provenance_state": "missing_source_pull",
            "record_count_delta": 0,
            "record_count_pct_change": 0.0,
            "score_delta": 0,
        }
    )

    assert prediction.label == "watch"
    assert "provenance" in prediction.reasons[0]


def test_metrics_include_accuracy_macro_f1_confusion_matrix_and_safety_disclaimer():
    true_labels = ["routine", "watch", "elevated"]
    predicted_labels = ["routine", "watch", "watch"]

    metrics = evaluate_classifier(true_labels, predicted_labels)

    assert metrics["accuracy"] == accuracy_score(true_labels, predicted_labels)
    assert metrics["macro_f1"] == macro_f1_score(true_labels, predicted_labels)
    assert "confusion_matrix" in metrics
    assert "prediction_counts" in metrics
    assert metrics["safety_disclaimer"] == PredictionSafetyDisclaimer


def test_safety_disclaimer_blocks_patient_specific_or_causation_framing():
    lowered = PredictionSafetyDisclaimer.lower()

    assert "public-data review priority only" in lowered
    assert "not medical advice" in lowered
    assert "diagnosis" in lowered
    assert "treatment guidance" in lowered
    assert "patient risk prediction" in lowered
    assert "clinical decision support" in lowered
    assert "proof of causation" in lowered