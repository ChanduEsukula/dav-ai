from ml_experiments.drug_reaction_theme_classifier import (
    DrugReactionThemeSafetyDisclaimer,
    RuleBasedDrugReactionThemeClassifier,
    accuracy_score,
    evaluate_classifier,
    keyword_scores,
    macro_f1_score,
    normalize_text,
    tokenize_text,
)
from ml_experiments.drug_reaction_theme_dataset import (
    ALLOWED_REACTION_THEME_LABELS,
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    TEXT_FEATURES,
    build_feature_rows,
    build_drug_reaction_theme_examples,
    build_labels,
)


def test_drug_reaction_theme_dataset_includes_all_allowed_labels():
    labels = set(build_labels())

    assert labels == ALLOWED_REACTION_THEME_LABELS
    assert labels == {
        "neurological",
        "gastrointestinal",
        "respiratory",
        "cardiovascular",
        "skin_allergy",
        "infection_immune",
        "metabolic",
        "general_other",
    }


def test_drug_reaction_theme_dataset_uses_openfda_drug_event_source():
    examples = build_drug_reaction_theme_examples()

    assert examples
    assert {example.source_id for example in examples} == {"openfda_drug_event"}


def test_drug_reaction_theme_feature_rows_include_expected_predictors():
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
    text = "Headache, DIZZINESS, and Tremor!"

    normalized = normalize_text(text)

    assert normalized == "headache dizziness and tremor"


def test_tokenize_text_returns_normalized_tokens():
    tokens = tokenize_text("Respiratory distress, cough, and wheezing.")

    assert tokens == ["respiratory", "distress", "cough", "and", "wheezing"]


def test_keyword_scores_detect_expected_reaction_theme_terms():
    scores = keyword_scores("Rash urticaria pruritus and angioedema reported.")

    assert scores["skin_allergy"] >= 4
    assert scores["metabolic"] == 0


def test_drug_reaction_theme_classifier_trains_and_predicts_allowed_labels():
    rows = build_feature_rows()
    labels = build_labels()

    classifier = RuleBasedDrugReactionThemeClassifier().fit(rows, labels)
    predictions = classifier.predict(rows)

    predicted_labels = {prediction.label for prediction in predictions}

    assert predicted_labels.issubset(ALLOWED_REACTION_THEME_LABELS)
    assert predicted_labels
    assert all(
        prediction.safety_disclaimer == DrugReactionThemeSafetyDisclaimer
        for prediction in predictions
    )
    assert all(0.0 <= prediction.confidence <= 1.0 for prediction in predictions)


def test_drug_reaction_theme_classifier_predicts_neurological():
    classifier = RuleBasedDrugReactionThemeClassifier()

    prediction = classifier.predict_one(
        {
            "reaction_terms": ["Headache", "Dizziness", "Migraine"],
            "top_reaction": "Headache",
        }
    )

    assert prediction.label == "neurological"
    assert prediction.confidence > 0
    assert "headache" in prediction.matched_keywords


def test_drug_reaction_theme_classifier_predicts_gastrointestinal():
    classifier = RuleBasedDrugReactionThemeClassifier()

    prediction = classifier.predict_one(
        {
            "reaction_terms": ["Nausea", "Vomiting", "Diarrhoea"],
            "top_reaction": "Nausea",
        }
    )

    assert prediction.label == "gastrointestinal"
    assert prediction.confidence > 0
    assert "nausea" in prediction.matched_keywords


def test_drug_reaction_theme_classifier_predicts_respiratory():
    classifier = RuleBasedDrugReactionThemeClassifier()

    prediction = classifier.predict_one(
        {
            "reaction_terms": ["Dyspnoea", "Cough", "Wheezing"],
            "top_reaction": "Dyspnoea",
        }
    )

    assert prediction.label == "respiratory"
    assert prediction.confidence > 0
    assert "dyspnoea" in prediction.matched_keywords


def test_drug_reaction_theme_classifier_predicts_cardiovascular():
    classifier = RuleBasedDrugReactionThemeClassifier()

    prediction = classifier.predict_one(
        {
            "reaction_terms": ["Palpitations", "Tachycardia", "Chest pain"],
            "top_reaction": "Palpitations",
        }
    )

    assert prediction.label == "cardiovascular"
    assert prediction.confidence > 0
    assert "palpitations" in prediction.matched_keywords


def test_drug_reaction_theme_classifier_predicts_skin_allergy():
    classifier = RuleBasedDrugReactionThemeClassifier()

    prediction = classifier.predict_one(
        {
            "reaction_terms": ["Rash", "Urticaria", "Pruritus"],
            "top_reaction": "Rash",
        }
    )

    assert prediction.label == "skin_allergy"
    assert prediction.confidence > 0
    assert "rash" in prediction.matched_keywords


def test_drug_reaction_theme_classifier_predicts_infection_immune():
    classifier = RuleBasedDrugReactionThemeClassifier()

    prediction = classifier.predict_one(
        {
            "reaction_terms": ["Infection", "Sepsis", "Immune disorder"],
            "top_reaction": "Infection",
        }
    )

    assert prediction.label == "infection_immune"
    assert prediction.confidence > 0
    assert "infection" in prediction.matched_keywords


def test_drug_reaction_theme_classifier_predicts_metabolic():
    classifier = RuleBasedDrugReactionThemeClassifier()

    prediction = classifier.predict_one(
        {
            "reaction_terms": ["Hyperglycaemia", "Hypoglycaemia", "Dehydration"],
            "top_reaction": "Hyperglycaemia",
        }
    )

    assert prediction.label == "metabolic"
    assert prediction.confidence > 0
    assert "hyperglycaemia" in prediction.matched_keywords


def test_drug_reaction_theme_classifier_defaults_to_general_other():
    classifier = RuleBasedDrugReactionThemeClassifier()

    prediction = classifier.predict_one(
        {
            "reaction_terms": ["Unexpected report", "Unclear event"],
            "top_reaction": "Unclear event",
        }
    )

    assert prediction.label == "general_other"
    assert prediction.confidence == 0.0
    assert prediction.matched_keywords == []


def test_drug_reaction_theme_metrics_include_expected_outputs():
    true_labels = [
        "neurological",
        "gastrointestinal",
        "respiratory",
        "cardiovascular",
    ]
    predicted_labels = [
        "neurological",
        "gastrointestinal",
        "respiratory",
        "respiratory",
    ]

    metrics = evaluate_classifier(true_labels, predicted_labels)

    assert metrics["accuracy"] == accuracy_score(true_labels, predicted_labels)
    assert metrics["macro_f1"] == macro_f1_score(true_labels, predicted_labels)
    assert "confusion_matrix" in metrics
    assert "prediction_counts" in metrics
    assert metrics["safety_disclaimer"] == DrugReactionThemeSafetyDisclaimer


def test_drug_reaction_theme_safety_disclaimer_blocks_unsafe_framing():
    lowered = DrugReactionThemeSafetyDisclaimer.lower()

    assert "public faers/openfda reaction-term theme only" in lowered
    assert "not medical advice" in lowered
    assert "diagnosis" in lowered
    assert "treatment guidance" in lowered
    assert "patient risk prediction" in lowered
    assert "clinical decision support" in lowered
    assert "incidence estimation" in lowered
    assert "proof of faers causation" in lowered