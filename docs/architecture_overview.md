# DavAI Architecture Overview

- **Updated:** July 1, 2026
- **Status:** Current portfolio architecture overview. This describes the implemented prototype and its boundaries, not a production healthcare deployment.

## Product Architecture

DavAI is organized around a search-first public-record workflow:

```text
React frontend
  -> typed API clients
  -> FastAPI routes
  -> query understanding and source planning
  -> source adapters and public/curated records
  -> normalized records, source roles, scores, summaries
  -> audit events, source pulls, payload hashes
  -> result UI, source verification, Explain These Results, Monitors
```

The strongest user-facing workflow is Safety Record Search. Focused Pharmacy, Food, and Cosmetic pages remain available for deeper module-specific review.

## Frontend Modules

| Area | Files / modules | Purpose |
|---|---|---|
| App shell and routing | `frontend/src/App.tsx`, `frontend/src/types/navigation.ts` | Page state, URL page handling, nav grouping, assistant context lifecycle. |
| Search-first home | `Hero.tsx`, `UniversalSafetySearch.tsx`, `SafetyWorkspace.tsx`, `ProductScanTeaser.tsx` | Primary search entry, examples, focused workflow cards, experimental label helper entry. |
| Safety Record Search | `PublicSafetySearchPage.tsx`, `frontend/src/api/realWorldSafety.ts` | Main user path for cross-source public safety results, evidence types, source details, verification links, and assistant context. |
| Focused safety pages | `PharmacySafetyPage.tsx`, `FoodSafetyPage.tsx`, `CosmeticSafetyPage.tsx` | Module-specific searches for drug recall/event, food recall/public-health-alert, and cosmetic event data. |
| Explain These Results | `AskDavAIChat.tsx`, `frontend/src/api/assistant.ts` | Context-grounded result explanation UI using sanitized structured context builders. |
| Saved Searches | `SavedMonitorsPage.tsx`, `frontend/src/api/savedMonitors.ts` | Repeatable public-record checks, manual runs, run history, insights, audit links. |
| Source trust and operations | `DataSourcesPage.tsx`, `AuditHistoryPage.tsx`, `SystemStatusPage.tsx` | Source registry, audit history, source-pull provenance, system/data-quality visibility. |
| Help and education | `AboutPage.tsx`, `FaqPage.tsx`, `InfoPage.tsx`, `HelpDocsSearch.tsx` | Plain-language product explanation, FAQ, and static documentation search. |
| ProductScan beta | `ProductScanPage.tsx` | Experimental label text/OCR input helper. It does not make safety decisions. |

## Backend Services

| Area | Files / modules | Purpose |
|---|---|---|
| FastAPI app | `backend/app/main.py` | App setup, middleware, CORS, route registration. |
| Safety Record Search | `backend/app/routes/real_world_safety.py`, `backend/app/services/search_workflows/real_world_safety_search.py` | Cross-source search orchestration for public safety records. |
| Query understanding | `real_world_query_understanding.py`, `query_normalization.py`, `foodradar_query_normalization.py` | Normalization, selected typo cleanup, intent/category handling, identifier detection. |
| Source planning | `real_world_source_planner.py` | Chooses relevant source adapters for a query instead of querying every source blindly. |
| Evidence summary | `safety_intelligence_summary.py`, `identifier_check.py` | Groups evidence by role and tells users what to verify. |
| Focused workflows | `recall_search.py`, `drug_signal_search.py`, `everyday_safety_search.py`, `cosmetic_signal_search.py` | Module-specific search, scoring, source context, and result contracts. |
| Assistant | `assistant_service.py`, `assistant_guardrails.py`, `llm_provider.py`, `backend/app/routes/assistant.py` | Bounded answer generation from current result context, guardrails, mock default provider, optional configured LLM providers. |
| Static docs retrieval | `static_docs_chunking.py`, `static_docs_ingestion.py`, `static_docs_retrieval.py`, `static_docs_embeddings.py`, `static_docs_semantic_preview.py` | Documentation chunking/search/preview foundation. This is not the primary product RAG path. |
| Semantic similarity | `semantic_similarity_service.py`, `recall_semantic_candidates.py`, `drug_signal_semantic_candidates.py`, `backend/app/nlp/semantic_similarity_preview.py` | Deterministic similarity previews and candidate helpers. |
| Saved Searches | `saved_monitors.py`, `saved_monitor_repository.py`, `scheduled_monitor_refresh.py`, `run_due_saved_monitors.py` | Persisted repeatable searches, manual runs, history, scheduling foundation, CLI guardrails. |
| Audit and provenance | `audit_events.py`, `audit_repository.py`, `source_pull_repository.py` | Audit history, source-pull metadata, payload hashes, source status. |
| Reports | `reports.py`, `report_pdf.py` | Bounded PDF report generation with source and limitation context. |

## API Routes

Current backend route families include:

- `/api/v1/real-world-safety/search`
- `/api/v1/recalls/search`
- `/api/v1/drug-events/search`
- `/api/v1/everyday-safety/search`
- `/api/v1/cosmetic-events/search`
- `/api/v1/sources`
- `/api/v1/audit-events`
- `/api/v1/system/status`
- `/api/v1/system/data-quality`
- `/api/v1/saved-monitors`
- `/api/v1/reports/safety-intelligence`
- `/api/v1/docs/search`
- `/api/v1/docs/chunks`
- `/api/v1/docs/embedding-preview`
- `/api/v1/docs/semantic-preview`
- `/api/v1/semantic-similarity/preview`
- `/api/v1/assistant/chat`

Regional Health Pulse backend routes and source metadata exist as scaffold/foundation work, but the normal user-facing frontend routing/copy is not part of the primary demo path.

## API Adapters and Sources

The source registry lives in `backend/app/sources/registry.py`. Source adapters live under `backend/app/services/safety_source_adapters/`.

| Source / adapter family | Current use |
|---|---|
| openFDA drug enforcement | Drug recall/enforcement records. |
| openFDA drug event | FAERS-style public adverse-event reports. |
| openFDA food enforcement | Food and supplement recall/enforcement records. |
| openFDA cosmetic event | Cosmetic adverse-event reports. |
| openFDA NDC, drug label, DailyMed, RxNorm | Drug identity, reference, and label context. |
| openFDA device enforcement, device event, UDI | Device recall, signal, and identity context depending on query. |
| FDA public recalls and safety communications | Public FDA page/advisory context. |
| USDA FSIS | Live public API in focused FoodSignal flows; curated official-source snapshot or fallback context in some cross-source paths. |
| CPSC | Curated official-source snapshot for consumer-product recall context. |
| NHTSA vPIC and recalls | Live public vehicle decode/recall lookup paths. |
| CDC/VAERS and CDC/FDA foodborne outbreak context | Curated/demo public-data context for signal/investigation roles. |

Important source boundary:

```text
Live API != curated snapshot != public page ingestion != scaffold
```

DavAI should describe those modes plainly because they affect freshness, completeness, and what the user can infer.

## Audit and Source Trail

DavAI treats provenance as part of the product, not an internal afterthought.

Audit/source trail concepts include:

- module/workflow name
- original and normalized query
- source ID and source name
- endpoint or reference URL
- retrieval timestamp
- upstream status
- record count
- audit ID
- source-pull metadata
- payload hash where available
- transform/scoring/disclaimer version context where supported
- source issue reporting when one source fails and others still return

The UI surfaces this through result source details, Sources, Audit History, System/Data Quality, and Saved Search audit links.

## Assistant Context Boundaries

The assistant feature is branded in the UI as **Explain These Results**.

It receives structured context built by frontend helper functions in `frontend/src/api/assistant.ts`, including:

- current query
- count
- source name and endpoint
- retrieval timestamp
- audit ID
- limited top results or top records
- evidence summary for Public Safety Search
- source checked/failed summaries
- result-specific limitations

It should not receive raw payloads, private user data, PHI, or hidden source dumps.

The backend assistant route:

- validates that the requested module has matching context
- applies question/output guardrails
- uses a mock provider by default when `ASSISTANT_LLM_ENABLED=false`
- can use a configured OpenAI or Gemini provider through backend-only environment variables
- instructs the model to answer only from the provided DavAI context
- returns source citations, limitations, and safety metadata

Correct claim:

> Explain These Results is a context-grounded assistant over current visible results and source metadata.

Incorrect claim:

> DavAI has full production RAG, a vector database, autonomous web browsing, or medical reasoning.

## Monitors Concept

Monitors are repeatable public-record checks. They are implemented as saved monitor foundations internally, but user-facing language emphasizes repeatable public-data review rather than production alerting.

Current capabilities include:

- create persisted search definitions for supported modules
- list saved searches
- delete saved searches
- manually run a saved search
- view run history
- compare latest and previous counts/scores where available
- view deterministic insight/change labels
- open linked audit records

Current limitations:

- no production alert delivery
- no public scheduling UI
- no notification preferences
- prototype/demo token auth exists, but there is no production RBAC or tenant isolation
- cosmetic saved-search creation is not at full parity

## Deterministic Intelligence and AI/ML Boundaries

Implemented production-connected intelligence is mostly deterministic:

- query normalization
- identifier detection
- source planning
- evidence-role classification
- review-priority scoring
- reaction/category summaries
- source freshness/status labels
- semantic-similarity previews
- static documentation search/preview foundation

AI/ML work that should be described carefully:

- Explain These Results can call an optional LLM provider, but only with current structured result context and guardrails.
- Offline ML experiments under `backend/ml_experiments` are not imported into production routes.
- Static docs embeddings/semantic preview are foundation work, not the main user-facing production RAG system.
- ProductScan uses browser-side label text/OCR assistance, but it is experimental and does not make safety decisions.

## Testing Strategy

Backend tests cover:

- route contracts
- source adapters
- source registry/schema alignment
- query understanding and normalization
- scoring and deterministic classifiers
- semantic similarity previews
- assistant route validation and guardrails
- audit/source-pull repositories
- saved search repositories and refresh foundations
- documentation chunking/search foundations

Frontend tests cover:

- App routing and assistant context lifecycle
- Safety Record Search hierarchy and assistant context wiring
- UniversalSafetySearch behavior
- focused safety pages
- AskDavAIChat behavior
- Saved Searches user flows
- Audit, Sources, System, and helper utilities

Common validation commands:

```bash
PYTHONPATH=backend python3 -m pytest backend/tests -q
cd frontend
npm run lint
npm test -- --run
npm run build
npm run test:e2e
```

Current verified local validation:

- Backend tests: 488 passed
- Frontend lint: passed
- Frontend tests: 31 files, 282 tests passed
- Frontend production build: passed
- Playwright smoke tests: 3 passed

## Production Readiness Gaps

DavAI is credible as a portfolio-grade prototype, but the following are still future work:

- production authentication, RBAC, tenant isolation, and durable user ownership policies
- production alert delivery and notification preferences
- scheduled refresh activation in a production environment
- more complete live ingestion for curated snapshot sources
- source freshness SLAs and production observability
- full deployed smoke validation after each hosted release
- stronger entity resolution for identifiers, lots, models, NDC packages, UDI, UPC, and VIN details
- production RAG evaluation if a vector-backed documentation or source retrieval assistant is added later
- LLM safety evaluation before presenting assistant output as production-ready

## Interview Positioning

Strongest honest summary:

> DavAI is a source-aware public-record safety search product. It demonstrates full-stack engineering, multi-source integration, evidence-type separation, auditability, saved searches, and a bounded assistant that explains current results without making medical, legal, or safety-verdict claims.
