# DrugSignal Intelligence Backend Verification

Date verified: 2026-05-08
Feature: DrugSignal Intelligence Score v1
Backend: $DAV_AI_BACKEND_URL

## Summary

The production Render backend was verified after adding DrugSignal Intelligence Score v1.

The `/api/v1/drug-events/search` endpoint now returns an `intelligence_score` object with an explainable score, label, data confidence, review priority, score version, and safety limitations.

## Production verification command

curl -s --max-time 30 "$DAV_AI_BACKEND_URL/api/v1/drug-events/search?q=metformin&limit=10" | python3 -m json.tool

## Observed response

Search query:

- metformin

Observed backend result:

- Count: 10
- Source: openFDA Drug Event API
- Endpoint: https://api.fda.gov/drug/event.json
- Audit ID: c89b9ede-59ac-459f-94cc-7bd5bb5df268
- Module: DrugSignal
- Upstream status: success
- Record count: 10
- Transform version: drug-event-transform-v0.1

Observed intelligence score:

- Score: 80
- Label: High
- Data confidence: Strong
- Top reaction concentration: 16.67
- Review priority: Review
- Score version: drug-signal-intelligence-v0.1

## Safety limitations verified

The backend response includes these limitations:

- FAERS adverse-event reports are safety signals only and do not prove causation.
- Scores are based on returned public openFDA records and reaction counts, not clinical incidence rates.

The endpoint also returns the standard medical disclaimer and FAERS disclaimer.

## Why this matters

This verifies that DrugSignal Intelligence is not only a frontend display feature.

The production backend now generates source-grounded, explainable AI-style scoring from public adverse-event data while preserving healthcare safety language.

## Current status

DrugSignal Intelligence Score v1 is live and working in the production backend.
