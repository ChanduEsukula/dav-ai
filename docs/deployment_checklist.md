# DAV AI Deployment Checklist

## Goal

Prepare DAV AI for a clean frontend/backend/database deployment review without changing product behavior. This checklist does not start an actual deployment.

## Current Local Baseline

- Backend tests: 488 passed
- Frontend tests: 282 passed
- Frontend lint: passed
- Frontend production build: passed
- Playwright smoke tests: 3 passed
- Alembic target for deployment: `head`
- Core workflows to smoke after deployment: Safety Record Search, RecallRadar, DrugSignal, FoodSignal, CosmeticSignal, Audit History, Sources, System Status, and Monitors
- Current demo guide: `docs/demo/PORTFOLIO_DEMO_PACKAGE.md`

## Backend Deployment Requirements

- Host: Render, Railway, or Fly.io
- Runtime: Python 3.13
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --app-dir backend`
- Required environment variables: `DATABASE_URL`, `ALLOWED_ORIGINS`, `DAVAI_ENV=production`, `AUTH_SECRET_KEY`
- Health check endpoint: `/health`
- Render sets `RENDER=true`, which DavAI also treats as deployed mode

## Database Requirements

- Host: Supabase PostgreSQL
- Migration tool: Alembic
- New database setup command: `alembic upgrade head`
- Existing manually-created database command: `alembic stamp head`
- Do not target or document old fixed revisions for deployment; use `head`.
- MVP database must not store PHI, patient identifiers, diagnosis history, treatment history, personal medication profiles, uploaded medical documents, or private health notes.
- In deployed mode, audit event writes, source-pull snapshot writes, saved monitor repository operations, scheduler locks, and user/profile repository storage must fail closed when durable persistence is missing or unavailable.

## Frontend Deployment Requirements

- Host: Vercel or Netlify
- Build command: `npm run build`
- Frontend directory: `frontend`
- Required environment variable: `VITE_API_BASE_URL` pointing to deployed backend URL

## Pre-Deployment Checks

Run backend checks from repository root:

```bash
PYTHONPATH=backend python3 -m pytest backend/tests -q
```

Run frontend checks from `frontend/`:

```bash
cd frontend
npm run lint
npm test -- --run
npm run build
npx playwright test
```

## Post-Deployment Smoke Test

1. Open deployed frontend URL
2. Open `/health` on the deployed backend
3. Search Safety Record Search for `air fryer`
4. Search RecallRadar for `eye drops`
5. Search DrugSignal for `aspirin`
6. Open Audit History
7. Confirm latest audit rows appear
8. Confirm source metadata, source-pull provenance, payload hashes where available, and safety boundaries are visible
9. Confirm Monitors can create, list, manually run, compare latest/previous values, and link to Audit History
10. Confirm provenance persistence failures are reported as persistence-specific `503` responses rather than upstream/public-source failure labels

## Do Not Deploy Yet If

- Backend tests fail
- Frontend tests fail
- Frontend build fails
- `DATABASE_URL` is missing
- `ALLOWED_ORIGINS` does not include deployed frontend URL
- `DAVAI_ENV=production` or equivalent deployed-mode detection is missing
- `AUTH_SECRET_KEY` is missing
- Audit History cannot read persisted events
- source-pull provenance cannot be written/read where expected
- scheduler-lock persistence is not verified in the target environment

## Next Engineering Decision

After this checklist is current, choose either actual deployment setup or observability improvements. Do not start new product features, public scheduling UI, alert delivery, RAG, OCR/CNN expansion, or payments until the core deployed demo is stable. Prototype/demo auth exists, but production RBAC and tenancy remain future work.
