# DAV AI Portfolio Case Study

## 1. Project Overview

DAV AI is a public-data healthcare and everyday safety intelligence platform that helps users search, review, audit, monitor, and explain openFDA, USDA FSIS, and scaffolded public-health safety signals.

The project is designed as a source-aware review workspace, not a medical chatbot or clinical decision-support tool. Its core value is turning public safety data into a traceable workflow with normalized results, deterministic scoring, audit history, saved monitors, and responsible ML readiness.

The current portfolio MVP story is intentionally focused:

```text
RecallRadar → DrugSignal → FoodRadar
```

CosmeticSignal, Regional Health Pulse, Saved Monitors, Data Sources, System Status, Audit History, Source Registry, source freshness, and provenance surfaces support the platform story, but they are secondary to the main demo path.

Final supporting docs:

- `docs/final_portfolio_mvp_checkpoint.md`
- `docs/final_portfolio_architecture.md`

## 2. My Role

I worked on DAV AI as a full-stack engineer, AI/ML engineer, responsible AI designer, and product builder.

My responsibilities included:

- designing the public-data review workflow
- building frontend product surfaces
- implementing backend APIs and service workflows
- adding deterministic scoring and safety briefings
- supporting auditability and source provenance
- creating saved-monitor workflows
- preparing offline responsible ML experiments
- documenting implementation status, safety boundaries, and future roadmap

## 3. Problem

Public healthcare safety data is available, but it is difficult to use effectively.

Users need a way to:

- search public safety records
- understand source context
- compare results over time
- preserve audit history
- avoid overclaiming adverse-event data
- separate public-data review from medical advice
- prepare for AI/ML safely

DAV AI addresses this problem by creating a structured public-data safety review workflow.

The workflow is:

Search public data → normalize results → score review priority → preserve audit trail → generate bounded briefing → save monitor → compare future changes → prepare for responsible ML.

## 4. Product Boundary

DAV AI is not a medical advice tool.

It does not provide:

- diagnosis
- treatment guidance
- medication-change guidance
- clinical decision support
- official product-safety verdicts
- patient-specific risk prediction
- causation claims
- outbreak prediction
- medical device functionality
- replacement guidance for FDA, USDA, CDC, clinicians, pharmacists, emergency services, or official source guidance

DAV AI uses public data only in the current MVP.

It does not use:

- PHI
- private patient records
- diagnosis history
- prescription history
- insurance data
- personal medical narratives
- addresses

The correct framing is:

> DAV AI supports public-data review. It does not make clinical decisions.

## 5. What I Built

The primary MVP modules are RecallRadar, DrugSignal, and FoodRadar. They are the first demo path because they show the same source-aware pattern across public recalls, public adverse-event reporting patterns, and everyday food/supplement safety.

### RecallRadar

RecallRadar allows users to search public recall data and review normalized recall records.

Key capabilities:

- public recall search
- normalized recall cards
- rule-based Recall Review Score
- source and audit metadata
- safety limitation language

The Recall Review Score is designed as a review-priority signal, not a product safety verdict.

### DrugSignal

DrugSignal supports review of openFDA Drug Event / FAERS-style reporting data.

Key capabilities:

- drug-event search
- top reaction summaries
- reporting-pattern review
- safety disclaimers
- deterministic briefing support

DrugSignal explicitly avoids saying that a drug caused a reaction. FAERS-style data is treated as reporting-pattern data only.

### FoodRadar

FoodRadar extends the source-aware workflow into everyday food and supplement safety.

Key capabilities:

- openFDA Food Enforcement search
- USDA FSIS Recall API coverage for meat, poultry, and egg-product recalls/public-health alerts
- source-checked result cards
- deterministic review-priority scoring
- highest-score and latest-recall sorting
- audit/source metadata
- official-source verification language

FoodRadar explicitly states that a missing result does not prove that a product is safe or unsafe. It also supports fail-soft multi-source behavior, so available source results can still render with source status when one upstream source errors.

### Supporting Surfaces

The following surfaces are implemented or scaffolded as secondary/supporting parts of the platform. They strengthen trust, traceability, and product depth, but they should not replace the RecallRadar → DrugSignal → FoodRadar portfolio story.

### CosmeticSignal

CosmeticSignal supports public cosmetic adverse-event report review.

Key capabilities:

- openFDA Cosmetic Event search
- query expansion for common cosmetic/product/reaction terms
- cosmetic reporting signal score
- top reported cosmetic reactions
- normalized cosmetic-event records
- audit/source metadata
- cosmetic adverse-event limitations

CosmeticSignal explicitly avoids causation claims. Cosmetic adverse-event reports may be incomplete, duplicated, delayed, influenced by reporting behavior, or missing context.

### Audit History

Audit History gives the system traceability.

Audit metadata includes:

- module
- source
- endpoint
- query
- query parameters
- retrieval timestamp
- record count
- transform version
- score version
- disclaimer version
- upstream status
- error information where applicable

This is one of the strongest engineering parts of the project because every intelligence output should be traceable.

### Data Sources and System Status

The Data Sources and System Status pages help users understand source availability and system behavior.

Key capabilities:

- source registry
- source transparency
- audit-backed freshness visibility
- operational status checks
- public-data limitation framing

### Saved Monitors

Saved Monitors allow repeatable public-data searches, including manual FoodRadar monitor create/run/history support and scheduled FoodRadar refresh backend foundation.

Key capabilities:

- create saved public-data searches
- prevent duplicates
- manually run monitors, including FoodRadar food/supplement recall monitors
- compare latest and previous results
- store run history
- link runs to audit history
- generate deterministic monitor insights

Saved Monitors are a foundation for longitudinal public-data review. FoodRadar now supports manual saved-monitor runs, latest score/count/audit tracking, run history, and scheduled-refresh backend execution. Saved Monitors are not yet a full production alerting system, and production Cron/alerts remain future work.

### Regional Health Pulse

Regional Health Pulse is an architecture scaffold for future public-health-style signal workflows.

It demonstrates how the same product pattern could extend to public-health datasets later.

Current boundary:

- scaffold/sample-data behavior only
- not live CDC/HHS surveillance
- not outbreak detection
- not emergency guidance

### Offline Responsible ML Experiments

DAV AI includes offline responsible ML experiments under `backend/ml_experiments`.

Current experiments:

- Public Safety Signal Review Priority Classifier v0.1
- Saved Monitor Anomaly & Trend Classifier v0.2
- Recall Reason NLP Classifier v0.3
- DrugSignal Reaction Theme Classifier v0.4

These experiments are intentionally offline only.

They are not connected to:

- FastAPI production routes
- frontend pages
- saved-monitor automation
- alerts
- user-facing recommendations
- clinical workflows

The ML experiments are used to test ML problem framing, weak-label datasets, feature engineering, labels, metrics, and safety disclaimers before any production ML integration.

## 6. Technical Architecture

### Frontend

The frontend is built with:

- React
- TypeScript
- Vite
- Vercel deployment at `https://dav-ai.vercel.app`
- Axios API clients
- component-based product pages
- custom CSS
- Vitest
- React Testing Library

Primary frontend areas include:

- RecallRadar
- DrugSignal
- FoodRadar

Supporting frontend areas include:

- CosmeticSignal
- Audit History
- Data Sources
- System Status
- Saved Monitors
- Regional Health Pulse
- deterministic Safety Briefing panels

### Backend

The backend is built with:

- FastAPI
- Render deployment at `https://medtrek-ai.onrender.com`
- Pydantic schemas
- route/service/scoring/repository separation
- openFDA clients
- deterministic scoring modules
- audit repository
- source registry
- saved-monitor workflows
- scheduled-refresh foundation
- PostgreSQL/Supabase-ready persistence
- Supabase/PostgreSQL audit, source, and saved-monitor persistence
- Alembic migrations
- pytest

### AI/ML Layer

The AI/ML layer is currently offline.

It includes:

- synthetic weak-label datasets
- explainable baseline classifiers
- text classification experiments
- metrics hooks
- explicit safety disclaimers
- no production inference

## 7. End-to-End Data Flow

A typical DAV AI workflow looks like this:

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
11. Future monitor runs compare latest vs. previous public-data activity.
12. Offline ML experiments prepare future review-priority and trend intelligence without changing production behavior.

FoodRadar adds a useful distributed-systems wrinkle: it combines openFDA Food Enforcement and USDA FSIS Recall API coverage, and it can display partial source success/failure instead of treating every upstream issue as a total product failure.

This makes the project more than a simple frontend calling an API. It has a review workflow, source registry, audit trail, scoring layer, persistence boundary, monitor loop, fail-soft source behavior, and responsible ML roadmap.

## 8. Responsible AI Decisions

The strongest responsible AI decision in DAV AI was keeping ML offline until the system has stronger data and governance.

Before production ML, the project needs:

- real public-data history
- reviewed labels
- evaluation metrics by class
- false-positive review
- false-negative review
- feature/version lineage
- model/version lineage
- UI limitation language
- rollback controls
- feature flags
- deployment monitoring

This is especially important because DAV AI is healthcare-adjacent, even though it uses public data only.

## 9. Engineering Strengths

DAV AI demonstrates several strong engineering practices:

- source-aware architecture
- audit trail design
- deterministic scoring before ML
- explicit safety boundaries
- route/service/repository separation
- typed frontend API clients
- saved-monitor workflow design
- source registry
- request/audit metadata
- backend and frontend tests
- CI workflow
- documentation discipline
- honest roadmap separation
- offline ML governance

The strongest engineering theme is:

> Build the trust layer before production AI.

## 10. Current Verification Snapshot

Latest confirmed verification evidence:

- Backend tests: 263 passed
- Frontend tests: 70 passed
- Frontend lint: passed
- Frontend production build: passed
- Backend deployment URL: `https://medtrek-ai.onrender.com`
- Frontend deployment URL: `https://dav-ai.vercel.app`
- Latest verified commit when the final checkpoint was written: `45be0be` Document deployed frontend FoodRadar smoke verification
- Current final docs commits also exist:
  - `ffb8d8e` Add final portfolio MVP checkpoint
  - `b02027e` Add final portfolio architecture document
- Final checkpoint doc: `docs/final_portfolio_mvp_checkpoint.md`
- Final architecture doc: `docs/final_portfolio_architecture.md`
- CI workflow includes backend tests, frontend tests, lint, build, and smoke-test coverage
- Live smoke tests confirmed `semantic_preview` appears in both `/api/v1/recalls/search` and `/api/v1/drug-events/search`.

Deployed backend smoke verified:

- `/api/v1/system/status` returned 200.
- API status was ok.
- Database was configured.
- Audit history was readable.
- Source registry returned 7 sources.
- FoodRadar API search for `chicken` returned 200 with audit metadata.
- FoodRadar fail-soft behavior was confirmed: openFDA Food Enforcement succeeded while USDA FSIS was marked error.

Deployed frontend smoke verified:

- Sources page loaded and showed 7 sources.
- System page loaded API ok, database configured, audit readable, and 7 sources.
- FoodRadar search for `chicken` rendered 1 matching public food/supplement recall record.
- FoodRadar displayed openFDA Food Enforcement success with 23 source records.
- FoodRadar displayed USDA FSIS error with 0 records.
- FoodRadar result card rendered review score 32 / Moderate.

Important note:

> This verification proves engineering quality and test coverage. It does not prove clinical validity or production ML readiness.

## 11. What Is Implemented

Primary MVP modules:

- RecallRadar
- DrugSignal
- FoodRadar

Secondary/supporting surfaces:

- CosmeticSignal
- Audit History
- Data Sources
- System Status
- Saved Monitors foundation, including manual FoodRadar monitor support
- Regional Health Pulse scaffold
- deterministic safety briefings
- source registry
- audit/source transparency
- source freshness surfaces
- source-pull metadata foundation
- provenance and payload-hash surfaces
- rule-based review scoring
- offline Responsible ML experiments
- backend tests
- frontend tests
- frontend linting
- CI workflow

## 12. What Is Not Production-Grade Yet

Not production-grade yet:

- production ML
- reviewed-label datasets
- clinical validation
- live CDC/HHS surveillance
- production alert delivery
- notification preferences
- auth/RBAC
- ProductScan
- OCR/CNN label scanning
- production Cron activation; scheduled FoodRadar refresh exists as backend foundation but is not production Cron-enabled
- full deployment observability dashboard
- model registry
- semantic search
- source-grounded RAG assistant
- deep learning models
- patient-specific workflows

## 13. Challenges and Tradeoffs

### Challenge 1: Avoiding Healthcare Overclaims

Because the project is healthcare-adjacent, it would be unsafe to overstate what public data can prove.

Decision:

- use safety disclaimers
- avoid causation claims
- avoid diagnosis/treatment language
- frame outputs as review support only

### Challenge 2: Adding ML Responsibly

It would be easy to connect ML predictions directly to the app, but that would be premature.

Decision:

- keep ML offline
- use synthetic weak-label datasets only for engineering shape
- require reviewed labels and evaluation before production ML

### Challenge 3: Balancing Product Scope

The project includes several modules, so scope control matters.

Decision:

- keep RecallRadar, DrugSignal, and FoodRadar as the primary MVP product loop
- describe CosmeticSignal as a secondary extension surface
- describe Regional Health Pulse as scaffold only
- keep advanced AI on the roadmap

## 14. Interview Value

### For AI Engineer Roles

DAV AI shows that I can design AI-ready workflows without rushing unsafe AI into production.

Key points:

- deterministic safety briefings
- future RAG roadmap
- source grounding
- responsible AI boundaries
- auditability before generation

### For ML Engineer Roles

DAV AI shows that I understand ML system readiness beyond model training.

Key points:

- offline baselines
- weak-label disclosure
- feature engineering
- metrics
- safety disclaimers
- reviewed-label roadmap
- production ML restraint

### For Backend Engineer Roles

DAV AI shows backend architecture maturity.

Key points:

- FastAPI
- service-layer workflows
- source clients
- repositories
- audit events
- request IDs
- scheduler locks
- persistence fallback
- pytest coverage

### For Full-Stack Engineer Roles

DAV AI shows end-to-end product engineering.

Key points:

- React + TypeScript frontend
- FastAPI backend
- typed API boundaries
- source-aware UI
- audit metadata display
- saved-monitor workflows
- frontend and backend tests

### For Responsible AI / Health-Tech Roles

DAV AI shows that I can build healthcare-adjacent software with safety boundaries.

Key points:

- public data only
- no PHI
- no clinical claims
- FAERS limitations
- auditability
- explainability
- offline ML governance

## 15. What I Would Improve Next

The next responsible engineering milestone is:

> Source reliability hardening, deployed smoke maintenance, and careful portfolio polish around the verified RecallRadar → DrugSignal → FoodRadar story.

This should come before deep learning, RAG, or production ML.

Recommended sequence:

1. Keep deployed smoke verification current for RecallRadar, DrugSignal, FoodRadar, Sources, System Status, and Audit History.
2. Harden source reliability and source-status language for openFDA and USDA FSIS.
3. Continue polishing source freshness, payload-change, and provenance surfaces as supporting trust features.
4. Export real public-data history from audit and monitor runs.
5. Add reviewed-label fixtures and evaluation dashboards.
6. Introduce feature-flagged internal ML previews only after evaluation and rollback controls exist.
7. Add semantic search or RAG only after stronger grounding.
8. Add deep learning only if data volume and use case justify it.

## 16. Final Summary

DAV AI is a portfolio-grade public-data safety intelligence platform with strong responsible AI foundations.

The project demonstrates:

- full-stack engineering
- public API integration
- auditability
- source provenance
- deterministic scoring
- saved-monitor workflows
- responsible AI boundaries
- offline ML experimentation
- test discipline
- documentation maturity

The most important engineering decision was not adding ML everywhere.

The strongest decision was building the trust layer first:

> source traceability, audit history, deterministic baselines, safety boundaries, and offline ML governance.

DAV AI is AI-ready, but it is not pretending to be production clinical AI. That honesty makes the project stronger for professors, senior engineers, and hiring managers.
