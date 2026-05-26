# Dav AI

**Healthcare safety intelligence from public FDA signals.**

Dav AI is a full-stack healthcare public-data safety intelligence prototype. It turns public FDA/openFDA recall and adverse-event data into source-aware, explainable review workflows with audit trails, versioned scoring, reaction classification, trend snapshots, deterministic role-based safety briefings, and repeatable saved-monitor workflows.

## Recent Highlight: Monitor Insights

Saved Monitors now include deterministic Monitor Insights for repeatable public-data searches. Each insight compares recent saved monitor runs and summarizes whether public-data activity appears stable, increased, decreased, notably changed, or insufficient for comparison.

Monitor Insights show record deltas, percent change, confidence level, insight versioning, related audit context, and a clear safety limitation. They are based only on stored Dav AI public-data monitor history and do not provide medical advice, diagnosis, treatment guidance, clinical decision support, or proof of causality.

This project is an MVP and portfolio-grade engineering prototype. It is not a medical device, not clinical decision support, and not a replacement for official FDA, CDC, clinician, pharmacist, or emergency guidance.

## Engineering Highlights

Dav AI is designed as a public-data healthcare safety intelligence platform with an emphasis on traceability, reproducibility, and operational transparency.

- Audit-backed source freshness for registered public FDA/openFDA data sources.
- Operational visibility through Data Sources freshness indicators and System Status source-freshness summaries.
- Reproducible source pulls with persisted `source_pulls` records, raw public-source snapshots, and stable SHA-256 payload hashing.
- Audit-linked traceability from API response to audit event to source pull to raw public openFDA payload.
- Safety/privacy boundary limited to public FDA/openFDA data only; Dav AI does not use PHI, private medical history, diagnoses, insurance information, prescription history, addresses, or private user records.
- Tested full-stack workflow covering backend behavior, frontend surfaces, production build checks, CI, and manual deployment smoke verification.

Dav AI is not medical advice or clinical decision support.

---

## Recent Milestone: Saved Monitors v2.6 Scheduler Locking and Test Isolation

Saved Monitors has moved beyond manual saved searches into a stronger monitoring foundation. The current v2.6 state includes persisted run history, latest/previous comparison, change indicators, audit links, backend scheduled-refresh foundation, scheduler CLI guardrails, database-backed scheduler locks, test-isolated backend persistence behavior, and a documented Render Cron dry-run plan.

This milestone was verified through backend tests, frontend tests, production build checks, GitHub Actions CI, manual browser verification, and manual scheduled-monitor CLI verification.

Production Cron is not enabled. Alerts, public scheduling UI, auth/RBAC, notification preferences, alert delivery, and production scheduler observability are not implemented yet.

Live deployment smoke verification also confirmed that migration `20260514_0003_create_saved_monitor_runs.py` was applied and that a temporary saved monitor could be created, manually run, reviewed through `GET /api/v1/saved-monitors/{monitor_id}/runs`, and deleted with cleanup back to an empty monitor list. The persisted smoke row had `status: success`, `record_count: 0`, an audit ID, and `error_message: null`. This verifies persistence and endpoint behavior, not clinical correctness.

Scheduler-lock verification confirmed that migration `20260519_0005_create_scheduler_locks.py` creates the `scheduler_locks` table, the configured database can acquire and release the saved-monitor scheduler lock, `python -m app.jobs.run_due_saved_monitors --limit 10` works with zero due monitors, and a real temporary due DrugSignal monitor for `aspirin` can run successfully and create a `saved_monitor_runs` row. After the manual run, `scheduler_locks` was empty, confirming lock release. Temporary monitor rows were cleaned up.

See:

```text
docs/render_cron_saved_monitors_plan.md
docs/deployment_verification.md
docs/operations_runbook.md
docs/saved_monitors_v2_1_release_checkpoint.md
```

---

## Current Project Status

Dav AI currently includes:

- **Regional Health Pulse MVP scaffold** for public-health signal review. This backend and frontend foundation uses a clearly labeled scaffold source, deterministic trend labeling, source registry metadata, audit summary metadata, source-pull snapshot handling, scaffold source freshness status, Audit History linking, Saved Monitors backend support, scheduled-refresh compatibility, and public-health safety disclaimers. It is not live CDC/HHS surveillance yet, not emergency guidance, not medical advice, and not a personal disease-risk predictor.

- **RecallRadar** for live openFDA Drug Enforcement recall search.
- **DrugSignal** for openFDA Drug Event / FAERS-style adverse-event reporting-pattern review.
- **Recall Review Score** for transparent recall review-priority scoring.
- **DrugSignal Intelligence Score v1** for explainable FAERS reporting-pattern scoring.
- **Reaction Classification v1** for rule-based grouping of DrugSignal reaction terms.
- **DrugSignal Trend Snapshot v1** for comparing the current DrugSignal result with stored audit history.
- **Safety Briefing Engine** for deterministic role-aware public-data safety briefings.
- **Source Registry** for public data source transparency.
- **Audit History** for persisted source/search traceability.
- **Saved Monitors v2.6 foundation** for saved repeatable RecallRadar, DrugSignal, and Regional Health Pulse searches, manual run checks, latest/previous comparison, run history, change indicators, duplicate prevention, audit linking, backend scheduled-refresh foundation, CLI guardrails, database-backed scheduler locks, and Render Cron dry-run planning.
- **System/Data Quality views** for operational and audit-persistence visibility.
- **Supabase/PostgreSQL audit and saved-monitor persistence** through fail-soft backend repositories.
- **GitHub Actions CI** for backend tests, frontend tests, frontend lint, frontend production build, and Playwright smoke testing.
- **Production deployment verification docs** for Vercel frontend, Render backend, and Supabase PostgreSQL.

The current product direction is to move from one-time public-data search toward repeatable safety monitoring workflows:

```text
Search → Score → Audit → Briefing → Monitor → Compare → Alert
```

---

## Product Foundation

The current product foundation is built around five ideas:

1. **Public-data safety intelligence**: Dav AI uses public FDA/openFDA data, not private medical records.
2. **Source transparency**: Results expose source names, endpoints, retrieval timestamps, source IDs, and update context.
3. **Auditability**: Searches generate audit IDs and persisted audit events for later review.
4. **Explainability**: Recall and DrugSignal scores are rule-based, versioned, and visible.
5. **Healthcare safety guardrails**: The app avoids medical advice, diagnosis, treatment guidance, medication-change recommendations, and FAERS causation claims.

Dav AI is intentionally focused on public-data traceability, operational readiness, and healthcare safety boundaries rather than generic chatbot behavior.

---

## Feature Status

| Status | Features |
|---|---|
| Implemented | RecallRadar; DrugSignal; Regional Health Pulse MVP scaffold; Audit History; System Status / Data Quality; Data Sources; deterministic safety briefings; Saved Monitors run history for RecallRadar, DrugSignal, and Health Pulse; saved-monitor latest/previous comparison; backend scheduled-refresh foundation; scheduler CLI guardrails; database-backed scheduler locks; Render Cron dry-run documentation. |
| Partial | Deployment hardening; production observability; scheduled refresh backend foundation; authentication/RBAC planning. |
| Planned | Production Cron activation; automated alerts; public scheduling UI; authentication/RBAC; notification preferences; briefing persistence/history; raw snapshot/hash-based reproducibility; live CDC/HHS-backed Regional Health Pulse data connectors; EnviroHealth Signal; CNN/OCR label scanner; RAG/LLM upgrades. |

---

## Current MVP: RecallRadar, DrugSignal, Audit History, Safety Briefings, and Saved Monitors

### RecallRadar

RecallRadar allows a user to search a product, drug, brand, or category and receive:

- Live public FDA recall records from the openFDA Drug Enforcement API.
- Normalized recall details.
- Recall reason and FDA classification.
- Recall status and initiation date.
- Distribution pattern and recalling firm.
- Transparent Recall Review Score.
- Plain-English review-priority explanation.
- Source timestamp and technical audit details.
- Medical safety disclaimer.
- Compact audit summary for source traceability.
- Persisted audit event when database persistence is configured.
- Role-based safety briefing.

### DrugSignal

DrugSignal allows a user to search a drug or medicinal product and receive:

- Live public openFDA Drug Event records.
- Top reported FAERS reactions.
- Relative count bars for reaction frequency within returned results.
- DrugSignal Intelligence Score v1.
- Signal strength label.
- Review priority.
- Data confidence label.
- Top reaction concentration.
- Rule-based Reaction Classification v1.
- DrugSignal Trend Snapshot v1.
- Record count and source metadata.
- Source endpoint and retrieval timestamp.
- FAERS causation disclaimer.
- Medical safety disclaimer.
- Empty-result handling for searches with no FAERS matches.
- Compact audit summary for source traceability.
- Persisted audit event when database persistence is configured.
- Role-based safety briefing.

### Audit History

Audit History allows users to review recent public-data searches and inspect traceability metadata such as audit ID, module, source, endpoint, query parameters, retrieval timestamp, upstream status, record count, transform version, score version, disclaimer version, and error messages when present.

The Audit History frontend includes:

- Recent audit event table.
- Selected audit detail panel.
- Module/status/search filters.
- Applied filter summary.
- CSV export.
- Copy audit ID.
- Copy trace summary.
- Copy audit link.
- Audit detail URL state and refresh preservation.

### Safety Briefing Engine

The Safety Briefing Engine generates deterministic role-based briefings for:

- Consumer.
- Pharmacy.
- Clinic.
- Public Health / Analyst.

Briefings are generated from structured RecallRadar and DrugSignal response data only. The current briefing engine does not use an LLM and does not provide diagnosis, treatment guidance, medication-change advice, or FAERS causation claims.

DrugSignal briefing output has been upgraded to use DrugSignal Intelligence Score v1 and Reaction Classification v1, with source/audit details and limitations kept visible.

### Saved Monitors v2.6 Foundation

Saved Monitors v2.6 foundation lets users save repeatable RecallRadar, DrugSignal, or Regional Health Pulse searches, manually run checks over time, review run history, compare latest and previous values, and rely on a backend scheduled-refresh foundation for future Cron-based execution.

Current manual workflow:

```text
Save monitor → Run check → Review latest score/count/audit ID → Review recent run history → Run again later → Compare latest and previous values
```

The current implementation supports:

- Saved monitor definitions for RecallRadar or DrugSignal.
- Supabase/PostgreSQL persistence when configured.
- Local fail-soft fallback when persistence is unavailable.
- Manual run checks from the backend and frontend.
- Latest and previous score fields.
- Latest and previous record-count fields.
- Change indicators for score and record-count movement.
- `Score N/A` and `Records N/A` when no previous values exist.
- `Score unchanged` and `Records unchanged` when values match across runs.
- Latest audit ID and last-checked timestamp.
- A link from the latest saved-monitor audit ID to Audit History.
- Run-history rows with run time, module, status, record count, score/label, and audit link when available.
- Duplicate prevention by module and normalized query.
- Clear frontend duplicate-monitor error display.
- Backend schedule metadata for future scheduled refresh.
- Due-monitor selection foundation.
- Backend CLI job for future scheduled execution.
- CLI guardrails with safe limit clamping.
- Database-backed scheduler locking through the `scheduler_locks` table.
- In-memory scheduler lock fallback for local/test-created repository instances.
- Render Cron dry-run documentation.

Saved Monitors includes a backend scheduled-refresh foundation, CLI guardrails, and database-backed scheduler locking, but production Cron is not enabled. It does not include automated alerts, public scheduling UI, user accounts, authentication/RBAC, briefing history, production scheduler observability, or alert delivery preferences.

Documentation:

```text
docs/saved_monitors_manual_verification.md
docs/saved_monitors_v2_1_release_checkpoint.md
docs/manual_saved_monitors_v1.md
docs/render_cron_saved_monitors_plan.md
```

---

## Current MVP Status

### Working now

- React + TypeScript frontend.
- FastAPI backend.
- Backend source registry for public FDA/openFDA source metadata.
- Sources endpoint and frontend Data Sources page.
- openFDA Drug Enforcement API integration.
- openFDA Drug Event API integration.
- RecallRadar end-to-end search workflow.
- DrugSignal end-to-end search workflow.
- Rule-based Recall Review Score.
- DrugSignal Intelligence Score v1.
- Reaction Classification v1.
- DrugSignal Trend Snapshot v1.
- Deterministic Safety Briefing Engine.
- Role-based briefings for Consumer, Pharmacy, Clinic, and Public Health / Analyst.
- Source-aware audit panels.
- Compact audit summaries in RecallRadar and DrugSignal responses.
- Internal audit event builder utility.
- Fail-soft audit persistence boundary.
- Supabase/PostgreSQL `source_registry` table.
- Supabase/PostgreSQL `audit_events` table.
- Supabase/PostgreSQL `saved_monitors` table.
- Supabase/PostgreSQL saved monitor run-history support.
- Supabase/PostgreSQL saved monitor schedule metadata support.
- Audit History list/detail API.
- Audit History frontend page with filters, detail panel, CSV export, and copy actions.
- Saved Monitors v2.6 foundation for creating, listing, deleting, duplicate prevention, manually running repeatable RecallRadar, DrugSignal, or Regional Health Pulse monitors, reviewing run history, and supporting backend scheduled-refresh groundwork.
- Saved monitor latest/previous comparison, run history, and change indicators.
- Backend scheduled-refresh foundation.
- Scheduler CLI guardrails.
- Database-backed scheduler locks through `scheduler_locks`.
- Backend tests isolated from the real `DATABASE_URL` by `backend/tests/conftest.py`.
- Render Cron dry-run documentation.
- System Status page.
- Data Quality panel.
- Request ID propagation and `X-Request-ID` response headers.
- Medical safety disclaimers.
- FAERS causation disclaimer for DrugSignal.
- Empty-result handling for RecallRadar and DrugSignal.
- Backend tests.
- Frontend tests.
- GitHub Actions CI.
- Docker Compose local development setup.
- Production deployment and verification documentation.

### Not built yet

- User accounts.
- Authentication and role-based access control.
- Production Cron activation.
- Automated alerts.
- Public scheduling UI.
- Briefing persistence.
- Alerting beyond saved-monitor run history.
- Alert delivery preferences.
- Formal ML model training.
- Embedding search or clustering model.
- Formal classifier evaluation dataset.
- Product analytics.
- Production observability dashboard.
- Production security hardening beyond current MVP configuration.

---

## Current Engineering Status

The active MVP modules are RecallRadar, DrugSignal, Regional Health Pulse MVP scaffold, Audit History, Safety Briefing Engine, Source Registry, System Status, Data Quality, and Saved Monitors v2.6 foundation.

Current engineering support includes:

- Live public openFDA source calls.
- Normalized backend response schemas.
- Typed frontend API models.
- Explainable scoring modules.
- Rule-based reaction classification module.
- Trend snapshot helper using stored audit history.
- Audit event construction and persistence.
- PostgreSQL/Supabase schema and Alembic migrations.
- Saved monitor repository, API, frontend page, and backend/frontend tests.
- Saved monitor duplicate prevention.
- Saved monitor change indicators.
- Backend scheduled-refresh foundation.
- Scheduler CLI guardrails.
- Database-backed scheduler lock repository and migration.
- Test isolation from the real `DATABASE_URL` by default.
- Render Cron dry-run planning with production Cron disabled.
- Request ID middleware and frontend request ID propagation.
- Production verification documentation for deployed behavior.
- Backend and frontend tests.
- Frontend lint and production build verification.
- AuditHistoryPage async interaction test cleanup.
- GitHub Actions CI.

Current backend test status:

```bash
120 passed
```

Current frontend test status:

```bash
61 passed
```

---

## Recall Review Score

Dav AI uses a transparent, rule-based **Recall Review Score** for RecallRadar.

The score is not a medical diagnosis, treatment recommendation, or official FDA replacement. It is a review-priority signal that helps users understand which public recall records may deserve closer attention.

### Current score inputs

The current Recall Review Score uses four public recall fields:

1. FDA classification severity.
2. Recall status.
3. Recall initiation recency.
4. Distribution scope.

### Component logic

| Component | Current logic |
|---|---|
| FDA classification | Class I receives the highest weight, followed by Class II and Class III. |
| Recall status | Ongoing recalls receive more weight than completed or terminated recalls. |
| Recency | Recent recalls receive more weight than older recalls. |
| Distribution scope | Nationwide or multi-state distribution receives more weight than local distribution. |

Current score version:

```text
recall-risk-v0.1
```

---

## DrugSignal

DrugSignal is the FAERS-style public adverse-event reporting-pattern module. It uses the openFDA Drug Event API to retrieve public adverse-event records for a searched drug or medicinal product.

Current DrugSignal response includes:

- Search query.
- Source name.
- Source endpoint.
- Retrieval timestamp.
- Record count.
- Medical disclaimer.
- FAERS causation disclaimer.
- Compact audit summary.
- DrugSignal Intelligence Score v1.
- Reaction Classification v1.
- DrugSignal Trend Snapshot v1.
- Top reported reactions from returned FAERS records.
- Relative count bars for comparing reaction frequency within returned results.
- Role-based safety briefing.

Important limitation:

FAERS adverse-event reports do **not** prove that a drug caused a reaction. Reports may be incomplete, duplicated, delayed, influenced by reporting patterns, or missing clinical context. DrugSignal is a reporting-pattern explorer, not a causation engine.

---

## DrugSignal Intelligence Score v1

DrugSignal Intelligence Score v1 is an explainable scoring layer for public FAERS adverse-event search results.

It summarizes returned openFDA Drug Event records into a transparent signal score without implying medical causation.

Current score version:

```text
drug-signal-intelligence-v0.1
```

Current score inputs:

- Returned FAERS record count.
- Top reaction concentration.
- Reaction diversity.
- Data confidence.

Current score output:

- Score from 0 to 100.
- Signal strength label.
- Review priority.
- Data confidence.
- Top reaction concentration.
- Score version.
- Safety limitations.

The score is based on returned public openFDA records and reaction counts, not clinical incidence rates.

Documentation:

```text
docs/drug_signal_intelligence_score.md
docs/drug_signal_intelligence_backend_verification.md
docs/drug_signal_intelligence_frontend_verification.md
```

---

## Reaction Classification v1

Reaction Classification v1 groups returned top FAERS reaction terms into understandable rule-based categories.

Current categories include:

- Neurological.
- Gastrointestinal.
- Respiratory.
- Cardiovascular.
- Skin / allergy.
- Infection / immune.
- Metabolic.
- General / other.

Current classifier version:

```text
reaction-classifier-v0.1
```

This is an NLP-style classification layer, but it is intentionally rule-based for the current MVP. That makes it easier to explain, test, audit, and keep healthcare-safe before adding ML or embedding-based clustering.

Documentation:

```text
docs/drug_signal_reaction_classification_verification.md
```

---

## DrugSignal Trend Snapshot v1

DrugSignal Trend Snapshot v1 compares the current DrugSignal result with the most recent stored DrugSignal audit event for the same query when previous history exists.

Current trend output includes:

- Trend label.
- Current record count.
- Previous record count.
- Previous audit ID.
- Previous timestamp.
- Plain-language explanation.
- Trend limitation.
- Trend version.

Current trend version:

```text
drug-signal-trend-v0.1
```

Current limitation:

Trend Snapshot v1 is based only on stored public-data searches in Dav AI. It does not represent all FDA activity and should not be interpreted as a complete surveillance signal.

Documentation:

```text
docs/drug_signal_trend_snapshot_verification.md
```

---

## Safety Briefing Engine

The Safety Briefing Engine turns structured RecallRadar and DrugSignal response data into deterministic role-based public-data safety briefings.

Current roles:

- Consumer.
- Pharmacy.
- Clinic.
- Public Health / Analyst.

Each briefing includes:

- Summary.
- What was found.
- What to verify.
- Suggested review checklist.
- Limitations.
- Source and audit details.
- Disclaimer.

RecallRadar briefings use structured recall response data and Recall Review Score output.

DrugSignal briefings use structured DrugSignal response data, including DrugSignal Intelligence Score v1 and Reaction Classification v1. The DrugSignal briefing UI displays Safety Briefing Engine v2.

The briefing engine does not use an LLM. It must not generate diagnosis, treatment guidance, medication-change advice, FAERS causation claims, or unsupported medical recommendations.

Documentation:

```text
docs/drug_signal_briefing_v2_verification.md
```

---

## Sources Registry

Dav AI includes a backend source registry to make public-data usage transparent and auditable.

Current registered sources:

- openFDA Drug Enforcement API for RecallRadar.
- openFDA Drug Event API for DrugSignal.

Sources endpoint:

```text
GET /api/v1/sources
```

The endpoint returns each source with:

- Source ID.
- Source name.
- Endpoint.
- Module.
- Description.
- Update cadence.

The frontend Data Sources page consumes this endpoint and displays registered public sources, modules, endpoints, descriptions, and update cadence.

---

## Audit Architecture

Dav AI separates public response metadata from internal audit event construction.

The backend currently supports:

- Compact audit summaries in RecallRadar and DrugSignal responses.
- Frontend display of compact audit summaries.
- Internal full audit event construction.
- Fail-soft audit repository boundary.
- PostgreSQL persistence into the `audit_events` table.
- Audit History list/detail endpoints.
- Audit History filters.
- Audit detail URL state.
- Audit copy/export actions in the frontend.
- Saved monitor audit linking after successful monitor runs.

The compact public audit summary includes:

- Audit ID.
- Source ID.
- Module.
- Upstream status.
- Record count.
- Transform version.

The full audit event additionally supports:

- Source name.
- Endpoint.
- Query parameters.
- Retrieval timestamp.
- Score version when applicable.
- Disclaimer version.
- Error message.
- Created timestamp.

Current Audit History endpoints:

```text
GET /api/v1/audit-events
GET /api/v1/audit-events/{audit_id}
```

Audit History is for public-data traceability only. It is not clinical record storage.

Current Saved Monitors endpoints:

```text
GET /api/v1/saved-monitors
POST /api/v1/saved-monitors
GET /api/v1/saved-monitors/{monitor_id}/runs
POST /api/v1/saved-monitors/{monitor_id}/run
DELETE /api/v1/saved-monitors/{monitor_id}
```

Saved Monitors endpoints support repeatable public-data searches across RecallRadar, DrugSignal, and Regional Health Pulse, manual run checks, and run history. The backend also includes a scheduled-refresh foundation, scheduler lock repository, and CLI job for future Cron execution. Production Cron, public scheduling UI, and alerting are not enabled yet.

---

## Persistence

Dav AI includes Supabase/PostgreSQL audit persistence and saved monitor persistence.

Current persistence support includes:

- `backend/db/schema.sql`.
- Alembic migrations for `source_registry`, `audit_events`, `saved_monitors`, saved monitor run history, saved monitor schedule metadata, and scheduler locks.
- `backend/app/db/database.py`.
- `backend/app/db/audit_repository.py`.
- `backend/app/db/saved_monitor_repository.py`.
- Fail-soft audit event inserts.
- Audit event reads for Audit History.
- Latest audit event lookup for DrugSignal Trend Snapshot v1.
- Source metadata stored in `source_registry`.
- Search/source audit events stored in `audit_events`.
- Saved monitor definitions, latest manual run state, schedule metadata, and run-history rows stored for saved-monitor workflows.
- Scheduler lock state stored in `scheduler_locks` while a scheduled-refresh job is active.

The current persistence layer stores:

- Source ID.
- Source name.
- Endpoint.
- Module.
- Search query.
- Query parameters.
- Retrieval timestamp.
- Upstream status.
- Record count.
- Transform version.
- Score version when applicable.
- Disclaimer version.
- Error message when applicable.
- Created timestamp.
- Saved monitor name, query, module, status, latest/previous score, latest/previous record count, latest audit ID, last-checked timestamp, schedule metadata, and run-history state.
- Scheduler lock name, lock owner, lock expiration, and timestamps while a job lock is active.

The current persistence layer does **not** store:

- Personal health records.
- Patient identifiers.
- Medication profiles tied to real users.
- Uploaded documents.
- Uploaded images.
- Private medical notes.
- User accounts or authentication records.
- Alert delivery state.

Database credentials must be stored only in local or deployment environment variables. Do not commit real credentials to GitHub.

---

## Safety Boundary

Dav AI provides public-data safety intelligence only.

It is not:

- Medical advice.
- Diagnosis.
- Treatment guidance.
- A medication-change recommendation system.
- A replacement for FDA, CDC, clinicians, pharmacists, emergency services, or official source guidance.

The app does not:

- Diagnose medical conditions.
- Recommend starting, stopping, or changing medication.
- Claim that public safety reports prove causation.
- Store PHI in the current MVP design.

FAERS adverse-event reports do **not** prove causation. They are reporting-pattern signals that may be incomplete, duplicated, delayed, biased by reporting behavior, or missing clinical context.

Users should verify official source records and consult qualified healthcare professionals for medical decisions.

---

## Tech Stack

### Frontend

- React.
- TypeScript.
- Vite.
- CSS.
- Axios.
- Vitest.
- React Testing Library.

### Backend

- FastAPI.
- Uvicorn.
- httpx.
- Pydantic.
- pytest.
- python-dotenv.
- psycopg.
- Alembic.

### Public Data Sources

- openFDA Drug Enforcement API.
- openFDA Drug Event API.

### Persistence

- Supabase PostgreSQL.
- SQL schema for source registry, audit events, saved monitors, saved monitor runs, saved monitor schedule metadata, and scheduler locks.
- Alembic migrations for source registry, audit events, saved monitors, saved monitor runs, saved monitor schedule metadata, and `scheduler_locks`.
- Fail-soft audit persistence repository.
- Fail-soft saved monitor repository.
- Database-backed scheduler lock repository with in-memory fallback for local/test-created repository instances.

### CI/CD

- GitHub Actions.
- Backend pytest job.
- Frontend test job.
- Frontend lint job.
- Frontend production build job.
- Playwright smoke test job.

### Local Containerization

- Docker.
- Docker Compose.
- Backend Dockerfile.
- Frontend Dockerfile.

---

## Local Development

### Backend

```bash
cd backend
source ../.venv/bin/activate
uvicorn app.main:app --reload
```

Backend runs at:

```text
http://127.0.0.1:8000
```

Health check:

```text
http://127.0.0.1:8000/health
```

FastAPI docs:

```text
http://127.0.0.1:8000/docs
```

Current core backend endpoints:

```text
GET /api/v1/recalls/search
GET /api/v1/drug-events/search
GET /api/v1/sources
GET /api/v1/audit-events
GET /api/v1/audit-events/{audit_id}
GET /api/v1/saved-monitors
POST /api/v1/saved-monitors
GET /api/v1/saved-monitors/{monitor_id}/runs
POST /api/v1/saved-monitors/{monitor_id}/run
DELETE /api/v1/saved-monitors/{monitor_id}
```

Additional operational endpoints:

```text
GET /health
GET /api/v1/system/status
GET /api/v1/system/data-quality
```

### Scheduled Monitor CLI

The scheduled monitor refresh foundation includes a backend CLI job for future Cron use.

From the backend service context:

```bash
cd /Users/chanduesukula/medtrek-ai/backend
python -m app.jobs.run_due_saved_monitors --limit 10
```

This command is for dry-run/manual verification only. Production Cron is not enabled.

The CLI uses database-backed scheduler locks when `DATABASE_URL` is configured and the `scheduler_locks` table exists. Migration `backend/migrations/versions/20260519_0005_create_scheduler_locks.py` creates that table. In-memory locking remains available for local/test-created repository instances.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at:

```text
http://localhost:5173
```

Frontend API configuration:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### Backend environment configuration

```env
DATABASE_URL=postgresql+psycopg://username:password@host:5432/database
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Use local `.env` files for development and deployment environment variables for hosted services. Do not commit real `.env` files or secrets.

---

## Docker Local Development

Dav AI can run locally with Docker Compose.

From the repository root:

```bash
docker compose up --build
```

This starts:

- FastAPI backend container.
- React/Vite frontend container.

Local URLs:

```text
Frontend: http://localhost:5173
Backend health check: http://localhost:8000/health
Backend API docs: http://localhost:8000/docs
```

Stop the containers:

```bash
docker compose down
```

Docker uses local environment files:

```text
backend/.env
frontend/.env
```

Do not commit real `.env` files or secrets to GitHub.

---

## Deployment Environment Notes

Dav AI is designed to deploy as separate frontend, backend, and database services.

Recommended MVP deployment path:

```text
Frontend: Vercel
Backend: Render or Railway
Database: Supabase PostgreSQL
```

Deployment environment variables:

Backend:

```env
DATABASE_URL=postgresql+psycopg://username:password@host:5432/database
ALLOWED_ORIGINS=https://your-frontend-domain.vercel.app
```

Frontend:

```env
VITE_API_BASE_URL=https://your-backend-domain.onrender.com
```

Production safety checks:

- Verify `/health` returns `{"status":"healthy"}`.
- Verify `/docs` loads correctly.
- Confirm RecallRadar search works from the deployed frontend.
- Confirm DrugSignal search works from the deployed frontend.
- Confirm Audit History can read persisted events.
- Confirm System/Data Quality views load.
- Confirm Saved Monitors can create, list, run, compare, and delete monitors.
- Confirm Supabase audit rows are created after successful searches.
- Confirm Supabase saved monitor rows are created after saved monitor creation.
- Confirm Supabase saved monitor run-history rows are created after monitor runs.
- Confirm CORS only allows trusted frontend origins.
- Confirm no real `.env` files or secrets are committed.

Credential hygiene checkpoint: after accidental database credential exposure, the Supabase database password was rotated, Render `DATABASE_URL` was updated, the backend was redeployed, and health, system status, and data-quality endpoints were verified successfully. Do not record database URLs or passwords in documentation.

---

## Testing

Run backend tests:

```bash
cd backend
pytest
```

Current backend test status:

```bash
120 passed
```

Backend test coverage includes:

- Recall Review Score behavior.
- RecallRadar route behavior.
- DrugSignal route behavior.
- DrugSignal Intelligence Score v1.
- Reaction Classification v1.
- DrugSignal Trend Snapshot v1.
- openFDA client behavior.
- Source registry endpoint behavior.
- Audit event construction.
- Database configuration.
- Fail-soft audit repository behavior.
- Audit History API behavior.
- System Status and Data Quality API behavior.
- Request ID middleware behavior.
- Saved Monitors backend behavior.
- Saved monitor duplicate prevention.
- Saved monitor manual run checks.
- Saved monitor latest/previous value preservation.
- Saved monitor run-history behavior.
- Scheduled refresh due-monitor selection and summary behavior.
- Scheduled monitor CLI guardrails.
- Database-backed scheduler lock behavior.
- Backend test isolation from the real `DATABASE_URL` through `backend/tests/conftest.py`.

Run frontend tests:

```bash
cd frontend
npm test
```

Current frontend test status:

```bash
61 passed
```

Frontend test coverage includes:

- App smoke rendering.
- RecallRadar component behavior.
- DrugSignal component behavior.
- DrugSignal Intelligence, classification, trend, and briefing UI behavior.
- Safety briefing generator behavior.
- Audit History filters, copy actions, CSV export, and URL state.
- System Status / Data Quality page behavior.
- Saved Monitors loading, empty state, creation, duplicate error handling, validation, RecallRadar/DrugSignal/Regional Health Pulse module selection, run checks, run history, latest/previous values, change indicators, delete confirmation, audit linking, and error states.

Run frontend lint and production build:

```bash
cd frontend
npm run lint
npm run build
```

GitHub Actions CI runs backend tests, frontend tests, frontend lint, frontend production build, and Playwright smoke testing on push and pull request.

---

## Manual Persistence Verification

Manual Supabase/PostgreSQL verification has been documented for audit persistence and saved monitor persistence.

Verified persisted audit rows include:

- Manual backend audit event insert.
- RecallRadar search audit event.
- DrugSignal search audit event.

Verified saved monitor persistence includes:

- Saved monitor creation.
- Saved monitor list retrieval after backend restart.
- Manual saved monitor run check.
- Saved monitor run-history persistence.
- Latest/previous score persistence.
- Latest/previous record-count persistence.
- Latest audit ID persistence.
- Last checked timestamp persistence.
- Schedule metadata persistence foundation.
- Scheduler lock acquisition and release through `scheduler_locks`.

Live v2.2 run-history smoke verification confirmed:

- `GET /api/v1/saved-monitors` returned `200` with `[]` before the smoke run.
- `POST /api/v1/saved-monitors` created a temporary smoke monitor.
- `POST /api/v1/saved-monitors/{monitor_id}/run` returned `200`.
- `GET /api/v1/saved-monitors/{monitor_id}/runs` returned `200` with a persisted run-history row.
- `DELETE /api/v1/saved-monitors/{monitor_id}` returned `204`.
- `GET /api/v1/saved-monitors` returned `200` with `[]` after cleanup.
- The persisted smoke row had `status: success`, `record_count: 0`, an audit ID, and `error_message: null`.

Manual scheduled-monitor verification also confirmed:

- Migration `20260519_0005_create_scheduler_locks.py` was applied.
- `scheduler_locks` existed in the configured database.
- `python -m app.jobs.run_due_saved_monitors --limit 10` worked with zero due monitors.
- A real temporary due DrugSignal saved monitor for `aspirin` ran successfully.
- A `saved_monitor_runs` row was created.
- `scheduler_locks` was empty after the job, confirming lock release.
- Temporary monitor rows were cleaned up.

Related docs:

```text
docs/persistence_plan.md
docs/audit_trail_design.md
docs/production_observability_verification.md
docs/saved_monitors_manual_verification.md
docs/saved_monitors_v2_1_release_checkpoint.md
docs/render_cron_saved_monitors_plan.md
```

---

## Production Verification Documentation

Production and verification documentation is kept in `docs/`.

Important verification docs include:

```text
docs/deployment_verification.md
docs/deployment_checklist.md
docs/backend_deployment_setup.md
docs/operations_runbook.md
docs/render_cron_saved_monitors_plan.md
docs/production_observability_verification.md
docs/frontend_request_id_verification.md
docs/system_status_verification.md
docs/system_data_quality_verification.md
docs/frontend_system_status_verification.md
docs/frontend_data_quality_verification.md
docs/drug_signal_intelligence_backend_verification.md
docs/drug_signal_intelligence_frontend_verification.md
docs/drug_signal_reaction_classification_verification.md
docs/drug_signal_briefing_v2_verification.md
docs/drug_signal_trend_snapshot_verification.md
docs/manual_saved_monitors_v1.md
docs/saved_monitors_manual_verification.md
docs/saved_monitors_v2_1_release_checkpoint.md
```

These docs support reproducibility, reviewer confidence, and production-readiness tracking.

---

## Near-Term Roadmap

Recommended next steps:

1. Keep RecallRadar, DrugSignal, Audit History, Source Registry, System/Data Quality, Safety Briefing Engine, and Saved Monitors v2.6 foundation stable.
2. Keep production Cron disabled until deployment-environment scheduler verification, scheduler observability, and rollback guidance are stronger.
3. Improve Trend Snapshot examples using repeated-query audit history.
4. Add frontend trend comparison visualization improvements.
5. Expand saved monitor detail and run-history review.
6. Re-verify database-backed scheduler locking in the target deployment environment before any recurring production job.
7. Add authentication and role-aware access control before user-specific scheduling or alerts.
8. Add a production observability dashboard or monitoring summary beyond current request tracing and operational transparency.
9. Add formal NLP/ML evaluation dataset for reaction classification.
10. Explore NLP-assisted clustering only after the rule-based baseline is evaluated.

---

## Project Direction

Dav AI should remain focused on healthcare public-data safety intelligence, source transparency, auditability, monitoring, and responsible AI guardrails.

It should not become a generic chatbot, generic dashboard, or medical advice tool.

The strongest next product direction is:

```text
Search → Score → Audit → Briefing → Monitor → Compare → Alert
```
