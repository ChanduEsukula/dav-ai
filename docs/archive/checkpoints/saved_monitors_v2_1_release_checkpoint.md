# Saved Monitors v2.1 Release Checkpoint

> Historical checkpoint note: This document describes DAV AI at an earlier project stage. It is retained for project history and may not reflect the current implementation. For current scope, architecture, and implemented/partial/future boundaries, see [README.md](../README.md) and [docs/current_architecture_overview.md](current_architecture_overview.md).

Date: 2026-05-12
Status: Completed and verified
Module: Saved Monitors
Project: DAV AI

## Summary

Saved Monitors v2.1 adds a stronger monitoring workflow foundation to DAV AI. Users can now save repeatable RecallRadar or DrugSignal searches, manually run checks, persist monitor state with Supabase/PostgreSQL, compare latest and previous results, prevent duplicate monitors, and open the related audit event for traceability.

This release moves Saved Monitors from a basic saved-search concept toward a real monitoring workflow.

## Completed Capabilities

- Create saved monitors for RecallRadar and DrugSignal.
- List saved monitors from persistent storage.
- Delete saved monitors with confirmation.
- Run saved monitor checks manually.
- Store latest score, previous score, latest record count, and previous record count.
- Display change indicators for score and record-count movement.
- Show `Score N/A` and `Records N/A` when no previous run exists.
- Show unchanged indicators when latest and previous values match.
- Link monitor run results to the related Audit History event.
- Prevent duplicate saved monitors for the same module and normalized query.
- Display duplicate-monitor API errors clearly in the UI.
- Preserve local-development fallback behavior when database persistence is unavailable.

## Verified UI Behavior

Manual browser testing confirmed:

- Saved Monitors page displays `Saved Monitors v2.1`.
- Monitor list includes latest score, previous score, records, previous records, and change indicators.
- New unchecked monitors show `Score N/A` and `Records N/A`.
- A monitor run updates status to `checked`.
- Running the same monitor twice shows previous values.
- Unchanged values render as `Score unchanged` and `Records unchanged`.
- View Audit appears after a successful run.
- Duplicate monitor creation shows a clear user-facing error.

## Verified Backend Behavior

Backend verification confirmed:

- Saved monitors are persisted in Supabase/PostgreSQL when configured.
- Alembic migration state is stamped at the saved monitors table revision.
- Manual run endpoint updates latest and previous result fields.
- Duplicate monitors are rejected using normalized query and module matching.
- Same query is allowed across different modules.
- Missing monitor IDs return `404`.

## Test Results

Backend:

- Full backend test suite: 76 passed.

Frontend:

- SavedMonitorsPage focused tests: 13 passed.
- Full frontend test suite: 49 passed.
- Production build completed successfully.

CI:

- GitHub Actions passed for the latest Saved Monitors v2.1 commits.

## Key Commits

- `d26dfb8` — prevent duplicate saved monitors.
- `352e854` — show duplicate saved monitor errors.
- `ca08aab` — add saved monitor change indicators.
- `9a2ba6` — verify saved monitor change indicators.

## Current Scope

Saved Monitors currently support manual run checks, Supabase persistence, latest/previous result comparison, change indicators, duplicate prevention, and audit linking.

## Future Work

- Scheduled monitor refresh.
- Alert notification design.
- Saved monitor detail page.
- Run history per saved monitor.
- Email or in-app alert preferences.
- Production deployment verification.
- More advanced trend detection over multiple runs.

## Release Assessment

Saved Monitors v2.1 is a meaningful product and engineering milestone. It demonstrates backend persistence, frontend state management, audit traceability, CI-backed testing, and manual verification discipline.

This feature is now portfolio-ready as a clear example of a healthcare safety intelligence workflow moving from search to monitoring.
