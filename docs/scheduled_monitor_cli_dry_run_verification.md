# Scheduled Monitor CLI Dry-Run Verification

## Date

May 15, 2026

## Purpose

This document records manual dry-run verification for the Saved Monitor scheduled-refresh CLI foundation.

Production Cron remains disabled. This verification confirms that the backend CLI entrypoint runs safely from the backend service context, applies limit guardrails correctly, emits a traceable `job_run_id` for scheduler observability, and now runs with DB-backed scheduler locking when the configured database includes `scheduler_locks`.

## Commands Run

From the backend directory:

```bash
cd /Users/chanduesukula/medtrek-ai/backend
source ../.venv/bin/activate
python -m app.jobs.run_due_saved_monitors --limit 10
python -m app.jobs.run_due_saved_monitors --limit 0
python -m app.jobs.run_due_saved_monitors --limit 999
```

Current manual verification command:

```bash
cd /Users/chanduesukula/medtrek-ai/backend
python -m app.jobs.run_due_saved_monitors --limit 10
```

## Results

### Normal Limit

Command:

```bash
python -m app.jobs.run_due_saved_monitors --limit 10
```

Observed result after adding `job_run_id` support:

```json
{
  "attempted_count": 0,
  "due_count": 0,
  "error_count": 0,
  "job_run_id": "scheduled-refresh-20260515-184620-6e8d1fe3",
  "job_started_at": "2026-05-15T18:46:20.326143+00:00",
  "requested_limit": 10,
  "run_ids": [],
  "safe_limit": 10,
  "skipped_count": 0,
  "status": "ok",
  "success_count": 0
}
```

### Minimum Guardrail

Command:

```bash
python -m app.jobs.run_due_saved_monitors --limit 0
```

Observed result:

```json
{
  "attempted_count": 0,
  "due_count": 0,
  "error_count": 0,
  "job_started_at": "2026-05-15T17:46:59.977351+00:00",
  "requested_limit": 0,
  "run_ids": [],
  "safe_limit": 1,
  "skipped_count": 0,
  "status": "ok",
  "success_count": 0
}
```

### Maximum Guardrail

Command:

```bash
python -m app.jobs.run_due_saved_monitors --limit 999
```

Observed result:

```json
{
  "attempted_count": 0,
  "due_count": 0,
  "error_count": 0,
  "job_started_at": "2026-05-15T17:47:00.673752+00:00",
  "requested_limit": 999,
  "run_ids": [],
  "safe_limit": 50,
  "skipped_count": 0,
  "status": "ok",
  "success_count": 0
}
```

## Verification Summary

The CLI entrypoint ran successfully from the backend service context.

Verified behavior:

- `--limit 10` preserved `safe_limit: 10`.
- `--limit 0` clamped to `safe_limit: 1`.
- `--limit 999` clamped to `safe_limit: 50`.
- JSON summaries included `requested_limit` and `safe_limit`.
- JSON summaries now include a traceable `job_run_id`.
- No due monitors were found during this dry run.
- No monitor runs were attempted.
- No alerts or notifications were sent.
- Production Cron was not enabled.

Additional scheduler-lock verification has since confirmed:

- DB-backed scheduler locks are implemented through the `scheduler_locks` table.
- Alembic migration `20260519_0005_create_scheduler_locks.py` creates the lock table.
- Backend tests isolate the real `DATABASE_URL` by default through `backend/tests/conftest.py`.
- A real temporary due DrugSignal saved monitor for `aspirin` ran successfully through the CLI.
- A `saved_monitor_runs` row was created.
- `scheduler_locks` was empty after the job, confirming lock release.
- Temporary monitor rows were cleaned up.

## Current Status

The scheduled-refresh CLI foundation is verified for no-due-monitor dry-run behavior, limit guardrails, traceable job-run IDs, DB-backed scheduler lock acquisition/release, and real due-monitor execution against a temporary DrugSignal monitor.

This does not enable or verify production recurring execution, alerting, monitor ownership, production scheduler observability, public scheduling UI, auth/RBAC, notification preferences, or alert delivery.

## Do Not Enable Production Cron Until

Before enabling recurring production Cron, the project still needs:

- Target deployment environment verification of DB-backed scheduler locking.
- Better scheduler observability.
- Searchable job/run IDs in production logs.
- Clear rollback instructions.
- Auth/RBAC and monitor ownership design.
- Alerting and notification preferences designed separately from scheduled execution.
