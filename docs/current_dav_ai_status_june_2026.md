# DAV AI Current Status - June 15, 2026

**Branch:** `feature/universal-safety-search`
**Baseline commit:** `226d499`
**Status:** Demo-stabilized portfolio prototype
**Source of truth:** Executable code and the validation results in this document

## Product Positioning

DAV AI is a full-stack public-data safety intelligence prototype. It helps users
search and review public FDA/openFDA and USDA safety records with visible source,
retrieval, audit, and scoring context.

The application is not a medical device, clinical decision-support system, safety
guarantee, production monitoring service, or production AI platform.

Current production behavior is primarily deterministic and rules-based. Offline ML
experiments are not connected to live routes. No production RAG, vector database,
OCR, ProductScan, or general-purpose LLM workflow is implemented.

## Canonical Routed Experience

The consolidated pages are the canonical product surfaces:

1. **Pharmacy Safety**
   - Combines official drug recall records and public FAERS reporting patterns.
   - Keeps recall and adverse-event evidence visibly separate.
   - Does not treat FAERS reports as proof of causation.

2. **Food Safety**
   - Reviews FDA food enforcement and USDA FSIS recall/public-health-alert records.
   - Covers food, supplements, meat, poultry, and egg-product searches.

3. **Cosmetic Safety**
   - Reviews public cosmetic-event reports, reactions, outcomes, and product context.
   - Does not treat reports as proof that a cosmetic caused an event.

Internal names such as RecallRadar, DrugSignal, FoodRadar, and CosmeticSignal still
appear in API payloads, audit records, report modules, and implementation details.
They are not separate routed pages in the current application.

## What Works

- Universal keyword-based safety search and category routing.
- Query normalization, typo suggestions for a controlled term list, and category hints.
- Consolidated Pharmacy, Food, and Cosmetic safety pages.
- Partial Pharmacy results when one of its two public sources fails.
- Recall review-priority sorting and compact record disclosures.
- Zero-result safety language that avoids declaring a product safe.
- Source registry, source metadata, request IDs, audit events, and source-pull snapshots.
- SHA-256 payload hashes and provenance/status surfaces.
- Audit History, Data Sources, and System Status pages.
- PDF report generation for supported internal workflows.
- Manual Saved Monitor checks for RecallRadar, DrugSignal, FoodRadar, and Regional
  Health Pulse.
- Deterministic monitor insights and saved-monitor run history.
- Regional Health Pulse sample/scaffold workflow with explicit limitations.

## Intentionally Hidden Or Restricted

### Ask DAV AI

The floating Ask DAV AI action is hidden when no real result context is available.
The current routed application does not yet wire consolidated page results into
`assistantContext`, so no visible chat entry point is shown.

The bounded assistant backend and component tests remain in the repository. They
must not be presented as an active routed demo feature until real page context is
connected and evaluated.

### Cosmetic Saved Monitors

Cosmetic monitor creation is hidden in the frontend and rejected by the create API
with HTTP 422. Database constraint and manual-run parity are incomplete.

Existing internal enum/scheduled-refresh code is not evidence of end-to-end support.
Do not advertise Cosmetic Safety monitors until schema, persistence, manual runs,
scheduled runs, UI, and tests all agree.

## Search Boundaries

Search is keyword-based. Users can search product, brand, generic, ingredient,
category, or reaction wording where supported by the relevant public source.

DAV AI does not currently provide guaranteed exact UPC, NDC, barcode, package-code,
or lot-number matching. Returned records may contain these fields for verification,
but the current source queries are not identifier-aware lookup services.

Search result counts represent records returned and processed within configured
source limits. They are not complete incidence, prevalence, exposure, or market-size
counts.

## Scoring Boundaries

- Recall and food records use `recall-review-priority-v0.2`.
- Drug reporting patterns use `drug-signal-intelligence-v0.1`.
- Cosmetic reporting patterns use `cosmetic-signal-score-v0.1`.

Each workflow now uses the same version constant for its score payload, audit
metadata, report input, and tests.

When DrugSignal or CosmeticSignal returns zero records, the UI and PDF presentation
show the result as unscored/not assessable. No numeric signal or confidence should be
interpreted from an empty result.

All scores are deterministic review aids over returned public records. They are not
medical-risk scores, clinical urgency estimates, causation findings, or official
regulatory determinations.

## Saved Monitor Boundaries

Saved Monitors currently support:

- manual checks
- run history
- latest/previous comparisons
- deterministic change insights
- audit links
- database persistence when configured
- scheduler and locking foundations

Saved Monitors do not currently provide:

- authenticated ownership
- production Cron activation
- email, SMS, push, or webhook alerts
- delivery retries or preferences
- production notification observability
- tenant isolation

The repository may use an in-memory fallback when database persistence is unavailable.
That behavior is suitable for tests/demos, not durable production monitoring.

## Not Production-Ready

The current project still lacks:

- authentication, RBAC, and user ownership
- tenant/workspace isolation
- retention, deletion, and export controls
- rate limiting and abuse protection
- robust upstream retries, backoff, caching, and circuit breaking
- guaranteed database durability and connection pooling
- production scheduler activation and alert delivery
- production metrics, traces, SLOs, and incident response
- deployed-environment and live-source release verification
- clinical validation or regulatory review

No PHI or personal medical information should be entered.

## Validation Snapshot

Validation completed locally on June 15, 2026:

| Check | Result |
|---|---|
| Backend pytest | **277 passed** |
| Frontend Vitest | **17 files, 148 tests passed** |
| Frontend ESLint | **Passed** |
| TypeScript and Vite production build | **Passed; 126 modules transformed** |
| Playwright Chromium smoke test | **1 passed** |
| `git diff --check` | **Passed** |

The Playwright smoke path verifies:

`Home -> Pharmacy Safety -> Food Safety -> Cosmetic Safety -> Sources -> Audit`

The in-app visual browser was unavailable during this sprint. Chromium Playwright
provided the executable browser check instead.

## Recommended Demo Story

1. Introduce DAV AI as a source-backed public-record review prototype.
2. Open Pharmacy Safety and explain the difference between recalls and FAERS reports.
3. Open Food Safety and show FDA/USDA source coverage.
4. Open Cosmetic Safety and emphasize reporting/causation boundaries.
5. Open Sources and Audit to demonstrate provenance.
6. Mention reports and supported manual monitors as extension workflows.

Do not demo Ask DAV AI or Cosmetic monitor creation in the current routed branch.

## Honest Portfolio Summary

DAV AI demonstrates full-stack engineering, public API integration, deterministic
scoring, source provenance, audit design, persistence foundations, PDF generation,
testing, and responsible safety boundaries.

Its strongest interview story is not autonomous AI. It is the engineering decision
to make public-data transformations inspectable, versioned, testable, and explicit
about what the evidence cannot prove.
