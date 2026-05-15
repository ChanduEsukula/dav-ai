# Render Cron Plan for Saved Monitor Refresh

## Purpose

This document describes how MedTrek AI can run Saved Monitor scheduled refreshes using Render Cron in the future.

This is a dry-run plan only. Production Cron is not enabled yet.

## Current Foundation

Implemented:

- Saved Monitor run history
- Schedule metadata fields
- Due-monitor selection
- Backend CLI job
- CLI guardrails
- Limit clamping from `1` to `50`
- JSON job summary with `requested_limit` and `safe_limit`

Not implemented:

- Alerts
- Auth/RBAC
- Public scheduling UI
- Production Cron activation
- Notification preferences
- On-call/incident workflow

## Proposed Render Cron Command

From the backend service context:

```bash
python -m app.jobs.run_due_saved_monitors --limit 10