# DavAI Documentation Index

This folder is organized so a recruiter, hiring manager, or senior engineer can find the current project story quickly without mistaking historical milestone notes for the latest state.

## Start Here

- [Main README](../README.md) — current product positioning, demo flow, source modes, safety boundaries, local setup, and latest validation counts.
- [Architecture Overview](architecture_overview.md) — current full-stack architecture, source adapters, audit/provenance model, assistant boundaries, and production gaps.
- [Portfolio Demo Package](demo/PORTFOLIO_DEMO_PACKAGE.md) — recommended interview/demo narrative, demo queries, resume bullets, and screenshot checklist.
- [Operations Runbook](operations_runbook.md) — health checks, request tracing, audit/source-pull persistence checks, scheduler-lock notes, and local verification steps.

## Current Technical References

- [Real-World Safety Sources](real_world_safety_sources.md) — current source families and public-safety source coverage.
- [Real-World Safety Query Understanding](REAL_WORLD_SAFETY_QUERY_UNDERSTANDING.md) — query normalization, intent, and identifier interpretation.
- [Identifier Check API/UI Summary](Identifier_Check_API_UI_Summary.md) — NDC, UPC, VIN, UDI, model, and lot verification concepts.
- [NHTSA Recall API Integration Summary](NHTSA_Recall_API_Integration_Summary.md) and [Vehicle Recall Check UI Summary](Vehicle_Recall_Check_UI_Summary.md) — vehicle safety integration notes.
- [DrugSignal Intelligence Score](drug_signal_intelligence_score.md) — deterministic public-report scoring context.
- [Source Freshness Payload Change Design](source_freshness_payload_change_design.md) — source freshness/provenance payload design.

## Roadmaps and Plans

These are forward-looking plans, not claims that the functionality is production-ready today.

- [AI Roadmap](ai_roadmap.md)
- [Production ML Integration Roadmap](production_ml_integration_roadmap.md)
- [ProductScan AI Roadmap](product_scan_ai_roadmap.md)
- [ProductScan OCR v2 Plan](productscan/PRODUCTSCAN_OCR_V2_PLAN.md)
- [Render Cron Saved Monitors Plan](render_cron_saved_monitors_plan.md)
- [Scheduled Monitor Locking Design](scheduled_monitor_locking_design.md)
- [Vector DB / RAG Plan](architecture/VECTOR_DB_RAG_PLAN.md)
- [Vector Storage Implementation Plan](architecture/VECTOR_STORAGE_IMPLEMENTATION_PLAN.md)

## Validation Snapshot

Latest verified local baseline:

- Backend tests: 488 passed
- Frontend lint: passed
- Frontend tests: 31 files, 282 tests passed
- Frontend build: passed
- Playwright smoke tests: 3 passed

Older verification notes and checkpoint reports are archived and should not override this current baseline.

## Archived / Historical Docs

Historical milestone notes, one-off verification reports, stale progress reports, and old positioning docs live under:

- `docs/archive/checkpoints/`
- `docs/archive/verification/`
- `docs/archive/reports/`
- `docs/archive/design-history/`
- `docs/archive/legacy_repo_reference_report.md`

These files are retained for project history. They may contain old branch names, older test counts, earlier architecture assumptions, or historical wording. Use them as timeline evidence only.

## Known Limitations to Keep Visible

DavAI is a public-data safety intelligence platform prototype. It is source-grounded and audit-oriented, but it is not production healthcare software, not medical advice, not diagnosis, not a safety verdict engine, and not a production predictive AI system.

Current limitations include prototype/demo auth, no production RBAC or tenancy, selected/incomplete source coverage, some curated official-source snapshots, no production alert delivery, no complete observability/SLO program, and no production vector database-backed RAG.
