# Dav AI — unified immersive glass implementation

Implemented locally October 27, 2026 on `feat/private-staging-authorization`. No commit, push, public deployment, backend change, release-data change or publication authorization change was performed. Existing dirty files, untracked work and backup files were preserved.

## Nine-screen image and screenshots

[Open the nine-screen review image](screenshots/unified-glass-2026-10-27/nine-screen-review.png). This is a board assembled from the implemented local application, not a speculative AI-generated mockup. The populated Explorer uses real frozen-release responses, without pharmaceutical API mocks. Research Pro is shown unpaired; it does not pretend a public hosted model is available.

| Screen | Desktop | Phone |
|---|---|---|
| Home | [Desktop](screenshots/unified-glass-2026-10-27/home-desktop.png) | [Phone](screenshots/unified-glass-2026-10-27/home-mobile.png) |
| Explorer overview | [Desktop](screenshots/unified-glass-2026-10-27/explorer-desktop.png) | [Phone](screenshots/unified-glass-2026-10-27/explorer-mobile.png) |
| Ask Everyday | [Desktop](screenshots/unified-glass-2026-10-27/ask-desktop.png) | [Phone](screenshots/unified-glass-2026-10-27/ask-mobile.png) |
| Operational Overview | [Desktop](screenshots/unified-glass-2026-10-27/overview-desktop.png) | [Phone](screenshots/unified-glass-2026-10-27/overview-mobile.png) |
| FAQ | [Desktop](screenshots/unified-glass-2026-10-27/faq-desktop.png) | [Phone](screenshots/unified-glass-2026-10-27/faq-mobile.png) |
| About and contact | [Desktop](screenshots/unified-glass-2026-10-27/about-desktop.png) | [Phone](screenshots/unified-glass-2026-10-27/about-mobile.png) |
| Explorer populated | [Desktop](screenshots/unified-glass-2026-10-27/explorer-populated-desktop.png) | [Phone](screenshots/unified-glass-2026-10-27/explorer-populated-mobile.png) |
| Explorer expanded | [Desktop](screenshots/unified-glass-2026-10-27/explorer-expanded-desktop.png) | [Phone](screenshots/unified-glass-2026-10-27/explorer-expanded-mobile.png) |

[Research Pro desktop](screenshots/unified-glass-2026-10-27/ask-research-pro-desktop.png) · [Compact evidence detail](screenshots/unified-glass-2026-10-27/board-evidence-compact.png) · [Capture receipt](screenshots/unified-glass-2026-10-27/capture-receipt.json).
The portable review HTML uses relative image references and can be opened beside its PNG files.

## Route-by-route before and after

| Route / state | Before | Implemented behavior |
|---|---|---|
| `/home` | Immersive hero, little response to clicking the current route | Existing capsule and orb preserved; slow ambient glow, card reactions, moving scroll cue, visible Home acknowledgement without clearing search or moving the page |
| `/` before selection | Plain search with no visual evidence overview | Centered pill search, shared ocean background, three matching neutral category cards; no fabricated site-wide metrics |
| `/` selected | Two long recall/FAERS columns; no Explorer label panel | Three equal compact glass panels: exact-product labels, historical recalls, ingredient reporting; explicit independent Expand/Collapse controls |
| Explorer expanded | Full data always competing for attention | Original records, source links, dates, versions, section states, matching provenance, coverage and limitations remain available on expansion |
| `/ask`, both modes | Different visual skins and no shared progress display | Shared glass tokens and Select Product → Choose Sources → Ask Question → Review Evidence sequence; existing pairing, confirmation, cohort, rerun and citation workflows retained |
| `/overview` | Six text-heavy static cards | Four luminous stages, staggered viewport activation, traveling connector highlights and keyboard-operable safeguard disclosures |
| `/faq` | Dark isolated hero with white accordion rows | Shared glass backdrop, native accessible disclosures, animated plus/minus treatment; original answers retained |
| `/about` | Long light-surface sections, no verified recruiter contact | Short glass story sections and Contact the Creator card with the supplied name, email and LinkedIn; GitHub omitted because no verified address was supplied |
| Navigation / mobile | Link navigation reloaded and unmounted research; route-specific palettes | Shared header and active pills, visible mode selector, contact action and responsive menu; internal navigation and browser history preserve the mounted research workspace |

Selected-product search results no longer arrive late and push evidence down the page. The selected view uses a compact identity panel with expandable provenance and a working **Change selected product** action. This action restores search; browser Back restores the selected product with collapsed panels.

## Evidence and safety decisions

- No backend authorization, publication, session capability or source-admission code was modified.
- The existing `/api/drugs/{id}/safety/labels` endpoint supplies admitted labels. The new frontend read rejects mismatched product IDs and filters out non-exact-product, non-product-scope and unrecognized-selection records. The backend already suppresses non-READY section text.
- Label marks represent stored section presence, never severity or a medication safety score. Missing text is explicitly distinguished from no warnings.
- Recall bars count classifications only among records actually returned. They do not claim current status, complete capture, or applicability to every package/lot.
- FAERS bars use stored `co_report_activity`, remain separately scoped to each ingredient, show the reporting window, and explicitly state the normalization (largest displayed value for that ingredient). They do not use association totals as reaction counts, sum ingredients, or imply causation, incidence, patients or personal risk.
- The real Ozempic example has no admitted selected label or linked recall record in this response; those limitations remain visible rather than replacing them with decorative statistics.
- The supported PDF dialog and POST export remain connected. There is no fake download control.
- Internal navigation preserves the in-memory research workspace. Existing expiry, cancellation, explicit reset, backend verification and unmount cleanup still apply; this does not extend capabilities or persist them to storage.
- Creator information is centralized in a typed configuration. Only Chandu Esukula, `esukulachandu@gmail.com`, and the supplied LinkedIn URL are rendered. No phone, job title or GitHub account was inferred.

## Exact content files changed in this pass

- `frontend/e2e/pharma-offline.spec.ts` — modified.
- `frontend/e2e/unified-glass.spec.ts` — created.
- `frontend/src/App.tsx` — modified.
- `frontend/src/api/drugCatalog.test.ts` — created.
- `frontend/src/api/drugCatalog.ts` — modified.
- `frontend/src/components/EvidencePanel.tsx` — created.
- `frontend/src/components/ExplorerSummaries.tsx` — created.
- `frontend/src/components/GlassNavigation.tsx` — created.
- `frontend/src/components/StoredDrugCatalog.test.tsx` — modified.
- `frontend/src/components/StoredDrugCatalog.tsx` — modified.
- `frontend/src/components/UnifiedExperience.test.tsx` — created.
- `frontend/src/components/creator.ts` — created.
- `frontend/src/portfolio/AboutPage.tsx` — modified.
- `frontend/src/portfolio/FaqPage.tsx` — modified.
- `frontend/src/portfolio/HomePage.test.tsx` — modified.
- `frontend/src/portfolio/OperationalOverview.tsx` — modified.
- `frontend/src/portfolio/portfolio.css` — modified.
- `frontend/src/portfolio/scene/ImmersiveOrb.tsx` — modified.
- `frontend/src/portfolio/scene/OrbScene.tsx` — modified.
- `frontend/src/research/DualMode.test.tsx` — modified.
- `frontend/src/research/EverydayWorkspace.tsx` — modified.
- `frontend/src/research/Workspace.tsx` — modified.
- `frontend/src/unified-glass.css` — created.
- `frontend/playwright.config.ts` — allows the verification API URL to be provided explicitly; the default loopback mock target remains unchanged.
- `scripts/capture_unified_glass.mjs` — reproducible local screen capture and board composition, with external browser requests blocked.
- `docs/ai/UNIFIED_IMMERSIVE_GLASS_REPORT.md` — this report.
- `docs/ai/screenshots/unified-glass-2026-10-27/` — desktop/phone captures, populated/expanded states, nine-screen PNG/HTML and JSON receipt.

No package additions or upgrades were made in this pass. The already-installed Motion, React Three Fiber and Three.js packages were reused. No external image, font, HDRI or animation service was introduced.

## Verification results

| Check | Result |
|---|---|
| `npm run lint` | Passed, no ESLint warnings |
| `npm test` | **148 passed**, 15 test files |
| `npm run build` | TypeScript and Vite passed |
| Complete default Chromium suite | **23 passed**, including 7 new glass-layout/interaction checks |
| Real outbound-blocked Explorer browser suite | **2 passed**: real search → PDF and real admitted Zepbound labels → source identity → change product → Back |
| Backend agent + Explorer API/PDF suite | **279 passed** (includes 246 agent checks and one artifact-backed API check) |
| Required frozen-release gate | **7/7 passed**, 370 other checks deselected; publication approval unchanged |
| Screenshot audit | 12 route/viewport probes (six routes at 1440 and 390 pixels), no document overflow or page exceptions |
| Broader responsive browser audit | Six routes at 320, 390, 768, 1366 and 1920 pixels; equal header geometry, selector and reduced-motion checks passed |
| Source chart regression | Three-column equal widths/heights at 1440, stacked cards at 768/390, exact numerical units, keyboard expansion, zero/malformed count handling passed |
| `git diff --check` | Passed |
| Outbound verification log | Empty; no blocked outbound request was attempted by the verification API |

Commands were executed, not inferred from earlier receipts:

```sh
cd frontend
npm run lint
npm test
npm run build
npx playwright test --workers=1 --output=/tmp/dav-ai-unified/final-browser
PHARMA_API_URL=http://127.0.0.1:18002 PHARMA_OFFLINE_SMOKE=1 npx playwright test --config=playwright.pharma.config.ts --workers=1 --output=/tmp/dav-ai-unified/final-real-labels-pdf

# Repository root
PYTHONPATH=backend .venv/bin/python -m pytest -q backend/tests/agent backend/tests/pharma_release/test_explorer_reports.py
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/pharma_release -m release_artifact --require-pharma-artifact -q
node scripts/capture_unified_glass.mjs
```

The default Chromium research/PDF journeys use existing HTTP fixtures. They are distinct from the two real frozen-release browser journeys. Local Ollama generation and live capability-authenticated research were not invoked. The dedicated research service was never exposed.

Early verification caught a stale navigation test that changed history without a browser event, two test-only TypeScript options, and an exact accessible-name mismatch. These were corrected. Capture review caught transient entrance frames, asynchronous search-result layout shifts, homepage light-control contrast, and FAQ icon style inheritance; final captures reflect those corrections. The initial capture origin was not admitted by the isolated verification API; only the two explicit loopback test origins were configured in that temporary process. The application CORS defaults were not broadened.

## Performance and accessibility observations

The main JS bundle is approximately **500.24 KB / 154.91 KB gzip**, the deferred scene **921.61 KB / 245.19 KB gzip**, and CSS **97.66 KB / 19.96 KB gzip**. The retired overview stylesheet is no longer imported; its source file was preserved. Large-chunk warnings are reported rather than hidden.

The scene stays lazy and pauses offscreen/when hidden. Narrow scenes use device pixel ratio 1; larger scenes are capped at 1.5. Reported low-memory/low-core devices use the static vector fallback. WebGL performance caveats, errors, context loss and reduced-motion changes also retain the static alternative. No canvas was added to informational routes.

Shared tokens govern widths, margins, surfaces, borders, radii and colors. Changes are scoped to the application shell. Category panels retain equal compact geometry on desktop and stack on smaller screens; long original details are revealed independently. A bounded summary scroll area can be used for products with multiple reporting ingredients.

Keyboard, focus indicators, native FAQ/flow disclosures, expanded-state buttons, persistent experience selection and runtime reduced-motion behavior were exercised. No full screen-reader certification, physical low-end-mobile benchmark, contrast audit of every legacy widget, Core Web Vitals measurement, Firefox or Safari verification is claimed. The explicit WebGL browser tests use a test-only software renderer; ordinary device fallback policy remains intact.

## Remaining limits and deployment blockers

- The research workspace still requires its local launcher and ephemeral pairing capability; the contact action does not imply that hosted research is available.
- Some FDA references remain generic stored provenance endpoints, as supplied by the release. No clinical source or claim-support certification was added.
- Dataset coverage is frozen and incomplete. Quotes, charts and resolved links do not establish complete evidence or individual medication safety.
- Publication remains unauthorized (`publication_validated=false`). No public deployment, tunnel, serving-gate bypass, paid infrastructure or external model call occurred.
- Existing dependency/build notices (including the Three.js Clock development deprecation and large deferred bundle) are not production-performance certification.

Ready for local visual review, including the real Explorer and supported export workflow.

## Diff scope

Against the source/e2e snapshot taken at the start of this task: **23 frontend source/test files, +628 / −290 lines**, plus one small Playwright configuration change, the capture script, this report and generated review artifacts. This separates the present task from earlier uncommitted work.

The full tracked working-tree diff relative to HEAD currently reports **35 files, +961 / −394 lines**; it includes earlier user changes and excludes untracked additions. No reset, cleanup, staging, commit, push or deployment was performed.
