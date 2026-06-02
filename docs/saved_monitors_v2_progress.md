# Saved Monitors v2 Progress Checkpoint

> Historical checkpoint note: This document describes DAV AI at an earlier project stage. It is retained for project history and may not reflect the current implementation. For current scope, architecture, and implemented/partial/future boundaries, see [README.md](../README.md) and [docs/current_architecture_overview.md](current_architecture_overview.md).

## Status

Saved Monitors v2 foundation is implemented, tested, manually verified, and CI-validated.

## Implemented Capabilities

- Create saved monitors for RecallRadar and DrugSignal.
- Persist saved monitors in Supabase/PostgreSQL when configured.
- Fall back safely to in-memory storage for local development.
- List saved monitors newest first.
- Delete saved monitors.
- Manually run saved monitor checks.
- Update latest score, latest record count, latest audit ID, and last checked timestamp.
- Preserve previous score and previous record count after repeated runs.
- Link saved monitor results to the related Audit History detail view.
- Prevent duplicate saved monitors for the same module and normalized query.
- Allow the same query across different modules.
- Show user-facing duplicate monitor errors in the frontend.
- Confirm delete before removing a saved monitor.

## Verification

Automated verification:

- Backend Saved Monitors route tests passed.
- Full backend test suite passed.
- Frontend SavedMonitorsPage tests passed.
- Full frontend test suite passed.
- Frontend production build passed.
- GitHub Actions passed.

Manual verification:

- Created RecallRadar saved monitor.
- Ran manual check and confirmed latest result metadata.
- Navigated from saved monitor to Audit History detail.
- Verified Supabase/PostgreSQL persistence after backend restart.
- Verified duplicate same-module/query monitor is blocked.
- Verified same query with different module is allowed.

## Current Scope

Saved Monitors currently support manual monitoring workflows. Scheduled refresh and alert notifications are intentionally future work.

## Recommended Next Steps

1. Add clearer UI copy explaining that duplicate detection is based on module plus search query.
2. Add optional “Last result changed” indicator comparing latest and previous score/record count.
3. Add saved monitor detail view or expandable row.
4. Add scheduled refresh design documentation.
5. Add alert notification design documentation.
