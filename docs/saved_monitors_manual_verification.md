# Saved Monitors Manual Verification

Date verified: 2026-05-12  
Environment: Local development  
Frontend: http://localhost:5173  
Backend: http://127.0.0.1:8000  

## Purpose

This document records a manual end-to-end verification of the Saved Monitors v2 foundation. The goal is to confirm that a user can create a saved monitor, manually run a check, receive updated result metadata, and navigate from the saved monitor result to the related Audit History detail.

## Prerequisites

- FastAPI backend running on port 8000.
- Vite frontend running on port 5173.
- Backend health endpoint returns healthy.
- Audit persistence is active when a database is configured.
- Saved monitor persistence may reset in local development when the backend uses in-memory fallback.

## Backend Health Check

Verified command:

    curl http://127.0.0.1:8000/health

Expected result:

    {"status":"healthy"}

## RecallRadar Saved Monitor Flow

Test monitor:

- Name: Eye drops monitor
- Query: eye drops
- Module: RecallRadar

Manual steps verified:

1. Opened the frontend at `http://localhost:5173`.
2. Navigated to the Monitors page.
3. Created a RecallRadar saved monitor.
4. Confirmed the monitor appeared in the monitor table.
5. Clicked Run Check.
6. Confirmed the monitor status changed to checked.
7. Confirmed latest score appeared.
8. Confirmed latest record count appeared.
9. Confirmed View Audit button appeared.
10. Clicked View Audit.
11. Confirmed the URL changed to include `page=audit` and `audit_id`.
12. Confirmed Audit History opened with the selected RecallRadar audit event.

Observed result:

- Status: checked
- Latest score: 85
- Records: 5
- Audit History selected the related RecallRadar audit event.

## Backend API Verification

Created a saved monitor through the API:

    curl -s -X POST http://127.0.0.1:8000/api/v1/saved-monitors \
      -H "Content-Type: application/json" \
      -d '{"name":"Eye drops monitor","query":"eye drops","module":"recallradar"}'

Verified saved monitor list:

    curl -s http://127.0.0.1:8000/api/v1/saved-monitors

Verified manual run endpoint:

    curl -s -X POST http://127.0.0.1:8000/api/v1/saved-monitors/{monitor_id}/run

Expected fields after run:

- `status`: checked
- `latest_audit_id`: populated
- `latest_score`: populated
- `latest_record_count`: populated
- `last_checked_at`: populated

## Notes

During local testing, duplicate Eye drops monitors appeared because one monitor was created through the browser and another through curl. This is expected behavior, not a defect.

Local saved monitors may reset when the backend reloads if the application is using in-memory fallback instead of a configured database with the `saved_monitors` table.

## Verification Status

Saved Monitors v2 foundation manual verification: Passed.

## Supabase Persistence Verification

Additional verification was completed after reconciling Alembic migration state.

Alembic initially reported the database at revision `20260505_0001`, while the `saved_monitors` table already existed in Supabase/Postgres. The existing table was inspected and confirmed to contain the expected columns and indexes for the Saved Monitors v2 migration. Alembic version drift was then reconciled with:

    alembic stamp head

After stamping, Alembic reported:

    20260511_0002 (head)

Persistence verification steps:

1. Confirmed backend health returned healthy.
2. Created a saved monitor through the API.
3. Confirmed the saved monitor appeared in the saved monitor list.
4. Confirmed older saved monitors still existed after backend restart.
5. Ran the saved monitor through the manual run endpoint.
6. Confirmed the persisted monitor updated with checked status, latest audit ID, latest score, record count, and last checked timestamp.

Observed persisted run result:

- Monitor: Persistence verification monitor
- Query: eye drops
- Module: RecallRadar
- Status: checked
- Latest score: 85
- Latest record count: 5
- Latest audit ID: populated

Supabase/Postgres persistence verification: Passed.

## Duplicate Monitor Verification

Verified duplicate prevention after adding module/query uniqueness rules.

Manual browser steps:

1. Created a RecallRadar saved monitor:
   - Name: Duplicate test monitor
   - Query: ibuprofen
   - Module: RecallRadar

2. Attempted to create another RecallRadar saved monitor with the same normalized query:
   - Name: Another duplicate test
   - Query: Ibuprofen
   - Module: RecallRadar

3. Confirmed the UI blocked the duplicate and displayed:
   - A saved monitor already exists for this module and query.

4. Created a monitor with the same query but a different module:
   - Name: Ibuprofen DrugSignal monitor
   - Query: ibuprofen
   - Module: DrugSignal

5. Confirmed this was allowed because uniqueness is scoped to module plus normalized query.

Observed result:

- Duplicate RecallRadar monitor was blocked.
- DrugSignal monitor with the same query was created successfully.
- Validation message after form reset was expected when Save Monitor was clicked with empty fields.

Duplicate saved monitor verification: Passed.
