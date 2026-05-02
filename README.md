# MedSignal AI

**Healthcare safety intelligence from public FDA signals.**

MedSignal AI is a full-stack healthcare safety intelligence prototype that turns public recall and adverse-event data into source-aware, explainable safety signals. The current product foundation includes **RecallRadar**, a live FDA recall search workflow powered by the openFDA Drug Enforcement API, and **DrugSignal**, a public FAERS adverse-event reporting pattern explorer powered by the openFDA Drug Event API.

This project is designed as a serious full-stack AI/data product prototype, not a static student demo.

---

## Current MVP: RecallRadar and DrugSignal

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

RecallRadar and DrugSignal are now both connected end-to-end through the React frontend and FastAPI backend. Briefing Engine, saved monitors, database persistence, and deployment are planned future phases.

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
- Source-aware audit panels
- Compact audit summaries in RecallRadar and DrugSignal API responses
- Internal audit event builder utility for future persistence
- Medical safety disclaimers
- FAERS causation disclaimer for DrugSignal
- Empty-result handling for searches with no FDA recall matches
- Empty-result handling for searches with no FAERS drug-event matches
- DrugSignal frontend page using the openFDA Drug Event API
- DrugSignal backend module using the openFDA Drug Event API
- DrugSignal top reported reactions display with relative count bars
- DrugSignal backend tests for route behavior, query validation, and openFDA client behavior
- Backend unit tests for recall scoring
- Backend route tests for success, empty-result, upstream failure, and query validation
- openFDA client tests for success, no-match, and server-error behavior
- Backend tests for the source registry endpoint
- Backend tests for audit event construction
- Backend response schemas for RecallRadar, DrugSignal, Sources, and Audit API objects
- Top-level audit metadata including source endpoint and score version
- Environment-based frontend API URL configuration
- Clean frontend/backend project structure

### Not built yet

- Database or Supabase persistence
- User accounts
- Saved searches or alerts
- Persistent audit logs
- AI Briefing Engine
- Frontend tests
- CI/CD pipeline
- Docker setup
- Production deployment

---

## Current Engineering Status

RecallRadar and DrugSignal are the active end-to-end MVP modules.

Current support includes:

- Live openFDA Drug Enforcement recall search
- Live openFDA Drug Event adverse-event search
- Public source registry endpoint for source transparency
- Frontend Data Sources page for registered public data sources
- Normalized RecallRadar result cards
- DrugSignal top reported reactions display with relative count bars
- Transparent rule-based Recall Review Score
- Compact audit summaries in RecallRadar and DrugSignal API responses
- Internal full audit event builder utility for future database persistence
- Source metadata and retrieval timestamps
- Medical safety disclaimer
- FAERS causation disclaimer for DrugSignal
- Empty-result handling for searches with no FDA matches
- DrugSignal empty-state UI for searches with no FAERS matches
- Backend scoring tests
- Audit event builder tests
- RecallRadar route tests for success, empty-result, upstream failure, and query validation
- DrugSignal route tests for success, empty-result, upstream failure, and query validation
- Sources endpoint response and required metadata tests
- openFDA Drug Enforcement client tests for success, no-match, and server-error behavior
- openFDA Drug Event client tests for success, no-match, and server-error behavior
- Backend response schemas for RecallRadar and DrugSignal API responses
- Top-level audit metadata including source endpoint and score version
- Environment-based frontend API URL configuration

Current backend test status:

```bash
26 passed
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

---

## Recall Review Score

MedSignal AI uses a transparent, rule-based **Recall Review Score** for the RecallRadar MVP.

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

Important limitation:

FAERS adverse-event reports do **not** prove that a drug caused a reaction. Reports may be incomplete, duplicated, influenced by reporting patterns, or missing clinical context. DrugSignal is a reporting-pattern explorer, not a causation engine.

---

## Sources Registry

MedSignal AI includes a backend source registry to make public-data usage transparent and auditable.

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

This is the foundation for future source transparency, audit logs, saved monitors, and briefing traceability.

---

## Audit Architecture

MedSignal AI separates public response metadata from internal audit construction.

The backend currently supports:

- Compact audit summaries in RecallRadar and DrugSignal responses
- Internal full audit event construction through a backend audit utility
- Audit event tests for standard success and error shapes

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

This design avoids coupling the frontend to future persistence internals while preparing the backend for Supabase/PostgreSQL audit logging later.

---

## Safety Boundary

MedSignal AI provides public-data safety intelligence only. It is not medical advice, diagnosis, or treatment.

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

### Backend

- FastAPI
- Uvicorn
- httpx
- Pydantic
- pytest

### Public Data Sources

- openFDA Drug Enforcement API
- openFDA Drug Event API

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

Current backend test status:

```bash
26 passed
```

Run frontend production build:

```bash
cd frontend
npm run build
```

---

## Planned Next Phases

1. Add frontend display of compact audit summaries for RecallRadar and DrugSignal
2. Add richer frontend loading and error states
3. Add frontend tests for RecallRadar and DrugSignal states
4. Add persistent audit trail
5. Add Supabase/PostgreSQL persistence
6. Build role-specific Safety Briefing Engine
7. Add CI/CD with GitHub Actions
8. Add Docker setup
9. Deploy frontend and backend
10. Add optional NLP, RAG, and OCR/CNN experiments later

---

## Project Direction

MedSignal AI should remain focused on healthcare safety intelligence, public-data signal monitoring, source transparency, and role-based decision support.

It should not become a generic weather app, generic chatbot, or broad unfocused dashboard.