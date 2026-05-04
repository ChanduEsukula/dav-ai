# MedTrek AI Frontend

This is the React + TypeScript + Vite frontend for MedTrek AI.

MedTrek AI is a healthcare safety intelligence product prototype that turns public FDA/openFDA recall and adverse-event data into source-aware, auditable safety signals and role-based safety briefings.

The current frontend supports:

- RecallRadar
- DrugSignal
- Safety Briefing Engine v1
- Data Sources page
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

The landing page explains the MedTrek AI product idea, public-data safety intelligence focus, and current MVP modules.

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
- Source metadata
- Audit details
- FAERS causation disclaimer
- Medical safety disclaimer
- Role-based safety briefing

Important: FAERS reports are reporting patterns only. They do not prove causation.

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
- Safety briefing generator tests

Current local frontend status:

```bash
20 passed
npm run lint
npm run build
```

GitHub Actions also runs frontend tests, lint, and production build on push and pull request.

---

## Safety Boundary

MedTrek AI provides public-data safety intelligence only.

It is not medical advice, diagnosis, or treatment. Users should consult a qualified healthcare professional for medical decisions.