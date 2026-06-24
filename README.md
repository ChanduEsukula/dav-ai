# Dav AI

**Dav AI is a full-stack public safety intelligence platform that helps users search fragmented U.S. public recall, enforcement, label, reference, vehicle, device, food, drug, cosmetic, and consumer-product records while preserving source provenance and avoiding unsupported safety claims.**

Dav AI is a portfolio-grade engineering project built with **React, TypeScript, FastAPI, PostgreSQL, Alembic, and public-data source adapters**. The strongest workflow is now **Public Safety Search**, which checks selected official/public sources, explains query interpretation, separates recalls from reference records, and links users back to official sources.

Dav AI does **not** determine whether a product is safe or unsafe. A no-result search is not a safety guarantee. The app is not medical advice, legal advice, clinical decision support, causation analysis, or a replacement for official recall instructions.

## Flagship Workflow: Public Safety Search

Public Safety Search is the main demo path.

It supports searches such as:

~~~text
tylonal              -> typo correction + Tylenol / acetaminophen context
Advil                -> brand-to-generic expansion and NDC/label reference records
air fryer            -> consumer product recall records
NDC 66715 6547       -> identifier-oriented drug reference search
blood sugar monitor  -> device/product wording normalization
2020 Toyota Camry    -> vehicle recall-style query path
~~~

The workflow shows:

- a plain-language search outcome
- whether recall/enforcement records were found
- whether official reference or label records were found
- whether signal reports were found
- query understanding and expansion terms
- source roles such as recall, reference, label, and signal
- official record links
- source failures or timeouts when they happen
- limitations and public-data caveats

Reference and label records are clearly marked as **not recalls**. Adverse-event signal records are not treated as proof of causation.

## Why This Is a Real-World Problem

Public safety information is spread across many agencies and databases. Different sources use different schemas, update schedules, identifiers, and meanings. Dav AI focuses on making those records easier to search, compare, and verify without pretending that partial public data can certify safety.

The project emphasizes:

- official/public source usage
- deterministic query handling instead of uncontrolled fuzzy matching
- source-aware result roles
- provenance and audit metadata
- fail-soft behavior when sources are unavailable
- conservative safety language
- repeatable tests and migration checks

## At a Glance

| Area | Current implementation |
|---|---|
| Frontend | React, TypeScript, Vite, Testing Library, Playwright smoke coverage |
| Backend | FastAPI, Pydantic, httpx, Uvicorn |
| Persistence | PostgreSQL/Supabase-oriented repositories, psycopg, Alembic migrations |
| Public sources | CPSC, FDA/openFDA, USDA FSIS, NHTSA, RxNorm/RxNav, DailyMed |
| Core workflow | Public Safety Search with query understanding, source roles, provenance, and official-source links |
| Supporting workflows | Pharmacy Safety, Food Safety, Cosmetic Safety, Audit, Sources, System Status, Saved Monitors |
| Testing | pytest, Vitest, ESLint, TypeScript build, Playwright smoke tests |
| Boundaries | Public records only; selected sources; no safety guarantee; not medical/legal advice |

## Phase 2 Source Expansion Status

Phase 2 is a validated prototype checkpoint, not a production deployment. The source registry and database schema now explicitly describe each source's integration mode and update cadence.

| Integration mode | Current implementation |
|---|---|
| **Live public API** (`live_public_api`) | NHTSA vPIC VIN decoding followed by NHTSA vehicle recall lookup using decoded or user-supplied make, model, and model year |
| **Curated official-source snapshot** (`curated_official_snapshot`) | USDA FSIS meat, poultry, and egg-product recalls/public health alerts, plus CPSC consumer-product recalls, loaded from curated local snapshots derived from official records |
| **Public page ingestion** (`live_public_page`) | FDA recall, market-withdrawal, and safety-alert notices fetched from public FDA pages rather than a structured API |
| **Prototype scaffold** (`prototype_scaffold`) | Regional Health Pulse architecture/demo path; no live CDC/HHS surveillance feed is connected |

USDA FSIS and CPSC are **not real-time integrations** in the current prototype. The next engineering step is to add automated FSIS/CPSC refresh jobs or implement a live ingestion mode with appropriate reliability, audit, and rate-limit handling.

## Current Demo Flow

Recommended recruiter/interviewer walkthrough:

~~~text
Home
  -> Public Safety Search
  -> Search: air fryer
  -> Show recall/enforcement result and official source link
  -> Search: Advil or tylonal
  -> Explain query understanding and reference-vs-recall distinction
  -> Open Audit / Sources briefly to show provenance and source registry
~~~

Secondary workflows:

~~~text
Pharmacy Safety
Food Safety
Cosmetic Safety
Saved Monitors
Audit History
Sources / System Status
~~~

For a short demo, lead with **Public Safety Search**. Use the other pages only to show breadth and reuse.

## Strongest Engineering Points

- Adapter-based normalization across heterogeneous official/public sources
- Deterministic query understanding with typo correction, joined-term cleanup, VIN/NDC/UPC detection, and brand/generic expansion
- Source-role classification that separates recall/enforcement records from reference, label, and signal records
- Fail-soft orchestration with source timeouts, partial results, and source issue reporting
- Audit and provenance model with source IDs, endpoints, queries, retrieval timestamps, transform versions, and payload hashes
- PostgreSQL source registry with Alembic seed alignment tests
- Typed FastAPI response contracts and typed React API clients
- Outcome-first UI with progressive disclosure for technical details
- Clear zero-result and no-safety-guarantee language
- Broad automated test coverage across backend, frontend, and smoke paths

## Validation

Current Phase 2 source-expansion checkpoint, validated June 24, 2026:

- **Backend pytest:** 409 passed
- **Frontend tests:** 243 passed
- **TypeScript/Vite build:** passed
- **`git diff --check`:** passed

Current tag:

- `phase2-source-metadata-alignment-v1`

## Portfolio Documentation

- [RealWorldSafety Query Understanding](docs/REAL_WORLD_SAFETY_QUERY_UNDERSTANDING.md)
- [Real-World Safety Sources](docs/real_world_safety_sources.md)
- [U.S. Real-World Safety Source Audit](docs/USA_REAL_WORLD_SAFETY_SOURCES.md)
- [Portfolio Demo Package](docs/demo/PORTFOLIO_DEMO_PACKAGE.md)
- [Architecture Overview](docs/architecture/ARCHITECTURE_OVERVIEW.md)
- [Operations Runbook](docs/operations_runbook.md)

## Honest Data Limitations

Dav AI uses selected public sources and curated official snapshots for some workflows so tests and demos remain deterministic. Coverage is not exhaustive. Source data may be incomplete, delayed, duplicated, temporarily unavailable, or hard to match without exact identifiers.

Dav AI does not currently provide complete lot, UPC, NDC package, VIN, UDI, or product-serial certainty for every query. Users must open official records and compare exact product details before acting.

## Product Boundaries

Dav AI is a portfolio-grade public-record verification workspace. It is not production-ready healthcare AI.

Dav AI does not:

- provide medical advice, diagnosis, or treatment guidance
- recommend starting, stopping, or changing medication
- determine whether a product is safe or unsafe
- prove that a drug or cosmetic caused a reported event
- calculate clinical incidence or patient-specific risk
- guarantee that an empty search means no safety issue exists
- provide complete or guaranteed UPC, NDC, or lot-level matching
- use production ML, RAG, an LLM, or OCR to make routed product-safety decisions
- provide production alert delivery or an enabled production scheduler
- include authentication, user ownership, RBAC, or tenant isolation
- store PHI, private patient records, insurance data, or prescription history

FAERS and cosmetic-event reports may be incomplete, duplicated, delayed, influenced by reporting behavior, or missing clinical context. Users must verify relevant records against official public sources before acting.

## Canonical Workflows

### Pharmacy Safety

Pharmacy Safety combines two related but distinct public-record views:

- openFDA Drug Enforcement recall records
- openFDA Drug Event / FAERS-style reporting patterns

The workspace keeps recall records separate from adverse-event summaries. Review scores are deterministic review-priority signals, not medical-risk scores. FAERS counts do not establish incidence or causation.

### Food Safety

Food Safety reviews supported public food and supplement records from:

- openFDA Food Enforcement
- a curated USDA FSIS official-source snapshot covering meat, poultry, and egg-product recalls/public health alerts

Users must compare the exact brand, product, package, lot/code, establishment number, date, and official recall notice. A possible text match does not prove that a user’s package is affected.

### Cosmetic Safety

Cosmetic Safety reviews public cosmetic-event reports, top reported reactions, outcomes, and product context.

Returned reports are public reporting signals only. They do not prove product defect or causation. Searches with no returned reports remain unscored or not assessable rather than being presented as evidence of safety.

## Supporting Product Surfaces

### Guided Search

The homepage search classifies a confirmed query into the most relevant canonical workflow. It uses controlled aliases and explicit workflow suggestions, not fuzzy-search or ML libraries.

### Audit and Provenance

Search workflows can preserve:

- workflow/module name
- original and normalized query
- source ID, name, and endpoint
- retrieval timestamp and upstream status
- record count
- transform and score versions
- request metadata
- source-pull metadata
- raw public-source snapshot reference
- stable payload hash

Audit History provides filtering, detail review, copy actions, CSV export, URL state, and source-pull context when available.

### Saved Monitors

Saved Monitors provide repeatable public-record checks with:

- persisted monitor definitions
- manual run checks
- run history
- latest and previous record counts
- latest and previous score metadata
- change indicators
- audit links
- duplicate prevention
- scheduler locking and a future scheduled-refresh foundation

Production Cron and alert delivery are not enabled. Cosmetic monitor creation remains unavailable until persistence and manual-run parity are complete.

### Sources and System Status

The Sources and System pages expose registered public sources, source freshness, backend health, audit persistence visibility, and data-quality context.

Regional Health Pulse remains a clearly labeled scaffold extension. It is not live CDC/HHS surveillance, outbreak detection, emergency guidance, or a primary demo workflow.

### PDF Reports

Dav AI can generate bounded PDF reports for supported public-record workflows. Reports include source context and limitations but are not clinical records, regulatory documents, official recall instructions, or safety certificates.

### Offline ML Experiments

Experimental ML baselines under `backend/ml_experiments` remain offline and are not imported into production FastAPI routes, frontend behavior, Saved Monitors, alerts, or scheduling.

They demonstrate evaluation and responsible-ML preparation only. Dav AI does not have a production ML pipeline.

## Architecture

```text
React + TypeScript frontend
  -> FastAPI workflow routes
  -> bounded normalization and deterministic transforms
  -> live APIs, public-page ingestion, curated official-source snapshots, and prototype scaffolds
  -> typed responses and PDF reports
  -> audit events, source pulls, payload hashes, monitor history
  -> PostgreSQL / Supabase persistence
```

Internal names such as RecallRadar, DrugSignal, FoodRadar, and CosmeticSignal remain in API modules, audits, reports, and historical documentation. The recruiter-facing application uses the consolidated Pharmacy Safety, Food Safety, and Cosmetic Safety pages.

## Repository Structure

```text
backend/
  app/
    routes/                 FastAPI routes
    services/               source clients and workflow services
    services/search_workflows/
    schemas/                Pydantic response contracts
    scoring/                deterministic review scoring
    db/                     audit, provenance, and monitor repositories
  migrations/               Alembic migrations
  ml_experiments/           offline-only experimental baselines
  tests/                    backend test suite

frontend/
  src/
    components/             routed pages and shared UI
    api/                    typed API clients
    utils/                  normalization and presentation helpers
    styles/                 page and component styles
  e2e/                      Playwright smoke tests

docs/
  architecture/
  demo/
  productscan/
```

## Public Data Sources

| Source | Use |
|---|---|
| openFDA Drug Enforcement API | Drug recall records |
| openFDA Drug Event API | FAERS-style adverse-event reporting patterns |
| openFDA Food Enforcement API | FDA-regulated food and supplement enforcement records |
| USDA FSIS curated official-source snapshot | Meat, poultry, and egg-product recall/public-health-alert coverage; no automated live refresh |
| CPSC curated official-source snapshot | Consumer-product recall coverage; no automated live refresh |
| NHTSA vPIC and Recalls APIs | Live VIN decoding and vehicle recall lookup by make/model/year |
| FDA public recall pages | Live public-page ingestion for recalls, market withdrawals, and safety alerts |
| openFDA Cosmetic Event API | Public cosmetic-event reports |
| Regional Health Pulse scaffold | Architecture/demo extension only |

Source availability and public-data quality can change. Dav AI surfaces source and retrieval context but does not control source completeness or timeliness.

## Backend API

Core search routes:

```text
GET /api/v1/recalls/search
GET /api/v1/drug-events/search
GET /api/v1/everyday-safety/search
GET /api/v1/cosmetic-events/search
```

Audit, source, monitor, and report routes:

```text
GET    /api/v1/sources
GET    /api/v1/audit-events
GET    /api/v1/audit-events/{audit_id}
GET    /api/v1/audit-events/{audit_id}/source-pull
GET    /api/v1/saved-monitors
POST   /api/v1/saved-monitors
GET    /api/v1/saved-monitors/{monitor_id}/runs
GET    /api/v1/saved-monitors/{monitor_id}/insights
POST   /api/v1/saved-monitors/{monitor_id}/run
DELETE /api/v1/saved-monitors/{monitor_id}
POST   /api/v1/reports/safety-intelligence
```

Operational routes:

```text
GET /health
GET /api/v1/system/status
GET /api/v1/system/data-quality
```

FastAPI documentation is available locally at `http://127.0.0.1:8000/docs`.

## Local Development

### Backend

Create and activate a virtual environment, then install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

Start the API:

```bash
cd backend
uvicorn app.main:app --reload
```

The backend runs at `http://127.0.0.1:8000`.

Backend environment configuration:

```env
DATABASE_URL=postgresql+psycopg://username:password@host:5432/database
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Database persistence is fail-soft in several MVP paths, but PostgreSQL is required to demonstrate durable audit, provenance, and Saved Monitor behavior.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:5173`.

Frontend API configuration:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Use local `.env` files for development. Do not commit credentials or real environment files.

## Docker

From the repository root:

```bash
docker compose up --build
```

Local services:

```text
Frontend: http://localhost:5173
Backend:  http://localhost:8000
API docs: http://localhost:8000/docs
```

Stop the containers:

```bash
docker compose down
```

## Testing

Backend:

```bash
cd backend
../.venv/bin/python -m pytest
```

Frontend unit/component tests:

```bash
cd frontend
npm test
```

Lint and production build:

```bash
cd frontend
npm run lint
npm run build
```

Playwright smoke test:

```bash
cd frontend
npm run test:e2e
```

Repository diff validation:

```bash
git diff --check
```

GitHub Actions runs the backend suite, frontend suite, lint, production build, and Playwright smoke coverage.

## Scheduled Monitor CLI

The backend includes a manual/dry-run scheduled-refresh foundation:

```bash
cd backend
python -m app.jobs.run_due_saved_monitors --limit 10
```

The job uses database-backed scheduler locks when configured. This is not an enabled production scheduler or alert-delivery system.

## Deployment Notes

The documented portfolio deployment shape is:

```text
Frontend: Vercel
Backend:  Render or Railway
Database: Supabase PostgreSQL
```

Required deployment configuration includes trusted CORS origins, backend/frontend API URLs, database credentials, schema migrations, and secret management.

Before representing a deployment as current, verify:

- `/health` and FastAPI docs
- all three canonical workflows
- Audit History and Sources/System pages
- persistent audit and monitor records
- PDF generation
- CORS restrictions
- absence of committed credentials

Production Cron, alert delivery, authentication, user ownership, retention controls, production observability, and independent safety review remain incomplete.

See [Deployment Verification](docs/deployment_verification.md), [Deployment Checklist](docs/deployment_checklist.md), and [Backend Deployment Setup](docs/backend_deployment_setup.md).

## Current Limitations

- Portfolio-grade prototype, not production-ready for uncontrolled public use
- No authentication, authorization, user ownership, or tenant isolation
- No production alert delivery or enabled production scheduler
- ProductScan browser-side OCR is experimental, user-reviewed, and not production-ready; no backend OCR, provider OCR, or Dav AI image storage is implemented
- No production ML, RAG, LLM, embedding, or vector-search pipeline
- No complete identifier-resolution system for UPC, NDC, lot, or package matching
- No guarantee that public-source data is complete, current, unique, or correctly linked to a user’s product
- No product-safety guarantee from either a match or a zero-result response
- No medical advice, diagnosis, treatment recommendation, or clinical decision support
- Additional hardening is required for rate limits, abuse prevention, caching, observability, retention, deletion, and incident response

## Project Direction

Dav AI’s engineering direction is:

```text
Search -> Normalize -> Review -> Audit -> Report -> Monitor -> Compare
```

The project deliberately prioritizes explainability, provenance, and bounded product behavior over unsupported AI claims.
