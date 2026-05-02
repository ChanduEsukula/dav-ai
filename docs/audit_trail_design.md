# MedSignal AI Audit Trail Design

## Purpose

The audit trail records how each safety signal was produced, which public source was used, when the data was retrieved, what query was sent, and what transformation or scoring version was applied.

The goal is source transparency, reproducibility, and reviewer trust.

---

## Why This Matters

MedSignal AI is a healthcare safety intelligence platform. It does not diagnose, prescribe, or claim causation. Because the app summarizes public FDA safety data, every result should be traceable back to:

- source name
- endpoint
- query
- retrieval timestamp
- record count
- transformation version
- score version
- disclaimer used

---

## Current Sources

### RecallRadar

- Source ID: openfda_drug_enforcement
- Source name: openFDA Drug Enforcement API
- Endpoint: https://api.fda.gov/drug/enforcement.json
- Module: RecallRadar

### DrugSignal

- Source ID: openfda_drug_event
- Source name: openFDA Drug Event API
- Endpoint: https://api.fda.gov/drug/event.json
- Module: DrugSignal

---

## Proposed Audit Event Fields

| Field | Purpose |
|---|---|
| audit_id | Unique event ID |
| module | RecallRadar, DrugSignal, future Briefing Engine |
| source_id | Registry source ID |
| source_name | Human-readable source name |
| endpoint | Public API endpoint |
| query | User/search query |
| query_params | Full query parameters sent upstream |
| retrieval_timestamp | When MedSignal retrieved the source data |
| upstream_status | Success, empty, or error |
| record_count | Number of records returned or reviewed |
| transform_version | Version of normalization/transformation logic |
| score_version | Version of scoring logic, if applicable |
| disclaimer_version | Version of disclaimer text used |
| error_message | Error details if source call failed |
| created_at | When audit event was stored |

---

## Proposed Tables for Future Database Phase

### source_registry

Stores source metadata.

Possible fields:

- source_id
- source_name
- endpoint
- module
- description
- update_cadence
- created_at
- updated_at

### audit_events

Stores one row per search, source call, or briefing generation.

Possible fields:

- audit_id
- module
- source_id
- endpoint
- query
- query_params_json
- retrieval_timestamp
- upstream_status
- record_count
- transform_version
- score_version
- disclaimer_version
- error_message
- created_at

### raw_snapshots

Stores raw source payloads or references to raw payload files.

Possible fields:

- snapshot_id
- audit_id
- source_id
- raw_payload_json
- payload_hash
- created_at

---

## Current App Status

Currently, MedSignal AI returns audit metadata directly in API responses. It does not persist audit events yet.

Current audit metadata includes:

- source_name
- endpoint
- retrieval_timestamp
- record count
- score_version for RecallRadar
- disclaimers

---

## Recommended Implementation Order

1. Keep returning audit metadata in API responses.
2. Add a simple audit event builder function in backend.
3. Add tests for audit event shape.
4. Add database only after schema is stable.
5. Store source registry and audit events in Supabase/PostgreSQL.
6. Add Data Sources / Audit page to show source metadata and future audit history.

---

## Safety Boundary

Audit trail data must not contain personal health information.

The MVP should only store public-data queries and source metadata. If user accounts or saved monitors are added later, privacy controls must be designed before storing user-specific health interests.

---

## Next Engineering Step

Before Supabase, create a backend utility that builds a standard audit event dictionary from RecallRadar and DrugSignal responses.

This keeps audit logic consistent and testable before persistence.