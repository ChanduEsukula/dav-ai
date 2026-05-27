# Dav AI ML Experiments

This folder contains offline ML experiments for Dav AI.

These experiments are not production FastAPI routes and do not change frontend, database, schema, migrations, saved monitors, or live application behavior.

The goal is to prove safe, source-grounded ML readiness using public-data metadata, weak labels, explainable baselines, evaluation metrics, and explicit healthcare safety boundaries.

## Current ML Experiment Set

Dav AI currently has four offline ML experiments:

1. Public Safety Signal Review Priority Classifier v0.1
2. Saved Monitor Anomaly & Trend Classifier v0.2
3. Recall Reason NLP Classifier v0.3
4. DrugSignal Reaction Theme Classifier v0.4

All experiments are dependency-free and use pure Python.

---

## Public Safety Signal Review Priority Classifier v0.1

The first experiment predicts public-data review priority for Dav AI signals.

Target labels:

- `routine`
- `watch`
- `elevated`

The model uses public-data operational metadata from:

- RecallRadar
- DrugSignal
- Regional Health Pulse

### Problem Statement

Given a public-data result or saved monitor-style signal from Dav AI, classify whether it should receive routine, watch, or elevated human review.

This is an operational triage label. It is not a medical-risk prediction.

### Predictors

Current predictors include:

- module
- source ID
- upstream status
- record count
- score
- score label
- query length
- query word count
- source-pull presence
- payload-hash presence
- freshness status
- provenance state
- record-count delta
- record-count percent change
- score delta

### Files

- `review_priority_dataset.py`
  - builds synthetic weak-label examples
  - includes examples across RecallRadar, DrugSignal, and Regional Health Pulse
  - defines categorical, numeric, and boolean predictor groups

- `review_priority_classifier.py`
  - includes a rule-based baseline classifier
  - includes categorical one-hot encoding
  - includes numeric standardization
  - includes deterministic train/test splitting
  - includes accuracy, macro F1, and confusion matrix helpers
  - includes mandatory safety disclaimer text

---

## Saved Monitor Anomaly & Trend Classifier v0.2

The second experiment predicts public-data saved-monitor change state.

Target labels:

- `insufficient_history`
- `stable`
- `increased`
- `decreased`
- `notable_increase`
- `notable_decrease`
- `source_warning`

This is a time-aware public-data monitoring experiment. It is designed to detect whether a saved monitor appears stable, increasing, decreasing, notably changed, lacking enough history, or affected by source/provenance warnings.

It does not predict patient risk, clinical outcomes, outbreak probability, or medical urgency.

### Predictors

Current predictors include:

- module
- source ID
- upstream status
- freshness status
- provenance state
- last scheduled status
- latest record count
- previous record count
- record-count delta
- record-count percent change
- latest score
- previous score
- score delta
- run count
- days since last run
- source-pull presence
- payload-hash presence
- payload-hash changed
- refresh enabled

### Files

- `saved_monitor_anomaly_dataset.py`
  - builds synthetic weak-label saved-monitor history examples
  - includes examples across RecallRadar, DrugSignal, and Regional Health Pulse
  - defines categorical, numeric, and boolean predictor groups

- `saved_monitor_anomaly.py`
  - includes a rule-based saved-monitor anomaly classifier
  - includes categorical one-hot encoding
  - includes numeric standardization
  - includes accuracy, macro F1, and confusion matrix helpers
  - includes mandatory safety disclaimer text

---

## Recall Reason NLP Classifier v0.3

The third experiment predicts public recall reason text category.

Target labels:

- `sterility`
- `contamination`
- `labeling`
- `packaging`
- `potency`
- `foreign_material`
- `temperature_control`
- `other`

This is a public FDA/openFDA recall-text categorization experiment. It classifies recall reason language into operational text categories.

It does not predict patient harm, product safety for a person, treatment guidance, or official FDA severity classification.

### Predictors

Current predictors include:

- reason for recall
- product description
- distribution pattern
- FDA classification text
- recall status
- reason text length
- reason word count
- product description length
- distribution pattern length
- combined recall text

### Files

- `recall_reason_dataset.py`
  - builds synthetic weak-label public recall reason examples
  - includes text, categorical, and numeric predictor groups
  - defines recall reason category labels

- `recall_reason_classifier.py`
  - includes text normalization
  - includes tokenization
  - includes keyword scoring
  - includes a rule-based recall reason classifier
  - includes confidence output
  - includes accuracy, macro F1, and confusion matrix helpers
  - includes mandatory safety disclaimer text

---

## DrugSignal Reaction Theme Classifier v0.4

The fourth experiment predicts public FAERS/openFDA reaction-term theme.

Target labels:

- `neurological`
- `gastrointestinal`
- `respiratory`
- `cardiovascular`
- `skin_allergy`
- `infection_immune`
- `metabolic`
- `general_other`

This is a public reaction-term theme classification experiment for DrugSignal-style adverse-event reporting patterns.

It categorizes reported reaction terms only. It does not claim that a drug caused a reaction.

### Predictors

Current predictors include:

- reaction terms
- top reaction
- source ID
- upstream status
- data confidence
- record count
- reaction count
- top reaction count
- top reaction concentration
- reaction diversity count
- reaction terms length
- reaction terms word count
- combined reaction text

### Files

- `drug_reaction_theme_dataset.py`
  - builds synthetic weak-label public FAERS/openFDA reaction theme examples
  - includes text, categorical, and numeric predictor groups
  - defines reaction theme labels

- `drug_reaction_theme_classifier.py`
  - includes text normalization
  - includes tokenization
  - includes keyword scoring
  - includes a rule-based DrugSignal reaction theme classifier
  - includes confidence output
  - includes accuracy, macro F1, and confusion matrix helpers
  - includes mandatory safety disclaimer text

---

## Why Weak Labels?

The current labels are weak labels, not clinical truth.

They are used to test:

- feature engineering
- preprocessing
- prediction output shape
- evaluation metrics
- safety framing
- future ML-readiness
- cross-module ML coverage
- explainable baseline behavior

A later version can use larger saved-monitor history, reviewed public-data examples, and stronger evaluation workflows.

---

## Safety Boundary

These experiments predict public-data operational labels only.

They are not:

- medical advice
- diagnosis
- treatment guidance
- patient-risk prediction
- clinical decision support
- proof of FAERS causation
- incidence estimation
- emergency guidance
- outbreak prediction
- official FDA severity classification

Every prediction object includes a safety disclaimer. Future production integration should preserve this behavior.

---

## Running Tests

From the backend folder, run the full ML experiment test set:

```bash
PYTHONDONTWRITEBYTECODE=1 ../.venv/bin/python -m pytest -p no:cacheprovider \
  tests/test_review_priority_classifier.py \
  tests/test_saved_monitor_anomaly_experiment.py \
  tests/test_recall_reason_classifier_experiment.py \
  tests/test_drug_reaction_theme_classifier_experiment.py