# Pharmaceutical explorer implementation report

Date: 2026-10-21 (America/Chicago). Implementation is left uncommitted on `chore/stabilize-davai-v3`. No push, merge, deployment or publication authorization occurred.

## Recovery and preservation

Source recovery branch: `recovery/pharma-before-simplification-20261021`, commit `0e4c5112f0075199d98bc0436b0f890b5b3b2a11`. An alternate Git index captured 580 reviewed source/documentation files, including relevant untracked pharmaceutical ingestion, research, release-builder and test work. Every captured blob was checked against its pre-change SHA-256. The active branch, HEAD (`4ca92a9`) and user index were left unchanged. This is the authorized recovery commit, not a simplified-implementation commit.

Private environment files, ignored datasets, SQLite files, regulatory downloads, PostgreSQL backups, and large research/evidence artifacts were excluded from newly staged recovery content. They remain locally intact. Historical source receipts were never rewritten. The initial inventory lists tracked, modified, untracked and ignored paths in `inventory.json`. Excluded data/evidence remain in place; the source branch is not a backup of those large local datasets.

The frozen database remains **4,825,108,480 bytes** and its SHA-256 matches both before and after verification:

`87779eda6b06c75f10603762b18f8c66a5cb7b12ed37d47ab1bf9b4825639c71`

The original verifier reports `Publication approved: False`; no receipt or metadata was changed to approve publication. `git diff --name-only -- data docs/evidence docs/finalization/evidence` is empty. All SQLite serving uses read-only, query-only connections. Existing release versions, archives, label/identity tables, raw ingestion/research data and backup paths were not deletion targets.

## Original and final structure

| Area | Original | Final |
|---|---:|---:|
| Files under backend/app | 162 | 56 |
| Files under frontend/src | 146 | 12 |
| Combined application source | 308 | 68 (77.9% reduction) |
| Files under backend/tests | 90 | 35 |
| Files under frontend/e2e | 2 | 2 |
| OpenAPI paths | 38 | 11 |
| Explicit Python runtime requirement pins | 27 | 14 |
| npm runtime dependencies | 4 | 3 |
| Frontend dist bytes, all emitted/copied files | 700,818 | 258,987 (63.0% reduction) |
| Frontend dist bytes, independently gzipped files | 176,794 | 82,151 (53.5% reduction) |

Counts use nonignored files under the stated directories, including tests, styles, assets, public-data fixtures and retained offline code; they exclude bytecode/cache output. They do not measure data/evidence repository storage. Baseline was built before edits using the same local toolchain. Final emitted JS is 242.32 kB and CSS 4.38 kB; original was 503.21 kB JS and 178.52 kB CSS. Container image size is not measured.

Original backend: routers for auth/profile, monitors, assistant/Ask, multi-domain live search, sources/audit/operational dashboards, semantic documentation retrieval, and reports, plus pharmaceutical ingestion/research/release modules.

Final backend: catalog and compatible stored safety routers, shared evidence/coverage, pharmaceutical PDFs, health/readiness; frozen-release repositories; separate retained offline ingestion/research/jobs. The Docker context allows only the read-only runtime files, not the offline tree.

Original frontend: auth provider, dozens of pages/components, multi-domain navigation, assistant, OCR, dashboards and clients, and approximately thirty style modules.

Final frontend:

```text
src/
  App.tsx, App.test.tsx, App.css, index.css, main.tsx
  api/client.ts, drugCatalog.ts, reports.ts
  components/StoredDrugCatalog.tsx, StoredDrugCatalog.test.tsx
  test/setup.ts, evidence.json
```

The existing StoredDrugCatalog was simplified into search/product selection, responsive evidence panels, freshness/source information, and a native keyboard-accessible PDF dialog. The exact selection survives back/refresh. Loading, missing/empty evidence, errors/retry, partial identity and source limitations remain explicit. Legacy service-worker caches are retired.

## Removed features and deletion evidence

Removed public application features: LLM/Ask/chat, RAG/embedding/vector retrieval, saved monitors/jobs, auth/accounts/profiles, food/consumer/cosmetic/vehicle search, OCR/ProductScan, Regional Health Pulse, semantic similarity, public audit/query-history and operational dashboards. Associated exclusive schemas, clients, components, styles, assets and tests were removed.

**302 files were deleted**; every path and reason is listed in `deleted-files.json`. `removal-plan.json` records the backend import closure and `INVENTORY.md` explains the dependency method. Each deletion was checked against its verified recovery blob before unlinking. An AST check found zero retained Python references to deleted modules. Mixed files were edited, including main, the existing PDF route/schema/renderer, release repository, API client, StoredDrugCatalog and consumer-label regression tests. PDF infrastructure was retained and adapted.

Retained for preservation: all pharmaceutical normalization, membership/identity, recall matching/applicability, consumer eligibility, P0-1 label admission, P0-2 gate/readiness, frozen releases and build scripts. Offline PostgreSQL repositories/migrations and FDA ingestion/communications tooling remain reproducible. Historical research/experiment datasets and their standalone tests remain offline; they are not imported by the runtime. Mixed-domain source-audit/snapshot scripts remain historical offline tooling where they include pharmaceutical source capture. None are exposed by the application or packaged into its image. Original architecture plans remain historical documents; the current architecture is `docs/architecture/PHARMACEUTICAL_EXPLORER.md`.

## API routes

Eight paths retained: `/`, `/health`, `/ready`, `/api/drugs/search`, `/api/drugs/{product_id}`, `/api/drugs/{product_id}/safety`, `/api/drugs/{product_id}/safety/{section}`, and `/api/drugs/{product_id}/timeline` (GET).

Three paths added: `GET /api/coverage`, `GET /api/drugs/{product_id}/evidence`, and `POST /api/v1/reports/pharmaceutical`.

The compatible safety/timeline API retains eligible label and curated-communication evidence without adding extra primary UI capabilities. Ingredient search now joins sealed ingredient membership, including combination products without a matching product alias. Monthly summaries read existing `ae_monthly` rows without imputing absent months as zero.

Thirty previous paths removed (some supported multiple HTTP methods; before/after OpenAPI specifications preserve exact method/schema details):

- `/api/drugs/{product_id}/ask`
- `/api/v1/assistant/chat`
- `/api/v1/audit-events/`
- `/api/v1/audit-events/{audit_id}`
- `/api/v1/audit-events/{audit_id}/source-pull`
- `/api/v1/auth/login`
- `/api/v1/auth/me`
- `/api/v1/auth/signup`
- `/api/v1/cosmetic-events/search`
- `/api/v1/docs/chunks`
- `/api/v1/docs/embedding-preview`
- `/api/v1/docs/search`
- `/api/v1/docs/semantic-preview`
- `/api/v1/drug-events/search`
- `/api/v1/everyday-safety/search`
- `/api/v1/pharma/releases/semaglutide`
- `/api/v1/profile`
- `/api/v1/real-world-safety/search`
- `/api/v1/recalls/search`
- `/api/v1/regional-health/search`
- `/api/v1/reports/safety-intelligence`
- `/api/v1/saved-monitors`
- `/api/v1/saved-monitors/{monitor_id}`
- `/api/v1/saved-monitors/{monitor_id}/insights`
- `/api/v1/saved-monitors/{monitor_id}/run`
- `/api/v1/saved-monitors/{monitor_id}/runs`
- `/api/v1/semantic-similarity/preview`
- `/api/v1/sources`
- `/api/v1/system/data-quality`
- `/api/v1/system/status`

See `routes-before.json` and `routes-after.json` for complete machine-readable contracts, including methods. FastAPI documentation/schema infrastructure remains at `/docs`, `/redoc` and `/openapi.json`.

## PDF implementation and privacy

`POST /api/v1/reports/pharmaceutical` accepts only product_id, required plain-text name (1–100 characters), and optional strict integer age (0–120). Extra fields, control characters and oversized bodies are rejected. The UI automatically populates the report title and read-only selected drug; the renderer derives the same title from the validated identity.

`drug_evidence` supplies both the explorer and renderer with the same frozen product, linked recall records, component AE summaries/top reactions/months, release ID, source dates/URLs and interpretation limits. The adapted existing ReportLab renderer uses BytesIO and escaped paragraphs, emits repeated table headers/page numbers and distinguishes NDC labeler from recalling firm. It includes identity/formulation/identifiers, recall dates/status/classification/reason/lots, report/serious counts, reaction activity, monthly trends, reporting dates, release/source vintages, citations and disclaimers. Names/ages never change the evidence or produce medical advice.

No names/ages are persisted, placed in URLs, filenames or request logs. No permanent PDF or temporary server report file is created. Browser fields reset on close/Escape or successful download. Both successes and validation failures have no-store response headers. Sources are official-URL allowlisted for presentation; report requests accept neither arbitrary URLs nor filesystem paths and perform no external fetches.

Resource controls: 4096-byte request bodies, 2 concurrent renders/process, 5 requests/client/minute, at most 4096 rate-limit client keys, evidence <=1.5 MB, <=200 linked recalls and <=20 ingredients, <=50 reactions and <=78 months per ingredient, output <=5 MB. Excess evidence is rejected explicitly, never silently omitted. Slots release on failure. Rate state contains only IPs/timestamps and is bounded/pruned. Limits are process-local; ingress controls remain a deployment prerequisite.

A real report was generated and all eight rendered pages visually inspected, including long monthly/reaction tables, references and pagination. Desktop/mobile screenshots were also visually reviewed. QA samples use synthetic report names and remain temporary, not application storage.

## Dependency and packaging changes

Removed from API runtime requirements (retained under offline/dev dependency groups where needed): `Pygments`, `alembic`, `certifi`, `httpcore`, `httpx`, `idna`, `ijson`, `iniconfig`, `packaging`, `pluggy`, `psycopg-binary`, `psycopg`, `pytest`.

FastAPI, Pydantic, Uvicorn, dotenv and ReportLab plus their pinned runtime support remain. `requirements-offline.txt` retains PostgreSQL, migration, streaming and HTTP build dependencies; `requirements-research.txt` retains DuckDB/PyArrow; `requirements-dev.txt` adds pytest/PDF extraction. A clean isolated environment installed the runtime requirements and imported/read the artifact without importing psycopg or httpx.

npm: removed `tesseract.js`; npm pruned 13 packages and updated package-lock.json. React, React DOM and Axios remain in use; development/test tools remain. No UI framework or model dependency was added.

Backend Docker packages only the runtime allowlist, uses an unprivileged user and defaults to deployed mode (denied). Frontend Docker builds static assets and serves them with Nginx. Compose is loopback-only, does not load private .env files or require PostgreSQL, and mounts the artifact read-only. `docker compose config --quiet` passed. Container images were not built; this is a packaging validation limitation.

CI installs development/offline dependencies for the retained full suite with a disposable PostgreSQL service, checks syntax/runtime imports, and runs frontend lint/unit/build and mocked browser journeys. Real artifact browser/contract checks are local opt-ins because the database is deliberately not committed. README, frontend docs, environment examples and current architecture were updated.

## Test counts and observed results

| Check | Original | Final observed result |
|---|---:|---|
| Backend cases | 901 collected from recovery source | **466 passed**, 0 skipped, 17.41 s with isolated temporary PostgreSQL |
| Frontend cases | **292 passed** before changes | **6 passed** |
| Browser cases | Prior suites were obsolete; no baseline execution claimed | **4 passed**, 8.5 s, including real offline search-to-PDF |
| Final edited PDF/admission tests | — | **42 passed** after final small edits |
| Python syntax/imports | — | Passed; runtime does not import PostgreSQL/HTTP clients |
| TypeScript compilation | — | Passed via production build |
| ESLint | — | Passed |
| Vite production build | Passed baseline | Passed final |
| Artifact verifier/checksum | Expected digest matched before edits | Passed after edits; publication approval remains false |
| API smoke/OpenAPI | 38 original paths captured | Health, readiness, search, coverage, evidence and PDF passed; 11 paths |
| Compose syntax | — | Passed |
| git diff --check | — | Passed |

The first baseline collection in backend/.venv lacked DuckDB/PyArrow; a complete recovery-source collection using the existing root .venv found 901 cases. Original backend success is not claimed. The first retained run passed 405 with 27 PostgreSQL skips; the final full run used a newly initialized isolated PostgreSQL cluster under /tmp and passed all 466 tests. No existing application database or backup was used. Test-node comparison records 481 removed/replaced names and 46 added/replaced names (net 435 fewer); renamed/rewritten tests account for part of those numbers. Frontend has 286 fewer unit cases because the old pages/features were removed, with new focused journey coverage supplemented by real-browser tests. Tests were not removed to hide failures.

All original pharmaceutical release-build, matching, ingestion, normalization and research tests remain except Ask-only behavior. P0-1 assertions remain against surviving consumer surfaces; mixed Ask tests were converted to direct evidence regressions, and historical PostgreSQL API tests now verify the retained offline repositories. New checks cover ingredient-only membership search, source attribution boundaries, PDF content/injection/age/headers/privacy/limits, missing/tampered artifacts, publication gates and real search-to-report behavior. Detailed receipts are in `verification/`.

## Remaining blockers and Antigravity handoff

1. **Publication remains unauthorized.** `publication_validated=false` is unchanged and deployed environments deny serving. Integrity is not approval; do not simply flip the flag or weaken the gate.
2. Recall coverage is partial; AE analytics are an ingredient cohort and retrospective revised snapshot. Preserve these limitations in all future UI/API/report changes. Review data quality and coverage before publication.
3. The 4.83 GB artifact remains the source of truth. A smaller production artifact must be a separate versioned, rebuilt-and-validated release; no table/data reduction occurred here.
4. Before multi-worker/public serving, review ingress-wide rate/body/time limits, proxy/client-address policy, private request logging, cache controls, monitoring, and artifact permissions. Current PDF limits are intentionally per process.
5. Build/test the actual container images in the target environment, review image/dependency patch levels, exercise cold-start checksum latency and memory/concurrency, and perform publication/accessibility/security acceptance. Container configuration and clean Python runtime were verified here; public operation was not authorized or tested.

Recommended next step: Antigravity should review this uncommitted source diff and the recovery/removal/verification receipts, then propose a separate publication-authorization and artifact-packaging change. Obtain explicit authorization before committing this implementation, pushing, merging or deploying. The cleanup is implemented and verified locally; it is not declared production-ready.
