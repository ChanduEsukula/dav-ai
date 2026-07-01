# Source Freshness Review Signals and Payload-Change Intelligence Design

> Historical planning note: This document describes DAV AI planning from an earlier project stage. It is retained for project history and may not reflect the current implementation. For current scope, architecture, and implemented/partial/future boundaries, see [README.md](../README.md), [docs/README.md](README.md), and [docs/architecture_overview.md](architecture_overview.md).

## Goal

Design the next DAV AI engineering milestone: source freshness review signals and payload-change intelligence.

This milestone should improve trust, auditability, and saved-monitor change detection before any production ML, RAG, or deep learning work.

## Scope

This is a design-first milestone. It should not change production behavior until the expected data model, signal logic, UI language, tests, and safety boundaries are clearly documented.

## Why This Comes Next

DAV AI already has:

- source registry
- audit events
- source-pull metadata
- payload hashes
- saved-monitor run history
- deterministic monitor insights
- offline Responsible ML experiments

The next responsible step is to turn source freshness and payload hashes into clearer review signals.

## Proposed Features

### 1. Source Freshness Review Signal

Create a deterministic review signal that summarizes whether a public-data source appears current, aging, stale, unknown, or unavailable based on DAV AI audit history.

Possible labels:

- fresh
- aging
- stale
- unknown
- source_error

This should be audit-backed and should not claim official source freshness unless the upstream source provides a trusted last-updated timestamp.

This is an operational review signal only. It should not be presented as a medical-risk score, product-safety score, or source-authority score.

### 2. Payload-Change Intelligence

Use stored source-pull payload hashes to identify whether the public-source response changed between runs.

Possible labels:

- first_seen
- unchanged
- changed
- unavailable
- unknown

This should support saved-monitor review, not clinical urgency, product danger, medical-risk prediction, or causation claims.

### 3. Saved Monitor Integration

Saved Monitors can display whether the latest run changed compared with the previous run.

Possible copy:

> Public-source response changed since the previous run.

or

> No payload-level change detected since the previous run.

This should be framed as public-data change detection only.

## Non-Goals

This milestone does not implement:

- production ML
- diagnosis
- treatment guidance
- patient-risk prediction
- clinical alerting
- live outbreak surveillance
- semantic search
- RAG assistant
- deep learning
- notification delivery

## Safety Boundary

Freshness and payload-change signals are operational review aids.

They do not prove:

- medical risk
- causation
- product danger
- outbreak activity
- clinical urgency
- source correctness
- personal safety
- official source completeness

## Implementation Areas To Review

Likely backend files:

- `backend/app/db/source_pull_repository.py`
- `backend/app/db/audit_repository.py`
- `backend/app/sources/registry.py`
- `backend/app/routes/sources.py`
- `backend/app/routes/saved_monitors.py`
- `backend/app/services/search_workflows/recall_search.py`
- `backend/app/services/search_workflows/drug_signal_search.py`
- `backend/app/services/search_workflows/regional_health_search.py`
- `backend/app/analytics/monitor_insights.py`
- `backend/app/schemas/sources.py`
- `backend/app/schemas/saved_monitors.py`

Likely frontend files:

- `frontend/src/components/DataSourcesPage.tsx`
- `frontend/src/components/SystemStatusPage.tsx`
- `frontend/src/components/SavedMonitorsPage.tsx`
- `frontend/src/api/sources.ts`
- `frontend/src/api/savedMonitors.ts`
- `frontend/src/styles/datasources.css`
- `frontend/src/components/SavedMonitorsPage.css`

Likely tests:

- backend source route tests
- backend source-pull repository tests
- backend saved-monitor route tests
- backend monitor-insights tests
- frontend Data Sources tests
- frontend Saved Monitors tests
- frontend System Status tests

## Recommended Implementation Sequence

1. Document expected freshness labels and payload-change labels.
2. Add deterministic review-signal helper with unit tests.
3. Extend backend schemas safely.
4. Add source route response fields.
5. Add saved-monitor response fields only if existing stored data supports them.
6. Add UI copy with clear limitations.
7. Add tests for normal, stale, unknown, error, first-seen, unchanged, and changed cases.
8. Update README and demo script after implementation.

## Interview Value

This milestone shows mature product engineering because it improves trust and review quality before adding heavier AI.

It strengthens the story:

> DAV AI uses audit history and payload hashes to make public-data changes visible and explainable before production ML.

## Recommended UI Language

Use:

- Source freshness
- Review signal
- Public-data change
- Payload changed
- Payload unchanged
- Last successful retrieval
- Last attempted retrieval
- Source unavailable
- Source status unknown

Avoid:

- risk score
- safety score
- medical risk
- clinical urgency
- product danger
- outbreak probability
- source is correct
- source is complete

## Example UI Copy

### Fresh source

> This source has a recent successful retrieval in DAV AI audit history.

### Aging source

> This source has not been refreshed recently. Verify official source pages before relying on the result.

### Stale source

> DAV AI has not successfully refreshed this source within the expected window. Treat results as needing source verification.

### Source error

> The latest retrieval attempt failed. DAV AI may show older stored context or no result for this source.

### Payload changed

> The public-source response changed compared with the previous saved-monitor run.

### Payload unchanged

> No payload-level change was detected compared with the previous saved-monitor run.

## Current Safety Positioning

Source freshness and payload-change intelligence should help users understand operational data quality. It should not create the impression that DAV AI can determine whether a product, drug, food, supplement, cosmetic, or public-health signal is personally safe or unsafe.

DAV AI should continue to point users back to official FDA, openFDA, USDA FSIS, or other authoritative public sources for verification.
