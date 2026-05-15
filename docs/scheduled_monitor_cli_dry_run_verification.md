# Scheduled Monitor CLI Dry-Run Verification

## Date

May 15, 2026

## Purpose

This document records manual dry-run verification for the Saved Monitor scheduled-refresh CLI foundation.

Production Cron remains disabled. This verification only confirms that the backend CLI entrypoint runs safely from the backend service context, applies limit guardrails correctly, and emits a traceable `job_run_id` for scheduler observability.

## Commands Run

From the backend directory:

```bash
cd /Users/chanduesukula/medtrek-ai/backend
source ../.venv/bin/activate
python -m app.jobs.run_due_saved_monitors --limit 10
python -m app.jobs.run_due_saved_monitors --limit 0
python -m app.jobs.run_due_saved_monitors --limit 999
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

## Current Status

The scheduled-refresh CLI foundation is verified for no-due-monitor dry-run behavior, limit guardrails, and traceable job-run IDs.

This does not verify production recurring execution, alerting, scheduler locking, monitor ownership, or production observability.

## Do Not Enable Production Cron Until

Before enabling recurring production Cron, the project still needs:

- Scheduler locking or lease protection.
- Better scheduler observability.
- Searchable job/run IDs in production logs.
- Clear rollback instructions.
- Auth/RBAC and monitor ownership design.
- Alerting and notification preferences designed separately from scheduled execution.
