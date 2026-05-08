# MedTrek AI Roadmap

## Current AI Position

MedTrek AI is becoming a source-grounded healthcare safety intelligence platform.

The project is intentionally not a generic medical chatbot. Its AI direction is focused on explainable, auditable, public-data intelligence.

Current AI-style capabilities include:

- DrugSignal Intelligence Score v1
- Safety briefing generation
- Source transparency
- Audit history
- Public-data traceability
- Healthcare safety disclaimers
- Data-quality visibility

## Completed AI Milestone: DrugSignal Intelligence Score v1

DrugSignal Intelligence Score v1 adds an explainable scoring layer to public FAERS adverse-event search results.

The score is based on:

- Returned FAERS record count
- Top reaction concentration
- Reaction diversity
- Data confidence

The score returns:

- Score from 0 to 100
- Signal strength label
- Review priority
- Data confidence
- Top reaction concentration
- Score version
- Safety limitations

Current score version:

- drug-signal-intelligence-v0.1

## Why This Matters

This milestone moves MedTrek AI beyond a public-data dashboard.

It now produces an explainable intelligence signal that is:

- Source-grounded
- Auditable
- Versioned
- Tested
- Displayed in production
- Documented
- Healthcare-safe

The system still avoids medical advice, diagnosis, treatment guidance, or claims of causation.

## Current Safety Boundary

DrugSignal Intelligence does not prove that a drug caused an adverse event.

FAERS reports are safety signals only and may be incomplete, duplicated, or influenced by reporting patterns.

Scores are based on returned public openFDA records and reaction counts, not clinical incidence rates.

## Current Implementation

Backend:

- backend/app/scoring/drug_signal_score.py
- backend/app/routes/drug_events.py
- backend/app/schemas/drug_events.py

Frontend:

- frontend/src/components/DrugSignal.tsx
- frontend/src/api/drugEvents.ts
- frontend/src/styles/drugsignal.css

Tests:

- backend/tests/test_drug_signal_score.py
- backend/tests/test_drug_events_route.py
- frontend/src/components/DrugSignal.test.tsx
- frontend/src/utils/briefingGenerator.test.ts

Documentation:

- docs/drug_signal_intelligence_score.md
- docs/drug_signal_intelligence_frontend_verification.md
- docs/drug_signal_intelligence_backend_verification.md

## Completed AI Milestone: Reaction Classification v1

Reaction Classification v1 groups returned FAERS reaction terms into understandable categories.

Categories include:

- Gastrointestinal
- Neurological
- Respiratory
- Cardiovascular
- Skin / allergy
- Infection / immune
- Metabolic
- General / other

The first version is intentionally rule-based because it is:

- Safer for healthcare context
- Easier to explain
- Easier to test
- Easier to audit
- A strong baseline before ML or embedding-based clustering

Implemented components:

- backend/app/scoring/reaction_classifier.py
- backend/tests/test_reaction_classifier.py
- frontend/src/components/DrugSignal.tsx
- docs/drug_signal_reaction_classification_verification.md

Current classifier version:

- reaction-classifier-v0.1

## Future AI Layer: NLP-Assisted Reaction Clustering

After rule-based classification, MedTrek AI can add lightweight NLP clustering.

Possible approaches:

- TF-IDF vectors
- Similarity grouping
- Embedding-based semantic clustering
- Reaction normalization
- Category confidence scoring

This should be added only after the rule-based baseline is implemented and tested.

## Future AI Layer: Source-Grounded Briefing Intelligence

The briefing engine can evolve into a more advanced AI-assisted module.

Important constraint:

Briefings should only use retrieved structured facts.

Future briefing inputs:

- Search query
- Source name
- Endpoint
- Retrieval timestamp
- Audit ID
- Record count
- Intelligence score
- Top reactions
- Reaction categories
- Safety limitations

The briefing output should remain:

- Role-aware
- Source-grounded
- Auditable
- Guardrailed
- Non-diagnostic

## Future AI Layer: Semantic Search

Semantic search can make RecallRadar and DrugSignal easier to use.

Examples:

- “eye drops with sterility problems”
- “reports involving breathing issues”
- “drug events related to balance or gait”
- “products with contamination concerns”

Possible tools later:

- Embeddings
- Vector search
- Query expansion
- Source-grounded retrieval

This should come after scoring and classification are stable.

## Future AI Layer: Anomaly and Trend Detection

MedTrek AI can later detect changes over time.

Possible features:

- Spike detection in adverse-event reports
- Recall trend changes
- New reaction category emergence
- Source update monitoring
- Time-window comparison

This would strengthen the MIT-style situational awareness direction.

## Recommended AI Roadmap

### Immediate

1. Keep DrugSignal Intelligence Score v1 stable.
2. Verify production behavior after deploys.
3. Add AI roadmap documentation.
4. Prepare demo narrative for DrugSignal Intelligence.

### Next

1. Add Reaction Classification v1.
2. Show reaction category summary in DrugSignal.
3. Add backend tests for category classification.
4. Document the classification rules and limitations.

### Later

1. Add NLP-assisted reaction clustering.
2. Add semantic search.
3. Add time-series trend detection.
4. Add source-grounded AI briefing enhancements.

## Interview Positioning

MedTrek AI can be described as:

A source-grounded healthcare safety intelligence platform that uses public FDA data, explainable scoring, audit trails, and safety guardrails to help users understand recall and adverse-event signals without making medical claims.

Strong resume framing:

Built MedTrek AI, a deployed healthcare safety intelligence platform using React, TypeScript, FastAPI, Supabase/PostgreSQL, openFDA, explainable signal scoring, audit trails, request tracing, and healthcare safety guardrails. Added DrugSignal Intelligence Score v1 to transform public FAERS adverse-event records into transparent, versioned, source-grounded safety signals.

## Current Best Next Move

Build Reaction Classification v1 for DrugSignal.

This is the best next AI-focused step because it adds real NLP-style intelligence while staying explainable, testable, and healthcare-safe.
