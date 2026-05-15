# MedTrek AI v2.1 Verified MVP Checkpoint

## Summary

This checkpoint verifies MedTrek AI v2.1 as a serious MVP and portfolio-grade engineering prototype. It demonstrates coherent full-stack product behavior, public-data traceability, audit persistence, explainable scoring, manual monitoring workflows, live deployment smoke verification, browser-level E2E coverage, saved monitor run history, and backend scheduled-refresh foundation work.

This is not production-ready healthcare software. It should not be used for clinical decision-making, diagnosis, treatment guidance, medication changes, regulatory action, or patient-specific care.

## Verified Checks

- Backend tests: 89 passed
- Frontend tests: 54 passed
- Frontend lint: passed
- Frontend production build: passed
- Playwright E2E smoke test: 1 passed locally
- Playwright E2E smoke test is included in GitHub Actions CI
- Live deployment smoke verification: passed
- Scheduled refresh CLI smoke check: passed with `status: ok` and `due_count: 0`

## Key Fix Included

- Commit `2e3bb54` aligned failed-upstream audit source IDs with source registry IDs.
- Registry IDs now used consistently:
  - `openfda_drug_enforcement`
  - `openfda_drug_event`

## Documentation Refresh Included

- Commit `89f49b0` refreshed docs with current test, build, migration, and audit checkpoint status.
- Commit `6c4ee1f` recorded successful live deployment smoke verification.
- Commit `1cfadd7` added this v2.1 verified MVP checkpoint note.
- Commit `c28a5b6` verified the v2.3 scheduled refresh foundation in deployment documentation.

## Demo-Safety Cleanup Included

- Commit `b60d7cd` removed placeholder Profile and Sign Up pages from the main demo flow.
- The app no longer implies that auth, RBAC, user accounts, or organization login are implemented.

## E2E and CI Coverage

- Commit `20c9d5c` added a Playwright demo smoke test.
- Commit `f97ca9c` added Playwright E2E smoke testing to GitHub Actions CI.
- The E2E smoke test verifies the implemented demo navigation path and confirms placeholder account links are not exposed.

## Current Implemented Modules

- RecallRadar
- DrugSignal
- Deterministic Safety Briefing Engine
- Audit History
- Data Sources
- System/Data Quality
- Saved Monitors v2.2 manual monitoring and run history
- Saved Monitors v2.3 scheduled refresh foundation
- Saved Monitors v2.4 scheduler guardrails

## Saved Monitors v2.2 Run History

Saved Monitors v2.2 added manual run history to the monitoring workflow. Users can save repeatable RecallRadar or DrugSignal searches, manually run checks, persist monitor state with Supabase/PostgreSQL, compare latest and previous results, review recent manual runs, view change indicators, prevent duplicate monitors, and open related Audit History events for traceability.

This added:

- `saved_monitor_runs` persistence
- `GET /api/v1/saved-monitors/{monitor_id}/runs`
- Run-history rows for successful manual runs
- Run-history rows for failed manual runs
- Frontend display of recent manual runs
- Audit links from saved monitor run history when available

## Saved Monitors v2.3 Scheduled Refresh Foundation

Saved Monitors v2.3 scheduled refresh foundation is implemented as backend infrastructure only. It includes migration `20260514_0004`, schedule metadata fields, due-refresh selection, a CLI job entrypoint, and unit tests.

This added:

- Schedule metadata fields on saved monitors
- `refresh_enabled`
- `refresh_interval_minutes`
- `next_run_at`
- `last_scheduled_run_at`
- `last_scheduled_status`
- Due-monitor repository selection
- Backend scheduled refresh service
- CLI entrypoint: `python -m app.jobs.run_due_saved_monitors --limit 10`
- Unit tests for scheduled refresh behavior

No production scheduler, auth/RBAC, public scheduling UI, or alerts were added.

## Saved Monitors v2.4 Scheduler Guardrails

Saved Monitors v2.4 scheduler guardrails were added for the backend CLI job. The job now clamps requested limits to a safe range, records `requested_limit` and `safe_limit` in the JSON summary, and has dedicated CLI guardrail tests.

This added:

- CLI default limit: `10`
- CLI minimum limit: `1`
- CLI maximum limit: `50`
- Limit clamping for accidental high values such as `--limit 500`
- JSON summary fields for `requested_limit` and `safe_limit`
- Dedicated tests for CLI limit behavior and output shape

This still does not enable production cron, alerts, auth/RBAC, or public scheduling UI.

## Live Deployment Verified

- Frontend: Vercel
- Backend: Render
- Database: Supabase PostgreSQL
- Current Alembic revision verified: `20260514_0004`
- Backend health endpoint returned healthy.
- Source registry endpoint returned the expected openFDA sources.
- RecallRadar live search worked.
- DrugSignal live search worked.
- Audit History endpoint worked.
- System/Data Quality endpoints worked.
- Saved Monitors list endpoint worked.
- Saved Monitor Run History v2.2 smoke flow passed.
- Scheduled refresh CLI smoke check passed with `status: ok` and `due_count: 0`.
- Frontend browser smoke checks passed for RecallRadar, DrugSignal, Sources, Audit, System/Data Quality, and Monitors.

## Not Production-Ready Yet

Remaining gaps include:

- No auth/RBAC.
- No production scheduler or Render Cron enabled yet.
- No alerts.
- No public scheduling UI.
- No raw source snapshot or payload hashing.
- No immutable audit/retention policy.
- No production observability dashboard/SLOs.
- No Regional Health Pulse or EnviroHealth implementation.
- No CNN/OCR, RAG, LLM chatbot, or advanced ML/anomaly detection.

## Best Demo Path

1. Run a RecallRadar search.
2. Review source and audit details.
3. Generate a role-based briefing.
4. Run a DrugSignal search.
5. Review reaction categories and trend snapshot.
6. Open Audit History.
7. Create and run a Saved Monitor.
8. Review Saved Monitor run history.
9. Review System/Data Quality.

## Next Recommended Sprint

- Add stronger scheduled-refresh job logging and operational documentation.
- Add Render Cron deployment notes, but keep production cron disabled until explicitly verified.
- Plan alerting separately from scheduled refresh.
- Add a clearer production observability roadmap.
- Decide whether the next major product step should be scheduler deployment, alerting, or auth/RBAC.