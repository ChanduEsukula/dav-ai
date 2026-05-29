# DAV AI Operations Runbook

This runbook explains how to verify the deployed DAV AI backend, trace requests with X-Request-ID, and troubleshoot public-data, audit-persistence, saved-monitor, and scheduled-refresh foundation issues.

## 1. Health check

Use the backend health endpoint to confirm the API process is running.

Local command:
curl -i http://localhost:8000/health

Production command:
curl -i $DAV_AI_BACKEND_URL/health

Expected JSON:
{"status":"healthy"}

The response should include an X-Request-ID header.

## 2. Trace a request with X-Request-ID

Every backend response should include an X-Request-ID header.

Send your own request ID:
curl -i -H "X-Request-ID: manual-check-001" $DAV_AI_BACKEND_URL/health

Expected behavior:
- The response reuses manual-check-001.
- Render logs should include the same request ID.
- Backend logs should include request start and completion events.

Useful log fields:
- event
- request_id
- method
- path
- status_code
- duration_ms
- client_host

## 3. Verify RecallRadar

Command:
curl -i "$DAV_AI_BACKEND_URL/api/v1/recalls/search?q=eye%20drops&limit=5"

Check:
- HTTP status is 200.
- Response includes query, count, audit, source_name, retrieval_timestamp, and medical_disclaimer.
- Response includes X-Request-ID.

Operational logs should include:
- openfda_request_started
- openfda_request_completed or openfda_request_failed
- product_module=RecallRadar
- source_id
- query
- upstream_status
- record_count
- duration_ms

## 4. Verify DrugSignal

Command:
curl -i "$DAV_AI_BACKEND_URL/api/v1/drug-events/search?q=metformin&limit=5"

Check:
- HTTP status is 200.
- Response includes top_reactions, faers_disclaimer, audit, and X-Request-ID.

Operational logs should include:
- openfda_request_started
- openfda_request_completed or openfda_request_failed
- product_module=DrugSignal
- source_id
- query
- upstream_status
- record_count
- duration_ms

## 5. Verify Audit History

Command:
curl -i "$DAV_AI_BACKEND_URL/api/v1/audit-events?limit=10"

Expected healthy persistence response:
{"status":"ok","persistence_available":true}

If the database is not configured:
{"status":"skipped","persistence_available":false}

If the database read fails:
{"status":"error","persistence_available":false}

Operational logs should include:
- audit_list_started
- audit_list_completed, audit_list_skipped, or audit_list_failed

## 6. Troubleshoot openFDA empty responses

An empty response does not always mean an error.

Possible causes:
- The query did not match openFDA records.
- The product or drug name is spelled differently in FDA records.
- openFDA returned 404 for no matches.
- The selected endpoint does not contain that product category.

Expected app behavior:
- Return HTTP 200.
- Show count: 0.
- Set audit upstream_status to empty.
- Preserve source metadata and timestamp.

Recommended checks:
curl -i "$DAV_AI_BACKEND_URL/api/v1/recalls/search?q=aurovela&limit=5"
curl -i "$DAV_AI_BACKEND_URL/api/v1/drug-events/search?q=aurovela&limit=5"

## 7. Troubleshoot openFDA errors

Possible causes:
- openFDA outage or rate limiting.
- Network timeout.
- Malformed source query.
- Upstream 5xx error.

Expected app behavior:
- Return HTTP 502.
- Include a clear message that openFDA data could not be retrieved.
- Log openfda_request_failed.
- Include the matching request_id.

Recommended actions:
1. Copy the X-Request-ID from the failed response.
2. Search Render logs for that request ID.
3. Check openfda_request_failed log fields.
4. Retry with a simpler query.
5. Verify the source endpoint in /api/v1/sources.

## 8. Troubleshoot Supabase audit persistence

Audit persistence is fail-soft. RecallRadar and DrugSignal should still respond even if audit insertion fails.

Possible causes:
- DATABASE_URL missing.
- Supabase database unavailable.
- Database password rotated but Render env var not updated.
- Schema migration not applied.
- Network or connectivity issue.

Expected app behavior:
- Search endpoints continue working.
- Audit insert returns skipped or error internally.
- Logs include audit_insert_skipped, audit_insert_failed, audit_list_skipped, or audit_list_failed.

Recommended checks:
1. Confirm Render environment has DATABASE_URL.
2. Confirm Supabase database is active.
3. Confirm Alembic migrations are at head, currently `20260519_0005`.
4. Call /api/v1/audit-events?limit=10.
5. Search Render logs using the request ID.


## Saved Monitor Scheduled Refresh Foundation

The backend includes a CLI entrypoint for future scheduled refresh jobs:

```bash
cd /Users/chanduesukula/dav-ai/backend
python -m app.jobs.run_due_saved_monitors --limit 10
```

This command runs only monitors where `refresh_enabled=true` and `next_run_at` is due. It records run-history rows but does not send alerts.

Current boundary:

- Scheduled refresh infrastructure exists.
- Migration `20260514_0004` adds schedule metadata fields.
- Migration `20260519_0005_create_scheduler_locks.py` adds the `scheduler_locks` table.
- DB-backed scheduler locking is implemented for scheduled refresh jobs.
- In-memory scheduler lock fallback remains available for local/test-created repository instances.
- The CLI job exists for a future Render Cron or similar scheduler.
- Production scheduling is not enabled until a Render Cron or equivalent scheduler is configured and lock behavior is re-verified in that deployment environment.
- Alerts are not implemented.
- Auth/RBAC is not implemented.
- Public scheduling UI is not implemented.
- Notification preferences and alert delivery are not implemented.

Expected no-due-monitor response shape:

```json
{
  "attempted_count": 0,
  "due_count": 0,
  "error_count": 0,
  "job_run_id": "scheduled-refresh-20260519-120000-abc12345",
  "job_started_at": "2026-05-19T12:00:00+00:00",
  "requested_limit": 10,
  "run_ids": [],
  "safe_limit": 10,
  "skipped_count": 0,
  "status": "ok",
  "success_count": 0
}
```

## Scheduler locking

Scheduled monitor refresh uses a scheduler lock named `saved-monitor-refresh`.

Current lock behavior:

- The job acquires a row in `scheduler_locks` before selecting due monitors.
- If an active lock exists, the job skips safely with `status: skipped` and `reason: active_scheduler_lock`.
- If a lock is expired, a later job can take it over.
- The job releases the lock when it finishes, including after handled monitor errors.
- Manual verification confirmed that `scheduler_locks` was empty after a successful real temporary due DrugSignal monitor run, confirming lock release.

Operational checks:

1. Confirm migration `20260519_0005_create_scheduler_locks.py` has been applied.
2. Run the CLI manually from the backend service context.
3. Confirm the JSON summary includes `job_run_id`, `requested_limit`, and `safe_limit`.
4. Confirm due monitor runs create `saved_monitor_runs` rows.
5. Confirm `scheduler_locks` does not retain a stale active lock after the job completes.

Production Cron remains disabled until final deployment-environment verification, scheduler observability, and rollback guidance are complete.

## 9. Local verification checklist

Before committing backend observability changes:
python3 -m compileall backend/app
pytest backend/tests
git status --short

Expected:
- compileall completes without errors.
- all backend tests pass.
- only intended files are modified.

## 10. Safety boundary

DAV AI provides public-data safety intelligence only.

It does not:
- provide medical advice
- diagnose conditions
- recommend starting, stopping, or changing medication
- claim FAERS reports prove causation
- replace FDA, CDC, pharmacists, clinicians, or emergency services
