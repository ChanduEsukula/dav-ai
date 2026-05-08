# DrugSignal Reaction Classification Verification

Date verified: 2026-05-08  
Feature: Reaction Classification v1  
Frontend: https://medtrek-ai.vercel.app

## Summary

DrugSignal now groups returned top FAERS reaction terms into explainable reaction categories.

This adds an NLP-style classification layer while staying rule-based, testable, auditable, and healthcare-safe.

## Production verification

Search query tested:

- metformin

Observed production behavior:

- DrugSignal Intelligence card displayed above the classification card.
- Reaction Classification card displayed successfully.
- Category names displayed.
- Category counts displayed.
- Grouped reaction terms displayed under each category.

Observed categories included:

- General / other
- Neurological
- Infection / immune
- Metabolic

Example grouped terms observed:

- General / other: Medication residue present, Splenomegaly, Unevaluable event
- Neurological: Balance disorder, Gait disturbance
- Infection / immune: Erysipelas, Osteomyelitis, Sepsis
- Metabolic: Weight increased

## Implemented components

Backend:

- backend/app/scoring/reaction_classifier.py
- backend/app/routes/drug_events.py
- backend/app/schemas/drug_events.py
- backend/tests/test_reaction_classifier.py
- backend/tests/test_drug_events_route.py

Frontend:

- frontend/src/api/drugEvents.ts
- frontend/src/components/DrugSignal.tsx
- frontend/src/components/DrugSignal.test.tsx
- frontend/src/styles/drugsignal.css
- frontend/src/utils/briefingGenerator.test.ts

## Classifier version

reaction-classifier-v0.1

## Safety note

Reaction categories are rule-based groupings of returned public adverse-event terms.

They do not prove causation, diagnosis, clinical incidence, or patient-level risk.

## Current status

Reaction Classification v1 is live and verified in production.
