# Dav AI Frontend

This is the React + TypeScript + Vite frontend for Dav AI.

Dav AI is a healthcare safety intelligence product prototype that turns public FDA/openFDA recall and adverse-event data into source-aware, auditable safety signals and role-based safety briefings.

The current frontend supports:

- RecallRadar
- DrugSignal
- Safety Briefing Engine v1
- Data Sources page
- Audit History page
- System Status / Data Quality page
- Saved Monitors v2 foundation
- Request ID propagation through the shared Axios client
- About / FAQ / placeholder support pages
- Frontend tests with Vitest and React Testing Library

---

## Frontend Stack

- React
- TypeScript
- Vite
- Axios
- Vitest
- React Testing Library
- CSS organized by component/page

---

## Current Frontend Features

### Landing Page

The landing page explains the Dav AI product idea, public-data safety intelligence focus, and current MVP modules.

### RecallRadar

RecallRadar allows users to search public FDA/openFDA Drug Enforcement recall records and view:

- Matched recall records
- Product descriptions
- Recall reasons
- FDA classification
- Recall status
- Recall initiation date
- Recalling firm
- Distribution pattern
- Transparent Recall Review Score
- Source metadata
- Audit details
- Medical safety disclaimer
- Role-based safety briefing

### DrugSignal

DrugSignal allows users to search public openFDA Drug Event / FAERS records and view:

- Top reported reaction terms
- Relative reaction-count bars
- Record count
- DrugSignal Intelligence Score v1
- Signal strength, review priority, data confidence, and top reaction concentration
- Reaction Classification v1
- DrugSignal Trend Snapshot v1
- Source metadata
- Audit details
- FAERS causation disclaimer
- Medical safety disclaimer
- Role-based safety briefing

Important: FAERS adverse-event reports are reporting patterns only. They do not prove that a drug caused a reaction.

### Safety Briefing Engine v1

The frontend includes a deterministic Safety Briefing Engine v1.

It generates role-based briefings for:

- Consumer
- Pharmacy
- Clinic
- Public Health / Analyst

Briefings are generated from structured RecallRadar and DrugSignal response data only. They do not use an LLM yet.

Each briefing includes:

- Summary
- What was found
- What to verify
- Suggested review checklist
- Limitations
- Source and audit details
- Disclaimer

The briefing engine must not provide diagnosis, treatment guidance, medication-change advice, or FAERS causation claims.

### Data Sources Page

The Data Sources page displays registered public data sources from the backend source registry endpoint.

Current source categories include:

- openFDA Drug Enforcement API
- openFDA Drug Event API

### Audit History

The Audit History page displays recent persisted public-data audit events when backend audit persistence is configured.

Current Audit History UI support includes:

- Recent audit event table
- Selected audit detail panel
- Module/status/search filters
- Applied filter summary
- CSV export
- Copy audit ID
- Copy trace summary
- Copy audit link
- Audit detail URL state

Audit History is for public-data traceability only. It is not clinical record storage.

### System Status / Data Quality

The System Status page provides operational transparency into the backend and audit persistence state.

Current System Status / Data Quality UI support includes:

- Backend API status
- Database configured status
- Audit readable status
- Registered source count
- Recent audit count
- Upstream status counts
- Latest audit event summary when available

This is operational transparency, not a full production observability dashboard with alerts, SLOs, or metrics dashboards.

### Saved Monitors

The Saved Monitors page is a v2 foundation for repeatable public-data searches.

Current Saved Monitors UI support includes:

- Create repeatable RecallRadar or DrugSignal monitor definitions
- List saved monitors
- Delete saved monitors
- Manually run a monitor check
- Show latest score, record count, last checked timestamp, and latest audit link when available

Saved Monitors is not yet scheduled monitoring or alerting. It does not yet include authentication/RBAC, scheduled refresh, automated notifications, or briefing history.

### Request ID Propagation

The shared Axios API client attaches an `X-Request-ID` header to outgoing backend requests. This helps connect frontend actions with backend request logs and response headers during debugging.

---

## Backend Requirement

The frontend expects the FastAPI backend to run locally at:

```text
http://127.0.0.1:8000
```

This can be overridden with:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

---

## Test Status

Current frontend test coverage includes:

- App smoke test
- RecallRadar component tests
- DrugSignal component tests
- Audit History component tests
- System Status / Data Quality component tests
- Safety briefing generator tests

Saved Monitors frontend tests should be added as the v2 foundation matures.

Current local frontend status:

```bash
27 passed
npm run lint
npm run build
```

GitHub Actions also runs frontend tests, lint, and production build on push and pull request.

---

## Safety Boundary

Dav AI provides public-data safety intelligence only.

It is not medical advice, diagnosis, or treatment. Users should consult a qualified healthcare professional for medical decisions.
