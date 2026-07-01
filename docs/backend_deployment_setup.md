# Backend Deployment Setup

## Goal

Deploy the FastAPI backend with a hosted PostgreSQL database and keep the public-data audit workflow working.

## Recommended Host

Use Render or Railway for the first backend deployment.

## Build Settings

- Root directory: repository root
- Runtime: Python 3.13
- Install command: `pip install -r backend/requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --app-dir backend`

## Required Environment Variables

- `DATABASE_URL`: hosted PostgreSQL connection string
- `ALLOWED_ORIGINS`: deployed frontend URL, local dev URL, or comma-separated allowed origins
- `DAVAI_ENV=production`: marks the backend as deployed so persistence/auth failures fail closed
- `AUTH_SECRET_KEY`: explicit secret for prototype/demo bearer-token signing in deployed mode

Example during early testing:

```text
ALLOWED_ORIGINS=http://localhost:5173
```

After frontend deployment, update it to include the deployed frontend URL.

Render also sets `RENDER=true`; DavAI treats that as deployed mode. In deployed
mode, missing or broken persistence should fail closed for audit event writes,
source-pull snapshot writes, saved monitor repository operations, scheduler
locks, and user/profile repository storage.

## Database Migration

For a fresh hosted database, run:

```bash
alembic upgrade head
```

For an existing database that was already manually created from `backend/db/schema.sql`, run:

```bash
alembic stamp head
```

Do not deploy to an old fixed revision. Deployment targets should always use
Alembic `head` for the current branch. If a database was manually created before
Alembic was introduced, inspect it carefully before using `alembic stamp head`.

## Health Check

Use:

```text
/health
```

Expected response should confirm the backend is healthy.

## Backend Smoke Test

After deployment, verify:

1. Root endpoint returns backend status
2. `/health` returns healthy status
3. RecallRadar search works from the frontend or API
4. DrugSignal search works from the frontend or API
5. Audit History can read persisted audit events
6. A provenance persistence failure returns a persistence-specific `503`, not an upstream/public-source `502`

## Safety Requirement

The deployed backend must remain public-data-only. Do not add PHI, patient identifiers, personal medication profiles, uploaded medical documents, diagnosis history, treatment history, or private health notes.

Current auth is prototype/demo token-based auth with an explicit deployed secret requirement. Do not present it as production RBAC, tenancy, or enterprise identity management.
