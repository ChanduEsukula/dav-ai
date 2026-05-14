# MedTrek AI Deployment Checklist

## Goal

Prepare MedTrek AI for a clean frontend/backend/database deployment without changing product behavior.

## Current Local Baseline

- Backend tests: 79 passed
- Frontend tests: 54 passed
- Frontend lint: passed
- Frontend production build: passed
- Alembic current revision: `20260514_0003`
- Core workflows verified locally: RecallRadar, DrugSignal, Audit History, Saved Monitors v2.2
- Demo script available: `docs/demo_script.md`

## Backend Deployment Requirements

- Host: Render, Railway, or Fly.io
- Runtime: Python 3.13
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --app-dir backend`
- Required environment variables: `DATABASE_URL`, `ALLOWED_ORIGINS`
- Health check endpoint: `/health`

## Database Requirements

- Host: Supabase PostgreSQL
- Migration tool: Alembic
- New database setup command: `alembic upgrade head`
- Existing manually-created database command: `alembic stamp head`
- MVP database must not store PHI, patient identifiers, diagnosis history, treatment history, personal medication profiles, uploaded medical documents, or private health notes.

## Frontend Deployment Requirements

- Host: Vercel or Netlify
- Build command: `npm run build`
- Frontend directory: `frontend`
- Required environment variable: `VITE_API_BASE_URL` pointing to deployed backend URL

## Pre-Deployment Checks

Run backend checks from repository root:

```bash
cd backend
source .venv/bin/activate
python -m pytest
```

Run frontend checks from `frontend/`:

```bash
npm test
npm run lint
npm run build
```

## Post-Deployment Smoke Test

1. Open deployed frontend URL
2. Search RecallRadar for `eye drops`
3. Search DrugSignal for `aspirin`
4. Open Audit History
5. Confirm latest audit rows appear
6. Confirm source metadata and safety boundary are visible
7. Confirm Saved Monitors can create, list, manually run, compare latest/previous values, and link to Audit History

## Do Not Deploy Yet If

- Backend tests fail
- Frontend tests fail
- Frontend build fails
- `DATABASE_URL` is missing
- `ALLOWED_ORIGINS` does not include deployed frontend URL
- Audit History cannot read persisted events

## Next Engineering Decision

After this checklist is committed, choose either actual deployment setup or observability improvements. Do not start Regional Health Pulse, EnviroHealth, OCR/CNN, RAG, auth, or payments until the core deployed demo is stable.
