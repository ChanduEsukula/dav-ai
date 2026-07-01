# DAV AI Deployment Verification

> Historical checkpoint note: This document describes DAV AI at an earlier project stage. It is retained for project history and may not reflect the current implementation. For current scope, architecture, and implemented/partial/future boundaries, see [README.md](../README.md) and [docs/current_architecture_overview.md](current_architecture_overview.md).

## Verified Deployment URLs

- Frontend: $DAV_AI_FRONTEND_URL
- Backend: $DAV_AI_BACKEND_URL
- Backend health check: $DAV_AI_BACKEND_URL/health
- Backend API docs: $DAV_AI_BACKEND_URL/docs

## Verified Stack

- Frontend host: Vercel
- Backend host: Render
- Database: Supabase PostgreSQL
- Migration tool: Alembic
- Current migration revision: `20260519_0005`
- Latest saved monitor run-history migration applied: `20260514_0003_create_saved_monitor_runs.py`
- Latest saved monitor scheduled-refresh foundation migration applied: `20260514_0004_add_saved_monitor_schedule_fields.py`
- Latest saved monitor scheduler-lock migration applied: `20260519_0005_create_scheduler_locks.py`

---

## Deployment Verification After Scheduler Lock and Saved Monitors v2.6 Updates

Date: 2026-05-19

Verified latest deployed versions after scheduler-lock, test-isolation, documentation, and frontend-copy updates.

### Backend Render Verification

Render backend service was verified live after deployment.

Latest relevant backend/docs deployment observed:

- `256dd2a docs: update scheduler lock and saved monitor status`

Verified deployed backend URLs:

- `GET /health`
- `GET /docs`
- `GET /api/v1/system/status`
- `GET /api/v1/system/data-quality`

Observed results:

- `/health` returned `{"status":"healthy"}`.
- `/docs` loaded the FastAPI Swagger UI.
- `/api/v1/system/status` returned `status: ok`.
- `/api/v1/system/status` confirmed database configured and audit readable.
- `/api/v1/system/status` confirmed source registry available with 2 registered sources.
- `/api/v1/system/data-quality` returned `status: ok`.
- `/api/v1/system/data-quality` confirmed `database_configured: true`, `audit_readable: true`, and `source_registry_count: 2`.

### Frontend Vercel Verification

Vercel frontend was verified live after deployment.

Latest frontend deployment observed:

- `f413cac fix: update saved monitors frontend scope copy`

Verified frontend URL:

- `$DAV_AI_FRONTEND_URL/?page=saved-monitors`

Observed results:

- Saved Monitors page loaded successfully.
- Page label now shows `Saved Monitors v2.6`.
- Updated scope note is live.
- Stale `Saved Monitors v2.2` label is gone.
- Stale wording that scheduled refresh is future Saved Monitors v2 work is gone.
- Current scope note now states that backend scheduler-lock protection exists while Production Cron, alert notifications, and public scheduling UI are not enabled yet.

### Saved Monitors Production Smoke Check

A temporary DrugSignal saved monitor was created and manually run from the Vercel frontend against the Render backend.

Observed results:

- Temporary monitor creation succeeded.
- Manual `Run Check` succeeded.
- Monitor status moved from `not checked` to checked state.
- Latest result showed records returned.
- Latest score and label were displayed.
- Recent manual run history was displayed.
- `View Audit` and `View run audit` actions were available.

Temporary verification monitor should be deleted after the smoke check to keep production data clean.

### Current Deployment Boundary

Production Cron remains disabled.

The deployment currently verifies:

- Render backend availability.
- Vercel frontend availability.
- Database connectivity.
- Source registry readability.
- Audit history readability.
- Saved Monitor create/run/history UI path.
- Frontend copy alignment with Saved Monitors v2.6 status.

The deployment does not yet enable:

- Render Cron scheduled execution.
- Public scheduling UI.
- Automated alerts.
- Notification preferences.
- Auth/RBAC.
- Production scheduler observability dashboard.

---

## Live Smoke Tests Passed

This confirms deployment smoke verification only. It does not mean DAV AI is production-ready healthcare software.

### Backend

- `GET /health` returned `200` healthy.
- `GET /docs` loaded FastAPI Swagger UI.
- `GET /api/v1/sources` returned `200` with 2 sources.
- `GET /api/v1/recalls/search?q=eye%20drops&limit=5` returned `200`.
- `GET /api/v1/drug-events/search?q=metformin&limit=5` returned `200`.
- `GET /api/v1/audit-events?limit=10` returned `200`.
- `GET /api/v1/system/status` returned `200`.
- `GET /api/v1/system/data-quality` returned `200`.
- `GET /api/v1/saved-monitors` returned `200`.
- Saved Monitor Run History v2.2 smoke flow passed.
- Saved Monitor Scheduled Refresh Foundation v2.3 smoke flow passed.
- Saved Monitor Scheduler Guardrails v2.4 smoke behavior passed locally.
- Saved Monitor Scheduler Locks v2.6 manual verification passed.
- Saved Monitors v2.6 frontend smoke flow passed.

Live backend verification details:

- `database.configured`: true
- `database.audit_readable`: true
- `source_registry_count`: 2
- `recent_audit_count`: 25 at the time of test
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
- Alembic current revision confirmed `20260519_0005 (head)`.
- Local CLI smoke against the configured database returned `status: ok` and `due_count: 0`.

This confirms the scheduled refresh foundation is wired safely, but production scheduling is not enabled yet. No Render Cron, alerts, auth/RBAC, or public scheduling UI were added.

### Saved Monitor Scheduler Guardrails v2.4

Commit `e4f313c` added scheduler guardrails for the backend CLI job.

Verified behavior:

- Backend tests passed with `203 passed`.
- The scheduled monitor CLI clamps requested limits to a safe range of `1` to `50`.
- The default CLI limit is `10`.
- A high requested limit such as `--limit 500` returns `safe_limit: 50`.
- CLI output includes both `requested_limit` and `safe_limit`.
- Local CLI smoke returned `status: ok`.
- Production Cron is still intentionally disabled.

This improves safety for a future Render Cron setup without enabling automated production scheduling yet.

### Saved Monitor Scheduler Locks v2.6

Commit `8c8b78f` added database-backed scheduler locks for the backend scheduled monitor refresh job.

Verified behavior:

- Migration `20260519_0005_create_scheduler_locks.py` created the `scheduler_locks` table.
- Backend tests isolate the real `DATABASE_URL` by default through `backend/tests/conftest.py`.
- Backend tests passed with `203 passed`.
- `python -m app.jobs.run_due_saved_monitors --limit 10` worked with zero due monitors.
- A real temporary due DrugSignal saved monitor for `aspirin` ran successfully.
- A `saved_monitor_runs` row was created.
- `scheduler_locks` was empty after the job, confirming lock release.
- Temporary monitor rows were cleaned up.

This confirms lock acquisition/release behavior for manual verification. Production Cron is still intentionally disabled until final deployment-environment verification, scheduler observability, and rollback guidance are complete.

### Saved Monitors v2.6 Frontend Smoke Verification

Commit `f413cac` updated the Saved Monitors frontend copy so the deployed UI matches the backend/docs status.

Verified behavior:

- Vercel production deployment was live on commit `f413cac`.
- Saved Monitors page loaded successfully at `$DAV_AI_FRONTEND_URL/?page=saved-monitors`.
- Page label showed `Saved Monitors v2.6`.
- Page description referenced manual checks, latest/previous comparison, run history, and audit events.
- Current scope note stated that backend scheduler-lock protection exists.
- Current scope note correctly stated that Production Cron, alert notifications, and public scheduling UI are not enabled yet.
- The stale `Saved Monitors v2.2` label was no longer visible.
- The stale wording that scheduled refresh was a future Saved Monitors v2 step was no longer visible.

Temporary production smoke behavior:

- A temporary DrugSignal monitor for `aspirin` was created from the Vercel frontend.
- Manual `Run Check` succeeded.
- Latest result showed returned records.
- Latest score and label were displayed.
- Recent manual run history appeared.
- `View Audit` and `View run audit` actions were available.
- Temporary verification monitor should be deleted after verification to keep production data clean.

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
- Saved Monitors v2.6 copy was visible after latest frontend deployment.
- Saved Monitor manual create/run/history path worked from the frontend.

---

## Deployment Fixes Applied

- Set Vercel `VITE_API_BASE_URL` to `$DAV_AI_BACKEND_URL`.
- Set Render `ALLOWED_ORIGINS` to include `$DAV_AI_FRONTEND_URL` and `http://localhost:5173`.
- Corrected Render `DATABASE_URL` value so it contains only the PostgreSQL connection string, not the `DATABASE_URL=` prefix.
- Applied Alembic migration `20260514_0003_create_saved_monitor_runs.py`.
- Applied Alembic migration `20260514_0004_add_saved_monitor_schedule_fields.py`.
- Applied Alembic migration `20260519_0005_create_scheduler_locks.py`.
- Rotated the Supabase database password after accidental exposure.
- Updated Render `DATABASE_URL` after password rotation.
- Redeployed the backend after credential rotation.
- Verified `/health`, `/docs`, `/api/v1/system/status`, `/api/v1/system/data-quality`, and `/api/v1/saved-monitors` after migration and redeploy.
- Verified Vercel frontend after Saved Monitors v2.6 frontend-copy update.

---

## Security Follow-Up Status

Completed: the exposed Supabase database password was rotated, Render `DATABASE_URL` was updated, and the backend was redeployed successfully.

Do not include old or new database URLs, passwords, or connection strings in docs, logs, tickets, screenshots, prompts, terminal output, or copied troubleshooting notes.

---

## Current Status

DAV AI is deployed end-to-end with live public FDA data, role-based safety briefings, source metadata, audit history, PostgreSQL persistence, Saved Monitors manual monitoring, saved monitor run history, Saved Monitors v2.3 scheduled-refresh foundation, Saved Monitors v2.4 scheduler guardrails, Saved Monitors v2.6 DB-backed scheduler locks, Saved Monitors v2.6 frontend copy alignment, and API documentation.

Remaining production-readiness gaps include:

- No auth/RBAC.
- No production scheduler or Render Cron enabled yet.
- No alerts.
- No public scheduling UI.
- No recurring scheduled run workflow beyond manual CLI verification.
- No raw payload hashing.
- No immutable audit/retention policy.
- No production observability dashboard/SLOs.

---

## Deployment Boundary

This deployment verification confirms the current MVP deployment state only.

DAV AI remains:

- A public-data safety intelligence prototype.
- Not a medical device.
- Not clinical decision support.
- Not a replacement for official FDA, CDC, clinician, pharmacist, or emergency guidance.

Production Cron should remain disabled until the deployment environment has documented scheduler observability, rollback guidance, recurring-job verification, and operational alerting expectations.
