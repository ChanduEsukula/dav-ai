# Dav AI readability, branding and verified inventory

Implemented locally on October 27, 2026. Branch and pre-existing uncommitted/untracked work preserved. No commit, push or deployment. No pharmaceutical records, authorization gates or local research authority changed. No packages added.

## Review

- Preview: http://127.0.0.1:15174/home
- The existing preview at http://127.0.0.1:5173/home also recovers the inventory using explicitly labeled development snapshot metadata if its older API still returns 404.
- [Before-and-after comparison](screenshots/readability-2026-10-27/before-after.png)
- [Browsable comparison](screenshots/readability-2026-10-27/before-after.html)
- [Before captures](screenshots/readability-2026-10-27/before/): all six routes, both modes, desktop 1440px and mobile 390px, plus inventory sections.
- [After captures](screenshots/readability-2026-10-27/after/): same route/mode/viewport matrix, populated medication discovery and loaded verified inventory.
- [Fresh read-only inventory verification](READABILITY_INVENTORY_VERIFICATION.json)

Screenshots show actual local UI; no mocked clinical data was used for the captures. Ask screenshots show the unpaired local-session boundary. Test fixtures exercise connected research separately. Snapshot captures use reduced motion for consistent framing; normal-motion animation is browser-tested.

## Typography and brand

`readability.css` centralizes semantic typography tokens: Everyday body 16px; Research Pro body 15px; product-table/row text 15px; controls 15px; labels/navigation 14px; secondary metadata 13px; card titles 20px. Existing responsive page/section heading hierarchy remains. Higher-contrast muted colors are #c1d9e2 in Everyday and #cfcee8 in Research Pro. Component-specific semantic selectors distinguish metadata from main prose rather than globally enlarging every element.

Product rows remain compact with 12px vertical padding. Pro retains table structure and expandable provenance. Filter controls now wrap into readable columns rather than squeezing five narrow inputs into a mobile row. Evidence summaries grow naturally instead of clipping text or requiring an internal scroll to read caveats; expansion buttons align across the three cards. Mobile evidence remains stacked.

The shared Home brand link now contains a decorative 34px glass halo/orbit emblem (30px on phones) beside the prominent Dav AI wordmark. It follows the teal/violet palette, runs one 1.2-second light sweep on entrance, and glows gently on hover or keyboard focus. There is no enclosing brand-area border or continuous logo rotation. Reduced motion removes the sweep. The existing Home link and active-page feedback remain functional.

## Sticky-header correction

The header stays in document flow and retains sticky behavior. A ResizeObserver measures its actual height plus sticky inset and a 20px gap, exposing `--navigation-clearance` to document scroll padding. This replaces inconsistent fixed anchor margins that differed across Home, About and research sections. Native anchors, cross-route contact links and skip navigation use the same clearance; keyboard focus is protected when a field would land under the header. The observer changes scroll clearance, not layout dimensions. Mobile menu overlays have a viewport-bounded scroll area. Header geometry stays identical across routes and modes.

## Why inventory was unavailable

The existing port-5173 Vite process inherits an API URL targeting port 18000, taking priority over `.env.local`. That long-running API does not contain the newly added `/api/coverage/inventory` route and returns **404**. The updated loopback API on port 8000 returns **200** with the validated release inventory. Neither an empty database nor missing metric records caused the message. The prior component displayed a generic failure for this request mismatch.

The frontend still prefers the validated API. For development only, a missing/unreachable local endpoint can load a small generated inventory JSON. `scripts/generate_dev_inventory.py` first calls the existing release connection/integrity/authorization checks, reconciles all 19 manifest table counts with read-only SQLite queries, and then exports only public inventory metadata. It removes acquisition IDs containing local paths and substitutes safe source keys. This is a deliberate generation step, not hand-maintained numbers; regenerate it after an authorized local release update.

The fallback is guarded by `import.meta.env.DEV`; the production build excludes its import and data. A production frontend continues to require its authorized API. A 503/integrity failure, 401/403 authorization failure, malformed payload or missing primary metric does not activate the snapshot fallback. No clinical records are served by this mechanism. The UI explicitly labels development snapshot metadata and its build date rather than presenting it as live API evidence.

If metrics genuinely cannot load, source descriptions remain visible with no numerical claims, a plain-language message and a working Retry action. Diagnostics are sanitized and contain no credentials or private acquisition paths. Numeric data appears only after validation.

## Three primary dataset metrics and one coverage indicator

| Primary metric | Exact value | Source, units and limitation |
| --- | ---: | --- |
| FDA drug labeling | 83,684 | `labels` rows / verified manifest count. Stored documents, including context/withheld material; not medication count or admitted consumer-label coverage. |
| Historical recalls | 17,974 | `recalls` rows / verified manifest count. Historical records, including unlinked records; not unique FDA events, current status or a brand-wide total. |
| FAERS reporting | 3,174 | `ae_summary` rows by ingredient ID. Ingredients with analytics; not patients, adverse effects, report frequency or risk. |

The separate frozen-release coverage strip states January 1, 2020–June 30, 2026 reporting-analysis coverage and build date October 6, 2026. Release ID: `dav-ai-pharma-v1-phase4b-communications-20261006`. Label export is September 25, 2026; NDC observation September 26. Source vintages vary and unknown dates stay unknown. Publication remains unauthorized.

Everyday and Pro use identical verified facts. Pro's source disclosure additionally exposes the already verified searchable-product and identifier metrics without adding more headline cards: 95,426 NORMAL_CONSUMER product rows, 115,585 distinct PRODUCT_NDC values, and 218,852 distinct PACKAGE_NDC values. NDC counts include regulatory-only runtime records and are not medication counts.

Fresh read-only verification also found 502,104 label sections, 4,684 distinct preserved nonmissing recall event IDs, and 8,228,685 summed **ingredient-report associations** across 3,174 analytical rows. These are deliberately omitted from headline cards: event IDs do not establish complete FDA history, and one report can associate with multiple ingredients. The association sum is not a global unique report or patient total. Reaction counts are never summed as patients. The older 262,887-label development corpus is not the current runtime label count and is not used as a homepage metric.

## Exact changed implementation and test files

1. `frontend/src/App.tsx` — import shared readability system.
2. `frontend/src/readability.css` — new semantic type tokens, contrast, compact layout, brand and sticky-offset styling.
3. `frontend/src/components/GlassNavigation.tsx` — compact SVG emblem, measured clearance and keyboard-focus protection.
4. `frontend/src/portfolio/DataInventory.tsx` — three cards, coverage strip, disclosures, safe development fallback and retry.
5. `frontend/src/api/drugCatalog.ts` — shared inventory validation, required primary metrics and release/coverage shape checks.
6. `frontend/src/generated/dev-inventory.json` — generated sanitized development-only verified metadata.
7. `frontend/src/portfolio/DataInventory.test.tsx` — three-card layout, shared facts, failure and retry checks.
8. `frontend/src/portfolio/Portfolio.test.tsx` — updated Inside Dav AI heading expectation.
9. `frontend/src/api/drugCatalog.test.ts` — missing-metric rejection and generated metadata verification.
10. `frontend/e2e/readability.spec.ts` — new mode/viewport typography, brand, anchor, malformed-response and fallback regressions.
11. `frontend/e2e/unified-glass.spec.ts` — activate scroll-triggered architecture nodes by scrolling them into view.
12. `frontend/e2e/portfolio.spec.ts` — allow software-rendered WebGL scene the same 20-second readiness budget as canvas creation.
13. `scripts/generate_dev_inventory.py` — read-only validated metadata generation.
14. `scripts/capture_readability.mjs` — repeatable before/after route and inventory captures.
15. `scripts/build_readability_board.mjs` — actual-screen comparison board.

Report artifacts: this file; `docs/ai/READABILITY_INVENTORY_VERIFICATION.json`; and the 60 screenshot/receipt/board files under `docs/ai/screenshots/readability-2026-10-27/` (each phase has 24 route images, 4 inventory images and a receipt; the root has PNG and HTML comparison boards). Unrelated previous work and prior screenshot directories remain intact.

## Verification results

- ESLint: pass.
- TypeScript (`tsc -b`) and Vite production build: pass.
- Vitest: **162 passed**, 17 files.
- Existing desktop/mobile Chromium suite: **25 passed** after adjusting viewport-triggered animation checks.
- New readability/branding/inventory Chromium checks: **4 passed**, including all six routes in both modes at 390/1440px, exact font sizes, semantic product-table readability, finite logo motion and reduced motion, keyboard focus, identical header geometry, safe anchor positions and no horizontal overflow.
- Real frozen-release Chromium journeys: **3 passed**, preserving medication-first discovery, product selection, source records and PDF download.
- Before/after capture receipts: 24 route checks per phase, zero page exceptions and zero horizontal-overflow findings; inventory screenshots are saved separately in each phase.
- Read-only source audit: all **19** manifest table counts reconcile; metadata contains no local acquisition paths; development snapshot payload absent from production JS.
- `git diff --check`: pass.

Early browser failures were diagnosed and corrected: larger text moved architecture nodes below the initial viewport, software WebGL needed its documented readiness budget, and a focus-visible test needed actual Tab navigation rather than programmatic focus after a pointer click. An overlapping test run lost its shared server; final checks ran without overlapping server ownership. No clinical behavior or authorization was relaxed to make tests pass.

No dependencies were added. Current production output is approximately 524 kB main JS (161 kB gzip), 127 kB CSS (25 kB gzip) and the unchanged lazy Three.js scene at 922 kB (245 kB gzip). The existing large-chunk build warning remains visible. No physical-device GPU or manual screen-reader audit is claimed. Clinical data, source verification, product confirmation, research pairing and publication authorization are untouched.
