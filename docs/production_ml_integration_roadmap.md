# Production ML Integration Roadmap

DAV AI now includes an offline ML experiment layer under `backend/ml_experiments/`.

The current ML experiments are intentionally offline. They are not production FastAPI routes, not user-facing features, not clinical decision systems, and not connected to frontend behavior.

This roadmap explains what must happen before any ML output is added to production workflows.

## Current Offline ML Experiments

DAV AI currently includes four offline, dependency-free ML baseline experiments:

1. **Public Safety Signal Review Priority Classifier v0.1**
   - Predicts `routine`, `watch`, or `elevated` public-data review priority.

2. **Saved Monitor Anomaly & Trend Classifier v0.2**
   - Predicts saved-monitor public-data change states such as `stable`, `increased`, `notable_increase`, or `source_warning`.

3. **Recall Reason NLP Classifier v0.3**
   - Categorizes public recall reason text into operational text categories such as `sterility`, `contamination`, `labeling`, `packaging`, `potency`, and related classes.

4. **DrugSignal Reaction Theme Classifier v0.4**
   - Categorizes public FAERS/openFDA reaction terms into themes such as `neurological`, `gastrointestinal`, `respiratory`, `cardiovascular`, and related classes.

These experiments prove ML readiness, not production readiness.

## Why ML Is Offline First

DAV AI is healthcare-adjacent and source-grounded. Even when using public data only, ML outputs can be misread as medical advice if they are not carefully framed.

The offline-first approach is intentional because production ML needs:

- real public-data history
- stronger datasets
- reviewed labels
- evaluation metrics
- false-positive and false-negative review
- safety language tests
- source provenance
- auditability
- feature/version lineage
- rollback controls
- clear UI framing

Passing unit tests is not enough to make an ML prediction safe for production use.

## What Production ML Must Not Do

DAV AI production ML must not predict or imply:

- patient-specific harm
- disease risk for an individual
- whether a drug caused an adverse event
- whether a product or medication is safe for a specific person
- whether someone should start, stop, or change medication
- clinical diagnosis
- treatment recommendations
- emergency guidance
- outbreak probability from scaffold-only data
- incidence or prevalence from FAERS reports
- official FDA severity classification beyond source data
- legal or compliance conclusions

Production ML should stay focused on public-data review support.

## Safe Production Framing

If ML is eventually integrated, it should be framed as:

- review-priority assistance
- public-data trend support
- source-aware triage
- recall reason categorization
- reaction theme categorization
- monitor change explanation

It should not be framed as:

- medical risk prediction
- clinical decision support
- AI diagnosis
- causation detection
- official regulatory judgment
- emergency alerting

Recommended UI language:

> ML-assisted review priority: Watch  
> Reason: record count increased, source is fresh, and provenance is complete.  
> Limitation: this is public-data monitoring only and is not medical advice.

## Phase 1: Data Readiness

Before production integration, DAV AI should collect and review more real public-data examples from:

- Audit History
- Saved Monitor runs
- Source Pull snapshots
- RecallRadar searches
- DrugSignal searches
- Regional Health Pulse searches

The goal is to move beyond synthetic weak-label examples.

Useful future dataset fields include:

- module
- source ID
- query
- upstream status
- record count
- score
- score label
- latest record count
- previous record count
- record-count delta
- record-count percent change
- score delta
- run count
- freshness status
- provenance state
- payload hash state
- audit ID
- transform version
- score version
- created timestamp

## Phase 2: Human-Reviewed Labels

Weak labels are useful for early experiments, but production ML should include reviewed labels.

Potential reviewed labels include:

- `routine`
- `watch`
- `elevated`
- `source_warning`
- `insufficient_history`
- `stable`
- `increased`
- `decreased`
- `notable_increase`
- `notable_decrease`

These labels should describe operational public-data review priority only.

They should not describe patient risk, diagnosis, treatment urgency, or medical severity.

## Phase 3: Evaluation

Before production integration, each model should be evaluated with:

- accuracy
- macro F1
- precision and recall per class
- confusion matrix
- false-positive review
- false-negative review
- calibration review if probabilities are shown
- module-specific performance
- source-specific performance
- safety phrase checks
- source/audit coverage checks

Important review questions:

- Does the model over-prioritize FAERS report counts as causation?
- Does it under-prioritize sharp recall changes?
- Does it treat source errors as medical risk instead of source warnings?
- Does it incorrectly treat empty results as “safe”?
- Does it treat Regional Health Pulse scaffold data as live outbreak surveillance?
- Does every prediction include source and limitation context?

## Phase 4: Internal Backend Preview

The first production-like integration should be backend-only and internal.

Possible route:

```text
POST /api/v1/ml/review-priority/preview