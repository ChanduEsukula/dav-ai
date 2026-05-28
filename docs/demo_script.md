# Dav AI Senior Engineering Demo Script

## 1. One-Sentence Product Description

Dav AI is a public-data healthcare safety intelligence workspace that helps users search, review, audit, monitor, and explain FDA/openFDA-style safety signals with source transparency, deterministic review workflows, and responsible AI boundaries.

Dav AI is not a medical chatbot, not a clinical decision-support system, not a diagnosis tool, and not a patient-risk prediction product.

## 2. Product Positioning

Dav AI should be presented as a public-data safety intelligence platform.

The strongest identity of the project is:

> A source-aware review workspace for public safety data, built with auditability, transparency, repeatable monitoring, deterministic scoring, and responsible ML governance.

The project should not be presented as:

- a medical advice tool
- a clinical AI assistant
- a patient diagnosis system
- a drug safety verdict engine
- a production ML prediction system
- a live outbreak surveillance platform

The correct framing is:

> Dav AI helps reviewers make sense of public safety data. It does not make clinical decisions.

## 3. Problem

Public healthcare safety data from sources like FDA/openFDA is available, but it is difficult to search, compare, audit, monitor, and explain in a structured way.

Raw public data often has several challenges:

- records are hard to review quickly
- source context is easy to lose
- repeated searches are manual
- changes over time are difficult to track
- audit history is usually missing
- users may overinterpret adverse-event data
- AI/ML outputs can be unsafe if not clearly bounded

The core problem Dav AI addresses is not diagnosis.

The core problem is review workflow:

> Search public data → normalize results → score review priority → preserve audit trail → generate bounded briefing → save monitors → compare future changes → prepare for responsible ML.

## 4. Demo Flow

### Step 1: Start With the Product Boundary

Before showing screens, explain the safety boundary clearly.

Say:

> Dav AI works with public FDA/openFDA-style data. It does not use PHI, private patient records, diagnosis history, prescription history, insurance data, or personal medical information. The goal is public-data review support, not medical advice.

This establishes maturity immediately and prevents the project from sounding like an unsafe healthcare chatbot.

---

### Step 2: RecallRadar

Show RecallRadar first.

Explain:

- RecallRadar searches public recall data.
- Results are normalized into reviewable cards.
- Each result is easier to scan than raw FDA/openFDA output.
- The Recall Review Score is rule-based and transparent.
- The score helps prioritize review attention.
- The score is not a product-specific safety verdict.

Key phrase:

> RecallRadar helps prioritize public-data review. It does not tell a patient what to do medically.

Senior-engineer explanation:

> I intentionally started with deterministic scoring rather than ML because recall review needs explainability, source traceability, and safety language before prediction. Each score should be understandable and auditable.

What to emphasize:

- normalized public-data search
- transparent scoring
- public-data limitation language
- no medical advice
- audit metadata attached to the workflow

---

### Step 3: DrugSignal

Show DrugSignal second.

Explain:

- DrugSignal uses openFDA Drug Event / FAERS-style reporting data.
- It summarizes reporting patterns and top reactions.
- It includes DrugSignal intelligence-style review indicators.
- It avoids causation claims.
- It treats FAERS data as reporting-pattern data only.

Key phrase:

> FAERS reports do not prove causation or incidence. Dav AI treats them as public reporting patterns only.

Senior-engineer explanation:

> This is one of the most important responsible AI boundaries in the project. Adverse-event reports can be incomplete, duplicated, delayed, biased, or missing clinical context. So the UI and backend language must avoid saying that a drug caused an event.

What to emphasize:

- reporting-pattern review
- no causation
- no incidence estimate
- no individual risk prediction
- safety disclaimers
- deterministic summarization before advanced AI

---

### Step 4: Audit History

Show Audit History after RecallRadar and DrugSignal.

Explain:

- Every public-data search should be traceable.
- Audit events capture source and workflow metadata.
- Audit fields include module, source, endpoint, query, query parameters, retrieval timestamp, record count, transform version, score version, disclaimer version, upstream status, and error information where applicable.
- This is one of the strongest senior-engineering parts of the system.

Key phrase:

> I wanted every intelligence output to be traceable back to source metadata, query behavior, transform version, score version, and disclaimer version.

Senior-engineer explanation:

> In an AI-adjacent healthcare project, the audit trail is not optional. Before adding more AI, I wanted the system to answer: where did this result come from, when was it retrieved, what logic transformed it, and what limitations were shown?

What to emphasize:

- auditability
- provenance
- versioned scoring/disclaimer logic
- traceability before AI ambition
- reviewer trust

---

### Step 5: Data Sources and System Status

Show Data Sources and System Status.

Explain:

- The source registry gives the product a single place to describe public data sources.
- System Status gives operational visibility.
- Data Sources helps users understand what is live, scaffolded, fresh, stale, or unavailable.
- This creates transparency instead of hiding source limitations.

Key phrase:

> A safety intelligence platform should not only show answers. It should show where the answers came from and how reliable the source pull was.

Senior-engineer explanation:

> This is part of turning the project from a simple API demo into an operational product. Source visibility, freshness, and audit-backed status are important for trust.

What to emphasize:

- source registry
- audit-backed freshness
- operational transparency
- public-data limitations
- user trust

---

### Step 6: Saved Monitors

Show Saved Monitors.

Explain:

- Users can save repeatable public-data searches.
- Manual runs compare latest and previous results.
- Saved Monitors create a foundation for longitudinal public-data review.
- Monitor insights are deterministic and bounded.
- Production alerts, Cron, auth/RBAC, and notification preferences are intentionally not fully productionized yet.

Key phrase:

> Saved Monitors create the foundation for longitudinal public-data review, but alerting requires ownership, preferences, and stronger safety controls before production use.

Senior-engineer explanation:

> This module turns one-time search into a repeatable workflow. But I intentionally avoid calling it a production alerting system because alerts in healthcare-adjacent workflows need user ownership, preferences, escalation rules, and careful safety copy.

What to emphasize:

- repeatable searches
- manual run history
- previous vs. latest comparison
- deterministic insight layer
- not full production alerting yet

---

### Step 7: Regional Health Pulse

Show Regional Health Pulse carefully.

Explain:

- Regional Health Pulse is an architecture scaffold.
- It demonstrates how public-health-style signal workflows could fit into the platform.
- It is not live CDC/HHS surveillance.
- It is not outbreak detection.
- It is not emergency guidance.
- It should be described as sample/scaffold behavior only.

Key phrase:

> This module is intentionally labeled as scaffold/sample-data behavior, not live surveillance or outbreak detection.

Senior-engineer explanation:

> I kept this module bounded because public-health signals can be easily overclaimed. The current value is architectural: it shows how the same search, score, audit, source, and monitor pattern could extend to public-health datasets later.

What to emphasize:

- scaffold only
- no outbreak claims
- architecture pattern reuse
- future connector potential
- honest product boundary

---

### Step 8: Offline Responsible ML Experiments

Show backend/ml_experiments.

Explain:

- ML was added offline first.
- The experiments use synthetic weak-label fixtures.
- They test ML problem framing, dataset shape, feature engineering, labels, metrics, and safety disclaimers.
- They are not wired into FastAPI routes.
- They are not shown in the frontend.
- They are not production ML models.
- They are not used for alerts or automated decisions.

Current offline experiments:

- Public Safety Signal Review Priority Classifier v0.1
- Saved Monitor Anomaly & Trend Classifier v0.2
- Recall Reason NLP Classifier v0.3
- DrugSignal Reaction Theme Classifier v0.4

Key phrase:

> I intentionally kept ML offline until real public-data history, reviewed labels, evaluation, error analysis, feature/version lineage, UI limitation language, and rollback controls exist.

Senior-engineer explanation:

> The responsible ML decision here is not just what I built. It is what I refused to productionize. In a healthcare-adjacent platform, passing tests is not enough to expose predictions to users. The system needs labels, evaluation, false-positive and false-negative review, feature lineage, versioning, monitoring, and rollback.

What to emphasize:

- offline-only ML
- weak-label disclosure
- deterministic baselines
- no production inference
- healthcare safety boundary
- maturity through restraint

## 5. Architecture Story

Dav AI follows a clean full-stack architecture.

Frontend:

- React
- TypeScript
- Vite
- Axios API clients
- component-based product pages
- custom CSS
- Vitest
- React Testing Library

Backend:

- FastAPI
- Pydantic schemas
- route/service/scoring/repository separation
- openFDA clients
- deterministic scoring modules
- audit repository
- source registry
- saved-monitor workflows
- scheduled-refresh foundation
- PostgreSQL/Supabase-ready persistence
- Alembic migrations
- pytest

AI/ML layer:

- offline experiments
- synthetic weak-label datasets
- explainable baseline classifiers
- text classification experiments
- metrics hooks
- safety disclaimers
- no production ML integration yet

System design principle:

> Dav AI is designed around traceability, public-data boundaries, deterministic review support, and responsible AI governance.

## 6. End-to-End Data Flow

A strong way to explain the system is with one end-to-end flow:

1. User enters a public-data search query.
2. Frontend sends a typed API request.
3. FastAPI route validates the request.
4. Service workflow calls the public data source.
5. Records are normalized.
6. Deterministic scoring or classification is applied where appropriate.
7. Source and audit metadata are generated.
8. Persistence stores audit/source-pull information when available.
9. Frontend displays results with source context and limitations.
10. User can save a monitor for repeatable review.
11. Future runs can compare latest vs. previous public-data activity.
12. Offline ML experiments prepare future review-priority and trend intelligence without changing production behavior.

Key phrase:

> The project is not just a frontend calling an API. It has a review workflow, source registry, audit trail, scoring layer, persistence boundary, monitor loop, and responsible ML roadmap.

## 7. Responsible AI Boundary

Dav AI does not use:

- PHI
- private patient records
- diagnosis data
- prescription history
- insurance data
- addresses
- personal medical narratives
- user-specific medical history

Dav AI avoids:

- medical advice
- diagnosis
- treatment recommendations
- medication-change guidance
- causation claims
- incidence claims
- outbreak prediction
- patient-specific risk prediction
- clinical decision support

Correct framing:

> Dav AI supports public-data review. It does not make clinical decisions.

## 8. Current Honest Status

### Implemented

- RecallRadar
- DrugSignal
- Data Sources
- System Status
- Audit History
- Saved Monitors foundation
- Regional Health Pulse scaffold
- deterministic safety briefings
- source registry
- audit/source transparency
- source-pull metadata foundation
- rule-based review scoring
- offline Responsible ML experiments
- backend tests
- frontend tests
- frontend linting
- CI workflow

### Partially Implemented

- Saved monitor scheduled-refresh foundation
- source freshness visibility
- source-pull and payload-hash foundation
- public-health-style Regional Health Pulse architecture
- PDF/report generation foundation
- responsible ML roadmap

### Not Production-Grade Yet

- production ML
- reviewed-label datasets
- clinical validation
- live CDC/HHS surveillance
- production alert delivery
- notification preferences
- auth/RBAC
- full deployment observability dashboard
- model registry
- semantic search
- source-grounded RAG assistant
- deep learning models
- patient-specific workflows

## 9. Interview Talking Points

### For AI Engineer Roles

Say:

> I built deterministic safety briefings first and kept LLM/RAG ideas on the roadmap until source grounding, evaluation, retrieval quality, and guardrails are mature.

Emphasize:

- grounded public-data workflows
- deterministic briefing logic
- responsible AI boundaries
- no unsafe chatbot claims
- future RAG only after better source grounding

### For ML Engineer Roles

Say:

> I started with offline ML baselines, weak-label disclosure, feature engineering, metrics, and safety tests before productionizing any model.

Emphasize:

- offline experiments
- feature design
- labels
- metrics
- error analysis roadmap
- reviewed labels as next step
- no production ML overclaiming

### For Backend Engineer Roles

Say:

> I can explain the backend from routes to services to scoring to persistence to audit history.

Emphasize:

- FastAPI
- route/service separation
- source clients
- repositories
- request IDs
- audit events
- scheduler locks
- persistence fallback
- tests

### For Full-Stack Engineer Roles

Say:

> I can walk through the full path from frontend search to backend source call to normalized results, scoring, audit persistence, and UI provenance display.

Emphasize:

- React + TypeScript
- typed API clients
- FastAPI backend
- source transparency
- user-facing limitations
- end-to-end workflow

### For Responsible AI / Health-Tech Roles

Say:

> The strongest responsible AI decision was keeping ML offline and bounded until the system has real data history, reviewed labels, evaluation, versioning, and rollback controls.

Emphasize:

- public data only
- no PHI
- no clinical claims
- FAERS limitations
- auditability
- explainability
- safety copy

## 10. What Makes This Senior-Engineering Level

The project shows senior-engineering instincts because it includes:

- clear product boundaries
- source-aware architecture
- audit trail design
- deterministic scoring before ML
- saved-monitor workflow design
- safety language in product flow
- test coverage across backend and frontend
- CI workflow
- documentation discipline
- honest roadmap separation
- restraint around production ML

The strongest senior-engineering point:

> The project does not rush to AI. It builds the trust, audit, source, and evaluation foundation first.

## 11. What I Should Not Overclaim

Do not say:

- This predicts patient risk.
- This detects outbreaks.
- This proves a drug caused a reaction.
- This is production ML.
- This is clinical decision support.
- This replaces FDA review.
- This gives medical advice.
- This is a live surveillance system.

Instead say:

- This supports public-data review.
- This prioritizes records for human review.
- This summarizes reporting patterns.
- This preserves source traceability.
- This uses deterministic baselines.
- This has offline ML experiments.
- This is designed for responsible ML integration later.

## 12. Current Verification Snapshot

Current verification from the responsible ML progress review:

- Backend tests: 182 passed
- Frontend tests: 64 passed
- Frontend lint: passed
- Repository was clean before and after inspection
- Frontend build was intentionally skipped locally to avoid modifying frontend/dist
- CI workflow includes backend tests, frontend tests, lint, build, and smoke-test coverage

Important explanation:

> The verification proves engineering quality and test coverage. It does not prove real-world clinical validity or production ML readiness.

## 13. Recommended Demo Order

Use this order in interviews or presentations:

1. Start with the product boundary.
2. Show RecallRadar.
3. Show DrugSignal.
4. Show Audit History.
5. Show Data Sources/System Status.
6. Show Saved Monitors.
7. Show Regional Health Pulse as scaffold only.
8. Show offline ML experiments.
9. End with roadmap and what you intentionally did not productionize.

This order tells a clean story:

> Public data → review workflow → traceability → monitoring → responsible ML roadmap.

## 14. Next Engineering Milestone

The next responsible technical milestone is:

> Source freshness risk scoring and payload-change intelligence.

This should come before deep learning, RAG, or production ML.

Why:

- the project already has source/audit foundations
- saved monitors need stronger change intelligence
- payload hashes can become meaningful change indicators
- source freshness matters for trust
- this improves the core product without unsafe AI overclaiming
- it creates better real-world data for later ML

Recommended next technical sequence:

1. Source freshness risk scoring
2. Payload-change intelligence
3. Real public-data dataset export from audit and monitor history
4. Reviewed-label fixtures
5. Evaluation dashboard
6. Feature-flagged internal ML preview
7. Semantic search or RAG only after stronger grounding
8. Deep learning only if data volume and use case justify it

## 15. Closing Statement

A strong closing line for interviews:

> Dav AI is my attempt to build an AI-ready healthcare safety intelligence platform the responsible way. I focused first on public-data workflows, source provenance, auditability, deterministic scoring, saved monitoring, and offline ML experiments before exposing any AI predictions to users. The goal is not to replace clinical judgment. The goal is to make public safety data easier to review, explain, and govern.

Another shorter version:

> The most important engineering decision in Dav AI was not adding ML everywhere. It was building the trust layer first: source traceability, audit history, deterministic baselines, safety boundaries, and offline ML governance.