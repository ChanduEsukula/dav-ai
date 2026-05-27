from ml_experiments.recall_reason_classifier import (
    RecallReasonSafetyDisclaimer,
    RuleBasedRecallReasonClassifier,
    accuracy_score,
    evaluate_classifier,
    keyword_scores,
    macro_f1_score,
    normalize_text,
    tokenize_text,
)
from ml_experiments.recall_reason_dataset import (
    ALLOWED_RECALL_REASON_LABELS,
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    TEXT_FEATURES,
    build_feature_rows,
    build_labels,
    build_recall_reason_examples,
)


def test_recall_reason_dataset_includes_all_allowed_labels():
    labels = set(build_labels())

    assert labels == ALLOWED_RECALL_REASON_LABELS
    assert labels == {
        "sterility",
        "contamination",
        "labeling",
        "packaging",
        "potency",
        "foreign_material",
        "temperature_control",
        "other",
    }


def test_recall_reason_feature_rows_include_expected_predictors():
    rows = build_feature_rows()

    assert rows

    first_row = rows[0]

    for feature in TEXT_FEATURES:
        assert feature in first_row

    for feature in CATEGORICAL_FEATURES:
        assert feature in first_row

    for feature in NUMERIC_FEATURES:
        assert feature in first_row

    assert "combined_text" in first_row


def test_normalize_text_lowercases_and_removes_punctuation():
    text = "Lack of Sterility Assurance, for Ophthalmic Solution!"

    normalized = normalize_text(text)

    assert normalized == "lack of sterility assurance for ophthalmic solution"


def test_tokenize_text_returns_normalized_tokens():
    tokens = tokenize_text("Incorrect LABEL strength printed on carton.")

    assert tokens == ["incorrect", "label", "strength", "printed", "on", "carton"]


def test_keyword_scores_detect_expected_category_terms():
    scores = keyword_scores("Visible particulate matter found in injectable solution.")

    assert scores["foreign_material"] >= 2
    assert scores["sterility"] == 0


def test_recall_reason_classifier_trains_and_predicts_allowed_labels():
    rows = build_feature_rows()
    labels = build_labels()

    classifier = RuleBasedRecallReasonClassifier().fit(rows, labels)
    predictions = classifier.predict(rows)

    predicted_labels = {prediction.label for prediction in predictions}

    assert predicted_labels.issubset(ALLOWED_RECALL_REASON_LABELS)
    assert predicted_labels
    assert all(prediction.safety_disclaimer == RecallReasonSafetyDisclaimer for prediction in predictions)
    assert all(0.0 <= prediction.confidence <= 1.0 for prediction in predictions)


def test_recall_reason_classifier_predicts_sterility():
    classifier = RuleBasedRecallReasonClassifier()

    prediction = classifier.predict_one(
        {
            "reason_for_recall": "Product may be non-sterile due to aseptic processing issue.",
            "product_description": "Injectable vial.",
            "distribution_pattern": "Distributed to hospitals.",
        }
    )

    assert prediction.label == "sterility"
    assert prediction.confidence > 0
    assert prediction.matched_keywords


def test_recall_reason_classifier_predicts_contamination():
    classifier = RuleBasedRecallReasonClassifier()

    prediction = classifier.predict_one(
        {
            "reason_for_recall": "Microbial contamination detected during testing.",
            "product_description": "Liquid oral product.",
            "distribution_pattern": "Distributed nationwide.",
        }
    )

    assert prediction.label == "contamination"
    assert prediction.confidence > 0
    assert "contamination" in prediction.matched_keywords


def test_recall_reason_classifier_predicts_labeling():
    classifier = RuleBasedRecallReasonClassifier()

    prediction = classifier.predict_one(
        {
            "reason_for_recall": "Incorrect label strength printed on carton.",
            "product_description": "Prescription tablets.",
            "distribution_pattern": "Distributed to pharmacies.",
        }
    )

    assert prediction.label == "labeling"
    assert prediction.confidence > 0
    assert "label" in prediction.matched_keywords or "incorrect" in prediction.matched_keywords


def test_recall_reason_classifier_predicts_packaging():
    classifier = RuleBasedRecallReasonClassifier()

    prediction = classifier.predict_one(
        {
            "reason_for_recall": "Bottle cap seal may fail due to packaging defect.",
            "product_description": "Oral suspension bottle.",
            "distribution_pattern": "Distributed to retail stores.",
        }
    )

    assert prediction.label == "packaging"
    assert prediction.confidence > 0
    assert "packaging" in prediction.matched_keywords


def test_recall_reason_classifier_predicts_potency():
    classifier = RuleBasedRecallReasonClassifier()

    prediction = classifier.predict_one(
        {
            "reason_for_recall": "Subpotent active ingredient below specification.",
            "product_description": "Prescription capsule.",
            "distribution_pattern": "Distributed to pharmacies.",
        }
    )

    assert prediction.label == "potency"
    assert prediction.confidence > 0
    assert "subpotent" in prediction.matched_keywords


def test_recall_reason_classifier_predicts_temperature_control():
    classifier = RuleBasedRecallReasonClassifier()

    prediction = classifier.predict_one(
        {
            "reason_for_recall": "Temperature excursion during refrigerated shipment.",
            "product_description": "Cold storage medication.",
            "distribution_pattern": "Distributed through specialty pharmacy.",
        }
    )

    assert prediction.label == "temperature_control"
    assert prediction.confidence > 0
    assert "temperature" in prediction.matched_keywords


def test_recall_reason_classifier_defaults_to_other_when_no_keywords_match():
    classifier = RuleBasedRecallReasonClassifier()

    prediction = classifier.predict_one(
        {
            "reason_for_recall": "Customer complaint investigation opened.",
            "product_description": "General healthcare product.",
            "distribution_pattern": "Limited distribution.",
        }
    )

    assert prediction.label == "other"
    assert prediction.confidence > 0 or prediction.matched_keywords


def test_recall_reason_classifier_returns_other_for_empty_text():
    classifier = RuleBasedRecallReasonClassifier()

    prediction = classifier.predict_one(
        {
            "reason_for_recall": "",
            "product_description": "",
            "distribution_pattern": "",
        }
    )

    assert prediction.label == "other"
    assert prediction.confidence == 0.0
    assert prediction.matched_keywords == []


def test_recall_reason_metrics_include_expected_outputs():
    true_labels = [
        "sterility",
        "contamination",
        "labeling",
        "packaging",
    ]
    predicted_labels = [
        "sterility",
        "contamination",
        "packaging",
        "packaging",
    ]

    metrics = evaluate_classifier(true_labels, predicted_labels)

    assert metrics["accuracy"] == accuracy_score(true_labels, predicted_labels)
    assert metrics["macro_f1"] == macro_f1_score(true_labels, predicted_labels)
    assert "confusion_matrix" in metrics
    assert "prediction_counts" in metrics
    assert metrics["safety_disclaimer"] == RecallReasonSafetyDisclaimer


def test_recall_reason_safety_disclaimer_blocks_unsafe_framing():
    lowered = RecallReasonSafetyDisclaimer.lower()

    assert "public recall reason text category only" in lowered
    assert "not medical advice" in lowered
    assert "diagnosis" in lowered
    assert "treatment guidance" in lowered
    assert "patient risk prediction" in lowered
    assert "clinical decision support" in lowered
    assert "official fda severity classification" in lowered