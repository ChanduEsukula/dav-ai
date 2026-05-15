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
- Current migration revision: `20260514_0004`
- Latest saved monitor run-history migration applied: `20260514_0003_create_saved_monitor_runs.py`
- Latest saved monitor scheduled-refresh foundation migration applied: `20260514_0004_add_saved_monitor_schedule_fields.py`

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
- Saved Monitor Run History v2.2 smoke flow passed.
- Saved Monitor Scheduled Refresh Foundation v2.3 smoke flow passed.

Live backend verification details:

- `database.configured`: true
- `database.audit_readable`: true
- `source_registry_count`: 2
- `recent_audit_count`: 25
- `upstream_status_counts` included `success` and `empty`, with `error` at 0 at the time of test
- Live source IDs were correct:
  - `openfda_drug_enforcement`
  - `openfda_drug_event`

### Saved Monitor Run History v2.2

Commit `811d7d4` implemented Saved Monitor Run History. Live backend smoke verification passed for the deployed Render backend.

Verified flow:

- `GET /api/v1/saved-monitors` returned `200` and initially `[]`.
- `POST /api/v1/saved-monitors` created a temporary smoke monitor.
- `POST /api/v1/saved-monitors/{monitor_id}/run` returned `200`.
- `GET /api/v1/saved-monitors/{monitor_id}/runs` returned `200` with a persisted run-history row.
- `DELETE /api/v1/saved-monitors/{monitor_id}` returned `204`.
- `GET /api/v1/saved-monitors` returned `200` and `[]` after cleanup.

The smoke run-history row had:

- `status`: `success`
- `record_count`: `0`
- `audit_id`: present
- `error_message`: `null`

This verified saved-monitor run-history persistence and endpoint behavior. It did not verify clinical correctness.

### Saved Monitor Scheduled Refresh Foundation v2.3

Commit `d8a6df4` added the backend-only scheduled refresh foundation for Saved Monitors.

Verified after deployment:

- Production backend `/health` returned `200`.
- Production `/api/v1/system/status` returned `200`.
- Production `/api/v1/saved-monitors` returned `200` with `[]`.
- Alembic current revision confirmed `20260514_0004 (head)`.
- Local CLI smoke against the configured database returned `status: ok` and `due_count: 0`.

This confirms the scheduled refresh foundation is wired safely, but production scheduling is not enabled yet. No Render Cron, alerts, auth/RBAC, or public scheduling UI were added.

### Frontend

- Vercel frontend loaded successfully.
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

- Set Vercel `VITE_API_BASE_URL` to `https://medtrek-ai.onrender.com`.
- Set Render `ALLOWED_ORIGINS` to include `https://medtrek-ai.vercel.app` and `http://localhost:5173`.
- Corrected Render `DATABASE_URL` value so it contains only the PostgreSQL connection string, not the `DATABASE_URL=` prefix.
- Applied Alembic migration `20260514_0003_create_saved_monitor_runs.py`.
- Applied Alembic migration `20260514_0004_add_saved_monitor_schedule_fields.py`.
- Rotated the Supabase database password after accidental exposure.
- Updated Render `DATABASE_URL` after password rotation.
- Redeployed the backend after credential rotation.
- Verified `/health`, `/api/v1/system/status`, `/api/v1/system/data-quality`, and `/api/v1/saved-monitors` after migration and redeploy.

## Security Follow-Up Status

Completed: the exposed Supabase database password was rotated, Render `DATABASE_URL` was updated, and the backend was redeployed successfully.

Do not include old or new database URLs, passwords, or connection strings in docs, logs, tickets, screenshots, prompts, terminal output, or copied troubleshooting notes.

## Current Status

MedTrek AI is deployed end-to-end with live public FDA data, role-based safety briefings, source metadata, audit history, PostgreSQL persistence, Saved Monitors v2.2 manual monitoring, saved monitor run history, Saved Monitors v2.3 scheduled-refresh foundation, and API documentation.

Remaining production-readiness gaps include:

- No auth/RBAC.
- No production scheduler or Render Cron enabled yet.
- No alerts.
- No public scheduling UI.
- No scheduled run-history workflow beyond the backend-only CLI foundation.
- No raw payload hashing.
- No immutable audit/retention policy.
- No production observability dashboard/SLOs.