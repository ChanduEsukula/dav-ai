# RealWorldSafety Audit / Source-Pull Constraint Investigation

**Date:** June 26, 2026
**Branch:** `docs/source-expansion-checkpoint`
**Context:** Local runtime issue observed during the senior UI audit after `portfolio-ui-polish-v1-docs`.
**Scope:** Investigation only. No backend code, migrations, routes, tests, or application behavior were changed.

## Symptom

During local Public Safety / RealWorldSafety searches, the API response still returned successfully, but backend logs showed:

- `audit_insert_failed`
- `source_pull_insert_failed`
- PostgreSQL check violation on `audit_events_module_check`
- PostgreSQL foreign-key violation on `source_pulls_audit_id_fkey`

The observed audit failure was for audit rows with:

```text
module = RealWorldSafety
source_id = cpsc_recalls_api
source_id = fda_recalls_market_withdrawals_safety_alerts
```

The user-facing search can still render results because the repositories catch persistence failures and return error metadata, but source-trail persistence is not reliable for Public Safety Search in this database state.

## Likely Root Cause

This is local/configured database schema drift plus missing source seed migrations in that database.

The configured database currently reports:

```text
alembic_versions: ['20260608_0009']
```

The repository Alembic head is:

```text
20260622_0011
```

The configured database also has an `audit_events_module_check` constraint that is not present in the current committed audit-events migration or schema snapshot:

```text
CHECK (
  module = ANY (
    ARRAY[
      'RecallRadar',
      'DrugSignal',
      'CosmeticSignal',
      'FoodRadar',
      'RegionalHealthPulse'
    ]
  )
)
```

That check does not allow `RealWorldSafety`, while the RealWorldSafety workflow writes audit events with `module="RealWorldSafety"`.

The same configured database also currently has no `source_registry` rows where `module = 'RealWorldSafety'`. That means even if the audit module check were widened or dropped, RealWorldSafety audit/source-pull persistence would still need source registry rows for source IDs such as `cpsc_recalls_api`, `fda_recalls_market_withdrawals_safety_alerts`, `rxnorm_rxnav_api`, and NHTSA sources.

## Classification

| Possible cause | Finding |
|---|---|
| Missing migration | Yes. The configured DB is at `20260608_0009`, while the repo head is `20260622_0011`. |
| Stale local DB schema | Yes. The DB has `audit_events_module_check`, but the current migration/schema snapshot does not define that constraint. |
| Overly narrow check constraint | Yes. The installed check allows old module names but rejects `RealWorldSafety`. |
| Seeded source registry mismatch | Yes. Runtime registry includes RealWorldSafety sources, but the configured DB query returned no `source_registry` rows with `module = 'RealWorldSafety'`. |
| Application code using a DB-disallowed value | Yes in the current DB state. The app correctly uses `RealWorldSafety`, but the installed DB constraint does not allow it. |
| Source-pull repository primary bug | No. The source-pull failure is downstream from the failed audit insert and missing/stale schema state. |

## Evidence

### RealWorldSafety writes `module="RealWorldSafety"`

- `backend/app/services/search_workflows/real_world_safety_search.py:174-195`
  builds a successful source audit event with `module="RealWorldSafety"`.
- `backend/app/services/search_workflows/real_world_safety_search.py:232-253`
  builds an error-source audit event with `module="RealWorldSafety"`.
- `backend/app/audit/audit_event.py:22-37`
  stores the caller-provided `module` directly in the audit event payload.

### Audit repository inserts the module directly

- `backend/app/db/audit_repository.py:61-99`
  inserts `audit_events.module` from the audit event payload.
- `backend/app/db/audit_repository.py:121-141`
  catches insert failures and returns `status="error"` instead of failing the API response.

### Source-pull persistence depends on audit/source registry integrity

- `backend/app/db/source_pull_repository.py:91-139`
  inserts `source_pulls.audit_id` and `source_pulls.source_id` from the same audit event.
- `backend/migrations/versions/20260521_0006_create_source_pulls_and_raw_snapshots.py:25-35`
  defines `source_pulls.audit_id` as a foreign key to `audit_events.audit_id` and `source_pulls.source_id` as a foreign key to `source_registry.source_id`.
- Because the audit insert fails, `source_pulls.audit_id` points to a non-existent `audit_events` row, producing the observed `source_pulls_audit_id_fkey` failure.

### Current committed audit table DDL does not include `audit_events_module_check`

- `backend/migrations/versions/20260505_0001_create_source_registry_and_audit_events.py:42-87`
  creates `audit_events` with checks for `upstream_status` and `record_count`, but no `module` check.
- `backend/db/schema.sql:16-38`
  matches that current shape: `audit_events` has no module check in the schema snapshot.

### Runtime registry and seed migrations expect RealWorldSafety sources

- `backend/app/sources/registry.py:26-109`
  defines drug/device/reference sources with `module="RealWorldSafety"`.
- `backend/app/sources/registry.py:130-207`
  defines outbreak, FDA public notice, CPSC, and NHTSA sources with `module="RealWorldSafety"`.
- `backend/app/sources/registry.py:219-240`
  includes those sources in `REGISTERED_SOURCES`.
- `backend/migrations/versions/20260622_0011_seed_real_world_safety_sources.py:20-140`
  seeds many RealWorldSafety source rows.
- `backend/db/schema.sql:77-219`
  also includes RealWorldSafety seed rows in the schema snapshot.

### Local/configured DB is behind repo head

Read-only database catalog inspection returned:

```text
alembic_versions ['20260608_0009']
audit_events_module_check CHECK ((module = ANY (ARRAY[
  'RecallRadar'::text,
  'DrugSignal'::text,
  'CosmeticSignal'::text,
  'FoodRadar'::text,
  'RegionalHealthPulse'::text
])))
real_world_sources []
```

The repository Alembic head command returned:

```text
backend/.venv/bin/python -m alembic heads
20260622_0011 (head)
```

### Tests do not catch this exact persistence/schema drift

- `backend/tests/test_real_world_safety_route.py:49-61`
  monkeypatches `save_audit_event` and `save_source_pull_with_snapshot` for route tests.

That is a reasonable unit-test isolation pattern, but it means RealWorldSafety route tests can pass while the configured DB rejects real persistence.

## Production / Demo Behavior Impact

Affected:

- Any environment using this same stale schema state.
- Public Safety Search source-trail trust.
- Audit History links for RealWorldSafety source checks.
- Source-pull provenance and raw snapshot persistence for Public Safety Search.
- Source freshness/status fidelity if it depends on stored audit/source-pull metadata.

Not directly affected:

- The immediate search response path, because persistence failures are caught and the workflow still returns results.
- Non-RealWorldSafety modules that use allowed audit modules and registered source IDs.

Unknown until checked:

- Hosted/demo production database state. If it is also at `20260608_0009` or still has `audit_events_module_check` without `RealWorldSafety`, it is affected. If it has current seeds and no narrow audit module check, it is not affected.

## Recommended Fix Options

### 1. Safest: Add a new Alembic reconciliation migration, then upgrade to head

Create a new migration after `20260622_0011` that explicitly reconciles installed DB drift:

- `drop constraint if exists audit_events_module_check` on `audit_events`, matching the current committed schema snapshot; or recreate it with `RealWorldSafety` included if the project still wants a DB-level module allowlist.
- Ensure RealWorldSafety source rows are present by relying on `20260622_0011` during `alembic upgrade head`, or by making the new migration idempotently upsert any missing RealWorldSafety rows.
- Optionally add a migration/schema alignment test that would fail if a runtime module cannot be persisted to audit events.

Why safest:

- Versioned, repeatable, reviewable.
- Fixes all environments the same way.
- Preserves the architecture story that schema changes are managed through Alembic.

### 2. Acceptable local/demo hotfix: Apply explicit SQL, then run migrations

For a one-off local/demo database, manually run SQL equivalent to:

```sql
alter table audit_events
drop constraint if exists audit_events_module_check;
```

Then run:

```bash
backend/.venv/bin/python -m alembic upgrade head
```

Why lower-ranked:

- Fast for one database.
- But it creates untracked schema history unless followed by a migration.
- Easy to forget in hosted/demo DBs.

### 3. Recreate the database from current schema/migrations

Drop and recreate the local demo database from current migrations/schema.

Why risky:

- Cleanest schema result.
- But destructive to local/demo data, saved searches, audit history, and source-pull history.
- Should not be used if the database contains any state worth preserving.

### 4. Not recommended: Change application code to use an older allowed module

Example: changing RealWorldSafety audit events to `FoodRadar`, `RecallRadar`, or another allowed module.

Why not:

- Hides the real schema problem.
- Makes audit history inaccurate.
- Breaks source registry semantics.
- Weakens the source-trail story for the exact feature being demoed.

## Exact Validation Commands After a Fix

From repo root:

```bash
backend/.venv/bin/python -m alembic heads
backend/.venv/bin/python -m alembic current
backend/.venv/bin/python -m alembic upgrade head
```

Read-only DB catalog verification:

```bash
cd backend
./.venv/bin/python -c "import psycopg; from psycopg.rows import dict_row; from app.db.database import get_database_url; url=get_database_url(); assert url; \
with psycopg.connect(url, row_factory=dict_row) as conn: \
    cur=conn.cursor(); \
    cur.execute(\"select version_num from alembic_version order by version_num\"); print(cur.fetchall()); \
    cur.execute(\"select conname, pg_get_constraintdef(oid) as definition from pg_constraint where conrelid = 'audit_events'::regclass order by conname\"); print(cur.fetchall()); \
    cur.execute(\"select count(*) as count from source_registry where module = 'RealWorldSafety'\"); print(cur.fetchone())"
```

Focused backend tests:

```bash
cd backend
./.venv/bin/python -m pytest tests/test_registry_schema_alignment.py
./.venv/bin/python -m pytest tests/test_real_world_safety_route.py
./.venv/bin/python -m pytest tests/test_source_pull_repository.py
./.venv/bin/python -m pytest tests/test_audit_repository.py
```

Manual runtime smoke:

```bash
cd backend
./.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In another terminal:

```bash
curl "http://127.0.0.1:8000/api/v1/real-world-safety/search?q=air%20fryer&limit=3&sort=score"
```

Expected result after fix:

- No `audit_insert_failed` logs.
- No `source_pull_insert_failed` logs.
- RealWorldSafety rows appear in `audit_events`.
- Matching source pulls appear in `source_pulls`.
- Source freshness/source trail shows stored pull metadata for successful source checks.

Final broad checks:

```bash
cd backend
./.venv/bin/python -m pytest
cd ../frontend
npm run build
npm test -- PublicSafetySearchPage
```

## Should This Be Fixed Before Demo Recording?

Yes, if the demo will show Public Safety Search source trails, Audit History, source freshness, or any claim that the flagship search is audit-backed.

It is not a blocker for a superficial UI-only demo because the search response still returns. But for the intended portfolio story, source-trail trust is central. A recruiter or senior engineer may ask whether records are actually persisted and traceable. This should be fixed before recording or presenting the source-trail/audit part of the demo.
