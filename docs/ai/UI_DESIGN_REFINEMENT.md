# Dav AI: existing-design visual audit and refinement

## Batch A — inventory before implementation

Audited HEAD `eda4886`, retaining uncommitted Phase 3B work and the two previously
modified Research Pro screenshots. No source/CSS was changed before this inventory,
historical screenshot review and current browser captures were completed.

### Current UI

| Surface | Classification | Assessment / action |
|---|---|---|
| Evidence Explorer `/` | REFINE | Keep exact-product search, URL state, recall/FAERS cards, source disclosures and PDF dialog. Correct theme contrast, narrow intrinsic page width, duplicate branding and mobile spacing. Preserve this existing URL. |
| Drug search/results/details | KEEP / REFINE | Existing selected-state semantics, identity and NDC details are useful. Improve selected-card feedback and focus. |
| Ask `/ask`: Everyday | REFINE | Keep spacious sage/teal identity, pairing/confirmation sequence and guided evidence cards. Add restrained entrance/completion motion. |
| Ask `/ask`: Research Pro | REFINE | Keep dark slate/cyan identity, cohort tray, table and single-product controls. Improve muted-text contrast, mobile header/tabs and restrained motion. |
| Grounded answer / Hybrid RAG panels | KEEP / REFINE | Preserve exact quote text, provenance, fallback and citation behavior. Add focus highlighting and reduced-motion-safe reveal/navigation. |
| PDF report dialog | KEEP | Preserve focus management, keyboard cancellation, transient details and download flow. |
| Landing, Operational Overview, About, FAQ | RESTORE / REFINE | Removed from current tree, found in history; reuse original visual structure and update outdated multi-domain claims. |

### Historical discovery

- `351a4a0` (original showcase), `822c5c9` (hero motion), `0e4c511`
  (latest preserved pre-simplification source), and `f8d241a` (removal/simplification)
  establish the lineage. Hero copy refinements also date to June/July 2026.
- Original Home: split hero, bold ink/blue/teal gradient type, mint/aqua canvas,
  soft grid texture, rounded white source illustration and floating cards; small
  radar/capsule SVGs, quick lanes and an educational workflow.
- Latest Operational Overview: six pastel source/workflow cards around a Dav AI
  engine, original inline SVGs, source-fabric strip and explicit boundaries.
- About / FAQ: dark navy banners with aqua light, rounded white content cards,
  numbered topics and native disclosure accordions.
- Original `hero.png` is a purple layered scaffold graphic, not the polished hero
  visible in the showcase. Reviewed but OPTIONAL; not reintroduced. `react.svg`
  and `vite.svg` are also obsolete scaffolding. Inline SVG/CSS graphics are the
  useful original assets, not generic stock imagery.
- Existing favicon/PWA artwork, manifest and retired service-worker source are
  retained; no cache/deployment policy changes.

Historical route inventory (source preserved in Git, no mass restoration):
Home, Public Safety Search, Operational Overview, DrugSignal/Pharmacy Safety,
FoodSignal, Personal Care Signals, ProductScan Lab, Regional Health Lab, Sources,
Audit, System Status, Saved Monitors, Signup, Login, Onboarding, Profile, About,
FAQ and Help. Food/cosmetic/vehicle/device labs, accounts, monitors and operations
panels are DEFERRED: their older service claims do not describe the current
pharmaceutical application. Sources/Help content is consolidated into the existing
provenance panels and restored FAQ/Overview. No historical source was deleted.

### Visual evidence and scope

Viewed existing historical Home, Operational Overview, About and FAQ screenshots
in `docs/finalization/evidence`. Captured the current app at 1440, 768 and 390 px
under `/private/tmp/dav-ai-ui-audit/before`: Explorer empty/results plus both Ask
connection states (12 PNGs). Real Zepbound evidence was loaded through the existing
read-only offline verification backend. Ask connection screens are real UI;
research result states will be verified separately with clearly identified fixtures.
Historical screenshots are archival observations, not a live historical backend.

## Implementation and verification

### Final navigation and page decisions

Primary navigation: **Home → Evidence Explorer → Ask Dav AI → About → FAQ**.
Operational Overview is linked from the Home workflow and supporting footer.

| Route / surface | Final decision |
|---|---|
| `/home` | Restored original landing composition and source illustration. Accessible from the brand and Home link. |
| `/` | Retained existing Evidence Explorer URL, query parameters, search and PDF flow. |
| `/ask` | Retained one shared research session with Everyday and Research Pro presentations. |
| `/overview` | Restored the original central-engine diagram, updated to the actual six-stage pharmaceutical research workflow. No KPI metrics. |
| `/about` | Restored dark hero and numbered cards; explains motivation, academic techniques and limitations. |
| `/faq` | Restored native accordions; retains approval/advice, sources, recall scope and FAERS questions, adds current confirmation, grounded-answer, local setup and PDF guidance. |
| Historical `?page=home/about/faq/operational-overview` links | Resolve to the appropriate restored content without adding a routing dependency. |
| Historical account, monitors, food/cosmetic/vehicle/device and regional-lab pages | Deferred, not revived or deleted. Their APIs and old multi-domain positioning are outside the current application. |
| Source/audit/help pages | Useful content is covered by existing evidence provenance and restored FAQ/Overview; no redundant navigation added. |

The root remains the working Explorer to avoid breaking existing entry points and
bookmarked product queries. `/home` is the portfolio landing. No deployment
routing configuration was changed.

### Batches B–D — refinements implemented

- Reused the June/July source/CSS lineage at `0e4c511`: split hero, original
  white source-sheet/floating-card construction, ink-to-teal typography, aqua/mint
  backgrounds, dark About/FAQ banners, pastel workflow cards, connector geometry,
  central Dav AI engine and all six original workflow SVG icon constructions.
- Scoped recovered styles under `.portfolio` so they cannot restyle research
  controls. Removed the historical perpetual decorative animations, blur filters
  and `will-change` declarations. No stock graphics, new raster images, remote
  fonts, chart widgets or animation dependencies were added.
- Replaced the illustrative priority score/bar chart with a clearly labeled
  source-trail illustration. It has no fake metrics or implied live results.
  Floating cards were repositioned after visual inspection to keep source-sheet
  labels unobstructed. Mobile keeps the original simplified single-sheet graphic.
- Restored educational workflow content describing identity, explicit product
  confirmation, SQL/Hybrid RAG, source admission, optional statement-ID selection
  and source review. The diagram describes capability and boundaries, not runtime
  availability or measured model performance.
- Retained approval/advice/recall/FAERS boundary content while removing obsolete
  scoring, food/cosmetic services and account/monitor claims. About explicitly
  states that independent claim-support review remains pending.
- Added a compact mobile navigation disclosure, active links, Escape-to-close
  with focus restoration, a global main-content skip link and route-specific
  document titles. The experience selector remains on the two functional routes;
  informational pages retain the original light portfolio identity.
- Preserved the Everyday sage/teal and Research Pro slate/cyan themes. Improved
  muted-text contrast, wrapped long release metadata, reduced unused top space,
  retained cohort/single-product tabs and corrected checkbox widths inherited
  from global input styling.
- Corrected hardcoded white evidence/coverage cards in Research Pro, both in the
  Explorer and detailed source briefings. Source record text and status semantics
  were not changed. Explorer now uses its available content width and one shared
  brand/navigation header, rather than repeated Dav AI branding.
- Added exact citation-target focus highlighting and scroll offsets for both
  Everyday accordion targets and Research Pro text targets. Citation scrolling
  becomes instant under reduced motion; normal motion retains smooth scrolling.
- Updated the misleading Research Pro pairing placeholder (the launcher does not
  issue `dav_pair_...` tokens) and replaced the Enterprise Workspace subtitle
  with Research Pro. No capability/authentication behavior changed.

### Motion and interaction details

Finite hero text/graphic entrances use 440–650 ms opacity/translate keyframes;
floating source cards enter with 250/350/450 ms delays and settle. Workspace-mode,
briefing completion, grounded-answer and RAG panels have short entrance motion.
Buttons, links, selected products and cards retain subtle color/border/hover
feedback. Existing research-running feedback is preserved and clipped to its
container. New decorative motion does not loop.

Scroll reveals progressively enhance browsers with CSS view timelines; content
remains visible when unsupported. FAQ uses native keyboard-accessible `details`
plus a short paragraph entrance and progressive intrinsic-height expansion/closing
where supported. Navigation gets a short mobile reveal and optional native
cross-document view transitions. No scroll-jacking or animated layout dimensions
were introduced outside disclosure expansion.

Reduced motion disables animations/transitions, leaves all content visible and
uses instant citation scrolling. FAQ focus rings sit inside their clipped rounded
surface so keyboard focus remains visible. New page graphics reserve fixed space;
entrances use transforms/opacity rather than moving document layout.

### Browser evidence and before/after comparisons

Screenshots remain under `/private/tmp/dav-ai-ui-audit` (`/tmp` is the macOS alias).
No repository screenshots were added or replaced.

| Comparison | Before | After |
|---|---|---|
| Explorer, 1440/768/390 | Narrow intrinsic-width layout; dark mode inherited white text on white evidence cards; repeated branding. | Full available content width; theme-aware cards, source details, tables and inputs; one shared brand header. |
| Ask Everyday, same widths | Existing guided sage/teal workflow. | Same identity and controls; consistent spacing, compact mobile navigation, finite entrances and citation highlighting. |
| Ask Research Pro, same widths | Large unused top space, low-contrast secondary text, white detailed cards and stretched checkboxes. | Content starts closer to navigation; readable source surfaces; correctly sized checkboxes, wrapped metadata and focused citations. |
| Home | Absent from current tree; archived original split hero/floating graphics reviewed. | Restored `/home` using original visual composition and current pharmaceutical content. This is archival-to-restored comparison, not a live old-backend run. |
| Overview / About / FAQ | Current routes absent; archived screenshots and historical source reviewed. | Restored original visual layouts with bounded current descriptions, keyboard disclosures and responsive scaling. |

Representative screenshots:

- Before: `/private/tmp/dav-ai-ui-audit/before/explorer-evidence-390.png`
- After: `/private/tmp/dav-ai-ui-audit/after/explorer-evidence-390.png`
- Landing desktop/mobile: `after/home-1440.png`, `after/home-390.png`
- Overview desktop/tablet/mobile: `after/overview-1440.png`, `after/overview-768.png`, `after/overview-390.png`
- About and FAQ: `after/about-{1440,768,390}.png`, `after/faq-{1440,768,390}.png`
- Matched connection views: `before/ask-{everyday,research_pro}-{1440,768,390}.png` and equivalent `after` files
- Synthetic result states: `after/result-{everyday,research_pro}-{1440,768,390}.png`
- Browser geometry/error inventory: `/private/tmp/dav-ai-ui-audit/browser-audit.json`

Restored pages and existing workspaces were rendered in installed Chromium at
1440×900, 768×900 and 390×900. The current/after real Explorer loaded Zepbound
NDC `0002-0152` through the existing offline verification server. No horizontal
overflow was detected in the route matrix or six result-state/mode/viewport checks.
Native FAQ Enter/Space, mobile menu Escape/focus, mode preference entry links,
main landmarks and normal/reduced motion were exercised. Full-page captures of
scrolled pages can place sticky chrome at the captured scroll position; final
result captures were standardized to the page top after checking source visibility.

Ask result screenshots deliberately use synthetic intercepted API fixtures,
including an unverified RAG candidate and generated extractive quote. They verify
rendering/navigation, not live clinical results, retrieval quality or model output.
The exact source target was opened, focused, and checked below the sticky header
in both modes at each width. The old backend was not launched or revived; the
historical comparison uses saved screenshots and historical source. Safari/Firefox
and pixel-difference baselines were not tested; this is manual visual review plus
browser behavior/geometry verification, not a cross-browser certification.

### Test results

- Frontend: **85 tests passed across 11 files**, including existing confirmation,
  cohort, evidence, fallback and provenance tests, six restored-page/navigation
  checks and one reduced-motion citation check.
- ESLint: **passed**.
- TypeScript + Vite production build: **passed**.
- Playwright: **10 passed**, covering search/selection/PDF at desktop/mobile,
  dialog focus restoration, both grounded-answer statuses and citation navigation,
  complete dual-mode/product-switching workflow, restored pages at all three widths,
  normal-motion settling and reduced-motion accessibility.
- Ad hoc browser audit: no page errors on restored pages; no horizontal overflow
  on inspected routes/result states; focused source targets remained below sticky
  navigation. The existing offline backend outbound-block log remained empty.
- `git diff --check`: **passed**.
- Backend/model evaluation: not rerun for this visual-only task. No backend code,
  model/retrieval architecture, authorization, release/publication metadata or
  database content changed. Phase 3B work remains uncommitted and intact.

During inspection, an initial screenshot lookup used an uppercase product name
against the mixed-case returned label; it was corrected without changing the app.
A result-capture selector initially assumed both modes used `.label-text`; Everyday
uses the actual disclosure element as its source target. Checking that target then
exposed missing scroll offset, which was fixed and passed all six final checks.
Two shell invocations used incorrect frontend-relative paths/cwd; no application
checks were bypassed, and the corrected test/build commands passed. There are no
remaining failing required checks.

Commands (from `frontend`):

```bash
npm test -- --run
npm run lint
npm run build
npx playwright test e2e/portfolio.spec.ts e2e/demo-smoke.spec.ts \
  e2e/grounded-answer.spec.ts e2e/dual-mode.spec.ts \
  --output=/private/tmp/dav-ai-ui-audit/playwright-final
```

### Exact changed files for this UI task

Modified:

- `frontend/src/App.tsx`
- `frontend/src/App.css`
- `frontend/src/components/StoredDrugCatalog.tsx`
- `frontend/src/research/Workspace.tsx`
- `frontend/src/research/ResearchProWorkspace.tsx`
- `frontend/src/research/GroundedAnswer.tsx`
- `frontend/src/research/GroundedAnswer.test.tsx`

Created/restored:

- `frontend/src/polish.css`
- `frontend/src/portfolio/HomePage.tsx`
- `frontend/src/portfolio/OperationalOverview.tsx`
- `frontend/src/portfolio/AboutPage.tsx`
- `frontend/src/portfolio/FaqPage.tsx`
- `frontend/src/portfolio/hero.css`
- `frontend/src/portfolio/operational.css`
- `frontend/src/portfolio/about.css`
- `frontend/src/portfolio/faq.css`
- `frontend/src/portfolio/portfolio.css`
- `frontend/src/portfolio/Portfolio.test.tsx`
- `frontend/e2e/portfolio.spec.ts`
- `docs/ai/UI_DESIGN_REFINEMENT.md`

All pre-existing untracked files and screenshot modifications were retained. No
commit, push, merge, deployment, dependency installation or security-gate change
was made. The only new runtime processes are local preview/verification servers,
bound to loopback using existing documented commands.

### Essential remaining recommendations

Keep the concise navigation and current page scope. Use `/home` as the portfolio
entry URL; making it the deployment root is a separate routing decision. Finish
independent evidence review and demo documentation, and retain selected temporary
screenshots outside OS-reclaimed storage when preparing the portfolio. Do a short
Safari/Firefox smoke check on the final demo machine; progressive CSS features have
static/native fallbacks. No additional dashboards, pages or major frontend phase
is recommended.
