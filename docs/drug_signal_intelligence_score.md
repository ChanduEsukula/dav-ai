# DrugSignal Intelligence Score v1

## Summary

DrugSignal Intelligence Score v1 is an explainable scoring layer for public FAERS adverse-event search results.

It is designed to summarize returned public openFDA Drug Event records into a transparent signal score without implying medical causation.

## Score version

drug-signal-intelligence-v0.1

## Inputs

The score uses only data returned by the current DrugSignal search:

- Record count
- Top reported reaction counts
- Top reaction concentration
- Reaction diversity
- Data confidence

## Components

### Record count component

- 0 records: 0 points
- 1–2 records: 15 points
- 3–9 records: 25 points
- 10+ records: 35 points

### Top reaction concentration component

Top reaction concentration is calculated as:

top reaction count / total top reaction mentions

- 60% or higher: 25 points
- 40% to 59%: 18 points
- 20% to 39%: 10 points
- Below 20%: 5 points

### Reaction diversity component

- 0 reactions: 0 points
- 1 reaction: 5 points
- 2–4 reactions: 12 points
- 5+ reactions: 20 points

### Data confidence component

- Limited: 5 points
- Moderate: 12 points
- Strong: 20 points

Data confidence is based on returned record count:

- 0–2 records: Limited
- 3–9 records: Moderate
- 10+ records: Strong

## Labels

Final score is capped at 100.

- 0–30: Low
- 31–60: Moderate
- 61–100: High

## Review priority

- Low score: Low
- Moderate score: Watch
- High score: Review

## Safety limitations

FAERS adverse-event reports are safety signals only and do not prove causation.

Scores are based on returned public openFDA records and reaction counts, not clinical incidence rates.

The score should not be interpreted as medical advice, diagnosis, treatment guidance, or proof that a drug caused an event.

## Current implementation

Backend scoring helper:

- backend/app/scoring/drug_signal_score.py

Backend route integration:

- backend/app/routes/drug_events.py

Backend schema:

- backend/app/schemas/drug_events.py

Frontend display:

- frontend/src/components/DrugSignal.tsx

Frontend API type:

- frontend/src/api/drugEvents.ts

Tests:

- backend/tests/test_drug_signal_score.py
- backend/tests/test_drug_events_route.py
- frontend/src/components/DrugSignal.test.tsx
- frontend/src/utils/briefingGenerator.test.ts
