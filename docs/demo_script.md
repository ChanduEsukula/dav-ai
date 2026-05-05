# MedTrek AI Demo Script

## Demo Goal

Show that MedTrek AI is a working full-stack public healthcare safety intelligence prototype with live FDA data, role-based safety briefings, source transparency, audit history, PostgreSQL persistence, and Alembic migration support.

## Start Backend

From the repository root:

```bash
cd ~/medtrek-ai
source .venv/bin/activate
uvicorn app.main:app --reload --app-dir backend
```

Expected backend URL: `http://127.0.0.1:8000`

## Start Frontend

In a second terminal:

```bash
cd ~/medtrek-ai/frontend
npm run dev
```

Expected frontend URL: `http://localhost:5173`

## Demo Flow

### RecallRadar

Search: `eye drops`

Verify that results load from openFDA Drug Enforcement API, audit metadata appears, and Safety Briefing Engine v1 generates a role-based briefing.

### DrugSignal

Search: `aspirin`

Verify that FAERS/openFDA Drug Event results load, FAERS limitation language is visible, audit metadata appears, and a safety briefing is generated.

### Audit History

Go to Audit.

Verify that persistence status shows active, recent rows include RecallRadar and DrugSignal searches, and the selected detail panel shows audit ID, module, query, source, endpoint, timestamp, upstream status, and record count.

## Safety Boundary

MedTrek AI provides public-data safety intelligence only. It is not medical advice, diagnosis, treatment guidance, a replacement for FDA/CDC/clinicians/pharmacists, or a causation engine for FAERS reports.

The MVP must not store PHI, patient identifiers, diagnosis history, treatment history, personal medication profiles, uploaded medical documents, or private health notes.

## Verified Local Status

- Backend tests: 41 passing
- Audit History API route tests added
- Frontend Audit History page tests added
- Alembic migration system added
- Existing database stamped to initial migration head: `20260505_0001`
- RecallRadar, DrugSignal, and Audit History verified end-to-end locally

## Current Best Next Engineering Step

Choose one: deployment readiness, saved monitors, or observability. Do not start Regional Health Pulse, EnviroHealth, OCR/CNN, RAG, auth, or payments until the core workflow is deployed or demo-ready.
