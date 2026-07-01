# DAV AI Roadmap

## Current AI Position

DAV AI is becoming a source-grounded healthcare safety intelligence platform.

The project is intentionally not a generic medical chatbot. Its AI direction is focused on explainable, auditable, public-data intelligence.

Current AI-style capabilities include:

- DrugSignal Intelligence Score v1
- Reaction Classification v1
- DrugSignal Trend Snapshot v1
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

This milestone moves DAV AI beyond a public-data dashboard.

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

## Completed AI Milestone: DrugSignal Trend Snapshot v1

DrugSignal Trend Snapshot v1 compares the current DrugSignal result with recent stored audit history when previous matching audit events are available.

Current v1 inputs:

- Current query
- Current record count
- Recent audit event for the same query/module when available
- Previous record count
- Previous timestamp
- Previous audit ID

Current v1 output:

- Simple trend label such as Increased, Decreased, Stable, or Insufficient history
- Current record count
- Previous record count when available
- Previous audit ID and timestamp when available
- Plain-language explanation
- Safety limitation that trend is based only on stored public-data searches in DAV AI

Why this matters:

It adds an early temporal intelligence layer and supports the MIT-inspired monitoring and situational-awareness direction of DAV AI. It is still limited because it depends on DAV AI's stored audit history, not all FDA activity.

## Future AI Layer: NLP-Assisted Reaction Clustering

After rule-based classification, DAV AI can add lightweight NLP clustering.

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

## Verified AI/NLP Readiness Milestone: Semantic Similarity Preview

RecallRadar and DrugSignal now include a verified semantic similarity preview in their search responses:

- `GET /api/v1/recalls/search` returns `semantic_preview`.
- `GET /api/v1/drug-events/search` returns `semantic_preview`.

The preview uses deterministic public-data text similarity only. It is intended to support future similar-record review, recall/reaction grouping, and safer NLP experimentation.

Verification:

- Backend tests passed with 235 passed.
- Live smoke tests confirmed `semantic_preview` appears for both RecallRadar and DrugSignal.

Safety boundaries:

- It is not production ML.
- It is not RAG or LLM output.
- It is not alerting.
- It is not medical advice, diagnostic output, care guidance, clinical decision support, or a medical device.
- It does not claim FAERS causation, product danger, patient-specific risk, outbreak activity, or clinical urgency.

## Future AI Layer: Semantic Search

Semantic search can make RecallRadar and DrugSignal easier to use after the deterministic preview is evaluated further.

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

DAV AI can later detect changes over time.

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
3. Keep Reaction Classification v1 and DrugSignal Trend Snapshot v1 documented as implemented baselines.
4. Add examples and test fixtures that make current scoring, classification, and trend behavior easier to review.

### Next

1. Evaluate and harden Reaction Classification v1 with test fixtures, examples, and future ML/NLP evaluation criteria.
2. Improve DrugSignal Trend Snapshot examples using repeated-query audit history.
3. Add clearer comparison language for score, record-count, and category changes where supported.
4. Keep FAERS limitations visible anywhere DrugSignal intelligence is described.

### Later

1. Add NLP-assisted reaction clustering.
2. Add semantic search.
3. Add time-series trend detection.
4. Add source-grounded AI briefing enhancements.

## Interview Positioning

DAV AI can be described as:

A source-grounded public-data safety intelligence platform prototype that uses public FDA data, explainable scoring, audit trails, and safety guardrails to help users understand recall and adverse-event signals without making medical claims.

Strong resume framing:

Built DAV AI, a deployment-ready public-data safety intelligence platform prototype using React, TypeScript, FastAPI, Supabase/PostgreSQL-oriented persistence, openFDA, explainable signal scoring, audit trails, request tracing, and safety guardrails. Added DrugSignal Intelligence Score v1 to transform public FAERS adverse-event records into transparent, versioned, source-grounded safety signals.

## Current Best Next Move

Evaluate and harden Reaction Classification v1 with test fixtures, examples, and future ML/NLP evaluation criteria.

This is the best next AI-focused step because Reaction Classification v1 is already implemented as a rule-based baseline. The next maturity step is to prove where it works, document where it is limited, and prepare a responsible path toward NLP-assisted clustering without weakening explainability or healthcare safety boundaries.
