# MedTrek AI Audit Trail Design

## Purpose

The audit trail records how each public safety signal was produced, which public source was used, when data was retrieved, what query was sent, and what transformation or scoring version was applied.

The goal is source transparency, reproducibility, and reviewer trust.

---

## Why This Matters

MedTrek AI is a healthcare safety intelligence platform. It does not diagnose, prescribe, or claim causation.

Because the app summarizes public FDA/openFDA safety data, every result should be traceable back to:

- source name
- endpoint
- query
- retrieval timestamp
- record count
- transformation version
- score version when applicable
- disclaimer used
- audit ID

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

## Current Audit Event Fields

| Field | Purpose |
|---|---|
| audit_id | Unique event ID |
| module | RecallRadar or DrugSignal |
| source_id | Registry source ID |
| source_name | Human-readable source name |
| endpoint | Public API endpoint |
| query | User/search query |
| query_params | Full query parameters sent upstream |
| retrieval_timestamp | When MedTrek retrieved the source data |
| upstream_status | success, empty, or error |
| record_count | Number of records returned or reviewed |
| transform_version | Version of normalization/transformation logic |
| score_version | Version of scoring logic, if applicable |
| disclaimer_version | Version of disclaimer text used |
| error_message | Error details if source call failed |
| created_at | When audit event was stored |

---

## Current Database Tables

MedTrek AI has Alembic migration tooling, and the initial migration creates `source_registry` and `audit_events`. The SQL schema also includes newer Saved Monitors fields, so migration/schema drift must be reconciled before treating all persistence features as production-ready.

### source_registry

Stores source metadata.

Current fields include:

- source_id
- source_name
- endpoint
- module
- description
- update_cadence
- created_at
- updated_at

### audit_events

Stores one row per search/source workflow.

Current fields include:

- audit_id
- module
- source_id
- source_name
- endpoint
- query
- query_params
- retrieval_timestamp
- upstream_status
- record_count
- transform_version
- score_version
- disclaimer_version
- error_message
- created_at

---

## Current App Status

MedTrek AI currently returns compact audit metadata directly in RecallRadar and DrugSignal API responses.

It also builds full audit events internally and persists them to Supabase/PostgreSQL through a fail-soft repository layer when `DATABASE_URL` is configured.

Current visible audit metadata includes:

- source name
- endpoint
- retrieval timestamp
- record count
- score version for RecallRadar
- audit ID
- source ID
- module
- upstream status
- transform version
- disclaimer

---

## Current UI Audit Surfaces

Audit/source details are visible in:

- RecallRadar audit panel
- RecallRadar technical audit details
- DrugSignal audit panel
- Safety Briefing Engine v1 source/audit section
- Data Sources page

---

## Safety Briefing Engine v1

Safety Briefing Engine v1 uses structured RecallRadar and DrugSignal response data to generate deterministic role-based safety briefings.

The briefing panel shows:

- role
- summary
- what was found
- what to verify
- suggested review checklist
- limitations
- source and audit details
- disclaimer

Current roles:

- Consumer
- Pharmacy
- Clinic
- Public Health / Analyst

The briefing engine does not use an LLM yet and must not produce diagnosis, treatment guidance, medication-change advice, or FAERS causation claims.

---

## Safety Boundary

Audit trail data must not contain personal health information.

The MVP should only store public-data queries and source metadata. If user accounts or saved monitors are added later, privacy controls must be designed before storing user-specific health interests.

Saved Monitors v2 foundation now exists for repeatable public-data monitor definitions and manual run checks. It still needs migration coverage, monitor-run audit events, privacy controls, and scheduled refresh design before it should be treated as production-ready monitoring.

---

## Known Gaps

Current audit architecture does not yet include:

- Briefing persistence
- Saved monitor run audit events
- Scheduled ingestion audit events
- Change detection history
- Raw upstream snapshot storage
- Full migration/schema alignment for newer tables such as `saved_monitors`
- Full production observability with dashboards, alerts, or SLOs
- PHI-safe user-specific privacy model

---

## Recommended Next Engineering Steps

1. Keep current audit metadata visible in API responses and UI.
2. Keep fail-soft audit persistence stable.
3. Keep README/docs aligned with implemented features and partial features.
4. Reconcile Alembic migration coverage with the current SQL schema.
5. Add monitor-run audit events for Saved Monitors v2 manual checks.
6. Harden Saved Monitors v2 with migration coverage, privacy controls, and scheduled refresh design.

## Audit History API and UI

MedTrek AI now includes an Audit History workflow for reviewing recent public-data search events.

### Backend endpoints

- `GET /api/v1/audit-events`
  - Returns recent audit events from the configured PostgreSQL/Supabase audit table.
  - Supports a `limit` query parameter.
  - Fails safely if persistence is not configured or cannot be read.

- `GET /api/v1/audit-events/{audit_id}`
  - Returns a single audit event by audit ID.
  - Returns a safe `not_found` response if the audit ID does not exist.

### Frontend page

The frontend includes an `Audit` navigation tab that opens the Audit History page. This page shows recent audit events in a review table and displays selected event details in a side panel.

### Fields shown

The Audit History workflow exposes safe public-data traceability fields:

- Audit ID
- Module
- Source ID
- Source name
- Source endpoint
- Query
- Query parameters
- Retrieval timestamp
- Upstream status
- Record count
- Transform version
- Score version
- Disclaimer version
- Error message, if present
- Created timestamp

### Safety boundary

Audit History is for public-data traceability only. It is not clinical record storage and must not contain PHI, patient identifiers, diagnosis history, treatment history, personal medication profiles, uploaded medical documents, or private health notes.

This feature supports source transparency, reproducibility, reviewer trust, and engineering auditability. It does not provide medical advice, diagnosis, treatment guidance, or causation claims.
