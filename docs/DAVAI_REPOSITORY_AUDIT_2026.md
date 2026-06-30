# DavAI Repository Audit - June 30, 2026

This audit reviews the current DavAI repository as a public safety intelligence
portfolio product. It focuses on what each area does, how the system connects,
what is impressive, what still looks prototype-level, and exactly what should be
changed next.

## Verification Snapshot

- Backend tests from repo root: `python3 -m pytest -q backend` -> 463 passed.
- Frontend build: `npm run build` -> passed.
- Frontend tests: `npm test` -> 31 files, 265 tests passed.
- Running backend tests from `backend/` currently fails because
  `test_refresh_real_world_safety_snapshots_cli.py` imports repo-level
  `scripts`. The README says to run `pytest` from `backend`, so either the test
  import path or docs should be corrected.
- Existing user edits were present before this report:
  `backend/app/services/safety_source_adapters/openfda_drug.py` and
  `backend/tests/test_real_world_safety_route.py`.

## Executive Summary

DavAI is not a basic CRUD app. It is a credible full-stack public-data safety
intelligence prototype with FastAPI, React, typed schemas, source adapters,
source registry, audit events, source-pull payload hashing, saved monitors,
scheduled refresh foundations, bounded assistant responses, deterministic NLP
previews, ML experiments, and strong test coverage.

The strongest product module is DrugSignal because it combines live public API
data, aggregation, deterministic scoring, reaction classification, trend
context, source/audit metadata, and careful FAERS limitations. FoodRadar,
CosmeticSignal, and RealWorldSafety are moving in the right direction, but they
need the same level of runtime provenance, freshness, change tracking, and
source-mode clarity.

The biggest product risk is truthfulness around data mode. Some flows are live,
some are live-first with snapshot fallback, some are local curated snapshots,
some are frontend-only experiments, and Regional Health Pulse is a scaffold.
That is acceptable for a portfolio project only if the UI and API make the mode,
pull time, fallback status, source status, payload hash, and limitations visible
everywhere.

## Repository Map

### Root

| Path | Purpose | Recommendation |
|---|---|---|
| `.github/workflows/ci.yml` | Runs backend tests and frontend lint/test/build/E2E on PRs and pushes. | Keep. Good portfolio signal. Consider adding backend command parity check from repo root. |
| `.gitignore` | Ignores Python, Node, env, cache, local artifacts. | Improve. It has a malformed `.DS_Storedata/...` line. Keep ignored local CPSC snapshot explicit. |
| `README.md` | Current project narrative, stack, safety boundaries, run/test commands, source modes. | Keep and update after this audit. Fix backend test command guidance or import path. |
| `MedSignal_AI_Repo_Reference_Report.md` | Legacy historical audit from an earlier app state/name. | Archive or delete. It is now misleading because it says no DB/auth/DrugSignal existed. |
| `alembic.ini` | Alembic migration config. | Keep. |
| `docker-compose.yml` | Local backend/frontend compose setup. | Improve. Frontend container runs Vite dev server, not production static serving. |
| `pytest.ini` | Root pytest config. | Keep. Important because root-level test command passes. |

### Backend Application

| Path | Purpose | Recommendation |
|---|---|---|
| `backend/Dockerfile` | Runtime backend image, installs requirements, copies `backend/app` and `data`. | Keep. Add healthcheck and decide whether scripts are needed in image. |
| `backend/.env.example` | Backend env template for DB, CORS, assistant config. | Keep. Add `AUTH_SECRET_KEY` and production warning. |
| `backend/requirements.txt` | Backend dependency pins. | Improve. `reportlab` is unpinned. |
| `backend/app/main.py` | FastAPI app, CORS, request ID middleware, route registration. | Keep. Rename legacy logger namespace `medtrek.request` to `dav_ai.request`. |
| `backend/app/audit/audit_event.py` | Builds audit event payloads with IDs, timestamps, versions. | Keep. Central to provenance. |

### Backend Routes

| Path | Purpose | Recommendation |
|---|---|---|
| `routes/recalls.py` | RecallRadar drug recall endpoint. | Keep. Needs parity with newer RealWorld source freshness. |
| `routes/drug_events.py` | DrugSignal FAERS endpoint. | Keep. Benchmark module. |
| `routes/everyday_safety.py` | FoodRadar food/supplement recall endpoint. | Keep. Add per-source freshness/change payloads. |
| `routes/cosmetic_events.py` | CosmeticSignal public cosmetic event endpoint. | Keep. Add recall-source audit/freshness as first-class output. |
| `routes/real_world_safety.py` | Cross-domain real-world safety search endpoint. | Keep. It is the best universal search backend. |
| `routes/assistant.py` | Ask DavAI route over current result context. | Keep. Modernize provider API later. |
| `routes/reports.py` | PDF safety report generation endpoint. | Keep. Ensure report claims are source-grounded. |
| `routes/saved_monitors.py` | Saved searches, manual runs, run history, insights. | Keep. Fix DB module constraints for `cosmeticsignal`. |
| `routes/sources.py` | Source registry with audit-backed freshness. | Keep. Make source mode/freshness reusable by search routes. |
| `routes/audit_events.py` | Audit history listing/detail and source-pull metadata. | Keep. Good recruiter signal. |
| `routes/system.py` | Health, system status, data quality. | Keep under Advanced/Admin UI. |
| `routes/auth.py`, `routes/profile.py` | Portfolio-demo auth/profile. | Keep with stronger production caveats and secret enforcement. |
| `routes/docs.py`, `routes/semantic_similarity.py` | Static docs search/chunk/embedding/semantic-preview endpoints. | Keep as retrieval infrastructure preview, not production RAG. |
| `routes/regional_health.py` | Regional Health Pulse scaffold endpoint. | Hide from consumer nav unless explicitly labeled experimental. |

### Backend Schemas

`backend/app/schemas/*` are Pydantic response/request contracts. They are a
major strength because the API is explicit and testable.

Key notes:

- `real_world_safety.py` includes `source_freshness` and
  `outbreak_context_found`, but the frontend TypeScript response type does not
  fully mirror those fields.
- `saved_monitors.py` supports `cosmeticsignal`, but `backend/db/schema.sql`
  constraints do not.
- `assistant.py` is strict (`extra="forbid"`) and keeps assistant context
  bounded. Keep this pattern.

### Backend Search Workflows and Services

| Path | Purpose | Recommendation |
|---|---|---|
| `search_workflows/drug_signal_search.py` | Live openFDA Drug Event workflow, top reactions, score, categories, trend, semantic preview, audit, source pull. | Keep as benchmark. |
| `search_workflows/recall_search.py` | openFDA Drug Enforcement plus FDA public notices, scoring, audit, semantic preview. | Keep. Add per-source audit instead of one primary audit only. |
| `search_workflows/everyday_safety_search.py` | FoodRadar multi-source workflow: openFDA Food, USDA FSIS, FDA notices, scoring, partial errors. | Keep. Clarify live FSIS vs snapshot modes across registry/adapters. |
| `search_workflows/cosmetic_signal_search.py` | openFDA Cosmetic Event plus FDA public notices, score, audit. | Keep. Add source freshness and trend snapshot like DrugSignal. |
| `search_workflows/real_world_safety_search.py` | Cross-source planner/fan-out/dedupe/rank/audit/freshness/identifier workflow. | Keep. This is the strategic backbone. Update stale limitations copy. |
| `search_workflows/real_world_query_understanding.py` | Normalizes queries, identifiers, expansions. | Keep. Add learned/curated synonym dictionary with tests. |
| `search_workflows/product_category_classifier.py` | Rule-based source/category hints. | Keep. Later replace/augment with lightweight classifier. |
| `search_workflows/real_world_source_planner.py` | Chooses source sets by intent. | Keep. Make source mode part of plan output. |
| `search_workflows/safety_intelligence_summary.py` | Role-based summary of recall/reference/label/signal/outbreak evidence. | Keep. Frontend must add outbreak role support. |
| `search_workflows/source_freshness.py` | Per-search freshness labels from source audit summaries. | Keep. Frontend should consume this directly. |
| `search_workflows/identifier_check.py` | Flags identifiers to verify: NDC/UPC/VIN/UDI/model/lot. | Keep. Excellent trust feature. |
| `openfda_client.py`, `openfda_drug_event_client.py`, `openfda_food_enforcement_client.py`, `openfda_cosmetic_event_client.py` | Thin live openFDA clients. | Keep. Add shared retry/rate-limit/date/pagination wrapper. |
| `usda_fsis_recall_client.py` | Live FSIS API client for FoodRadar. | Keep. Align registry/docs that currently call FSIS snapshot-only in some places. |
| `official_public_notice_search.py`, `safety_source_adapters/fda_public.py` | Live FDA public notice table/detail parser and normalization. | Keep. Add parser-health tests and DOM-change monitoring. |
| `safety_source_adapters/*` | Normalizes CPSC, FSIS, openFDA, RxNorm, DailyMed, UDI, VAERS, NHTSA, CDC outbreak records into common records. | Keep, but mark snapshot-only adapters clearly and convert highest-value ones to live-first. |
| `assistant_service.py`, `assistant_guardrails.py`, `llm_provider.py` | Context-grounded assistant with regex guardrails and mock/OpenAI/Gemini providers. | Keep. Modernize OpenAI provider and add groundedness checks. |
| `report_pdf.py` | PDF report generation with source/safety context. | Keep. Make report branding cleaner and ensure no unsupported conclusions. |
| `static_docs_*`, `semantic_similarity_service.py`, `nlp/semantic_similarity_preview.py` | Deterministic docs/search/similarity previews. | Keep as experiments. Do not call production RAG/vector search yet. |
| `auth_*` | Standard-library password hashing and signed bearer token auth. | Keep for portfolio. Require non-default secret in deployed environments. |
| `scheduled_monitor_refresh.py` | Backend scheduled refresh foundation with scheduler lock and run history. | Keep. Connect to real cron only after DB constraints are fixed. |

### Backend Data, Persistence, Jobs, ML

| Path | Purpose | Recommendation |
|---|---|---|
| `backend/app/db/database.py` | DB URL and persistence visibility. | Keep. Make memory fallback highly visible. |
| `audit_repository.py`, `source_pull_repository.py` | Audit and raw-source snapshot persistence. | Keep. Major differentiator. |
| `saved_monitor_repository.py`, `scheduler_lock_repository.py`, `documentation_chunks_repository.py`, `user_repository.py` | Persistence for saved searches, locks, docs chunks, auth/profile. | Keep. Add integration tests with a real test DB before claiming production readiness. |
| `backend/db/schema.sql` | Manual SQL schema mirror. | Improve. Missing `cosmeticsignal` constraints and may drift from Alembic. |
| `backend/migrations/versions/*` | Alembic migration history through users/profile/saved-monitor ownership. | Keep. Add migration for `cosmeticsignal` saved monitors. |
| `backend/jobs/ingest_documentation_chunks.py` | CLI-style docs chunk ingestion. | Keep. Useful RAG foundation. |
| `backend/jobs/run_due_saved_monitors.py` | CLI entry for scheduled monitor refresh. | Keep. Document root command and DB requirements. |
| `backend/ml_experiments/*` | Offline classifiers/anomaly datasets for recall reasons, reactions, review priority, monitor anomaly. | Keep under "experiments". Do not present as production ML. |
| `backend/tests/*` | Broad backend test suite covering routes, adapters, scoring, source freshness, auth, docs, monitors, ML experiments. | Keep. Strongest engineering evidence. |

### Frontend

| Path | Purpose | Recommendation |
|---|---|---|
| `frontend/package.json`, `package-lock.json` | React 19/Vite 8/TypeScript/Vitest/Playwright/Tesseract deps. | Keep. Add exact Node version in `.nvmrc` or docs because local Node is v25 but CI uses 24. |
| `frontend/Dockerfile` | Runs Vite dev server in container. | Replace for production with static build served by nginx/Caddy or platform host. |
| `frontend/src/App.tsx` | SPA router, URL state, auth gate, assistant context. | Keep. Consider extracting route map to reduce switch complexity. |
| `frontend/src/types/navigation.ts` | Page IDs and primary/advanced nav grouping. | Keep. Consumer-first nav is mostly right. |
| `frontend/src/api/*` | Typed Axios clients. | Keep. Fix RealWorldSafety type drift and add source freshness types. |
| `frontend/src/auth/AuthContext.tsx` | Frontend auth/session wrapper. | Keep. Add token expiration handling and production copy. |
| `PublicSafetySearchPage.tsx` | Active universal cross-source search result page. | Keep. Consume backend `source_freshness` directly and add outbreak role UI. |
| `PharmacySafetyPage.tsx` | Active pharmacy/drug/recall safety page. | Keep. Treat as DrugSignal quality target. |
| `FoodSafetyPage.tsx` | Active FoodRadar page. | Keep. Add per-source status/change/freshness panel. |
| `CosmeticSafetyPage.tsx` | Active CosmeticSignal page. | Keep. Add trend/freshness parity with DrugSignal. |
| `UniversalSafetySearch.tsx` | Homepage routing preview. | Keep. For public-safety queries, consider running a lightweight preview instead of only handoff. |
| `ProductScanPage.tsx`, `ProductScanTeaser.tsx`, `productScan*` utils | Frontend-only OCR/input assistance using Tesseract and deterministic extraction. | Keep labeled beta. Do not present as product verification. |
| `RegionalHealthPulse.tsx` | Sample/scaffold public-health workflow UI. | Keep hidden under Advanced/Experiments. |
| `DataSourcesPage.tsx`, `SystemStatusPage.tsx`, `AuditHistoryPage.tsx` | Advanced operations and provenance UI. | Keep under Advanced/Admin. |
| `SavedMonitorsPage.tsx` | Saved searches and run history UI. | Keep. Add clear persistence mode banner. |
| `AskDavAIChat.tsx` | Floating context-grounded assistant. | Keep. Make citations/source limitations more prominent. |
| `SourceIntegrationBadge.tsx`, `SourceDetailsDisclosure.tsx` | Source mode and detail components. | Keep. Expand source-mode mapping beyond CPSC/FSIS/NHTSA/FDA page/regional. |
| `QueryTypeahead.tsx`, `QueryNormalizationNotice.tsx` | Search UX helpers. | Keep. |
| `AboutPage.tsx`, `FaqPage.tsx`, `HelpDocsSearch.tsx`, `InfoPage.tsx`, auth/profile/onboarding pages | Support/info/auth surfaces. | Keep and reduce outdated wording. |
| `DrugSignal.tsx`, `RecallRadar.tsx`, `FoodRadar.tsx`, `CosmeticSignal.tsx` | Older standalone modules not imported by the live app. | Merge unique UI into active pages, then delete with tests. |
| `Signals.tsx` | Unused old signal cards component. | Delete. |
| `AuditPanel.tsx`, `SafeInsightCards.tsx`, `SafetyBriefingPanel.tsx` | Only used by older unused modules. | Keep only if moved into active pages; otherwise delete with old modules. |
| `FloatingSafetyReportIntake.tsx` | Not imported by the live app. | Delete or wire intentionally into active pages. |
| `assets/react.svg`, `assets/vite.svg` | Starter assets. | Delete. |
| `assets/hero.png` | Hero asset, if still used in CSS or docs. | Verify usage; keep only if visually used. |
| `frontend/src/styles/*` | Global/page styles. | Keep for now. Prune after component cleanup. |
| `frontend/src/components/*.test.tsx`, `utils/*.test.ts` | Frontend tests for active and legacy components. | Keep for active code; delete/update after component cleanup. |
| `frontend/e2e/demo-smoke.spec.ts` | Playwright smoke demo. | Keep. Add source-mode/freshness assertions. |

### Data

| Path | Purpose | Recommendation |
|---|---|---|
| `data/safety_sources/*/*_curated_records.json` | Local curated official-source snapshots used by adapters/fallbacks/tests. | Keep only as cache/fallback with explicit `refreshed_at`, `payload_sha256`, source URL, and UI label. |
| `data/safety_sources/cpsc/cpsc_demo_records.json` | Small manually selected CPSC demo subset loaded by adapter fallback. | Remove from production search path. Keep only as test fixture if needed. |
| `data/safety_sources/cpsc/cpsc_daily_products_curated_records.json` | Larger CPSC curated official snapshot. | Keep as cache until live CPSC adapter is implemented; show freshness. |
| `data/source_audits/snapshot_refresh_manifest.json` | Snapshot refresh metadata. | Keep. Fix `cpsc_recalls` vs registry `cpsc_recalls_api` ID mismatch. |
| `data/source_audits/*audit*.json` | Source exploration/audit outputs. | Move to docs/archive or keep under `data/source_audits` as developer artifacts. Do not drive runtime UI. |

### Scripts

| Path | Purpose | Recommendation |
|---|---|---|
| `scripts/refresh_real_world_safety_snapshots.py` | Pulls curated snapshots and writes manifest. | Keep. Promote into scheduled/cache refresh architecture with dry-run CI tests. |
| `scripts/audit_usa_daily_safety_apis.py`, `audit_recall_expansion_sources.py`, `audit_final_recall_enrichment_sources.py` | Source research scripts. | Keep as developer utilities; move outputs to archive. |
| `scripts/build_cpsc_demo_records.py`, `scripts/search_cpsc_demo_records.py` | Demo subset tooling. | Retire after removing demo records from runtime path. |
| `scripts/search_cpsc_snapshot.py` | Local CPSC snapshot search helper. | Keep until live CPSC adapter is done. |

### Docs

The docs folder contains valuable evidence of disciplined engineering, but it
has too many checkpoint files. This makes the project look less clean than the
code deserves.

Keep as canonical:

- `README.md`
- `docs/architecture/ARCHITECTURE_OVERVIEW.md`
- `docs/architecture/VECTOR_DB_RAG_PLAN.md`
- `docs/operations_runbook.md`
- `docs/demo/PORTFOLIO_DEMO_PACKAGE.md`
- `docs/productscan/PRODUCTSCAN_OCR_V2_PLAN.md`
- `docs/current_dav_ai_status_june_2026.md`
- this audit

Archive or consolidate:

- Repeated frontend/backend verification checkpoint docs.
- Old progress reports that conflict with the current product state.
- `MedSignal_AI_Repo_Reference_Report.md`.
- `docs/usa_safety_sources_registry.json`, unless updated from "planned" to
  actual implementation status.

## Dead, Outdated, Fake, Demo, Snapshot, and Duplicate Code

### Remove or quarantine now

1. `data/safety_sources/cpsc/cpsc_demo_records.json`
   - Current adapter loads it after the daily CPSC snapshot.
   - Even if records came from official data, the filename and selection logic
     make it look like demo data in production search.
   - Move selected examples into backend fixtures if tests need them.

2. `scripts/build_cpsc_demo_records.py` and `scripts/search_cpsc_demo_records.py`
   - Keep only as historical/dev tooling or delete after tests are migrated.

3. `frontend/src/components/Signals.tsx`
   - No live imports.

4. `frontend/src/components/DrugSignal.tsx`, `RecallRadar.tsx`,
   `FoodRadar.tsx`, `CosmeticSignal.tsx`
   - Superseded by active area pages and not imported by `App.tsx`.
   - Merge unique briefing/report UI if still desired, then remove.

5. `frontend/src/components/AuditPanel.tsx`, `SafeInsightCards.tsx`,
   `SafetyBriefingPanel.tsx`
   - Currently only used by those unused standalone components.

6. `frontend/src/components/FloatingSafetyReportIntake.tsx`
   - Not imported by active app.

7. `frontend/src/assets/react.svg`, `frontend/src/assets/vite.svg`
   - Vite starter artifacts.

### Keep but label clearly

1. Curated snapshots under `data/safety_sources`.
   - Keep as cache/fallback/test inputs.
   - Never present them as live data.
   - Show `refreshed_at`, source URL, payload hash, and fallback reason.

2. `RegionalHealthPulse`.
   - Keep as scaffold only, hidden under Advanced/Experiments.
   - Do not call it live surveillance or outbreak detection.

3. `static_docs_embeddings.py`.
   - Keep as deterministic fake embedding preview.
   - Do not call it production semantic search or RAG.

4. Assistant mock provider.
   - Keep for local demos.
   - UI should show provider/model and whether answer was mock or LLM-backed.

### Fix misleading or stale copy

- `real_world_safety_search.py` `LIMITATIONS` says some openFDA sources are
  curated even though food/drug adapters are now live-first with snapshot
  fallback.
- `README.md` still mixes "current mode" labels that differ by route.
- `docs/usa_safety_sources_registry.json` marks implemented sources as
  `planned`.
- `MedSignal_AI_Repo_Reference_Report.md` is historically useful but stale.

## Product Direction for 2026+

The product should be positioned as:

> DavAI is a source-grounded public safety intelligence workspace that turns
> fragmented public recall, adverse-event, label, identifier, and public notice
> data into explainable, auditable safety-review workflows.

The 2026+ version should feel like an AI intelligence dashboard, not a CRUD app:

- First screen: universal safety search with source-aware results, not marketing.
- Result cards: source role, source mode, retrieved time, freshness, confidence,
  exact fields to verify, and official source link.
- Detail views: separate recall/enforcement from reference identity, label, and
  signal reports.
- Visual system: clean glass panels, dense but readable intelligence layout,
  restrained motion, source/status chips, payload hash/audit details in
  expandable panels.
- Do not use fake metrics in hero/dashboard visuals. Replace decorative sample
  score/charts with live "recent source checks" or a truthful empty-state
  preview.
- Admin pages stay under Advanced/Admin, not primary consumer navigation.

## Real-Time and Live Recall System

Target architecture:

1. A source registry defines endpoint, source mode, refresh mode, cadence,
   supported filters, pagination, and source role.
2. A source runner pulls each source with timeout, retry, rate limit, and
   structured error handling.
3. A normalization layer converts source payloads into canonical records.
4. A snapshot store records raw payload, hash, retrieved_at, source status,
   query params, and transform version.
5. A diff layer compares latest payload hash and normalized record IDs against
   prior pulls.
6. Search responses include:
   - source
   - source mode
   - retrieved_at
   - last successful pull
   - fallback used
   - response status
   - confidence
   - records added/removed/changed since prior pull
7. UI shows:
   - "Live public API"
   - "Live page ingestion"
   - "Cached official snapshot"
   - "Fallback snapshot used because source timed out"
   - "No matching public record found, not a safety guarantee"

Highest-value live upgrades:

- CPSC live adapter replacing runtime demo fallback.
- RealWorldSafety FSIS live-first adapter to match FoodRadar's live FSIS
  client.
- Live-first RxNorm, DailyMed, openFDA NDC, drug label, UDI, device event,
  device enforcement where feasible.
- Daily/cron refresh job for source snapshots with manifest persisted to DB.
- One-year trend tables by category/product/source.
- "Same period last year" comparisons from stored normalized records.

## Product Search UI Coverage

Current state:

- `PublicSafetySearchPage` has strong loading/error/empty/result/source panels.
- `FoodSafetyPage`, `CosmeticSafetyPage`, and `PharmacySafetyPage` are active
  and tested, but source freshness/change parity is uneven.
- `UniversalSafetySearch` previews pharmacy/food/cosmetic but hands public
  safety queries to the full page without running the full search.
- Old standalone module components are duplicated and unused.

Add these UI states everywhere:

- Loading with source names being checked.
- Empty with "no public record found" caveat.
- Partial result with failed sources listed.
- Source unavailable with retry/time.
- Fallback snapshot used with reason and timestamp.
- Successful live result with source mode and retrieved_at.
- Ambiguous query with clarifying choices.
- Partial match with "verify exact lot/NDC/UPC/VIN/model" checklist.
- Changed since last refresh.

## Unstructured to Structured API Transformation

Already implemented:

- Adapter normalization into `NormalizedSafetyRecord`.
- FDA public notice HTML parsing and sentence extraction.
- Query normalization and identifier checks.
- Rule-based category/source planning.
- Deterministic scoring and reaction classification.
- Basic semantic/text similarity previews.

Next improvements:

- Add canonical product entity model:
  `product_name`, `brand`, `manufacturer`, `model`, `package_size`,
  `lot`, `UPC`, `NDC`, `UDI`, `VIN`, `source_field_paths`,
  `normalization_confidence`.
- Add product-name normalization:
  lowercasing, punctuation cleanup, dosage/package stripping, brand/generic
  mapping, and alias dictionaries.
- Add manufacturer matching:
  exact, normalized, alias, and fuzzy match with confidence.
- Add reason classification:
  contamination, allergen, undeclared ingredient, mislabeling, sterility,
  device malfunction, fire/burn, choking, crash/vehicle, other.
- Add semantic dedupe:
  source-specific IDs first, then normalized title/product/company/date/lot
  similarity.
- Add temporal trend analysis:
  weekly/monthly record counts by category/source/entity.
- Add grounded summaries:
  only generated from normalized fields with source citations and field-level
  provenance.

Use classic NLP first:

- Regex/identifier parsers for UPC/NDC/VIN/UDI/lot/date.
- Rule-based reason classifier with tests.
- TF-IDF/MinHash or rapidfuzz-style matching for dedupe.
- Small embeddings for candidate ranking only after deterministic filters.
- LLM only for summarizing already-selected source records, never for deciding
  whether a product is recalled.

## LLM and Agent Architecture

Do not add LangChain/LangGraph/LlamaIndex yet for the core app. The current
custom workflow architecture is clearer and safer. Agent frameworks become
worth it only when there are many tools, multi-step plans, retries, and human
approval states.

Recommended architecture:

- Keep deterministic source planners for search.
- Add a lightweight "SafetyReportAgent" service only as an orchestrator:
  1. interpret query
  2. call approved source workflows
  3. normalize records
  4. compare and dedupe
  5. build structured report
  6. pass report context to LLM for short explanation
  7. validate output against source IDs and safety policies
- No autonomous browsing for safety claims.
- Every LLM response must include citations to current result context.
- Provider should be swappable and backend-only.

Low-cost dev model recommendation:

- Keep mock provider as default for tests/local demos.
- For cheap live demos, use a low-cost "mini/flash-lite" class model with
  low temperature and short outputs.
- Modernize OpenAI integration from legacy chat completions to the current
  Responses API before expanding usage.
- Gemini Flash/Flash-Lite can be cost-effective for development, but keep the
  provider optional and disclose provider/model in UI.

## Deep Learning and Advanced Analysis

Do now:

- Reason classification with rule-based baseline and offline classifier
  experiments.
- Product/manufacturer fuzzy matching.
- Semantic dedupe preview for normalized records.
- Trend/anomaly scoring over saved monitor runs.
- Lightweight entity extraction for identifiers and product fields.

Future work:

- Embedding-backed product similarity search.
- NER model for product/manufacturer/lot/identifier extraction.
- Anomaly detection for recall spikes by category/source/manufacturer.
- Forecasting only after enough historical normalized data exists.
- Vector database RAG only for documentation/source-grounded report retrieval,
  not safety decisions.

## Data Sources and API Direction

Current source families:

- openFDA Drug Enforcement, Drug Event, Food Enforcement, Cosmetic Event.
- openFDA Drug Label, NDC, Device Enforcement, Device Event, UDI.
- RxNorm/RxNav and DailyMed.
- FDA recalls/public notices and device safety communications.
- USDA FSIS recalls/public health alerts.
- CPSC consumer product recalls.
- NHTSA vPIC and recalls.
- CDC/VAERS public vaccine reports.
- CDC/FDA foodborne outbreak context.
- Regional Health Pulse scaffold.

Recommended source priorities:

1. openFDA live endpoints for drugs, food, devices, cosmetics, labels, NDC.
2. FDA public recalls page for current notices missing from structured APIs.
3. USDA FSIS live recalls for meat/poultry/egg.
4. CPSC live recall API for consumer products.
5. NHTSA recalls/vPIC for vehicle queries.
6. RxNorm and DailyMed live lookups for drug identity/label context.
7. VAERS and foodborne outbreak data as signal/context only with strong caveats.
8. FDA MAUDE/device event data for device signals.
9. openFDA food event/CAERS for food/supplement/cosmetic adverse-event context.

Each source entry should store:

- live query support
- pagination support
- date filtering support
- update cadence
- rate limits
- last successful pull
- last failure
- normalized record count
- source role
- official URL

## Backend Improvement Roadmap

Must fix now:

- Remove CPSC demo records from runtime search.
- Add frontend RealWorldSafety type parity for `source_freshness`,
  `outbreak_context_found`, and `outbreak_context` role.
- Fix saved monitor DB constraints for `cosmeticsignal`.
- Fix README/backend pytest command mismatch.
- Fix `.gitignore` malformed line.
- Pin `reportlab`.
- Update stale source-mode copy and docs.

High impact:

- Shared public-source HTTP client with retries, rate limits, date filters,
  pagination, and structured upstream errors.
- Source mode registry consumed by backend and frontend.
- Per-source audits for FoodRadar/CosmeticSignal/RecallRadar, not only
  aggregate audits.
- Change detection: added/removed/changed records since last pull.
- Source refresh job that writes DB source pulls, not just local JSON.

Production readiness:

- Require DB for production saved monitors/audit history.
- Require `AUTH_SECRET_KEY` outside local dev.
- Add structured JSON logging and deployment health probes.
- Add CORS env validation.
- Add real DB integration tests in CI via service container.
- Add alerting/error budgets for source fetch failures.

## Frontend Improvement Roadmap

Must fix now:

- Remove/merge unused standalone module components.
- Expand source integration badges for openFDA, RxNorm, DailyMed, UDI, VAERS,
  FSIS live, and snapshot fallback.
- Display backend `source_freshness` directly in Public Safety Search.
- Add "source unavailable" and "fallback used" panels to every search page.
- Add persistence mode banner to Saved Searches.

UI polish:

- Replace fake/decorative hero score/chart/orbs with truthful source workflow
  preview or real recent source status.
- Use dense, premium dashboard panels rather than large marketing cards.
- Standardize result card anatomy:
  source badge, role, retrieved time, confidence, exact identifiers to verify,
  official link, audit link.
- Keep Advanced/Admin pages visually quieter and clearly labeled.

## Exact Implementation Plan

### Sprint 1: Truthfulness and cleanup

Files to change:

- `backend/app/services/safety_source_adapters/cpsc.py`
  - Stop loading `cpsc_demo_records.json` in runtime adapter.
  - Return clear `local_curated_official_snapshot` metadata from the daily
    snapshot only.
- `data/safety_sources/cpsc/cpsc_demo_records.json`
  - Move to `backend/tests/fixtures` or delete.
- `scripts/build_cpsc_demo_records.py`
- `scripts/search_cpsc_demo_records.py`
  - Delete or move to archive.
- `data/source_audits/snapshot_refresh_manifest.json`
  - Fix CPSC source ID.
- `backend/app/services/search_workflows/real_world_safety_search.py`
  - Update stale limitations and fallback copy.
- `frontend/src/api/realWorldSafety.ts`
  - Add `source_freshness`, `outbreak_context_found`, and `outbreak_context`
    role types.
- `frontend/src/components/PublicSafetySearchPage.tsx`
  - Render backend `source_freshness`; add outbreak role display.
- `frontend/src/utils/sourceIntegrationMode.ts`
  - Add live/snapshot mappings for all registered sources.
- `backend/db/schema.sql`
- new Alembic migration
  - Add `cosmeticsignal` to saved monitor constraints.
- `.gitignore`
  - Fix malformed line.
- `backend/requirements.txt`
  - Pin `reportlab`.
- `README.md`
  - Correct test command and source-mode narrative.

Tests:

- `backend/tests/test_real_world_safety_route.py`
- `backend/tests/test_refresh_real_world_safety_snapshots_cli.py`
- `backend/tests/test_saved_monitors_route.py`
- `backend/tests/test_scheduled_monitor_refresh.py`
- `frontend/src/components/PublicSafetySearchPage.test.tsx`
- `frontend/src/utils/sourceIntegrationMode.test.ts`

### Sprint 2: Live refresh and change tracking

Files to change:

- `backend/app/sources/registry.py`
  - Add `integration_mode`, `refresh_mode`, `supports_pagination`,
    `supports_date_filter`, `source_role`.
- `backend/app/services/safety_source_adapters/base.py`
  - Add canonical source metadata and normalized record stable ID.
- `backend/app/db/source_pull_repository.py`
  - Add prior-pull lookup helpers.
- `backend/app/scoring/source_freshness.py`
  - Extend payload-change helpers to normalized-record deltas.
- `scripts/refresh_real_world_safety_snapshots.py`
  - Persist refresh results through DB option.
- `backend/app/jobs/run_source_refresh.py`
  - New job for source refresh.
- `backend/app/routes/sources.py`
  - Expose last changed/added/removed counts.
- `frontend/src/components/DataSourcesPage.tsx`
- `frontend/src/components/SystemStatusPage.tsx`
  - Show refresh stats and change deltas.

### Sprint 3: DrugSignal quality parity

Files to change:

- `backend/app/services/search_workflows/everyday_safety_search.py`
  - Add FoodRadar trend snapshot and per-source audits.
- `backend/app/services/search_workflows/cosmetic_signal_search.py`
  - Add CosmeticSignal trend snapshot, reaction categories, per-source audits.
- `backend/app/trends/*`
  - Add food/cosmetic trend builders.
- `frontend/src/components/FoodSafetyPage.tsx`
- `frontend/src/components/CosmeticSafetyPage.tsx`
  - Add DrugSignal-style intelligence panels, trends, limitations, and source
    confidence.

### Sprint 4: UI consolidation

Files to remove/merge:

- `frontend/src/components/DrugSignal.tsx`
- `frontend/src/components/RecallRadar.tsx`
- `frontend/src/components/FoodRadar.tsx`
- `frontend/src/components/CosmeticSignal.tsx`
- `frontend/src/components/Signals.tsx`
- `frontend/src/components/AuditPanel.tsx`
- `frontend/src/components/SafeInsightCards.tsx`
- `frontend/src/components/SafetyBriefingPanel.tsx`
- `frontend/src/components/FloatingSafetyReportIntake.tsx`
- associated tests only after unique behavior is ported.

Then prune CSS selectors from:

- `frontend/src/styles/drugsignal.css`
- `frontend/src/styles/recallradar.css`
- `frontend/src/styles/foodradar.css`
- `frontend/src/styles/cosmeticsignal.css`

### Sprint 5: Modern AI layer

Files to change:

- `backend/app/services/llm_provider.py`
  - Modernize OpenAI provider, keep Gemini optional, add provider metadata.
- `backend/app/services/assistant_service.py`
  - Add answer-grounding validation against provided citations.
- `backend/app/services/assistant_guardrails.py`
  - Add structured policy categories and output checks.
- `backend/app/schemas/assistant.py`
  - Add citation IDs/source URLs and unsupported-question metadata.
- `frontend/src/components/AskDavAIChat.tsx`
  - Show provider/model, source citations, and context limitations upfront.

## Recruiter-Facing Explanation

DavAI is a full-stack AI product engineering portfolio project for public
safety intelligence. It helps users search and interpret public recall,
adverse-event, food safety, cosmetic, vehicle, drug label, and product-safety
records while preserving source links, retrieval timestamps, audit trails,
payload hashes, and safety limitations.

What makes it impressive:

- It is not just a UI. It has a real FastAPI backend, public API clients,
  source adapters, database schema, migrations, audit persistence, source-pull
  hashes, scheduled monitor foundations, and broad tests.
- It treats AI responsibly. Ask DavAI answers only from current result context,
  includes source citations/limitations, and refuses medical advice or
  causation claims.
- It shows product judgment. DrugSignal separates public reporting patterns
  from causation, uses deterministic scoring, classifies reactions, and explains
  confidence/limitations.
- It is architected for growth. RealWorldSafety already plans sources,
  normalizes records, dedupes, ranks, tracks source failures, and returns
  provenance.

What still looks student-level:

- Some UI files are duplicated or unused.
- Some source modes are stale or inconsistent.
- Curated/demo snapshots are too close to runtime product paths.
- Production deployment hardening is incomplete.
- The docs folder needs consolidation.

The next thing to build:

Make every module match DrugSignal's level of source-grounded intelligence:
live-first public data, per-source status, source freshness, changed-since-last
refresh, clear fallback labeling, structured normalization, confidence, and a
premium intelligence-dashboard UI.

