# Scheduled Monitor Locking Design

## Purpose

This document defines the design for scheduler locking / lease protection before enabling production Cron for Saved Monitor refresh.

Production Cron is not enabled yet. This design is a prerequisite for safer future recurring execution.

## Problem

The scheduled monitor refresh foundation can be triggered through the backend CLI job:

```bash
cd backend
python -m app.jobs.run_due_saved_monitors --limit 10
```

If this command is later executed by Render Cron, overlapping jobs could occur because of retries, slow upstream API calls, manual runs, or misconfigured schedules.

Without locking, two scheduler jobs could:

- Select the same due monitors.
- Run the same monitor twice.
- Create duplicate run-history rows.
- Overwrite schedule metadata.
- Make audit history harder to interpret.
- Produce confusing operational logs.

## Goal

Add a simple scheduler lock / lease so only one saved-monitor scheduled refresh job runs at a time.

## Non-Goals

This design does not add:

- Production Cron activation.
- Alerts.
- Notification preferences.
- Public scheduling UI.
- Auth/RBAC.
- Distributed task queues.
- Celery, Redis, or background workers.
- Clinical or medical decision logic.

## Recommended Lock Model

Use a database-backed lock table.

Suggested table name:

```text
scheduler_locks
```

Suggested columns:

```text
lock_name TEXT PRIMARY KEY
locked_by TEXT NOT NULL
locked_until TIMESTAMPTZ NOT NULL
created_at TIMESTAMPTZ NOT NULL DEFAULT now()
updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
```

For Saved Monitor scheduled refresh, use:

```text
lock_name = "saved-monitor-refresh"
locked_by = job_run_id
```

## Lease Duration

Recommended initial lease duration:

```text
15 minutes
```

Reasoning:

- Long enough for small batches of due monitors.
- Short enough that a crashed job does not block the scheduler indefinitely.
- Can be revisited after production timing data exists.

## Acquire Behavior

When a scheduler job starts:

1. Generate a `job_run_id`.
2. Try to acquire lock `saved-monitor-refresh`.
3. If no lock exists, create it.
4. If lock exists but `locked_until <= now`, take it over.
5. If lock exists and `locked_until > now`, skip the job safely.

## Release Behavior

When the scheduler job finishes:

1. Release the lock only if `locked_by` matches the current `job_run_id`.
2. If another job has taken over an expired lock, do not delete that newer lock.
3. Log release success or failure.

## CLI Output When Lock Is Acquired

If the lock is acquired and no monitors are due:

```json
{
  "status": "ok",
  "job_run_id": "scheduled-refresh-20260515-184620-6e8d1fe3",
  "job_started_at": "2026-05-15T18:46:20.326143+00:00",
  "due_count": 0,
  "attempted_count": 0,
  "success_count": 0,
  "error_count": 0,
  "skipped_count": 0,
  "requested_limit": 10,
  "safe_limit": 10,
  "run_ids": []
}
```

## CLI Output When Lock Is Active

If another scheduler job already holds a valid lock:

```json
{
  "status": "skipped",
  "reason": "active_scheduler_lock",
  "job_run_id": "scheduled-refresh-20260515-184700-abc12345",
  "lock_name": "saved-monitor-refresh",
  "requested_limit": 10,
  "safe_limit": 10,
  "run_ids": []
}
```

## Repository Behavior

Add a small scheduler lock repository with methods such as:

```text
acquire_lock(lock_name, locked_by, locked_until, now) -> bool
release_lock(lock_name, locked_by) -> bool
```

Expected behavior:

- `acquire_lock` returns `True` if lock was created or expired lock was taken over.
- `acquire_lock` returns `False` if active lock exists.
- `release_lock` deletes/releases only if current job owns the lock.
- Failures should be logged clearly.

## Local / Test Fallback

For local tests, support an in-memory lock fallback similar to saved monitor and audit repository patterns.

The fallback should support:

- Acquire new lock.
- Reject active lock.
- Take over expired lock.
- Release owned lock.
- Refuse release by non-owner.

## Test Plan

Backend tests should cover:

1. Acquiring a new lock succeeds.
2. Active lock causes scheduler job to return `status: skipped`.
3. Expired lock can be taken over.
4. Lock is released after successful job completion.
5. Lock is released after job error.
6. Lock is not released by a different `job_run_id`.
7. CLI summary includes `job_run_id`, `requested_limit`, `safe_limit`, and lock skip reason.
8. Existing scheduled refresh tests still pass.

## Safety Notes

Scheduler locking does not make the system production-ready by itself.

Before enabling production Cron, MedTrek AI still needs:

- Scheduler observability.
- Clear rollback instructions.
- Auth/RBAC and monitor ownership.
- Alerting design and notification preferences.
- Production monitoring for job failures.
- Careful review of duplicate-run behavior.

## Current Recommendation

Implement scheduler locking before enabling any recurring production Cron job.

Keep production Cron disabled until lock behavior is implemented, tested, documented, and manually verified.
