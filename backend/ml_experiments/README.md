# Dav AI ML Experiments

This folder contains offline ML experiments for Dav AI.

These experiments are not production FastAPI routes and do not change frontend, database, schema, migrations, saved monitors, or live application behavior.

## Current Experiment

### Public Safety Signal Review Priority Classifier v0.1

The first experiment predicts public-data review priority for Dav AI signals.

Target labels:

- `routine`
- `watch`
- `elevated`

The model uses public-data operational metadata from:

- RecallRadar
- DrugSignal
- Regional Health Pulse

## Problem Statement

Given a public-data result or saved monitor-style signal from Dav AI, classify whether it should receive routine, watch, or elevated human review.

This is an operational triage label. It is not a medical-risk prediction.

## Safety Boundary

This experiment predicts public-data review priority only.

It is not:

- medical advice
- diagnosis
- treatment guidance
- patient-risk prediction
- clinical decision support
- proof of FAERS causation
- emergency guidance
- outbreak prediction

## Predictors

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

## Current Implementation

The current implementation is dependency-free and uses pure Python.

Files:

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

## Why Weak Labels?

The current labels are weak labels, not clinical truth.

They are used to test:

- feature engineering
- preprocessing
- prediction output shape
- evaluation metrics
- safety framing
- future ML-readiness

A later version can use larger saved-monitor history and reviewed public-data examples.

## Running Tests

From the backend folder:

```bash
PYTHONDONTWRITEBYTECODE=1 ../.venv/bin/python -m pytest -p no:cacheprovider tests/test_review_priority_classifier.py