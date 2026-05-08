# MedTrek AI

**Healthcare safety intelligence from public FDA signals.**

MedTrek AI is a full-stack healthcare safety intelligence prototype that turns public recall and adverse-event data into source-aware, explainable safety signals and deterministic role-based safety briefings.

The current product foundation includes:

- **RecallRadar**: a live FDA recall search workflow powered by the openFDA Drug Enforcement API
- **DrugSignal**: a public FAERS adverse-event reporting pattern explorer powered by the openFDA Drug Event API
- **Safety Briefing Engine v1**: a deterministic role-based briefing layer for RecallRadar and DrugSignal

This project is designed as a serious full-stack AI/data product prototype, not a static student demo.

---

## Current MVP: RecallRadar, DrugSignal, and Safety Briefing Engine v1

RecallRadar allows a user to search a product, drug, brand, or category and receive:

- Live public FDA recall records
- Normalized recall details
- Recall reason and FDA classification
- Recall status and initiation date
- Distribution pattern and recalling firm
- Transparent Recall Review Score
- Plain-English explanation
- Source timestamp and technical audit details
- Medical safety disclaimer
- Compact audit summary for source traceability
- Role-based safety briefing

DrugSignal allows a user to search a drug or medicinal product and receive:

- Live public openFDA Drug Event records
- Top reported FAERS reactions
- Relative count bars for reaction frequency
- Record count and source metadata
- Source endpoint and retrieval timestamp
- FAERS causation disclaimer
- Medical safety disclaimer
- Empty-result handling for searches with no FAERS matches
- Compact audit summary for source traceability
- Role-based safety briefing

Safety Briefing Engine v1 generates deterministic role-based briefings for:

- Consumer
- Pharmacy
- Clinic
- Public Health / Analyst

Briefings are generated from structured RecallRadar and DrugSignal response data only. The current briefing engine does not use an LLM and does not provide diagnosis, treatment guidance, medication-change advice, or FAERS causation claims.

RecallRadar and DrugSignal are connected end-to-end through the React frontend and FastAPI backend. Audit events are persisted to Supabase/PostgreSQL through a fail-soft backend repository layer. Safety Briefing Engine v1 is implemented as a deterministic, role-based frontend briefing layer for RecallRadar and DrugSignal. Frontend tests, backend tests, GitHub Actions CI, local Docker Compose setup, and deployment environment configuration are active. Saved monitors, production deployment, database migrations, and production hardening remain future phases.

---

## Current MVP Status

### Working now

- React + TypeScript frontend
- FastAPI backend
- Backend source registry for FDA source metadata
- Sources endpoint exposing registered public data sources
- Frontend Data Sources page using the backend source registry endpoint
- openFDA Drug Enforcement API integration
- openFDA Drug Event API integration
- RecallRadar end-to-end search workflow
- DrugSignal end-to-end search workflow
- Rule-based Recall Review Score
- Deterministic Safety Briefing Engine v1 for RecallRadar and DrugSignal
- Role-based safety briefings for Consumer, Pharmacy, Clinic, and Public Health / Analyst
- Safety briefing source/audit details
- Source-aware audit panels
- Compact audit summaries in RecallRadar and DrugSignal API responses
- Frontend display of compact audit summaries for RecallRadar and DrugSignal
- Internal audit event builder utility
- Fail-soft audit persistence boundary wired into RecallRadar and DrugSignal routes
- Real Supabase/PostgreSQL audit event persistence for RecallRadar and DrugSignal
- Supabase `source_registry` table for registered public data sources
- Supabase `audit_events` table for persisted source/search audit events
- Medical safety disclaimers
- FAERS causation disclaimer for DrugSignal
- Empty-result handling for searches with no FDA recall matches
- Empty-result handling for searches with no FAERS drug-event matches
- DrugSignal frontend page using the openFDA Drug Event API
- DrugSignal backend module using the openFDA Drug Event API
- DrugSignal top reported reactions display with relative count bars
- Safety briefing generator unit tests
- Frontend component tests with Vitest and React Testing Library
- DrugSignal backend tests for route behavior, query validation, and openFDA client behavior
- Backend unit tests for recall scoring
- Backend route tests for success, empty-result, upstream failure, and query validation
- openFDA client tests for success, no-match, and server-error behavior
- Backend tests for the source registry endpoint
- Backend tests for audit event construction
- Backend tests for database configuration and fail-soft persistence behavior
- Backend response schemas for RecallRadar, DrugSignal, Sources, and Audit API objects
- Top-level audit metadata including source endpoint and score version
- Environment-based frontend API URL configuration
- Environment-based backend database URL configuration
- Production-configurable backend CORS origins
- GitHub Actions CI for backend tests, frontend tests, lint, and build
- Docker Compose local development setup for frontend and backend
- Clean frontend/backend project structure

### Not built yet

- User accounts
- Authentication/roles
- Saved searches or alerts
- Saved monitors
- Production deployment
- Database migrations
- Briefing persistence
- LLM/RAG briefing upgrade
- CNN/OCR product label scanner
- Production observability/logging
- Production security hardening

---

## Current Engineering Status

RecallRadar, DrugSignal, and Safety Briefing Engine v1 are the active end-to-end MVP modules.

Current support includes:

- Live openFDA Drug Enforcement recall search
- Live openFDA Drug Event adverse-event search
- Public source registry endpoint for source transparency
- Frontend Data Sources page for registered public data sources
- Normalized RecallRadar result cards
- DrugSignal top reported reactions display with relative count bars
- Transparent rule-based Recall Review Score
- Deterministic role-based safety briefings for RecallRadar and DrugSignal
- Compact audit summaries in RecallRadar and DrugSignal API responses
- Frontend display of compact audit summaries for RecallRadar and DrugSignal
- Internal full audit event builder utility
- Fail-soft audit persistence boundary wired into RecallRadar and DrugSignal routes
- Real PostgreSQL audit event persistence through Supabase connection pooling
- Source metadata stored in Supabase/PostgreSQL
- Audit events stored in Supabase/PostgreSQL after successful RecallRadar and DrugSignal searches
- Source metadata and retrieval timestamps
- Medical safety disclaimer
- FAERS causation disclaimer for DrugSignal
- Empty-result handling for searches with no FDA matches
- DrugSignal empty-state UI for searches with no FAERS matches
- Backend scoring tests
- Audit event builder tests
- Database configuration helper tests
- Fail-soft audit repository tests
- RecallRadar route tests for success, empty-result, upstream failure, and query validation
- DrugSignal route tests for success, empty-result, upstream failure, and query validation
- Sources endpoint response and required metadata tests
- openFDA Drug Enforcement client tests for success, no-match, and server-error behavior
- openFDA Drug Event client tests for success, no-match, and server-error behavior
- Frontend App smoke test
- RecallRadar component tests
- DrugSignal component tests
- Safety briefing generator tests
- GitHub Actions CI for backend tests, frontend tests, frontend lint, and frontend production build
- Docker Compose setup for running frontend and backend locally
- Backend CORS configuration through `ALLOWED_ORIGINS`
- Backend response schemas for RecallRadar and DrugSignal API responses
- Request ID middleware with production-verified `X-Request-ID` response headers
- Top-level audit metadata including source endpoint and score version
- Environment-based frontend API URL configuration
- Environment-based backend database configuration

Current backend test status:

```bash
45 passed
```

Current frontend test status:

```bash
27 passed
```

Recent stability improvements:

- No-match openFDA searches now return `count: 0` and `results: []` instead of a false backend error.
- RecallRadar now displays a clear empty-state message when no FDA recall records match.
- DrugSignal now displays a clear empty-state message when no FAERS records match.
- Recall scoring now uses timezone-aware UTC dates.
- RecallRadar route responses now use backend Pydantic schemas.
- Audit metadata now includes top-level source endpoint and score version.
- Source metadata is centralized through a backend source registry.
- Sources are exposed through `GET /api/v1/sources`.
- openFDA client behavior is tested with mocked HTTP responses.
- Query validation is tested for short queries and invalid limits.
- DrugSignal backend endpoint returns top reported FAERS reactions with a causation disclaimer.
- DrugSignal frontend page is connected to the tested backend endpoint.
- DrugSignal reaction counts are displayed with relative visual bars.
- API responses now include compact audit summaries while full audit-event construction remains internal.
- Compact audit summaries are now visible in the RecallRadar and DrugSignal UI.
- RecallRadar and DrugSignal now call the fail-soft audit repository after building audit events.
- Audit events are now persisted to Supabase/PostgreSQL after RecallRadar and DrugSignal searches.
- Safety Briefing Engine v1 now generates deterministic role-based briefings from structured RecallRadar and DrugSignal data.
- Frontend tests now cover App rendering, RecallRadar behavior, DrugSignal behavior, and briefing generator behavior.
- GitHub Actions CI is active and passing.
- Docker Compose now builds and runs the frontend and backend locally.
- Backend CORS origins are now configurable for deployment.

---

## Recall Review Score

MedTrek AI uses a transparent, rule-based **Recall Review Score** for the RecallRadar MVP.

The score is not a medical diagnosis, treatment recommendation, or official FDA replacement. It is a review-priority signal that helps users understand which public recall records may deserve closer attention.

### Current score inputs

The current score uses four public recall fields:

1. **FDA classification severity**
2. **Recall status**
3. **Recall initiation recency**
4. **Distribution scope**

### Component logic

| Component | Current logic |
|---|---|
| FDA classification | Class I receives the highest weight, followed by Class II and Class III |
| Recall status | Ongoing recalls receive more weight than completed or terminated recalls |
| Recency | Recent recalls receive more weight than older recalls |
| Distribution scope | Nationwide or multi-state distribution receives more weight than local distribution |

The backend returns both the final score and the component-level scores so the result is explainable.

Current score version:

```text
recall-risk-v0.1
```

---

## DrugSignal

DrugSignal is the second MVP module. It uses the openFDA Drug Event API to retrieve FAERS adverse-event reports for a searched drug or medicinal product.

Current DrugSignal response includes:

- Search query
- Source name
- Source endpoint
- Retrieval timestamp
- Record count
- Medical disclaimer
- FAERS causation disclaimer
- Top reported reactions from returned FAERS records
- Relative count bars for comparing reaction frequency within the returned results
- Compact audit summary for traceability
- Role-based safety briefing

Important limitation:

FAERS adverse-event reports do **not** prove that a drug caused a reaction. Reports may be incomplete, duplicated, influenced by reporting patterns, or missing clinical context. DrugSignal is a reporting-pattern explorer, not a causation engine.

---

## Safety Briefing Engine v1

Safety Briefing Engine v1 is a deterministic frontend briefing layer that turns structured RecallRadar and DrugSignal response data into role-based public-data safety briefings.

Current roles:

- Consumer
- Pharmacy
- Clinic
- Public Health / Analyst

Each briefing includes:

- Summary
- What was found
- What to verify
- Suggested review checklist
- Limitations
- Source and audit details
- Disclaimer

The briefing engine uses existing structured API response fields only, including:

- Query
- Record count
- Recall score or top FAERS reaction
- Source name
- Endpoint
- Retrieval timestamp
- Audit ID
- Medical disclaimer
- FAERS disclaimer when applicable

The current briefing engine does not use an LLM. This keeps the MVP explainable, deterministic, testable, and safer for healthcare-adjacent public-data workflows.

The briefing engine must not generate:

- Diagnosis
- Treatment guidance
- Medication-change advice
- Claims that FAERS reports prove causation
- Unsupported medical recommendations

---

## Sources Registry

MedTrek AI includes a backend source registry to make public-data usage transparent and auditable.

Current registered sources:

- openFDA Drug Enforcement API for RecallRadar
- openFDA Drug Event API for DrugSignal

Sources endpoint:

```text
GET /api/v1/sources
```

The endpoint returns each source with:

- Source ID
- Source name
- Endpoint
- Module
- Description
- Update cadence

The frontend Data Sources page consumes this endpoint and displays registered public sources, modules, endpoints, descriptions, and update cadence.

The same source metadata is also stored in the Supabase/PostgreSQL `source_registry` table as the database foundation for audit logging and future briefing traceability.

---

## Audit Architecture

MedTrek AI separates public response metadata from internal audit construction.

The backend currently supports:

- Compact audit summaries in RecallRadar and DrugSignal responses
- Frontend display of compact audit summaries in RecallRadar and DrugSignal audit panels
- Internal full audit event construction through a backend audit utility
- Fail-soft audit repository boundary
- Real PostgreSQL persistence into the `audit_events` table
- Audit event tests for standard success and error shapes
- Repository tests for skipped, saved, and fail-soft error outcomes

The compact public audit summary includes:

- Audit ID
- Source ID
- Module
- Upstream status
- Record count
- Transform version

The internal audit event builder additionally supports:

- Source name
- Endpoint
- Query parameters
- Retrieval timestamp
- Score version
- Disclaimer version
- Error message
- Created timestamp

The routes build full audit events and pass them through a fail-soft audit repository boundary. Audit events are now saved to the `audit_events` PostgreSQL table through Supabase connection pooling. If database persistence fails, the search workflow still returns a normal response while the persistence error is handled internally.

This design avoids coupling the frontend to database persistence internals while keeping the backend ready for future saved monitors, role-specific briefings, and deployment traceability.

---

## Persistence

MedTrek AI now includes working Supabase/PostgreSQL audit persistence.

Current persistence support includes:

- `docs/persistence_plan.md`
- `backend/.env.example`
- `backend/db/schema.sql`
- database configuration helper
- fail-soft audit repository
- live inserts into the `audit_events` table
- source metadata stored in the `source_registry` table
- Supabase connection pooling for local PostgreSQL access
- local `DATABASE_URL` loading through `backend/.env`

The current persistence layer stores:

- Source ID
- Source name
- Endpoint
- Module
- Search query
- Query parameters
- Retrieval timestamp
- Upstream status
- Record count
- Transform version
- Score version when applicable
- Disclaimer version
- Error message when applicable
- Created timestamp

The current persistence layer does **not** store:

- Personal health records
- Patient identifiers
- Medication profiles tied to real users
- Uploaded documents
- Uploaded images
- Private medical notes
- User accounts or authentication records

Database credentials must be stored only in local or deployment environment variables. Do not commit real credentials to GitHub.

---

## Safety Boundary

MedTrek AI provides public-data safety intelligence only. It is not medical advice, diagnosis, or treatment.

The app does not:

- Diagnose medical conditions
- Recommend medication changes
- Replace FDA, CDC, clinician, pharmacist, or emergency guidance
- Claim that public safety reports prove causation

Users should verify source records and consult qualified healthcare professionals for medical decisions.

---

## Tech Stack

### Frontend

- React
- TypeScript
- Vite
- CSS files
- Axios
- Vitest
- React Testing Library

### Backend

- FastAPI
- Uvicorn
- httpx
- Pydantic
- pytest
- python-dotenv
- psycopg

### Public Data Sources

- openFDA Drug Enforcement API
- openFDA Drug Event API

### Persistence

- Supabase PostgreSQL
- SQL schema for source registry and audit events
- Supabase transaction pooler connection
- Fail-soft audit persistence repository

### CI/CD

- GitHub Actions
- Backend pytest job
- Frontend test job
- Frontend lint job
- Frontend production build job

### Local Containerization

- Docker
- Docker Compose
- Backend Dockerfile
- Frontend Dockerfile

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

Current backend endpoints:

```text
GET /api/v1/recalls/search
GET /api/v1/drug-events/search
GET /api/v1/sources
```

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

Use `frontend/.env.example` as the reference file for local configuration.

### Backend environment configuration

```env
DATABASE_URL=postgresql://username:password@host:port/database
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

For Supabase local development, use the Supabase transaction pooler connection string in `backend/.env`.

Use `backend/.env.example` as the reference file for future database configuration. Do not commit real credentials.

---

## Docker Local Development

MedTrek AI can also run locally with Docker Compose.

From the repository root:

```bash
docker compose up --build
```

This starts:

- FastAPI backend container
- React/Vite frontend container

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

Do not commit real `.env` files or secrets to GitHub. Use `.env.example` files as references.

---

## Deployment Environment Notes

MedTrek AI is designed to deploy as separate frontend and backend services.

Recommended MVP deployment path:

```text
Frontend: Vercel
Backend: Render or Railway
Database: Supabase PostgreSQL
```

### Backend environment variables

The backend requires:

```env
DATABASE_URL=postgresql+psycopg://username:password@host:5432/database
ALLOWED_ORIGINS=https://your-frontend-domain.vercel.app
```

`DATABASE_URL` should point to the Supabase PostgreSQL connection string.

`ALLOWED_ORIGINS` should contain the deployed frontend URL. For multiple allowed origins, use a comma-separated list:

```env
ALLOWED_ORIGINS=http://localhost:5173,https://your-frontend-domain.vercel.app
```

Do not commit real database credentials or production secrets to GitHub.

### Frontend environment variables

The frontend requires:

```env
VITE_API_BASE_URL=https://your-backend-domain.onrender.com
```

For local development, use:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### Production safety notes

Before public deployment:

- Verify `/health` returns `{"status":"healthy"}`.
- Verify `/docs` loads correctly.
- Confirm RecallRadar and DrugSignal searches work from the deployed frontend.
- Confirm Supabase audit rows are created after successful searches.
- Confirm CORS only allows trusted frontend origins.
- Confirm no real `.env` files or secrets are committed.

---

## Testing

Run backend tests:

```bash
cd backend
pytest
```

Current backend test coverage includes:

- Recall Review Score behavior
- Successful RecallRadar route response
- Empty-result RecallRadar route response
- RecallRadar upstream failure handling
- RecallRadar query validation for short queries and invalid limits
- Compact RecallRadar audit summary behavior
- openFDA Drug Enforcement client success behavior
- openFDA Drug Enforcement client no-match behavior
- openFDA Drug Enforcement client server-error behavior
- Successful DrugSignal route response
- Empty-result DrugSignal route response
- DrugSignal upstream failure handling
- DrugSignal query validation for short queries and invalid limits
- Compact DrugSignal audit summary behavior
- openFDA Drug Event client success behavior
- openFDA Drug Event client no-match behavior
- openFDA Drug Event client server-error behavior
- Sources endpoint response and required metadata tests
- Audit event builder success and error shape tests
- Database configuration helper tests
- Fail-soft audit repository tests for skipped, saved, and error outcomes

Current backend test status:

```bash
45 passed
```

Run frontend tests:

```bash
cd frontend
npm test
```

Current frontend test coverage includes:

- App smoke rendering
- RecallRadar component behavior
- DrugSignal component behavior
- Safety briefing generator behavior

Current frontend test status:

```bash
27 passed
```

Run frontend lint and production build:

```bash
cd frontend
npm run lint
npm run build
```

---

## Manual Persistence Verification

Manual Supabase/PostgreSQL verification completed successfully.

Verified persisted audit rows include:

- Manual backend audit event insert
- RecallRadar search audit event
- DrugSignal search audit event

Expected rows appear in the Supabase `audit_events` table with module, source ID, query, upstream status, record count, transform version, score version when applicable, and disclaimer version.

---

## Planned Next Phases

1. Keep RecallRadar, DrugSignal, Safety Briefing Engine v1, and Audit History stable and documented
2. Add database migration strategy
3. Prepare frontend/backend deployment
4. Add saved searches or alert-monitoring workflows
5. Add scheduled ingestion and change detection history
6. Add optional NLP, RAG, and OCR/CNN experiments later
7. Add production observability and security hardening

---

## Project Direction

MedTrek AI should remain focused on healthcare safety intelligence, public-data signal monitoring, source transparency, auditability, and role-based decision support.

It should not become a generic weather app, generic chatbot, or broad unfocused dashboard.

### Audit History

MedTrek AI includes an Audit History workflow for reviewing recent public-data searches.

The backend exposes:

- `GET /api/v1/audit-events`
- `GET /api/v1/audit-events/{audit_id}`

The frontend includes an `Audit` navigation tab where recent audit events can be reviewed in a table with selected event details.

Audit History shows source and transformation metadata such as audit ID, module, source name, endpoint, query parameters, retrieval timestamp, upstream status, record count, transform version, score version, disclaimer version, and error messages when present.

This is public-data traceability only. It is not PHI storage, not clinical record storage, and not medical advice.
## Manual Saved Monitors v1

MedTrek AI supports a manual saved-monitor workflow using existing RecallRadar, DrugSignal, source metadata, audit history, and safety briefing features.

A reviewer can repeat the same product or drug search over time, record the score, record count, source timestamp, audit ID, and briefing output, then compare future results against previous checks.

This validates the Saved Monitors product direction before backend automation, scheduled refresh, and alerting are implemented.
