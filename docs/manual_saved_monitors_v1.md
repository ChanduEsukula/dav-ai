# Manual Saved Monitors v1

Date: May 8, 2026

Historical/manual workflow note: this document describes the manual monitor workflow before the Saved Monitors v2 foundation. Current code now includes saved monitor definitions, manual run checks, run history, scheduled-refresh backend foundation, and DB-backed scheduler locks. Production Cron, public scheduling UI, and alerts remain disabled/not implemented.

## Purpose

Manual Saved Monitors v1 demonstrates how DAV AI can support recurring public-data safety monitoring. It was written before the current Saved Monitors v2 foundation added saved monitor definitions and manual run checks.

The goal is to prove the workflow manually using the current RecallRadar, DrugSignal, Audit History, source metadata, and Safety Briefing features.

## Manual Monitor Table

| Monitor | Module | Records | Score | Priority/Label | Latest Audit ID | Last Checked | Notes |
|---|---|---:|---:|---|---|---|---|
| eye drops | RecallRadar | 5 | 52 | Moderate | dc1352aa-d612-4e70-87ce-58491deec56e | May 8, 2026, 2:55 PM | Top matched product: CVS Health Redness Relief Lubricant Redness Reliever Eye Drops, sterile, 1 fl. oz. Recall reason: lack of assurance of sterility. FDA classification/status shown as Class II / Completed. |
| baby formula | RecallRadar | 0 | N/A | No matching records / Empty | 7cd5f7ac-6110-48ee-9937-de261fe46c12 | May 8, 2026, 2:57 PM | No FDA recall records matched the current openFDA Drug Enforcement search. This does not prove the product is safe or unsafe; it only means no matching records were returned for this query. Try brand, product name, ingredient, or category for deeper checking. |
| metformin | DrugSignal | 10 | 80 | High / Review / Strong data confidence | 782f9bf8-4a04-49c9-99b0-8be03086ace8 | May 8, 2026, 2:57 PM | DrugSignal reviewed 10 FAERS records. Score: 80/100. Top reaction concentration: 16.67%. Leading category: General / other. Top reported reaction term: Gait disturbance. Trend snapshot: insufficient history. |

## Manual Workflow

1. Open RecallRadar or DrugSignal.
2. Search a product, drug, brand, or category.
3. Record the returned record count, score, label, source timestamp, and audit ID.
4. Review the generated safety briefing.
5. Record the main findings and limitations.
6. Repeat the same query later.
7. Compare the latest result against the previous score, record count, and audit ID.

## What This Proves

This manual workflow proves that DAV AI is not only a one-time search tool. It can already support repeatable safety-monitoring behavior using existing product features.

The current workflow is:

Search → Score → Audit ID → Briefing → Repeat later → Compare change

## Product Value

Manual Saved Monitors v1 shows the product direction clearly:

- RecallRadar can track recurring product or category searches.
- DrugSignal can track recurring adverse-event signal searches.
- Audit IDs make each check traceable.
- Source timestamps make results reviewable.
- Briefings convert raw public data into role-aware safety summaries.
- No-result cases are handled responsibly without claiming that a product is safe.

## Saved Monitors v2 Direction

The current Saved Monitors v2 foundation has started converting this manual workflow into a product module. It now includes saved query name, module type, latest/previous score fields, latest/previous record-count fields, latest audit ID, and last-checked timestamp for manual runs.

Production-ready monitoring still needs:

- score change
- previous audit ID
- scheduled refresh
- alert status
- role-specific briefing history

## Demo Script

DAV AI currently supports a manual saved-monitor workflow. For example, a reviewer can search “eye drops” in RecallRadar, see five matching FDA recall records, review the Moderate score, inspect the audit ID, and read a consumer safety briefing.

The reviewer can also search “baby formula” and see that no matching records were returned, while the app still warns that no-result output does not prove safety.

In DrugSignal, a search for “metformin” returns a high signal score, reaction categories, top reported reactions, trend snapshot status, source metadata, and an audit ID.

This proves the core monitoring loop while Saved Monitors v2 continues toward production-ready persistence, scheduled refresh, and automated alerts.
