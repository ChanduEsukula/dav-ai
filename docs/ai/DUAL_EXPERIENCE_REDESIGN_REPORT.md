# Dav AI dual-experience redesign — local review

Date: October 27, 2026. Branch preserved: `feat/private-staging-authorization`.
No commit, push, deployment, database mutation or publication authorization.

## Review artifacts and preview

- Updated isolated preview: http://127.0.0.1:15174/home (read-only API on loopback port 8000).
- [16-screen comparison board](screenshots/dual-experience-2026-10-27/dual-experience-board.png)
- [Browsable board](screenshots/dual-experience-2026-10-27/dual-experience-board.html)
- [Full-size desktop/mobile captures and receipt](screenshots/dual-experience-2026-10-27/)
- [Read-only data reconciliation](DUAL_EXPERIENCE_DATA_AUDIT.json)

These are actual implemented screens, not generated aspirational mockups. Both modes cover Home, Explorer, Ask, Operational Overview, FAQ and About, with additional populated Xanax discovery and exact-product captures. Research is shown honestly unpaired; no operator pairing credential was read. Captures use reduced motion for repeatability and show the static orb fallback. Normal-motion WebGL, independent animation, context loss and preference changes are separately browser-tested.

The pre-existing Vite preview on port 5173 inherits an API override targeting port 18000, whose process has older routes. Its environment takes priority over `.env.local`. Existing servers were left intact. Use the isolated preview to review the new endpoints and UI together; no hosting configuration was broadened.

## Resulting behavior

Searching Xanax first opens medication discovery, with admitted label-document coverage, deduplicated linked recall records and separate ingredient analytics. Only then does the user select a strength, dosage form and recorded labeler/NDC. Stored brand-base aliases can include XR: original product IDs and sealed formulation IDs remain separate. No generic-name grouping authorizes equivalence or research.

Populated results replace introductory artwork with three equal-width compact evidence panels. Recall reasons appear directly in the summary; Expand discloses original record metadata, dates, source links and per-product lot limitations. Product rows display company, strength, dosage form and NDC rather than repeating the medication name. Additional source/identity details are expandable. Existing exact-product evidence and PDF export are retained.

Everyday uses aqua/teal, larger controls, simpler product rows, plain-language summaries and suggested questions that fill the input without running research. Research Pro uses indigo/violet, denser semantic product tables, labeler/NDC filters, sorting, technical identifiers/provenance and evidence display controls. Its existing authorized cohort, retrieval and research controls are preserved. Mode changes preserve query and selected product; publication, pairing and exact-product confirmation boundaries remain in place.

Portfolio routes previously forced the Everyday theme even when Research Pro was selected; shared glass CSS also contained hardcoded teal colors. The mode now reaches every route, scene and fallback, with shared header geometry and palette-specific variables. Background palettes crossfade; reduced-motion disables the transition. Everyday always displays all evidence panels even if a Pro display filter was previously chosen.

Operational Overview now explains the actual build and serving architecture: FDA snapshots → offline ingestion/validation → frozen read-only SQLite → FastAPI and bounded retrieval → React source-linked outputs/PDF. SVG API, processing, database, retrieval and document symbols have subdued connections and expandable details. Everyday combines database/application steps; Pro exposes five technical stages and module references. BGE/FAISS and Ollama are explicitly optional, without claiming they are configured or all outputs require AI.

## Homepage content map

| Before | Implemented replacement |
| --- | --- |
| Immersive hero with same presentation in both modes | Mode-specific headline, palette and capsule; shared functioning search and CTAs |
| Repeated product-identity/traceability story | Verified release inventory with counting methods, dates and limitations |
| Repeated broad evidence promises | Four concrete capabilities: identity, recall reasons, reporting analytics and local research |
| Large generic perspective cards | Compact guided/technical comparison with working mode links |
| Repeated multi-column limitations | One expandable limitation section |
| No concise actual engineering explanation | Architecture preview linking to detailed Operational Overview |

No student-project marketing, invented FDA affiliation, fake live status, safety scores or nonfunctional download controls were introduced.

## Data audit and counting contract

All 19 manifest table counts reconciled with fresh read-only SQLite `COUNT(*)` queries. Runtime release: `dav-ai-pharma-v1-phase4b-communications-20261006`; built October 6, 2026. The immutable artifact, existing admission rules and serving/publication gates were preserved.

| Homepage metric | Verified value | Definition / scope |
| --- | ---: | --- |
| Stored label documents | 83,684 | `labels` rows, including context/withheld documents; not all admitted exact-product evidence |
| Searchable product records | 95,426 | `products` with `NORMAL_CONSUMER`; strengths and labelers remain separate |
| Stored recall records | 17,974 | `recalls` rows, including unlinked records; neither unique FDA events nor all FDA recall history |
| Ingredients with analytics | 3,174 | `ae_summary` rows by ingredient ID; not reports, patients or adverse effects |
| Distinct product NDCs | 115,585 | Distinct preserved PRODUCT_NDC values, including regulatory-only runtime records |
| Distinct package NDCs | 218,852 | Distinct preserved PACKAGE_NDC values, including regulatory-only runtime records |

The older 262,887-document extraction corpus is not the current runtime label count and is not shown as consumer label coverage. Runtime `products` has 116,741 total rows, which differs intentionally from searchable consumer products. NDC observation date is September 26, 2026; label export September 25. FAERS analytics window is January 1, 2020–June 30, 2026. Other source export/observation dates are disclosed separately; missing dates remain unknown.

### Xanax discovery audit

- 9 eligible stored brand/base-alias product matches, including 2 separate Xanax XR products; 6 sealed formulation identifiers.
- 1 distinct admitted label document, linked to 4 products (4 links). Label documents are unioned by sealed label ID only after existing consumer admission checks.
- 2 distinct linked historical recall records: D-0161-2016, **Subpotent Drug**, Pfizer Inc.; D-0444-2026, **Failed Dissolution Specifications**, Viatris Inc.
- Recall records are unioned by sealed recall ID, never summed across product links. A recall record is not necessarily a unique FDA event. Per-product lot scope and source status remain attached. The older selected-product count of one described one exact NDC, not the whole discovery scope. Two is the count linked to these returned products in this release, not a claim about all Xanax recalls.
- Alprazolam is listed once by sealed ingredient ID: **18 stored ingredient-report associations** in this artifact/window. This is not brand-specific, a patient count, incidence or confirmed causation. Reaction bars retain their separate reaction co-report activity units. Counts are never summed across ingredients into a medication total.
- Unknown analytics remains null/unavailable rather than zero. No matches or links does not establish absence of historical evidence.

New overview queries cap discovery at 100 products and disclose truncation. Filters affect displayed product rows, not the overview's stated scope. Identifier, ingredient and prefix fallback is labeled separately from stored brand aliases. Browser API guards reject inconsistent or foreign-bound summaries and malformed inventory responses; errors never invent totals.

## Changed files in this implementation

Frontend behavior and visual system:
- `frontend/src/App.tsx`, `dual-experience.css`
- `frontend/src/api/drugCatalog.ts`
- `frontend/src/components/MedicationDiscovery.tsx`, `StoredDrugCatalog.tsx`
- `frontend/src/portfolio/HomePage.tsx`, `DataInventory.tsx`, `OperationalOverview.tsx`
- `frontend/src/portfolio/scene/ImmersiveOrb.tsx`, `OrbScene.tsx`, `StaticOrb.tsx`
- `frontend/src/research/Workspace.tsx`, `EverydayWorkspace.tsx`, `EverydayEvidence.tsx`

Additive read-only API:
- `backend/app/main.py` router registration
- `backend/app/routes/medications.py`
- `backend/app/schemas/medication_overview.py`
- `backend/app/services/pharma/medication_overview.py`

Verification and artifacts:
- New `MedicationDiscovery.test.tsx`, `DataInventory.test.tsx`; updated StoredDrugCatalog, HomePage, Portfolio, Workspace and API unit tests
- Actual-release fixtures in `frontend/src/test/{medication-overview,data-inventory}.fixture.json`
- `frontend/e2e/{pharma-offline,unified-glass,demo-smoke}.spec.ts`
- `backend/tests/pharma_release/{test_medication_overview,test_explorer_reports}.py`
- `scripts/audit_dual_experience_inventory.py`, `scripts/capture_dual_experience.mjs`
- This report, audit JSON, and new screenshot directory. Previous screenshot sets and unrelated dirty/untracked work remain.

## Verification

- ESLint: pass.
- TypeScript and Vite production build: pass.
- Vitest: **158 passed** across 17 files.
- Existing Chromium regressions: **23 passed**, covering keyboard navigation, 320/390/768/1366/1920 layouts, symmetric evidence, PDF dialog, mode workflow, authenticated research fixtures and WebGL/reduced-motion behavior.
- Additional Pro palette/geometry checks across all six routes at 390 and 1440 pixels: **2 passed**; the keyboard search resilience check was rerun and passed.
- Real frozen-release Chromium journeys with outbound network blocked: **3 passed**, including medication-first scope/mode persistence and actual PDF download. Final medication overview symmetry and fully visible summary caveats were also checked against the real artifact.
- Pharmaceutical-release and agent backend regressions: **634 passed**. Initial sandbox run could not bind loopback sockets; rerun with loopback access passed all tests.
- Required artifact gate: **8/8 passed**, publication authorization unchanged.
- All 19 manifest table counts reconciled. Outbound verification log is empty.
- Screenshot receipt records 50 desktop/mobile captures with no page exceptions or horizontal overflow at 1440 and 390 pixels; broader viewport coverage comes from browser regressions.

## Dependencies, performance and limits

No packages added or versions changed in this implementation. Existing React 19, R3F 9, Three 0.186 and Motion are reused. Scene remains lazy, decorative, device-aware and replaceable with a static fallback. Palette changes reuse the mounted scene rather than allocating another renderer. Animations use transforms/opacity and pause or disappear under reduced motion.

Current production artifacts: main JS approximately 521 kB (160 kB gzip), lazy scene 922 kB (245 kB gzip), CSS 119 kB (24 kB gzip). Vite's existing >500 kB chunk warning remains visible. The large Three chunk is the tradeoff for the requested 3D scene; it is not loaded for reduced-motion/unavailable-WebGL paths. No extra postprocessing/bloom dependency was added. Read-only aggregation is bounded to 100 products and retains admission checks rather than using unverified site-wide mockup totals.

No live FDA refresh, live local model quality benchmark, physical-device GPU benchmark or screen-reader manual audit is claimed. Browser screenshots of Ask show the real local pairing boundary, not a fabricated connected answer. Existing authorization, exact-product confirmation, source verification and local-service isolation are not replaced by the discovery overview. Publication remains unauthorized. Nothing has been committed, pushed or deployed.
