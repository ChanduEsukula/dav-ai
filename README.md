# Dav AI

**Dav AI is a React, TypeScript, FastAPI, and PostgreSQL public-data safety review workspace that helps users search FDA/USDA records, normalize common queries, review source evidence, and preserve provenance through audit metadata.**

Dav AI is a full-stack portfolio project focused on trustworthy public-record verification. The current demo is organized around three canonical workflows:

- **Pharmacy Safety**: drug recall records and public adverse-event reporting patterns
- **Food Safety**: food, supplement, meat, poultry, and egg-product safety records
- **Cosmetic Safety**: public cosmetic-event reports and reaction patterns

The application does not determine whether a product is safe or unsafe. It is not medical advice, clinical decision support, a causation engine, or a replacement for official FDA/USDA guidance.

## At a Glance

| Area | Current implementation |
|---|---|
| Frontend | React, TypeScript, Vite, Axios, CSS |
| Backend | FastAPI, Pydantic, httpx, Uvicorn |
| Persistence | PostgreSQL/Supabase, psycopg, Alembic |
| Public sources | openFDA Drug Enforcement, Drug Event, Food Enforcement, Cosmetic Event; USDA FSIS recall records |
| Testing | pytest, Vitest, Testing Library, Playwright |
| Delivery | Docker Compose, GitHub Actions, Vercel/Render-oriented deployment documentation |

### Current Demo Scope

The recommended walkthrough is:

```text
Home guided search
  -> Pharmacy Safety
  -> Food Safety
  -> Cosmetic Safety
  -> Audit History
  -> Sources / System Status
  -> Saved Monitors
```

The homepage and canonical safety pages include bounded query normalization and accessible typeahead suggestions. Approved aliases help with common misspellings, plurals, and no-space terms without applying uncontrolled fuzzy matching:

```text
xanex         -> xanax
strawberries  -> strawberry
hairdye       -> hair dye
proteinpowder -> protein powder
```

When normalization changes a query, Dav AI preserves the original input and explains the change:

> Showing results for “strawberry” based on your search “strawberries.”

### Strongest Engineering Points

- Consolidated, typed React workflows instead of separate demo modules
- Bounded and testable query normalization in the frontend and backend
- Keyboard-accessible search suggestions
- Source-aware FDA/openFDA and USDA adapters
- Deterministic, versioned review signals rather than opaque safety predictions
- Audit events with source, query, retrieval, transform, and score metadata
- Source-pull provenance, raw public-source snapshots, and SHA-256 payload hashes
- PostgreSQL-backed Saved Monitor history and comparison metadata
- Source registry, freshness, System Status, and Data Quality surfaces
- Bounded PDF report generation with source context and limitations
- Clear zero-result behavior that does not imply a safety guarantee
- Offline-only ML experiments kept separate from production routes

## Validation

Current validated checkpoint:

- **Backend pytest:** 308 passed
- **Frontend tests:** 186 passed
- **ESLint:** passed
- **TypeScript/Vite build:** passed
- **Playwright Chromium smoke test:** passed
- **`git diff --check`:** passed

Relevant stable tags:

- `demo-stable-june-2026`
- `demo-polished-query-june-2026`
- `productscan-ocr-v2-plan-june-2026`

## Portfolio Documentation

- [Portfolio Demo Package](docs/demo/PORTFOLIO_DEMO_PACKAGE.md)
- [Architecture Overview](docs/architecture/ARCHITECTURE_OVERVIEW.md)
- [ProductScan OCR v2 Plan](docs/productscan/PRODUCTSCAN_OCR_V2_PLAN.md)
- [Current Executable Status](docs/current_dav_ai_status_june_2026.md)
- [Operations Runbook](docs/operations_runbook.md)

ProductScan OCR v2 is a **planning document only**. No OCR route, provider, dependency, upload UI, or deployed OCR workflow exists in the current application.

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
- use production ML, RAG, an LLM, or OCR in routed product behavior
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
- USDA FSIS recall and public-health-alert coverage for meat, poultry, and egg products

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
  -> openFDA / USDA public source clients
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
| USDA FSIS Recall API | Meat, poultry, and egg-product recall/public-health-alert coverage |
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
- No deployed OCR; ProductScan OCR v2 is planning only
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
