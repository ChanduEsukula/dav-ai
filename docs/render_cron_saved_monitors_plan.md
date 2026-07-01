# Render Cron Plan for Saved Monitor Refresh

## Purpose

This document describes how DAV AI can run Saved Monitor scheduled refreshes using Render Cron in the future.

This is a dry-run plan only. Production Cron is not enabled yet.

## Current Foundation

Implemented:

- Saved Monitor run history
- Schedule metadata fields
- Due-monitor selection
- Backend CLI job
- CLI guardrails
- Limit clamping from `1` to `50`
- JSON job summary with `requested_limit` and `safe_limit`
- Scheduled workflow request IDs for RecallRadar and DrugSignal runs
- Database-backed scheduler locking through `scheduler_locks`
- Alembic migration `20260519_0005_create_scheduler_locks.py`
- In-memory scheduler lock fallback for local/test-created repository instances

Not implemented:

- Alerts
- Production RBAC and tenancy
- Public scheduling UI
- Production Cron activation
- Notification preferences
- On-call/incident workflow
- Production scheduler observability dashboard

## Proposed Render Cron Command

From the backend service context:

```bash
cd /Users/chanduesukula/dav-ai/backend
python -m app.jobs.run_due_saved_monitors --limit 10
```

The command should be tested manually in the target deployment environment before any scheduled Render Cron activation.

## Current Locking Status

DB-backed scheduler locking is implemented for the scheduled monitor refresh job. The lock repository uses the `scheduler_locks` table when database persistence is configured and falls back to in-memory lock behavior for local/test-created repository instances.

Manual verification confirmed that `python -m app.jobs.run_due_saved_monitors --limit 10` works with zero due monitors, a real temporary due DrugSignal saved monitor for `aspirin` can run successfully, a `saved_monitor_runs` row is created, and `scheduler_locks` is empty after the run, confirming lock release.

## Dry-Run Checklist

Before enabling any recurring production Cron job:

1. Confirm backend environment variables are configured.
2. Confirm database connectivity from the deployed backend environment.
3. Run the CLI command manually from the backend service context.
4. Confirm the command returns a JSON summary.
5. Confirm `requested_limit` and `safe_limit` appear in the summary.
6. Confirm safe limit clamping works for low and high values.
7. Confirm behavior when no monitors are due.
8. Confirm due monitors create run-history rows.
9. Confirm successful runs preserve audit IDs when available.
10. Confirm failed runs are recorded as error rows.
11. Confirm logs include enough detail to trace the job.
12. Confirm `scheduler_locks` acquires during the job and releases afterward.
13. Confirm no alerts or notifications are sent.
14. Confirm production Cron remains disabled after the dry run.

## Expected No-Due-Monitors Output Shape

Example shape when no monitors are due:

```json
{
  "status": "ok",
  "due_count": 0,
  "attempted_count": 0,
  "success_count": 0,
  "error_count": 0,
  "skipped_count": 0,
  "requested_limit": 10,
  "safe_limit": 10
}
```

Exact timestamps and optional fields may vary.

## Do Not Enable Production Cron Until

Production Cron should remain disabled until the following are addressed:

- Direct scheduled refresh integration is re-tested in the target deployment environment.
- Scheduler job logs are easy to search by job ID, request ID, or run ID.
- DB-backed job locking behavior is verified in the same environment where Cron will run.
- Scheduler failures are observable from production logs or a dashboard.
- Alerting behavior is designed separately from scheduler execution.
- Notification preferences exist before any user-facing alerts are sent.
- Production RBAC, tenancy, and durable monitor ownership policies are designed before user-specific scheduling.
- Operational rollback instructions are documented.

## Safety Boundary

The scheduled refresh foundation only reruns saved public-data searches and records run history.

It does not diagnose, recommend treatment, send medical advice, claim causation, or replace FDA, clinician, pharmacist, or public-health guidance.

## Current Recommendation

Keep Render Cron disabled.

Use the CLI manually for dry-run verification and continue hardening deployment-environment scheduler verification, scheduler observability, auth/RBAC, and alert design before enabling recurring production execution.
