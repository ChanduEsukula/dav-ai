# DavAI Visual UI/Product Audit: Portfolio UI Polish v1

- **Date:** June 26, 2026
- **Checkpoint reviewed:** `portfolio-ui-polish-v1-docs`
- **HEAD during review:** `287c2f6 Document portfolio UI polish checkpoint`
- **Branch:** `docs/source-expansion-checkpoint`
- **Scope:** Visual and product-path review only. No source code changes were made.

## Review Method

I ran the local app with:

- FastAPI backend: `http://127.0.0.1:8000`
- Vite frontend: `http://127.0.0.1:5173`

I reviewed desktop and narrow mobile screenshots for:

- Home
- Search / Public Safety Search
- Pharmacy Safety
- Food Safety
- Cosmetic Safety
- Saved Searches
- Sources
- About
- FAQ
- Help

Screenshot captures were saved outside the repository under `/private/tmp/davai-ui-audit`.

## First Impression

DavAI now feels much closer to a polished portfolio product than a class project. The typography, spacing, calm teal/blue palette, dark search headers, card system, and source-boundary language all create a credible first impression.

The main issue is not visual quality. The issue is product focus. The app still exposes too many internal surfaces too early: focused safety pages, Audit, Sources, System, FAQ, Help, ProductScan, source IDs, old module names, and operational language. A recruiter can understand that the project is serious, but they may not immediately know which single path matters most.

The strongest demo path is visible, but it still has competition from too many other choices.

## Demo-Readiness Score

**7 / 10**

DavAI is demo-ready with a guided script. It is not yet self-explanatory enough for an unguided recruiter click-through. The biggest blockers are crowded navigation, mobile first-screen overload, stale About/Saved Searches copy, and Public Safety result hierarchy issues.

## What Looks Strong

- The overall visual system feels calm, modern, and credible.
- The Safety Record Search section is now clearly branded as the main product action.
- The dark page headers for Search, Pharmacy, Food, and Cosmetic pages feel premium and consistent.
- Result cards look professional and source-backed.
- Source status and verification language are much stronger than a generic recall lookup.
- Food Safety has a good right-side source coverage panel that shows source status, records, and integration modes.
- Cosmetic empty states are careful and appropriately avoid causation or safety claims.
- Saved Searches has real workflow depth: creation, manual checks, run history, source trails, and latest/previous comparisons.
- Sources is strong for senior engineering credibility because it shows source registry, freshness, endpoints, and provenance thinking.
- FAQ and Help are visually clean and useful as support surfaces.

## What Feels Crowded or Confusing

### Navigation

The nav still shows too many first-level choices:

```text
Home, Search, Saved Searches, About, Pharmacy Safety, Food Safety, Cosmetic Safety, Audit, Sources, System, FAQ, Help
```

This reads as an internal product map instead of a polished user journey. It also creates a visible active-pill overlap/spacing issue around `Pharmacy Safety` when other nav items are active.

Recommendation: keep `Search`, `Saved Searches`, and `About` as primary. Move focused pages, Audit, Sources, System, FAQ, and Help under `Advanced` or a secondary menu.

### Home

The homepage is visually polished but still makes users pass through:

1. brand/nav
2. hero copy
3. focused module buttons
4. hero preview card
5. then Safety Record Search

On mobile, the actual search is below the first screen. For a search-first product, this is still too late.

Recommendation: on mobile, show a one-sentence value prop and the search box first. Move focused module cards below the first search action.

### Public Safety Search

The result page has strong ingredients but the order is not yet optimal.

Observed issues:

- `Vehicle Recall Check` appears for `air fryer`, which is a consumer product query. This is distracting and looks incorrect.
- The `Evidence types found` promise is not visually prominent above the record list.
- The result list appears before source/evidence interpretation becomes clear.
- `Download results` is visible but disabled-looking, which makes the product feel unfinished.
- The floating `Explain These Results` button overlaps content on mobile and competes with right-rail panels on desktop.
- The right rail is useful, but it becomes dense and competes with the primary result list.

Recommendation: for Public Safety results, use this order:

```text
Query summary
Evidence types found
Sources checked and verification links
Top matched records
What to verify next
Optional advanced technical context
```

Show vehicle recall tools only when the query looks vehicle-related.

### Focused Safety Pages

Pharmacy, Food, and Cosmetic pages are visually coherent, but they still read as separate products rather than focused views inside one product.

Specific observations:

- Pharmacy query `Advil` shows a banner suggesting Public Safety Search, even though Advil is a valid pharmacy-style query. This may confuse a recruiter.
- Food Safety source coverage is strong, but the floating assistant button overlaps the right column.
- Cosmetic Safety handles zero results responsibly, but labels like `No returned-report signal` feel awkward.

Recommendation: keep these pages available, but position them as focused search modes rather than primary nav destinations.

### Saved Searches

Saved Searches is credible but still leaks internal language:

- `RecallRadar`
- `DrugSignal`
- `FoodRadar`
- `monitor`
- `monitor-insight-v0.2`
- `scheduler-lock`
- `payload hash`

The final `Current scope` paragraph is honest but too dense and technical for a normal user or recruiter.

Recommendation: rename visible module choices to:

- Drug recalls
- Drug event reports
- Food records

Move technical scope details into an `Advanced implementation notes` disclosure.

### Sources

Sources is strong engineering evidence, but it reads as an operations page. The first screen is impressive to engineers, less useful to normal users.

Recommendation: keep Sources under Advanced. Surface source trust in the result pages through compact badges and verification links instead of expecting users to visit Sources.

### About

About is the most outdated visible page.

It still says:

- `Healthcare safety intelligence`
- `public-health signals`
- `scaffolded public-health signal data`
- `RecallRadar`
- `DrugSignal`
- `Saved Monitors`

That conflicts with the current polished product direction.

Recommendation: update About to match the new positioning:

> DavAI helps people search selected public safety records, understand evidence types, and verify official source links. It is not medical or legal advice.

## What Should Be Avoided

Do not add:

- fake live metrics
- fake risk scores that imply safe/unsafe judgment
- real-time alert claims unless production alerting is actually implemented
- medical advice, legal advice, diagnosis, treatment, or causation language
- more homepage modules
- more animations or decorative dashboard cards
- production RAG, production ML, or vector database claims
- ProductScan as a main workflow before it is stronger

The app is strongest when it says:

> public records, source-aware, evidence type, verification, source trail, not medical or legal advice.

## What Should Be Added

- A compact source trust strip near the main search:
  - Public records
  - Evidence types separated
  - Official source links
  - Not medical/legal advice
- A first-class `Evidence types found` card immediately after Public Safety search summary.
- A compact `Sources checked` card before the result list, not only in advanced details.
- A source-mode legend:
  - Live API
  - Public page
  - Curated snapshot
  - Prototype scaffold
- A single `Advanced` nav menu or disclosure.
- A mobile-safe placement for `Explain These Results`.
- A clearer empty state for Public Safety Search that does not show vehicle-specific content unless relevant.

## Copy To Simplify

| Current copy | Suggested direction |
|---|---|
| `Safety review for air fryer` | `Public records for air fryer` |
| `Dav AI turns public recall... into source-aware public-data intelligence` | `Search selected public safety records and verify official source links.` |
| `Choose a safety lens` | `Need a focused search?` |
| `No returned-report signal` | `No public cosmetic event reports returned` |
| `RecallRadar`, `DrugSignal`, `FoodRadar` in user-facing controls | `Drug recalls`, `Drug event reports`, `Food records` |
| `Saved Monitors` / `monitor` | `Saved Searches` / `saved search` |
| `Source-aware intelligence` | `Public records with source links` |
| `Audit-backed freshness` | `Freshness based on DavAI audit history` |
| `Current scope: ... scheduler-lock protection...` | Move to Advanced implementation notes |

## Too Technical For Recruiters or Normal Users

These are useful engineering details, but should be hidden or moved lower:

- source IDs like `openfda_drug_enforcement`
- `payload hash`
- `scheduler-lock`
- `monitor-insight-v0.2`
- `transform version`
- `score version`
- `RecallRadar`, `DrugSignal`, `FoodRadar`
- `scaffolded public-health signal`
- `deterministic saved-search insights`
- long source freshness disclaimers in primary visual areas

Keep these available for senior engineers in Advanced, Sources, Audit, or docs.

## Mobile and Responsive Issues

High-impact mobile issues:

- The nav consumes the entire first screen on mobile.
- Safety Record Search is below hero/module content instead of being the first action.
- The floating `Explain These Results` button overlaps the search form/result header on mobile.
- Public Safety right-rail content stacks into a very long page after the result list.
- Saved Searches stacks mechanically well, but the page becomes very dense and technical.
- ProductScan appears on the mobile homepage after focused modules, adding another choice before the user understands the main product.

Recommendation: mobile should start with:

```text
DavAI
Search public safety records
[search box]
example chips
source/verification badges
```

Everything else should be below or behind a menu.

## Accessibility, Keyboard, and Readability Issues

Positive:

- Most buttons have visible text labels.
- Search fields have labels.
- Page headings are visually clear.
- Result cards use consistent visual grouping.

Concerns:

- Some low-contrast faded text is difficult to read, especially the vehicle card in empty/search result states.
- Small uppercase labels with wide letter spacing can become hard to read.
- Disabled-looking `Source details` and `Download Excel` controls may confuse users if they are interactive or unavailable.
- The floating assistant button can cover content and may create awkward keyboard focus order.
- The oversized hero headings on About/FAQ/Sources create dramatic first screens but reduce scan efficiency.
- The nav active-pill overlap indicates spacing/responsive fragility.

Recommended accessibility checks before recruiter demo:

- Keyboard tab through Home, Search results, and Saved Searches.
- Verify visible focus states on nav, search inputs, example chips, disclosures, and Explain These Results.
- Check color contrast on faded helper text and disabled-looking controls.
- Ensure `Explain These Results` is reachable and does not obscure focused controls on mobile.

## Top 5 Highest-Impact Improvements

1. **Simplify nav and mobile first screen.**
   Keep `Search`, `Saved Searches`, and `About` primary. Move Pharmacy/Food/Cosmetic/Audit/Sources/System/FAQ/Help under `Advanced` or a secondary menu.

2. **Make Safety Record Search truly first on mobile.**
   Put the search box directly after a short value prop. Move hero module cards and ProductScan lower.

3. **Polish Public Safety result hierarchy.**
   Show evidence types and sources checked before records. Hide vehicle recall content unless the query is vehicle-related. Remove or hide disabled export until it works.

4. **Clean stale/internal copy.**
   Update About, FAQ, Saved Searches, and visible module labels so they match the current public-record/search-first positioning.

5. **Fix `Explain These Results` placement.**
   Attach it to the result summary or place it as a stable action below the summary on mobile. Avoid floating overlap.

## Low-Risk Quick Wins

- Change `Safety review for X` to `Public records for X`.
- Hide the Vehicle Recall Check card unless query classification is vehicle/VIN/equipment.
- Remove or hide the disabled `Download results` card until export is functional.
- Rename Saved Search module labels away from internal module names.
- Replace `monitor` with `saved search` in visible Saved Searches copy.
- Collapse the Saved Searches `Current scope` paragraph.
- Update About page headline and body to current positioning.
- Move ProductScan teaser below focused searches or behind Beta/Advanced.
- Fix nav active-pill spacing/overlap.
- Add a mobile-specific position for `Explain These Results`.

## Changes Not Recommended Right Now

- Do not redesign the entire visual system. The core visual language is already good.
- Do not add more data modules before the primary path is cleaner.
- Do not add more charts, graphs, dashboards, or animations.
- Do not make ProductScan the main demo path yet.
- Do not build new RAG/vector DB work just for demo polish.
- Do not add fake freshness, source quality, risk, or alert metrics.
- Do not remove engineering credibility pages entirely; move them under Advanced.

## Runtime Note From Visual Pass

While capturing the Public Safety Search pages, local API responses returned successfully, but backend logs showed audit/source-pull insert failures for `RealWorldSafety` because the local database rejected the module value against `audit_events_module_check`. This did not block the visual review, but it matters for demo confidence because DavAI's source-trail story depends on audit persistence.

Recommendation: before a recruiter demo that opens Audit/source-trail details from Public Safety Search, verify the local or deployed database migration/constraint state supports the current `RealWorldSafety` audit module.

## Suggested Next 1-2 Commits

### Commit 1: Simplify Demo Navigation and User-Facing Copy

**Goal:** Make the app easier to understand in the first 30 seconds.

Likely files:

- `frontend/src/types/navigation.ts`
- `frontend/src/components/Navbar.tsx`
- `frontend/src/styles/navbar.css`
- `frontend/src/components/AboutPage.tsx`
- `frontend/src/data/faqs.ts`
- `frontend/src/components/SavedMonitorsPage.tsx`

Changes:

- Reduce primary nav to Search, Saved Searches, About.
- Move operational/focused pages under Advanced or secondary nav.
- Update About/FAQ/Saved Searches stale language.
- Rename visible module labels in Saved Searches.

Risk: medium.
Impact: very high for recruiter clarity.

### Commit 2: Polish Safety Record Search Result Flow

**Goal:** Make the flagship page feel undeniable in a demo.

Likely files:

- `frontend/src/components/PublicSafetySearchPage.tsx`
- `frontend/src/styles/public-safety-search.css`
- `frontend/src/components/AskDavAIChat.tsx`
- `frontend/src/styles/ask-dav-ai.css`

Changes:

- Show evidence types and sources checked before records.
- Hide vehicle recall helper unless query is vehicle-related.
- Hide disabled export until functional.
- Move or restyle `Explain These Results` so it does not overlap content, especially on mobile.
- Rename `Safety review for X` to `Public records for X`.

Risk: medium.
Impact: very high for demo flow and user confidence.

## Final Verdict

DavAI is close to recruiter-ready. The project already looks sophisticated and technically credible. The next polish should not add new capability. It should remove competing choices, hide internal vocabulary, and make the flagship Safety Record Search path visually obvious on desktop and mobile.

The product should present itself as:

> Search selected public safety records, understand evidence types, verify source links, and explain current results within clear limits.
