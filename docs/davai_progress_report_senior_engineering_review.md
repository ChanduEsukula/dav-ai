# DavAI Progress Report — Senior Engineering Portfolio Review

**Review date:** June 25, 2026  
**Repository:** `/Users/chanduesukula/dav-ai`  
**Reviewed branch:** `docs/source-expansion-checkpoint`  
**Reviewed commit:** `6a51f02` (`source-expansion-checkpoint-v1`)  
**Review posture:** Read-only engineering and portfolio assessment. No application logic was changed.

## 1. Executive Summary

DavAI is a full-stack public safety intelligence prototype that helps users search, compare, and interpret fragmented public records from FDA/openFDA, USDA FSIS, CPSC, NHTSA, NLM/RxNorm, DailyMed, CDC/FDA outbreak sources, and VAERS-oriented vaccine signal data. Its central engineering problem is not simply “search a recall API.” It is the harder problem of combining records that have different schemas, identifiers, update patterns, evidence meanings, and safety limitations into one explainable review workflow.

The current flagship experience is Public Safety Search. It performs deterministic query normalization, detects selected identifiers, plans which sources are relevant, runs source adapters, normalizes heterogeneous records, preserves evidence roles, returns partial results when a source fails, and exposes source and audit context. Supporting modules cover pharmacy, food, cosmetics, saved monitors, system status, audit history, PDF reporting, documentation retrieval, and an experimental browser-side ProductScan OCR workflow.

This is a strong graduate-level portfolio project. It is substantially more mature than a normal CRUD application because it includes:

- heterogeneous public-data integration;
- typed backend and frontend contracts;
- a 21-source registry;
- PostgreSQL/Alembic persistence;
- audit events and source-pull provenance;
- stable SHA-256 payload hashes;
- deterministic scoring and classification;
- source freshness and payload-change signals;
- manual and scheduled-monitor foundations;
- PDF generation;
- browser OCR;
- documentation retrieval and semantic-preview foundations;
- offline ML experiments; and
- broad automated testing.

The project feels close to a credible product prototype, but not to a production public-safety or healthcare platform. Its strongest qualities are provenance, safety wording, source-role separation, testing discipline, and visible restraint around causation and medical claims. Its largest gaps are production identity and tenancy, automated ingestion, deployment verification at the current commit, operational monitoring, data-quality evaluation, frontend/backend contract drift, documentation sprawl, and the absence of a production ML or RAG evaluation pipeline.

**Overall portfolio assessment: 9/10 for a graduate student project.** It is ready to discuss seriously in interviews when framed as a source-aware public-data intelligence platform rather than as a deployed medical AI system.

## 2. Repository Review Scope

The review covered the repository’s 452 tracked files through file inventories, symbol and test inventories, configuration inspection, current documentation, recent Git history, and content-level review of the main implementation paths.

### Main areas reviewed

- **Backend application:** `backend/app/`
  - FastAPI application and middleware
  - API routes
  - Pydantic schemas
  - source clients and adapters
  - search workflows
  - scoring, classification, trends, and monitor analytics
  - audit, source-pull, saved-monitor, scheduler-lock, and documentation repositories
  - PDF generation
  - assistant guardrails and provider abstraction
  - documentation retrieval, chunking, embeddings, and semantic-preview code
- **Backend tests:** `backend/tests/`
  - 55 test files and 378 direct test declarations, with additional parametrized cases
  - fixtures for CPSC, FDA public pages, NHTSA recalls, and VIN decoding
- **Offline ML:** `backend/ml_experiments/`
  - review-priority, monitor-anomaly, recall-reason, and reaction-theme experiments
  - weak-label datasets and evaluation utilities
- **Database:** `backend/db/schema.sql`, `backend/migrations/`
  - 11 Alembic revisions
  - source registry, audit events, saved monitors, monitor runs, scheduler locks, source pulls, raw snapshots, and documentation chunks
- **Frontend application:** `frontend/src/`
  - React application shell and URL state
  - routed product pages
  - typed API clients
  - query normalization and routing
  - safety briefing utilities
  - ProductScan OCR and image-quality checks
  - source and audit surfaces
  - responsive and accessibility-oriented CSS
- **Frontend tests:** component, utility, application, and Playwright smoke coverage
- **Data:** `data/`
  - curated official-source snapshots
  - source audits and refresh manifests
  - CPSC, drug, food, device, vaccine, and outbreak records
- **Scripts:** `scripts/`
  - source audits
  - snapshot refresh
  - CPSC demo/snapshot tooling
- **Configuration and delivery:** Dockerfiles, Docker Compose, GitHub Actions, pytest, Vite, TypeScript, ESLint, Playwright, environment examples, PWA assets, and service worker
- **Documentation:** 71 Markdown files under `docs/`, plus the root README and historical repository reference report
- **History:** recent commits and tags, especially source-freshness, UDI, VAERS, outbreak-context, and FDA safety-communication milestones

Generated caches, dependency directories, build artifacts, `.git`, virtual environments, and binary image assets were not treated as source-review targets.

## 3. Current Product Vision

DavAI’s current product idea is a **public safety intelligence assistant and verification workspace** built over fragmented government and public datasets.

The vision includes:

- recall and enforcement intelligence;
- adverse-event signal review;
- foodborne outbreak and investigation context;
- medical-device identity and advisory context;
- government/public API aggregation;
- structured and unstructured record normalization;
- plain-language safety explanations;
- exact-identifier verification;
- source transparency;
- auditability and reproducibility; and
- longitudinal monitoring.

The project has clearly evolved from “display structured API results” into an intelligence layer with a repeatable pipeline:

```text
User query
  -> deterministic query understanding
  -> source planning
  -> adapter execution
  -> normalized records
  -> evidence-role classification
  -> bounded summary and verification guidance
  -> source freshness, audit, and provenance
  -> optional monitoring or report generation
```

That evolution matters. A raw API viewer can show records, but it does not explain whether a record is a recall, identity reference, label, adverse-event report, outbreak investigation, or advisory. DavAI increasingly preserves those distinctions rather than flattening all safety-related information into a misleading binary answer.

The best current product positioning is:

> DavAI is a source-aware public safety intelligence and recall-verification platform that helps users locate and interpret public records without converting incomplete evidence into unsupported safety or causation claims.

## 4. Current Features Implemented

### Public Safety Search

`backend/app/services/search_workflows/real_world_safety_search.py` and `frontend/src/components/PublicSafetySearchPage.tsx` implement the broadest workflow.

Current capabilities include:

- typo and phrase correction;
- brand-to-generic context;
- VIN, NDC, UPC, and UDI-oriented detection;
- domain hints for drugs, food, devices, vehicles, vaccines, and consumer products;
- intent-based source planning;
- concurrent source execution with per-source timeouts;
- partial-result behavior;
- normalization into a shared record contract;
- deduplication and relevance/date sorting;
- identifier-verification guidance;
- evidence-aware summary generation;
- official-source links;
- source audit summaries; and
- source freshness/provenance details.

This is the project’s strongest recruiter demo because it shows search, data engineering, source orchestration, safety design, and frontend explanation in one flow.

### Recall intelligence

RecallRadar and the consolidated Pharmacy/Public Safety surfaces search public enforcement records, normalize result fields, calculate deterministic review-priority scores, and preserve audit metadata.

Why it matters: public recall records are difficult to scan and compare directly. DavAI makes the fields reviewable while reminding users to verify the exact product, lot, package, model, or identifier.

### Drug adverse-event signals

DrugSignal uses openFDA Drug Event / FAERS-style data to aggregate top reactions, calculate a deterministic signal score, classify reaction themes, compare against stored prior searches, and expose semantic-similarity previews.

Why it matters: adverse-event reporting patterns answer a different question from recalls. The implementation correctly states that reports do not prove causation, incidence, personal risk, or medical urgency.

### Food safety

FoodRadar combines openFDA Food Enforcement, USDA FSIS coverage, and FDA public notices. It supports query-intent logic, normalized records, review-priority sorting, source status, and official verification language.

Why it matters: food safety spans multiple agencies and data formats. Multi-source, fail-soft behavior is a stronger engineering signal than a single API call.

### Cosmetic safety

CosmeticSignal searches public cosmetic-event reports, extracts products, reactions, outcomes, and signal summaries, and also includes normalized FDA public recall notices.

Why it matters: it demonstrates reuse of the public-data workflow in a domain where adverse-event reports are particularly easy to overinterpret.

### Medical-device intelligence

Recent source expansion adds:

- openFDA device enforcement records;
- openFDA device adverse-event reports;
- openFDA UDI identity/reference records; and
- FDA Medical Device Safety Communications.

Why it matters: a device question may require identity verification, recall evidence, signal reports, and advisory context. Those layers should not be treated as equivalent.

### Vaccine signal review

The `cdc_vaers` adapter and source-planning path provide curated VAERS signal records for vaccine-oriented queries.

Why it matters: this expands beyond recall-only search while preserving the critical boundary that a VAERS report is not proof that a vaccine caused an event.

### Foodborne outbreak context

The CDC/FDA foodborne outbreak adapter adds pathogen, food vehicle, state, illness, hospitalization, death, status, and investigation context.

Why it matters: an active investigation may be relevant before, after, or without a formal recall. The application explicitly avoids treating investigation context as automatic proof against a branded product.

### Source registry, freshness, and provenance

`backend/app/sources/registry.py` contains 21 registered sources. Source pages expose descriptions, endpoints, update cadence, audit-backed freshness status, last retrieval context, and persistence visibility.

Search workflows can preserve:

- source ID and endpoint;
- normalized query;
- retrieval timestamp;
- upstream status;
- record count;
- transform and score versions;
- request ID;
- source-pull ID;
- raw public-source snapshot;
- stable payload hash; and
- payload-change status.

Why it matters: provenance is the project’s clearest senior-engineering differentiator.

### Audit History

Audit APIs and UI support filtering, detail review, URL state, CSV export, trace-copy actions, and source-pull metadata.

Why it matters: a reviewer can trace an output to its source, query, timestamp, transform, and persistence record.

### Saved Monitors

Saved Monitors support persisted monitor definitions, duplicate prevention, manual runs, run history, latest/previous comparisons, deterministic change insights, payload-change labels, and links to audit events. A scheduler CLI, database lock, safe execution limits, and due-monitor logic form a future Cron foundation.

Why it matters: this introduces longitudinal review rather than one-time search.

Current limitation: production Cron and alert delivery are not enabled. Cosmetic monitor support is also inconsistent across schema, manual-route, and scheduled-refresh code.

### PDF report generation

The backend produces bounded PDF reports for recall, drug-signal, food, and cosmetic workflows. The report intake avoids PHI fields and includes public-data and medical-safety disclaimers.

Why it matters: it turns search output into a portable artifact while preserving source limitations.

### ProductScan OCR

ProductScan is now more than a roadmap item. It provides:

- local image preview;
- browser-side Tesseract OCR;
- image-size, brightness, contrast, and file-size warnings;
- extraction of possible product, brand, NDC, UPC, lot, and date terms;
- user confirmation before routing; and
- no-image-storage language.

Why it matters: it is an honest multimodal input-assistance prototype.

Current limitation: it is not a CNN, vision transformer, product-recognition model, or verified barcode/identifier resolver. OCR output remains user-reviewed text.

### Documentation retrieval and RAG foundations

DavAI includes:

- allowlisted static documentation search;
- deterministic Markdown chunking;
- documentation-chunk persistence;
- a deterministic fake embedding interface;
- semantic-preview retrieval; and
- a Help Docs Search UI with cited file paths and line ranges.

Why it matters: this is a sensible low-risk first retrieval domain.

Current limitation: there is no production vector database, production embedding provider, retrieval evaluation suite, or citation-grounded generative answer pipeline.

### Ask DavAI backend

The backend includes a bounded assistant route, context schemas, OpenAI/Gemini provider abstractions, a disabled-by-default mock mode, input guardrails, output checks, citations, and limitation handling.

Current limitation: `assistantContext` is currently fixed to `null` in the routed frontend, so Ask DavAI is intentionally not an active user-facing feature in the current application path.

### Testing and CI

The latest source-expansion checkpoint reports:

- **439 backend tests passed**
- **253 frontend tests passed**
- **frontend production build passed**

The current GitHub Actions workflow is configured to run:

- backend pytest;
- frontend lint;
- frontend Vitest;
- TypeScript/Vite production build; and
- Playwright Chromium smoke tests.

The latest checkpoint did not report a fresh lint or Playwright result, so those should be rerun before claiming current release readiness.

## 5. Technical Architecture Review

### Backend framework

The backend uses FastAPI, Pydantic, httpx, psycopg, Alembic, ReportLab, and Uvicorn.

Strengths:

- clear route/service/schema separation;
- reusable search workflows used by routes and monitors;
- typed response models;
- request-ID middleware;
- source-specific adapter boundaries;
- audit and provenance persistence;
- explicit source and safety errors;
- deterministic transformations; and
- good testability.

Weaknesses:

- direct database connections per operation with no pool;
- broad exception handling in some workflows;
- limited retry/backoff/circuit-breaker behavior;
- no rate limiting or abuse controls;
- prototype/demo token auth but no production RBAC or tenancy;
- saved-monitor DB failures now fail closed in deployed mode, but other persistence surfaces still need a deployment-mode audit;
- legacy logger names were cleaned during the recruiter-readiness pass;
- no consistent dependency pin for `reportlab`; and
- no production metrics, distributed traces, SLOs, or incident alerting.

### Frontend framework

The frontend uses React 19, TypeScript, Vite, Axios, Vitest, Testing Library, Playwright, Tesseract.js, and a PWA shell.

Strengths:

- typed API clients;
- explicit loading/error/empty states;
- responsive layouts;
- focus-visible and reduced-motion support;
- URL query restoration;
- stale-request protection;
- progressive disclosure for technical source details;
- strong component and utility tests; and
- careful zero-result and causation copy.

Weaknesses:

- hand-built URL/query routing instead of a full router;
- very large components, including a Public Safety page over 1,300 lines;
- a large CSS footprint with several files above 700–1,500 lines;
- duplicated old and consolidated product surfaces;
- backend/frontend contract drift for UDI, outbreak roles, and `source_freshness`;
- incomplete integration-mode labels for newer curated sources;
- assistant backend not connected to routed result context; and
- no visual-regression suite.

### API and source structure

The application has separate APIs for recalls, drug events, cosmetics, everyday safety, real-world/public safety, sources, documentation, audits, system status, saved monitors, reports, regional health, semantic similarity, and the assistant.

The adapter pattern is the right choice. Each adapter owns source-specific loading, query matching, normalization, payload hashing, and error semantics, while `NormalizedSafetyRecord` gives the orchestration layer a shared contract.

The primary architectural caveat is that many “API” sources in Public Safety currently use curated official-source snapshots. The source registry and UI generally disclose this, but the project should make that distinction uniformly visible for every new source.

### Database and storage

The schema is more mature than a typical portfolio application. It includes:

- source registry;
- audit events;
- saved monitors;
- monitor runs;
- scheduler locks;
- source pulls;
- raw source snapshots; and
- documentation chunks.

Strengths:

- migrations are versioned;
- runtime registry and SQL seeds are tested for alignment;
- raw payload reads are intentionally not exposed through provenance APIs;
- stable hashes support reproducibility;
- public-data-only boundaries are documented.

Weaknesses:

- no user or tenant ownership;
- no retention/deletion/export policy;
- no queue or durable ingestion-job model;
- no connection pooling;
- no backup/restore evidence at the current checkpoint; and
- no pgvector or production retrieval index.

### Testing strategy

Testing is a major strength. Coverage includes:

- source adapters and source planning;
- route contracts;
- scoring and classifier boundaries;
- audit and source-pull repositories;
- source freshness;
- scheduled monitors and locks;
- documentation retrieval/chunking/embedding previews;
- assistant refusals and unsafe-output replacement;
- frontend query state and routing;
- no-result safety language;
- ProductScan OCR states;
- source integration labels;
- component behavior; and
- Playwright demo smoke paths.

The next maturity step is not simply “more tests.” It is stronger contract and evaluation testing:

- generated OpenAPI-to-TypeScript compatibility;
- source-role parity tests across backend and frontend;
- golden query sets with precision/recall;
- live-source smoke tests behind controlled flags;
- visual regression;
- PDF rendering regression;
- accessibility automation; and
- production-like persistence tests.

### Error handling and observability

The system has request IDs, structured log events, per-source failure status, partial results, system pages, and audit history. That is production-minded.

It is still prototype-level because it lacks centralized telemetry, retry policy, source SLOs, schema-drift alarms, queue visibility, alerting, and explicit production degraded-mode behavior. Silent in-memory saved-monitor fallback is useful for local tests but risky in a deployed system because a write may appear successful without being durable.

### Separation of concerns

The backend separation is generally strong. The frontend is less clean because the product evolved quickly: standalone branded components, consolidated pages, historical styles, and newer Public Safety components now coexist. The correct next refactor is to consolidate shared evidence, result, source, audit, and boundary components after the current product contract is frozen.

### Production-like versus prototype-level

Production-like:

- typed APIs;
- migration discipline;
- source registry;
- audit/provenance;
- payload hashing;
- request IDs;
- fail-soft source orchestration;
- CI;
- broad tests;
- safety boundaries.

Prototype-level:

- snapshot-heavy source ingestion;
- no auth or tenancy;
- no production scheduler/alerts;
- no operational dashboards or SLOs;
- no current deployment verification for the newest source expansion;
- limited dataset evaluation;
- no production ML/RAG pipeline;
- frontend contract drift;
- documentation inconsistency; and
- large, rapidly evolved UI components.

## 6. AI / Deep Learning / RAG Opportunity Review

### 6.1 RAG over Safety Documents and APIs

RAG is a strong fit when it is used to explain and cite evidence, not to issue safety verdicts.

A responsible DavAI RAG workflow could:

- retrieve FDA, USDA, CPSC, CDC, NHTSA, and NLM records relevant to a query;
- retrieve long public notices, labels, communications, and investigation pages;
- summarize lengthy recall notices;
- compare multiple records across agencies;
- answer “what does this record mean?” questions;
- explain evidence differences in simple language;
- cite exact records or document sections;
- state when available context is insufficient; and
- preserve source, version, retrieval time, and checksum metadata.

The repository already has useful prerequisites:

- deterministic documentation chunking;
- allowlisted corpus selection;
- chunk IDs and content hashes;
- a documentation-chunk table;
- embedding-provider interfaces;
- semantic-preview retrieval;
- audit and request-ID patterns; and
- assistant guardrails.

The recommended first production-aligned RAG use case is a **Safety Source Guide**, not a product-specific answer engine. It should answer questions such as:

- What is the difference between a recall and an adverse-event report?
- What should I verify in an NDC, UDI, VIN, UPC, or lot number?
- What does an FDA safety communication mean?
- Why does a no-result search not prove safety?

Guardrails should require citations, refuse personal medical advice, distinguish retrieved facts from generated explanation, and return “insufficient support” when retrieval is weak.

### 6.2 NLP for Messy and Unstructured Data

NLP can add substantial value because many public notices are inconsistent, verbose, HTML-heavy, or only partially structured.

Useful extraction targets include:

- product names;
- brands and manufacturers;
- symptoms and adverse effects;
- affected populations;
- dates;
- geographic locations;
- severity or urgency language;
- recall reasons;
- regulatory actions;
- remedies;
- lot/model/package identifiers;
- pathogens and food vehicles; and
- relationships among recalls, communications, and investigations.

Realistic techniques:

- named entity recognition for products, organizations, dates, locations, pathogens, and identifiers;
- document classification for recall, advisory, signal, investigation, and reference roles;
- text classification for recall-reason categories;
- entity resolution across brands, generics, manufacturers, NDCs, UDIs, and model names;
- semantic search using transformer embeddings;
- duplicate and near-duplicate clustering;
- topic clustering for adverse-event narratives;
- extractive summarization for high-stakes source fidelity; and
- constrained abstractive summarization with citations.

The current rule-based recall-reason and reaction-theme classifiers are good baselines. They provide interpretable categories and safety tests before a transformer model is introduced.

### 6.3 Deep Learning and Neural Network Opportunities

Deep learning should be added only where it outperforms simpler methods on a measured task.

Good text-focused opportunities:

- transformer-based severity or review-priority classification;
- sentence embeddings for semantic matching;
- cross-encoder reranking for retrieved records;
- clustering similar recalls or adverse-event narratives;
- sequence or temporal models for source-specific trend detection;
- language models for citation-grounded summaries; and
- learned entity linking across agencies.

CNNs are not the natural first choice for DavAI’s text-heavy records. They become relevant if ProductScan evolves into image understanding:

- package-label region detection;
- barcode or symbol localization;
- logo/brand recognition;
- package-type classification;
- defect/image anomaly detection; or
- text-region enhancement before OCR.

For ProductScan, a vision transformer or OCR-specific multimodal model may eventually be more useful than a classic CNN alone. The current Tesseract implementation is an appropriate prototype because it keeps images local and forces user confirmation. It should not be described as deep learning implemented by DavAI.

### 6.4 Predictive Safety Intelligence

DavAI could eventually detect or prioritize:

- emerging product-safety signals;
- increases in adverse-event reporting;
- geographic clusters;
- recurring foodborne pathogen/vehicle patterns;
- manufacturers or categories with repeated enforcement actions;
- changes in recall frequency or classification;
- similarity between historical recalls and new complaints;
- source outages or schema changes; and
- unusual payload or record-count changes.

A realistic signal-detection design would:

1. ingest source data on a schedule;
2. normalize entities and timestamps;
3. deduplicate records;
4. calculate source-aware baseline rates;
5. compare recent windows with historical windows;
6. generate an operational review signal;
7. attach supporting records and confidence; and
8. require human review.

Important cautions:

- public reports are incomplete and biased;
- reporting volume is not incidence;
- duplicate reports can inflate apparent trends;
- source policy changes can look like real-world spikes;
- geographic fields may be missing or misleading;
- false positives can cause unnecessary alarm;
- false negatives can create false reassurance;
- correlation is not causation; and
- public-safety predictions can have regulatory and reputational consequences.

The correct output language is “public-data signal requiring review,” not “this product caused harm” or “an outbreak is occurring.”

### 6.5 AI Guardrails and Responsible AI

DavAI should preserve and expand its current guardrails:

- never provide diagnosis or treatment guidance;
- never recommend starting, stopping, or changing medication;
- never infer personal risk from public data;
- cite every source-grounded answer;
- separate source facts from model interpretation;
- show confidence and retrieval sufficiency;
- use “public-data signal” and “review priority” language;
- require human review for high-impact conclusions;
- log retrieval inputs, model/version metadata, citations, and refusals;
- avoid storing PHI or private health narratives;
- test adversarial prompts and unsupported-answer behavior;
- maintain regression sets for causation and zero-result claims;
- evaluate citation precision and unsupported-claim rate;
- support rollback and model/version comparison; and
- show clear “not enough information” responses.

The project’s current decision to keep offline ML experiments out of production routes is responsible. The next step should be evaluation infrastructure, not a larger model.

## 7. Innovation Assessment

DavAI is more innovative than a normal CRUD application because it combines heterogeneous public sources and preserves what each type of evidence actually means. The novel value is not any single score or UI card. It is the combination of source planning, normalized records, evidence roles, provenance, exact-identifier guidance, bounded summaries, monitoring foundations, and responsible limitations.

Source transparency matters because public safety data is partial, delayed, and easy to misinterpret. A system that shows where information came from, when it was checked, how it was transformed, and what it cannot prove is more credible than a fluent but opaque “AI answer.”

Senior engineers are likely to be impressed by:

- the adapter architecture;
- migration/registry alignment tests;
- fail-soft orchestration;
- audit and payload hashing;
- the distinction among recall, reference, signal, outbreak, and advisory evidence;
- explicit non-causation language;
- broad automated testing; and
- the decision to keep experimental ML offline.

The project needs more originality and depth in measured AI behavior. Most current “intelligence” remains deterministic. That is a good safety decision, but an AI-focused portfolio should eventually include one rigorously evaluated retrieval or NLP model with a clear baseline, dataset, metrics, error analysis, and production boundary.

| Dimension | Rating | Assessment |
|---|---:|---|
| Product idea | **9/10** | Meaningful public-good problem with a clear trust angle. |
| Technical execution | **8.5/10** | Strong full-stack breadth, provenance, migrations, tests, and adapters; some drift and scale debt remain. |
| AI potential | **9/10** | Excellent fit for retrieval, NLP, entity resolution, clustering, and signal detection. |
| Current AI implementation | **6.5/10** | Good baselines, OCR, semantic previews, and guardrails, but no production model or RAG evaluation. |
| Portfolio strength | **9/10** | Strong graduate portfolio when presented honestly and concisely. |
| Interview storytelling | **9/10** | Clear problem, tradeoffs, safety decisions, and architecture depth. |
| Production readiness | **4/10** | Missing identity, tenancy, ingestion operations, alerting, SLOs, and current deployment verification. |

## 8. Fit for a University of St. Thomas Graduate AI Student Portfolio

DavAI represents a graduate AI student well because it connects AI thinking with software and data engineering rather than treating AI as an isolated notebook.

### AI and data engineering relevance

- heterogeneous source ingestion;
- schema normalization;
- source and evidence taxonomy;
- semantic similarity;
- document chunking and embedding interfaces;
- weak-label experiments;
- classification baselines;
- trend and anomaly framing;
- evaluation utilities;
- provenance and model-safety thinking.

### Software engineering relevance

- React/TypeScript frontend;
- FastAPI/Pydantic backend;
- PostgreSQL and Alembic;
- typed API boundaries;
- Docker and CI;
- tests across layers;
- request logging;
- job and lock design;
- PDF output;
- error and degraded-state handling.

### Public-good and social-impact angle

The project addresses a genuine public problem: safety information exists, but it is fragmented and difficult to interpret. The strongest social-impact feature is the refusal to transform partial evidence into a confident safety verdict.

### Full-stack and product thinking

The repository shows end-to-end ownership: data source selection, backend integration, persistence, frontend design, operational tooling, documentation, testing, deployment planning, and interview positioning.

### Strong interview talking points

- “I designed evidence roles because a recall, adverse-event report, and safety communication do not mean the same thing.”
- “I used deterministic scoring first because high-stakes outputs need explainability and regression tests.”
- “I preserve source pulls and payload hashes so outputs can be traced.”
- “I kept ML experiments offline until I had a responsible evaluation plan.”
- “I built fail-soft multi-source search because government APIs and public pages can be incomplete or unavailable.”
- “I added browser OCR as input assistance, but require user confirmation and do not treat OCR as verified identity.”

The project should be described as **AI-ready and AI-assisted**, not as a production deep-learning platform.

## 9. Gaps and Weaknesses

### Product and scope

- The project has many surfaces and historical names. A recruiter can lose the main story.
- Public Safety Search should remain the primary narrative; other modules should support it.
- The evidence taxonomy is stronger in the backend than in the frontend.

### Live data and ingestion

- Many Public Safety adapters use small curated official-source snapshots.
- UDI, VAERS, outbreak, and safety-communication expansions are not live ingestion pipelines.
- Refresh scripts exist, but automated scheduled source ingestion is incomplete.
- There is no source schema-drift monitoring or backfill system.

### Authentication and data ownership

- No authentication, RBAC, user ownership, or tenant isolation.
- Saved monitors and audit history are not scoped to a user or organization.
- There are no retention, deletion, or export controls.

### Operations

- Production Cron is not enabled.
- Alert delivery is not implemented.
- No centralized metrics, traces, SLOs, or paging.
- Database access does not use a connection pool.
- Saved monitors can fall back silently to memory.
- No rate limiting, quotas, or abuse protection.

### Frontend/backend contract drift

The current frontend `realWorldSafety.ts` contract does not include:

- the UDI identifier key;
- the `outbreak_context` role;
- the `outbreak_context_found` flag; or
- the backend `source_freshness` array.

As a result, newer source roles can degrade into “Other,” and the UI reconstructs freshness from older fields instead of consuming the dedicated contract. FDA safety communications also lack a first-class advisory role.

### Maintainability

- Several frontend files are very large.
- CSS is extensive and distributed across many overlapping historical styles.
- Standalone and consolidated module components coexist.
- The source registry dictionaries are not perfectly uniform.
- Documentation contains many historical checkpoints with stale counts and claims.

### AI and evaluation

- No production ML model.
- No production vector store.
- No model registry, feature lineage, drift detection, or rollback.
- Weak-label datasets are synthetic or handcrafted.
- No large, reviewed golden dataset.
- No benchmark against strong baselines.
- No measured retrieval precision, citation accuracy, or hallucination rate.

### Deployment

Historical documents describe Vercel, Render, and Supabase deployments, but the newest source-expansion commit has not been verified in those documents. Current deployment readiness should not be claimed without a fresh migration, smoke, and source-mode check.

### UI and accessibility

- Accessibility foundations exist, but no comprehensive automated accessibility audit is present.
- Visual grouping should more clearly separate recalls, references, signals, investigations, and advisories.
- ProductScan requires careful mobile and low-powered-device testing because browser OCR can be expensive.
- PDF output lacks a visual regression workflow.

## 10. Six Advanced Innovative Application Ideas

### 10.1 Cross-Agency Safety Evidence Graph

**Datasets/APIs:** FDA/openFDA enforcement, NDC, UDI, device events, DailyMed, RxNorm, CPSC, USDA FSIS, NHTSA, VAERS, outbreak investigations, safety communications.

**AI/ML method:** entity resolution, graph construction, graph embeddings, relationship scoring, and rule-based evidence typing.

**User problem:** users cannot easily see that a brand, generic ingredient, manufacturer, device model, recall, advisory, and adverse-event report may refer to related but non-equivalent entities.

**Why innovative:** it turns disconnected rows into an explainable evidence network while preserving source meaning.

**MVP:** link records with exact identifiers and normalized names; show a graph of product, company, recall, signal, and advisory nodes.

**Advanced version:** learned cross-source entity matching, temporal graph analysis, confidence scoring, and graph-based retrieval for cited briefings.

### 10.2 Emerging Public-Data Signal Detector

**Datasets/APIs:** recurring openFDA events, VAERS public data, device events, cosmetic events, saved-monitor history, source freshness, and payload hashes.

**AI/ML method:** seasonal baselines, change-point detection, robust z-scores, Bayesian monitoring, and later sequence models.

**User problem:** reviewers cannot manually notice gradual or sudden increases across repeated public-data pulls.

**Why innovative:** it combines operational provenance with time-aware signal detection rather than relying on raw counts.

**MVP:** scheduled snapshots and deterministic threshold alerts with source-quality warnings.

**Advanced version:** source-specific baselines, duplicate correction, uncertainty intervals, geography-aware trends, and human-reviewed signal labels.

### 10.3 Recall Similarity and Root-Cause Explorer

**Datasets/APIs:** recall reasons, product descriptions, classifications, manufacturers, categories, and historical enforcement records.

**AI/ML method:** transformer embeddings, cross-encoder reranking, topic clustering, and recall-reason classification.

**User problem:** reviewers struggle to find similar historical recalls or recurring failure patterns.

**Why innovative:** it supports comparative investigation rather than simple keyword matching.

**MVP:** embed normalized recall text and show the five most similar records with shared terms and source citations.

**Advanced version:** cluster recurring root causes by manufacturer/category, track changes over time, and generate evidence-grounded comparison briefs.

### 10.4 Cited Safety Brief Generator

**Datasets/APIs:** normalized DavAI records, official notices, source registry, public labels, safety communications, and outbreak documents.

**AI/ML method:** hybrid retrieval, reranking, constrained RAG, citation validation, and claim-level grounding checks.

**User problem:** official notices are long, technical, and distributed across sources.

**Why innovative:** the output would explain multiple evidence types without treating them as equivalent.

**MVP:** generate a short brief from selected records with mandatory inline citations and a fixed limitations section.

**Advanced version:** role-specific briefs for consumers, pharmacists, analysts, and public-health teams with claim-to-source traceability and automated citation verification.

### 10.5 Multimodal Product Identity Resolver

**Datasets/APIs:** user-provided package images, OCR text, barcodes, NDC, UPC, UDI, RxNorm, NDC Directory, CPSC product fields, and recall records.

**AI/ML method:** OCR, barcode detection, vision-language models, logo recognition, entity resolution, and confidence calibration.

**User problem:** users may not know the exact searchable product name or identifier.

**Why innovative:** it connects the physical package to structured public records while keeping the user in control.

**MVP:** improve current ProductScan with barcode decoding, field-aware extraction, and exact identifier validation.

**Advanced version:** multimodal matching across package image, label text, manufacturer, shape, and public product records with calibrated uncertainty.

### 10.6 Geographic Safety Context Map

**Datasets/APIs:** outbreak states, recall distribution patterns, CPSC/NHTSA geography where available, public-health open data, and source freshness.

**AI/ML method:** geocoding, spatial clustering, temporal aggregation, anomaly detection, and uncertainty visualization.

**User problem:** reviewers cannot easily understand where a recall, outbreak investigation, or public-data signal is relevant.

**Why innovative:** it combines evidence type, time, geography, and source confidence in one review surface.

**MVP:** map explicit source-provided states and distribution regions without inference.

**Advanced version:** statistically controlled cluster detection, regional trend comparisons, source-coverage overlays, and analyst-reviewed alerts.

## 11. Recommended AI Roadmap

### Phase 1: Stronger Data Intelligence

- define a versioned unified evidence schema;
- add first-class recall, reference, label, signal, outbreak, and advisory roles;
- normalize source registry metadata;
- connect the frontend directly to `source_freshness`;
- implement live ingestion where reliable;
- add scheduled snapshots, idempotency, and schema validation;
- create cross-source entity IDs;
- build golden query and matching datasets;
- measure precision, recall, duplicate rate, and source coverage.

### Phase 2: RAG Assistant

- use the existing documentation chunking and storage foundation;
- add a real embedding provider behind a development flag;
- add pgvector/Supabase Vector or an equivalent evaluated store;
- implement hybrid keyword/vector retrieval;
- add cross-encoder reranking if needed;
- require citations and retrieval sufficiency;
- expose a bounded Source Guide Assistant;
- evaluate citation precision, grounded-answer rate, refusals, and unsupported claims.

### Phase 3: Signal Detection and ML

- create scheduled historical datasets;
- add time-window baselines;
- evaluate severity/review-priority classifiers;
- cluster similar recalls and adverse-event narratives;
- add anomaly and change-point detection;
- calibrate confidence;
- perform source-specific and class-specific error analysis;
- keep outputs human-review oriented.

### Phase 4: Deep Learning and Multimodal

- add barcode and identifier decoding;
- improve OCR preprocessing;
- evaluate package-label region detection;
- test vision-language extraction against a labeled package dataset;
- compare CNN/vision-transformer methods only where images add measurable value;
- preserve local processing or explicit privacy controls;
- require user confirmation before searching or saving.

### Phase 5: Portfolio-Ready Demo and Production Foundations

- freeze one canonical demo journey;
- deploy the latest migrations and source modes;
- record current smoke evidence;
- add auth and ownership;
- enable scheduled jobs with monitoring;
- add source and model dashboards;
- publish an architecture diagram and evaluation report;
- include screenshots and a short demo video;
- prepare concise interview stories and measured results.

## 12. What to Build in the Next 3 Days

### Day 1: Contract and documentation coherence

- Update the frontend Real World Safety types for UDI, outbreak context, advisory context, and `source_freshness`.
- Give UDI, VAERS, outbreak, and safety-communication sources accurate integration-mode labels.
- Make the evidence-role taxonomy consistent across backend summary, frontend grouping, and result badges.
- Choose one current architecture/status document as the source of truth and mark older docs as historical.
- Update the demo script to use the newest source-expansion examples.

**Deliverable:** one truthful source/evidence contract that the API, UI, tests, and demo all share.

### Day 2: Strengthen the existing retrieval prototype

- Build a small reviewed evaluation set for Help Docs Search and semantic retrieval.
- Measure keyword baseline versus semantic-preview retrieval.
- Add expected citations and “no supported answer” cases.
- Add a bounded citation-backed answer prototype over DavAI documentation only.
- Keep external LLM use disabled by default and require retrieval citations.

**Deliverable:** one evaluated RAG-style prototype with metrics, examples, and safety tests—not merely a new endpoint.

### Day 3: Demo, deployment, and visual polish

- Group Public Safety results visibly by recall, reference, signal, outbreak, and advisory evidence.
- Run backend tests, frontend tests, lint, build, and Playwright.
- Run a fresh local smoke for UDI, VAERS, outbreak, device communication, ProductScan, Sources, and Audit.
- Apply migrations in the intended deployment environment.
- Verify current frontend/backend/database deployment and record exact evidence.
- Capture 5–7 screenshots and a 90-second demo.

**Deliverable:** a verified portfolio checkpoint tied to one commit and one concise demo narrative.

## 13. Interview Story

### 30-second version

> I built DavAI, a full-stack public safety intelligence platform using React, TypeScript, FastAPI, PostgreSQL, and Alembic. It searches and normalizes fragmented public records from agencies such as FDA, USDA, CPSC, NHTSA, NLM, and CDC-related sources. The key design decision was to separate recalls from identity records, adverse-event signals, outbreak investigations, and advisories, while preserving audit metadata and source provenance. It is a portfolio prototype, not a medical decision system.

### 2-minute version

> Public safety data is available, but it is fragmented across agencies and each source means something different. A recall record, an adverse-event report, a UDI record, and a safety communication should not be presented as the same kind of evidence.
>
> I built DavAI as a source-aware review platform. The backend performs deterministic query understanding, detects selected identifiers, plans which sources to check, runs adapters concurrently, normalizes records, and returns partial results if one source fails. It also creates audit events, stores source-pull metadata and raw public snapshots when persistence is configured, and hashes payloads for reproducibility.
>
> The frontend explains what evidence was found, what sources were checked, what the user should verify, and why a no-result search is not a safety guarantee. I also built saved-monitor foundations, PDF reports, browser OCR, documentation retrieval, and offline ML baselines.
>
> The responsible AI decision was to keep current production behavior mostly deterministic and keep experimental ML offline until I have better datasets, evaluation metrics, and rollback controls. The next step is an evaluated, citation-grounded retrieval assistant and live scheduled ingestion.

### Technical deep-dive version

> The architecture uses a registry-driven adapter pattern. Each public source has a stable ID and metadata. Source-specific adapters convert heterogeneous data into a shared `NormalizedSafetyRecord`, while the query-understanding layer applies bounded corrections and detects VIN, NDC, UPC, and UDI-oriented input. A source planner maps intent to primary and secondary sources.
>
> The search workflow executes adapter calls with source-level timeouts, records source failures without discarding successful results, deduplicates and ranks records, creates an evidence-aware safety summary, and persists per-source audit and source-pull metadata. The provenance model includes request IDs, source IDs, endpoints, query parameters, timestamps, transform versions, payload hashes, and optional raw snapshots.
>
> PostgreSQL is managed through Alembic migrations and consistency tests verify that runtime registry entries match SQL seed data. Saved Monitors reuse the same workflows and add run history, payload-change comparison, scheduler locking, and a future Cron entry point.
>
> On the AI side, I have deterministic semantic previews, documentation chunking and embedding interfaces, browser OCR, and four offline classification experiments. None are presented as clinical inference. If I productionize AI, I would start with hybrid retrieval over an allowlisted corpus, mandatory citations, a golden evaluation set, and unsupported-claim testing before adding any generative summary.

### Company-specific angles

- **Google:** search federation, relevance, typed APIs, source planning, concurrency, partial failure, evaluation.
- **Apple:** user trust, on-device/browser OCR, progressive disclosure, privacy boundaries, clear consumer wording.
- **Microsoft:** enterprise data contracts, auditability, identity/tenancy roadmap, operational controls, migration discipline.
- **NVIDIA:** embeddings, clustering, multimodal ProductScan, time-series signal detection, and why GPU acceleration is not yet necessary.
- **Healthcare/public safety:** evidence meaning, causation boundaries, official verification, source freshness, and human review.

## 14. Final Verdict

### Is this project worth continuing?

Yes. It addresses a real public-data problem, has a credible architecture, and already demonstrates unusually strong breadth for a student project.

### Is it good enough for a portfolio?

Yes. It is portfolio-ready now if presented honestly:

- source-aware public safety intelligence;
- strong full-stack engineering;
- audit and provenance;
- deterministic, explainable intelligence;
- responsible AI restraint;
- broad tests;
- clear production gaps.

### What would make it next-level?

The next-level version would not merely add more sources or another dashboard. It would demonstrate:

1. automated, monitored live ingestion;
2. one consistent evidence contract across backend and frontend;
3. an evaluated citation-grounded retrieval assistant;
4. a reviewed dataset and measurable NLP model;
5. authentication and tenant ownership;
6. production scheduler and alert operations; and
7. current deployment evidence tied to a release commit.

### What should be prioritized first?

The highest priority is **coherence and evaluation**:

- align the newest source roles and freshness contract across the stack;
- freeze one canonical product/demo path;
- create a golden query and retrieval evaluation set;
- verify current deployment;
- then add one measured AI feature.

The project does not need more hype. It needs a clean evidence taxonomy, live ingestion discipline, current deployment proof, and one AI capability whose value is demonstrated with metrics.

**Final assessment:** DavAI is a serious, above-average graduate AI/full-stack portfolio project and a credible product prototype. It is not production-ready public-safety infrastructure or a production deep-learning system, but its provenance-first architecture and responsible treatment of high-stakes public data provide an excellent foundation for both.

---

## Ask DavAI Context Assistant Update

After the initial checkpoint, Ask DavAI was wired into real result context across Pharmacy, Food, Cosmetic, and the flagship Public Safety Search workflow.

Commits:
- `9ba62a2` — Wire Ask DavAI to safety result context
- `72c919b` — Add Ask DavAI context for public safety search

Validation:
- Backend full test suite: 440 passed
- Frontend production build: passed
- Frontend full test suite: 253 passed

This assistant remains context-grounded. It uses sanitized public safety result summaries, source metadata, audit context, identifier verification guidance, and limitations. It is not full production RAG, not a clinical decision system, and not a safety guarantee engine.
