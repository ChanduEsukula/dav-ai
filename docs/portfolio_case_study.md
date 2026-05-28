# Dav AI Portfolio Case Study

## 1. Project Overview

Dav AI is a public-data healthcare safety intelligence platform that helps users search, review, audit, monitor, and explain FDA/openFDA-style safety signals.

The project is designed as a source-aware review workspace, not a medical chatbot or clinical decision-support tool. Its core value is turning public safety data into a traceable workflow with normalized results, deterministic scoring, audit history, saved monitors, and responsible ML readiness.

## 2. My Role

I worked on Dav AI as a full-stack engineer, AI/ML engineer, responsible AI designer, and product builder.

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

Dav AI addresses this problem by creating a structured public-data safety review workflow.

The workflow is:

Search public data → normalize results → score review priority → preserve audit trail → generate bounded briefing → save monitor → compare future changes → prepare for responsible ML.

## 4. Product Boundary

Dav AI is not a medical advice tool.

It does not provide:

- diagnosis
- treatment recommendations
- medication-change guidance
- clinical decision support
- patient-specific risk prediction
- causation claims
- outbreak prediction

Dav AI uses public data only.

It does not use:

- PHI
- private patient records
- diagnosis history
- prescription history
- insurance data
- personal medical narratives
- addresses

The correct framing is:

> Dav AI supports public-data review. It does not make clinical decisions.

## 5. What I Built

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

Saved Monitors allow repeatable public-data searches.

Key capabilities:

- create saved public-data searches
- prevent duplicates
- manually run monitors
- compare latest and previous results
- store run history
- link runs to audit history
- generate deterministic monitor insights

Saved Monitors are a foundation for longitudinal public-data review. They are not yet a full production alerting system.

### Regional Health Pulse

Regional Health Pulse is an architecture scaffold for future public-health-style signal workflows.

It demonstrates how the same product pattern could extend to public-health datasets later.

Current boundary:

- scaffold/sample-data behavior only
- not live CDC/HHS surveillance
- not outbreak detection
- not emergency guidance

### Offline Responsible ML Experiments

Dav AI includes offline responsible ML experiments under `backend/ml_experiments`.

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
- Axios API clients
- component-based product pages
- custom CSS
- Vitest
- React Testing Library

Important frontend areas include:

- RecallRadar
- DrugSignal
- Audit History
- Data Sources
- System Status
- Saved Monitors
- Regional Health Pulse
- deterministic Safety Briefing panels

### Backend

The backend is built with:

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

A typical Dav AI workflow looks like this:

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

This makes the project more than a simple frontend calling an API. It has a review workflow, source registry, audit trail, scoring layer, persistence boundary, monitor loop, and responsible ML roadmap.

## 8. Responsible AI Decisions

The strongest responsible AI decision in Dav AI was keeping ML offline until the system has stronger data and governance.

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

This is especially important because Dav AI is healthcare-adjacent, even though it uses public data only.

## 9. Engineering Strengths

Dav AI demonstrates several strong engineering practices:

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

Current verification from the responsible ML progress review:

- Backend tests: 182 passed
- Frontend tests: 64 passed
- Frontend lint: passed
- Repository state: clean before and after inspection
- CI workflow includes backend tests, frontend tests, lint, build, and smoke-test coverage

Important note:

> This verification proves engineering quality and test coverage. It does not prove clinical validity or production ML readiness.

## 11. What Is Implemented

Implemented:

- RecallRadar
- DrugSignal
- Audit History
- Data Sources
- System Status
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

## 12. What Is Not Production-Grade Yet

Not production-grade yet:

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

- keep RecallRadar, DrugSignal, Audit History, and Saved Monitors as the core product loop
- describe Regional Health Pulse as scaffold only
- keep advanced AI on the roadmap

## 14. Interview Value

### For AI Engineer Roles

Dav AI shows that I can design AI-ready workflows without rushing unsafe AI into production.

Key points:

- deterministic safety briefings
- future RAG roadmap
- source grounding
- responsible AI boundaries
- auditability before generation

### For ML Engineer Roles

Dav AI shows that I understand ML system readiness beyond model training.

Key points:

- offline baselines
- weak-label disclosure
- feature engineering
- metrics
- safety disclaimers
- reviewed-label roadmap
- production ML restraint

### For Backend Engineer Roles

Dav AI shows backend architecture maturity.

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

Dav AI shows end-to-end product engineering.

Key points:

- React + TypeScript frontend
- FastAPI backend
- typed API boundaries
- source-aware UI
- audit metadata display
- saved-monitor workflows
- frontend and backend tests

### For Responsible AI / Health-Tech Roles

Dav AI shows that I can build healthcare-adjacent software with safety boundaries.

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

> Source freshness risk scoring and payload-change intelligence.

This should come before deep learning, RAG, or production ML.

Recommended sequence:

1. Source freshness risk scoring
2. Payload-change intelligence
3. Real public-data dataset export from audit and monitor history
4. Reviewed-label fixtures
5. Evaluation dashboard
6. Feature-flagged internal ML preview
7. Semantic search or RAG after stronger grounding
8. Deep learning only if data volume and use case justify it

## 16. Final Summary

Dav AI is a portfolio-grade public-data safety intelligence platform with strong responsible AI foundations.

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

Dav AI is AI-ready, but it is not pretending to be production clinical AI. That honesty makes the project stronger for professors, senior engineers, and hiring managers.