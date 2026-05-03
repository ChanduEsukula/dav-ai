# MedSignal AI Audit Trail Design

## Purpose

The audit trail records how each public safety signal was produced, which public source was used, when data was retrieved, what query was sent, and what transformation or scoring version was applied.

The goal is source transparency, reproducibility, and reviewer trust.

---

## Why This Matters

MedSignal AI is a healthcare safety intelligence platform. It does not diagnose, prescribe, or claim causation.

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
| retrieval_timestamp | When MedSignal retrieved the source data |
| upstream_status | success, empty, or error |
| record_count | Number of records returned or reviewed |
| transform_version | Version of normalization/transformation logic |
| score_version | Version of scoring logic, if applicable |
| disclaimer_version | Version of disclaimer text used |
| error_message | Error details if source call failed |
| created_at | When audit event was stored |

---

## Current Database Tables

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

MedSignal AI currently returns compact audit metadata directly in RecallRadar and DrugSignal API responses.

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

---

## Known Gaps

Current audit architecture does not yet include:

- Audit history UI
- Briefing persistence
- Saved monitor audit events
- Scheduled ingestion audit events
- Change detection history
- Raw upstream snapshot storage
- Formal migration system
- Production observability/logging
- PHI-safe user-specific privacy model

---

## Recommended Next Engineering Steps

1. Keep current audit metadata visible in API responses and UI.
2. Keep fail-soft audit persistence stable.
3. Update README/docs to reflect Safety Briefing Engine v1.
4. Add Docker/deployment preparation next.
5. Add migration tooling before expanding database schema.
6. Add saved monitors only after deployment and privacy boundaries are clearer.