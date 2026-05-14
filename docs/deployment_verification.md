# MedTrek AI Deployment Verification

## Verified Deployment URLs

- Frontend: https://medtrek-ai.vercel.app
- Backend: https://medtrek-ai.onrender.com
- Backend health check: https://medtrek-ai.onrender.com/health
- Backend API docs: https://medtrek-ai.onrender.com/docs

## Verified Stack

- Frontend host: Vercel
- Backend host: Render
- Database: Supabase PostgreSQL
- Migration tool: Alembic
- Current migration revision: `20260514_0003`

## Live Smoke Tests Passed

This confirms deployment smoke verification only. It does not mean MedTrek AI is production-ready healthcare software.

### Backend

- `GET /health` returned `200` healthy.
- `GET /api/v1/sources` returned `200` with 2 sources.
- `GET /api/v1/recalls/search?q=eye%20drops&limit=5` returned `200`.
- `GET /api/v1/drug-events/search?q=metformin&limit=5` returned `200`.
- `GET /api/v1/audit-events?limit=10` returned `200`.
- `GET /api/v1/system/status` returned `200`.
- `GET /api/v1/system/data-quality` returned `200`.
- `GET /api/v1/saved-monitors` returned `200`.

Live backend verification details:

- `database.configured`: true.
- `database.audit_readable`: true.
- `source_registry_count`: 2.
- `recent_audit_count`: 25.
- `upstream_status_counts` included `success` and `empty`, with `error` at 0 at the time of test.
- Live source IDs were correct:
  - `openfda_drug_enforcement`
  - `openfda_drug_event`

### Frontend

- Vercel frontend loaded successfully
- RecallRadar search for `eye drops` worked.
- Source/audit details were visible.
- Role-based briefing was visible.
- DrugSignal search for `metformin` worked.
- Score, reactions, reaction categories, and trend snapshot were visible.
- Sources page loaded.
- Audit page loaded recent events.
- System/Data Quality page loaded.
- Monitors page loaded.

## Deployment Fixes Applied

- Set Vercel `VITE_API_BASE_URL` to `https://medtrek-ai.onrender.com`
- Set Render `ALLOWED_ORIGINS` to include `https://medtrek-ai.vercel.app` and `http://localhost:5173`
- Corrected Render `DATABASE_URL` value so it contains only the PostgreSQL connection string, not the `DATABASE_URL=` prefix

## Security Follow-Up

Open unless confirmed completed: the Supabase database password should be rotated because it was exposed during deployment troubleshooting. After rotation, update Render `DATABASE_URL` and redeploy the backend.

## Current Status

MedTrek AI is deployed end-to-end with live public FDA data, role-based safety briefings, source metadata, audit history, PostgreSQL persistence, Saved Monitors v2.2 manual monitoring, and API documentation.

Remaining production-readiness gaps include no auth/RBAC, no scheduled monitor refresh, no alerts, no scheduled run-history workflow beyond manual runs, no raw payload hashing, no immutable audit/retention policy, and no production observability dashboard/SLOs.
