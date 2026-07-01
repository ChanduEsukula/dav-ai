# DrugSignal Safety Briefing Engine v2 Verification

Date verified: 2026-05-08  
Feature: Safety Briefing Engine v2  
Frontend: $DAV_AI_FRONTEND_URL

## Summary

Safety Briefing Engine v2 is live for DrugSignal.

The briefing now uses DrugSignal Intelligence Score and Reaction Classification output to create a richer, role-aware, source-grounded safety briefing.

## Production verification

Search query tested:

- metformin

Observed production behavior:

- Safety Briefing Engine v2 label displayed.
- Consumer briefing displayed.
- DrugSignal source pill displayed.
- What was found section included score, priority, confidence, concentration, leading category, and top reaction.
- What to verify section included score version and reaction classifier version.
- Limitations section included scoring and rule-based classification limitations.

## Observed v2 briefing details

What was found included:

- 10 FAERS record(s) reviewed for reporting-pattern context.
- DrugSignal Intelligence score: 80/100 High.
- Review priority: Review.
- Data confidence: Strong.
- Top reaction concentration: 16.67%.
- Leading reaction category: General / other.
- Top reported reaction term: Gait disturbance.
- Adverse-event reporting patterns are not proof of causation.

What to verify included:

- Drug name, brand/generic naming, and source query context.
- Score version: drug-signal-intelligence-v0.1.
- Reaction classifier version: reaction-classifier-v0.1.
- FAERS limitations before interpreting reaction terms or categories.

Limitations included:

- FAERS reports are safety signals only and do not prove causation.
- Scores are based on returned public openFDA records and reaction counts, not clinical incidence rates.
- Reaction classification is rule-based and may group incomplete or ambiguous public adverse-event terms.
- This briefing is not medical advice, diagnosis, or treatment guidance.

## Implemented components

Frontend:

- frontend/src/utils/briefingGenerator.ts
- frontend/src/utils/briefingGenerator.test.ts
- frontend/src/components/SafetyBriefingPanel.tsx
- frontend/src/components/DrugSignal.test.tsx

Related AI layers:

- DrugSignal Intelligence Score v1
- Reaction Classification v1

## Safety note

Safety Briefing Engine v2 summarizes public-data safety signals only.

It does not provide medical advice, diagnosis, treatment guidance, clinical causation, clinical incidence, or patient-level risk.

## Current status

Safety Briefing Engine v2 is live and verified in production.
