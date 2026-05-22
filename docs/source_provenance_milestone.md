# Source Provenance and Reproducibility Milestone

## Summary

MedTrek AI now has an audit-backed public-data provenance layer for its FDA/openFDA safety intelligence workflows.

This milestone moves the project beyond a search-and-display prototype. RecallRadar and DrugSignal now preserve operational source freshness, audit-linked source pull metadata, and raw public-source snapshots with stable payload hashes.

## What changed

### 1. Audit-backed source freshness

The `/api/v1/sources` endpoint now returns source freshness metadata based on stored audit history.

Each registered source can report:

- freshness status
- freshness label
- last successful retrieval timestamp
- last attempted retrieval timestamp
- last record count
- last error message
- freshness reason

This allows the app to distinguish between static source metadata and operational source health.

### 2. Source freshness in the UI

The Data Sources page now displays freshness information for each public source.

The System Status page also summarizes source freshness counts:

- fresh sources
- delayed sources
- error sources
- unknown sources

This makes source health visible from an operations perspective.

### 3. Source pull persistence

The backend now includes `source_pulls`, a table that stores reproducible public-source retrieval metadata.

Each source pull records:

- pull ID
- linked audit ID
- source ID and source name
- endpoint
- query
- query parameters
- retrieval timestamp
- upstream status
- record count
- transform version
- stable payload hash

### 4. Raw public-source snapshots

The backend now includes `raw_source_snapshots`, a table that stores the exact raw public openFDA payload associated with a source pull.

This creates a reproducibility trail from API response to audit event to source pull to raw public-source snapshot to stable payload hash.

The API does not expose raw payloads by default. It only returns trace metadata such as snapshot status, source pull ID, and payload hash.

## Why this matters

This milestone makes MedTrek AI more credible as a healthcare safety intelligence platform.

The system can now answer:

- What public source was queried?
- When was it retrieved?
- What query parameters were used?
- How many records were returned?
- Was the source fresh, delayed, unknown, or in error?
- What exact raw public payload supported the result?
- Has the payload changed, based on a stable hash?

This is important for public-data safety workflows because results must be explainable, traceable, and reproducible.

## Safety and privacy boundary

This feature stores public FDA/openFDA payloads only.

It should not store:

- personal health information
- user medical history
- diagnoses
- prescription history
- insurance information
- private user records
- addresses or identifying patient details

MedTrek AI remains a public-data safety intelligence tool, not a medical advice or clinical decision-support system.

## Verification

Local verification completed:

- Backend tests: 100 passed
- Frontend tests: 54 passed
- Frontend lint: passed
- RecallRadar smoke test: source_snapshot_status = saved
- DrugSignal smoke test: source_snapshot_status = saved

GitHub verification completed:

- PR #1: Audit-backed source freshness merged
- PR #2: Source pulls and raw snapshots merged
- Vercel deployment: ready

## Interview explanation

A concise way to explain this milestone:

“I strengthened MedTrek AI’s provenance layer by adding audit-backed source freshness, source pull persistence, raw public-source snapshots, and stable payload hashing. This means each safety result can be traced back to the exact openFDA payload, retrieval timestamp, query parameters, audit event, and payload hash, without exposing raw payloads directly in the API response.”

## Next recommended step

The next engineering step is to add a safe Source Pull Detail API and UI.

Suggested scope:

- expose source pull metadata by pull ID
- show linked audit ID, source, query, timestamp, record count, and payload hash
- do not expose raw payload by default
- optionally add a backend-only/admin-safe raw snapshot inspection path later