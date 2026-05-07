# MedTrek AI Operations Runbook

This runbook explains how to verify the deployed MedTrek AI backend, trace requests with X-Request-ID, and troubleshoot public-data and audit-persistence issues.

## 1. Health check

Use the backend health endpoint to confirm the API process is running.

Local command:
curl -i http://localhost:8000/health

Production command:
curl -i https://medtrek-ai.onrender.com/health

Expected JSON:
{"status":"healthy"}

The response should include an X-Request-ID header.

## 2. Trace a request with X-Request-ID

Every backend response should include an X-Request-ID header.

Send your own request ID:
curl -i -H "X-Request-ID: manual-check-001" https://medtrek-ai.onrender.com/health

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
curl -i "https://medtrek-ai.onrender.com/api/v1/recalls/search?q=eye%20drops&limit=5"

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
curl -i "https://medtrek-ai.onrender.com/api/v1/drug-events/search?q=metformin&limit=5"

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
curl -i "https://medtrek-ai.onrender.com/api/v1/audit-events?limit=10"

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
curl -i "https://medtrek-ai.onrender.com/api/v1/recalls/search?q=aurovela&limit=5"
curl -i "https://medtrek-ai.onrender.com/api/v1/drug-events/search?q=aurovela&limit=5"

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
3. Confirm Alembic migration 20260505_0001 has been applied.
4. Call /api/v1/audit-events?limit=10.
5. Search Render logs using the request ID.

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

MedTrek AI provides public-data safety intelligence only.

It does not:
- provide medical advice
- diagnose conditions
- recommend starting, stopping, or changing medication
- claim FAERS reports prove causation
- replace FDA, CDC, pharmacists, clinicians, or emergency services
