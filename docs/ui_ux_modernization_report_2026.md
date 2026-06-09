# DAV AI UI/UX Modernization Report 2026

**Review perspective:** Senior product design, frontend engineering, and UI systems engineering  
**Product position:** Graduate AI/full-stack portfolio project for public-data safety intelligence  
**Primary product story:** Search -> Normalize -> Explain -> Audit -> Report/Monitor  
**Review date:** June 2026  
**Implementation status:** Recommendation report only. No application code or API contracts were changed.

## Executive Summary

DAV AI already has more product depth than a typical student portfolio application. Its strongest user-facing qualities are:

- real public-data workflows rather than static mock screens
- clear source and retrieval metadata
- visible audit and provenance concepts
- deterministic, explainable scoring
- serious safety boundaries
- meaningful operational surfaces such as Audit History, Saved Monitors, Data Sources, and System Status
- a bounded assistant that works from current result context

The current UI, however, presents these strengths through too many competing visual and narrative layers. The homepage repeats the same core-module story in the hero module buttons, Safety Workspace, Operational Overview, and Signals. Individual modules repeat the same safety language through helper text, source strips, Safe Insight Cards, summaries, score explanations, briefings, disclaimers, and provenance panels. The result is credible but visually busy, long, and less decisive than it should be.

The current styling also mixes several visual directions:

- pale healthcare dashboard
- glassmorphism landing page
- animated AI/product showcase
- dark technical dashboard cards
- purple consumer report funnel
- dense operational admin console

Each direction is reasonable in isolation, but together they weaken DAV AI's product identity.

### Recommended Direction

DAV AI should become an **evidence-first safety intelligence workspace**:

- calm, light, and information-dense
- source and audit metadata treated as first-class product features
- strong typography and grid structure instead of decorative gradients
- one clear primary workflow per page
- technical detail available through progressive disclosure
- safety boundaries consistent and visible without dominating every section
- animations limited to state transitions and operational feedback
- assistant presented as a contextual analysis panel, not a generic chatbot

The visual target should feel closer to a restrained public-data command center or developer-facing intelligence product than an AI marketing website.

### Highest-Priority Changes

1. Simplify the homepage to one hero, one workflow explanation, and one core-module launcher.
2. Replace the hero's sample score and decorative chart with a truthful provenance workflow preview.
3. Consolidate repeated safety copy into a shared boundary system.
4. Normalize module shells, cards, buttons, status treatments, and metadata layouts.
5. Resolve navigation density and the two competing floating actions.
6. Make Audit History the visual reference for the rest of the product.
7. Remove "coming next" controls and any UI that implies unavailable functionality.
8. Reduce glassmorphism, oversized radii, infinite animation, and decorative status pulses.

### Review Method

This assessment is based on the current React component hierarchy, CSS implementation, interaction states, copy, semantic markup, responsive breakpoints, and current feature branch. The local frontend was started successfully, but the in-app visual browser surface was unavailable during this review. Recommendations therefore avoid unsupported pixel-level claims and focus on directly observable implementation and product-structure evidence.

---

## Current Strengths to Keep

### 1. Trustworthy Core Palette

The current ink, slate, teal, blue, and green palette is appropriate for public-data safety intelligence. It communicates:

- seriousness
- source transparency
- operational status
- healthcare-adjacent caution without looking clinical or institutional

Keep the underlying palette, but use it more selectively. Teal should remain the primary action and provenance accent. Green should mean successful or verified status. Amber and red should be reserved for warnings and failures. Purple should not operate as a second primary brand color.

### 2. Strong Information Architecture Inside Audit History

Audit History has the clearest dashboard structure in the product:

- filters
- a scannable event list
- selected-detail context
- copy/export actions
- basic and technical views
- source-pull provenance

The desktop list/detail split is a good model for other data-heavy pages. It demonstrates that DAV AI is not only a search interface but an inspectable engineering system.

### 3. Expandable Result Cards

The use of native `details` and `summary` elements for RecallRadar, DrugSignal, FoodRadar, CosmeticSignal, briefings, scoring details, and provenance is a good foundation. It:

- keeps dense records manageable
- supports progressive disclosure
- avoids modal overload
- provides useful semantic behavior

The concept should remain, although the number of nested accordions should be reduced.

### 4. Visible Source and Audit Metadata

Source name, retrieval time, endpoint, audit ID, transform version, score version, payload hash, and source status are differentiators. These details should not be removed. They should be reorganized into a consistent evidence pattern:

1. compact source summary near the result
2. expanded evidence panel for technical detail
3. direct link to the relevant Audit History record

### 5. Accessible Foundations

The application already includes:

- `focus-visible` treatments
- semantic headings
- labels for form fields
- `aria-live` status regions
- keyboard-triggered searches
- button disabled states
- semantic `details` controls
- reduced-motion handling

These are meaningful strengths for a portfolio project. The modernization should strengthen these patterns rather than replace them with visually custom but inaccessible controls.

### 6. Honest Product Boundaries

DAV AI avoids claiming:

- diagnosis
- treatment
- causation
- safety guarantees
- patient-specific risk
- production monitoring

This honesty improves the product. The recommendation is not to reduce the substance of these boundaries, but to present them through a reusable system that is easier to scan.

### 7. Real Operational Surfaces

Saved Monitors, System Status, Data Sources, Reports, and Audit History make DAV AI feel like a system rather than a landing page. Keep these surfaces and make them visually related through one operations design language.

### 8. Context-Bounded Assistant

Ask DAV AI is conceptually strong because it answers from the selected module result rather than acting as an open-ended chatbot. This is a better portfolio story than a generic text box connected to an LLM.

---

## Current Weaknesses / Repetition / Irrelevant Elements

## A. Visual System Fragmentation

### Mixed Brand Directions

The primary application uses teal, blue, green, white, and slate. The report drawer introduces a purple-indigo gradient and sparkle emoji. FoodRadar uses dark navy source cards. About uses a dark marketing hero. Operational Overview adds glass scanning effects and persistent glowing status dots.

This creates the impression that different features were designed from different templates.

**Recommendation:** Use one product system:

- neutral page canvas
- white or lightly tinted content surfaces
- teal primary actions
- blue informational states
- green verified/success
- amber caution
- red error
- no separate purple report identity

### Excessive Glassmorphism

Many major surfaces use:

- semi-transparent white backgrounds
- `backdrop-filter`
- large soft shadows
- radial gradients
- blurred decorative layers
- oversized rounded corners

This treatment is repeated so often that no surface feels more important than another.

**Recommendation:** Reserve glass or elevated treatment for:

- the top navigation
- drawers
- selected or floating contextual panels

Use solid surfaces and subtle borders for most content.

### Radius and Shadow Inflation

The design relies heavily on:

- `border-radius: 999px`
- 24-40px card radii
- multiple shadows per surface

Large radii make the product feel friendly, but too many make operational data feel soft and less precise.

**Recommended radius scale:**

| Role | Radius |
|---|---:|
| Inputs and compact controls | 8-10px |
| Buttons | 10-12px |
| Standard cards | 14-16px |
| Major panels and drawers | 18-20px |
| Pills and status badges | 999px |

Use a single low-elevation shadow for floating or selected content. Default cards should rely on borders and background contrast.

## B. Homepage Repetition

The homepage currently communicates the core modules repeatedly:

1. Hero module cards
2. Safety Workspace cards
3. Operational Overview cards
4. Full RecallRadar section
5. Full DrugSignal section
6. Full FoodRadar section
7. Full CosmeticSignal section
8. Signals cards

The user receives multiple versions of "choose a module" before reaching meaningful product interaction.

### Recommended Homepage Reduction

Keep:

- concise hero
- one actual product preview or provenance workflow
- one core-module launcher
- one short engineering credibility strip

Remove or relocate:

- duplicate module launcher
- generic Signals section
- large Operational Overview grid from the homepage
- full secondary modules from the default landing flow

Move Operational Overview to About or a dedicated Architecture page. Place CosmeticSignal behind "More modules" or its own route.

## C. Hero Credibility Problems

The hero uses:

- a decorative dashboard simulation
- a sample score of `82`
- fake chart bars
- floating "Recall", "Source", and "Audit" cards
- gradient orbs

Although the value is labeled as a sample, a reviewer can interpret it as a fake metric. It also conflicts with the requirement to avoid vague AI visuals and fake product evidence.

### Replace With a Truthful Product Preview

The hero's right side should show a compact, static workflow:

```text
openFDA / USDA FSIS
        |
Normalized record
        |
Explainable score
        |
Audit ID + source timestamp
        |
Report or monitor
```

This can be rendered as a restrained stack of real field labels:

- Source: openFDA Drug Enforcement
- Transform: recall-transform-v0.1
- Score: deterministic, versioned
- Evidence: audit ID + retrieval timestamp
- Assistant: current-result context only

Do not display a numerical score until a real query has produced one.

## D. Navigation Density and Styling Gaps

The navigation exposes:

- Home
- RecallRadar
- DrugSignal
- FoodRadar
- Monitors
- Audit
- Sources
- System
- About
- FAQ
- Help

This is too much for a single horizontal capsule. The `nav-actions` group also lacks the same explicit styling applied to `.nav-links button`, which creates a maintainability and likely consistency problem.

### Recommended Navigation

**Primary:**

- Workspace
- Monitors
- Audit

**Module selector:**

- RecallRadar
- DrugSignal
- FoodRadar
- More

**Operations menu:**

- Sources
- System Status

**Secondary menu:**

- About
- Help

FAQ can be part of Help. CosmeticSignal can be inside More. Regional Health should be labeled Experimental and kept out of primary navigation.

At mobile sizes, use a single menu or bottom sheet rather than converting every navigation group into a large grid.

## E. CSS Architecture Debt

The current CSS has multiple broad selectors redefined across files:

- `.eyebrow`
- `.search-field`
- `.field-label`
- `.field-helper`
- `.loading-helper`
- `.source-summary`
- `.source-card`
- `.metadata-grid`
- `.empty-state`
- `.disclaimer`

This creates cascade-dependent behavior. Import order becomes part of the component contract.

The styles also reference undefined custom properties:

- `--color-text-primary`
- `--color-text-muted`
- `--text`

Some files are very large:

- `recallradar.css` exceeds 1,000 lines
- `hero.css` exceeds 700 lines
- `operational-overview.css` exceeds 700 lines
- `audit-history.css` exceeds 500 lines

### Recommended CSS Direction

Create:

- `styles/tokens.css`
- `styles/base.css`
- `styles/layout.css`
- `styles/components/forms.css`
- `styles/components/buttons.css`
- `styles/components/status.css`
- `styles/components/data-card.css`

Use component-prefixed selectors for feature-specific styling. Avoid adding a CSS framework solely for this cleanup.

## F. Excessive Repeated Safety Copy

Important statements are repeated through:

- hero trust line
- operational trust pills
- search helper text
- Safe Insight Cards
- consumer summaries
- score cards
- empty states
- briefing disclaimers
- assistant header
- assistant limitations
- module boundary accordions
- report intake warnings and checkboxes
- About page safety note

Repetition protects the product legally and ethically, but it reduces scanability and makes every screen feel defensive.

The solution is a hierarchy of safety communication, described later in this report.

## G. Competing Floating Actions

Ask DAV AI and Get Your Safety Report both use fixed-position controls in the lower-right area. Their desktop spacing is manually coordinated, and the mobile report button expands across the screen while the assistant remains fixed above it.

This creates:

- possible overlap
- inconsistent priority
- reduced mobile content space
- unclear primary action

**Recommendation:** Use one contextual utility rail or one "Actions" button that opens:

- Ask about this result
- Generate report
- Save monitor

Only enable actions supported by the current module and result context.

## H. Unavailable Features Shown as Controls

The report preview displays:

- Save email intent - coming next
- Save to My Safety Profile - coming next
- Monitor this weekly - coming next

Two are disabled and one records only intent. These controls make the report flow feel like a product mockup rather than a finished student portfolio feature.

**Recommendation:** Remove unavailable actions from the primary UI. A small text note can say:

> Email delivery and scheduled monitoring are roadmap items.

The working PDF download should be the clear completion state.

## I. Misleading Operational Language

Phrases such as:

- "Live data flow"
- "secure backend wakes up"
- "Timestamp verified"

should be used carefully.

"Live data flow" can imply continuous processing. "Secure backend" is not proven by a loading message. "Timestamp verified" is ambiguous.

Prefer:

- "Queries public source on request"
- "Connecting to the DAV AI API"
- "Retrieval timestamp recorded"

## J. Naming and Copy Inconsistency

The UI uses:

- DAV AI
- Dav AI
- DavAI

Standardize the product name as **DAV AI** everywhere.

Also standardize:

- "review score" instead of switching between risk score, signal score, and intelligence score where the distinction is not important
- "public source" for data origin
- "evidence details" for provenance
- "limitations" for module-specific boundaries

---

## Recommended 2026 Visual Direction

## 1. Product Concept: Evidence-First Safety Workspace

The visual model should communicate:

> DAV AI turns public safety records into inspectable, explainable work.

This should be visible through structure rather than slogans.

### Personality

- calm
- precise
- technically literate
- transparent
- restrained
- serious without looking governmental
- modern without looking speculative

### Avoid

- glowing AI blobs
- random particles
- generic chatbot bubbles
- fake analytics charts
- excessive gradients
- every card appearing elevated
- infinite decorative animation
- purple "AI magic" styling

## 2. Page Shell

Use a consistent application shell:

```text
Top bar
  Brand | Module switcher | Operations | About

Page header
  Breadcrumb / module
  Title and one-sentence purpose
  Boundary badge

Primary workspace
  Search or control area
  Result summary
  Results

Evidence rail or details
  Source
  Retrieved
  Audit ID
  Limitations
```

On desktop, technical metadata can use a narrow right rail when it adds value. On tablet and mobile, move the rail below results or into a bottom sheet.

## 3. Layout Grid

Use a 12-column desktop grid with:

- maximum content width: 1200-1280px
- page gutter: 24-32px desktop
- page gutter: 16-20px mobile
- 8px spacing base
- 24-32px between major blocks
- 64-80px between major homepage sections

Avoid 100px-plus spacing between every section. Large whitespace should identify a new product chapter, not compensate for repeated content.

## 4. Typography

The current system font stack is appropriate. Keep it or use a local/system-first `Inter` or `Geist` stack without adding a blocking font dependency.

Recommended scale:

| Role | Desktop | Mobile |
|---|---:|---:|
| Hero | 56-64px | 40-46px |
| Page title | 40-48px | 32-38px |
| Section title | 28-34px | 24-28px |
| Card title | 17-20px | 16-18px |
| Body | 15-17px | 15-16px |
| Metadata | 12-13px | 12-13px |

Reduce ultra-tight negative letter spacing. The product should feel precise rather than editorial.

## 5. Color Roles

| Role | Recommendation |
|---|---|
| Canvas | soft neutral blue-white |
| Primary surface | white |
| Secondary surface | very light slate/teal |
| Text | deep navy/slate |
| Primary action | deep teal |
| Information | blue |
| Verified/success | green |
| Caution | amber |
| Error | red |
| Experimental | muted violet or amber badge only |

Do not use a purple-to-teal gradient as a primary control treatment.

## 6. Card Taxonomy

Create clear card roles:

1. **Action card** - clickable module or action
2. **Result row** - expandable record summary
3. **Metric card** - one value with label and context
4. **Evidence card** - source, audit, retrieval, version
5. **Boundary card** - concise safety limitation
6. **Status row** - source/system operational state

Do not style all six with the same large radius, shadow, and gradient.

## 7. Above-the-Fold Homepage

### Recommended Layout

**Left column:**

- eyebrow: Public-data safety intelligence
- headline: Turn public safety records into explainable, auditable decisions.
- one short paragraph
- primary CTA: Open RecallRadar
- secondary CTA: Explore audit trail
- compact boundary line: Public data only | No PHI | Informational, not medical advice

**Right column:**

A real workflow preview:

- source record
- normalized fields
- deterministic score explanation
- audit ID
- bounded assistant context

### Engineering Credibility Strip

Below the hero, include a compact row:

- React + TypeScript
- FastAPI
- PostgreSQL
- Typed API contracts
- Audit-linked provenance
- Tested frontend and backend

This should be labeled "Built as a graduate full-stack AI engineering project," not presented as customer metrics or certifications.

### Homepage Section Order

1. Hero and real workflow preview
2. Core modules: RecallRadar, DrugSignal, FoodRadar
3. How evidence flows: Source -> Normalize -> Explain -> Audit
4. Operational capabilities: Report, Monitor, Assistant
5. Engineering and responsible-AI note

CosmeticSignal, Regional Health, FAQ, and detailed operations should not all appear as full homepage sections.

---

## Module-by-Module UI Recommendations

## 1. RecallRadar

### Keep

- clear query input
- source count and retrieval timestamp
- expandable recall result rows
- visible review score and label
- score component explanation
- audit link and provenance
- sorting by score or date

### Simplify

- Remove the full Safe Insight Cards block from the default result flow.
- Merge the source strip and consumer summary into one result header.
- Show one concise boundary badge near the module heading.
- Move briefing generation behind a "Create briefing" action.
- Keep technical score components and audit metadata collapsed.

### Recommended Result Hierarchy

1. Search
2. Result summary: count, source, retrieved time
3. Highest-priority result and why
4. Result rows
5. Contextual actions: Ask DAV AI, Generate report, Save monitor
6. Evidence and limitations

### Default Result Row

Show:

- product name
- recall class
- status
- date
- review score
- source

Hide until expanded:

- full product description
- firm
- distribution
- score components
- "what to check next"
- technical metadata

### Demo Improvement

After a search, automatically focus or scroll to the result summary. Highlight the audit link as a real workflow continuation, not a footer detail.

## 2. DrugSignal

### Keep

- FAERS-specific causation boundary
- intelligence score and component context
- top reported reactions
- reaction category grouping
- trend snapshot
- audit metadata

### Simplify

- Remove the generic three-card Safe Insight block.
- Make the intelligence score card more compact.
- Keep "Top reported reactions" open by default.
- Keep classification and trend sections collapsed.
- Move score version to technical details.
- Avoid repeating "does not prove causation" in the section header, helper, score card, Safe Insight Card, and audit footer.

### Recommended Visual Priority

1. query and FAERS boundary
2. record count and source
3. top reaction pattern
4. score explanation
5. trend/classification
6. technical evidence

### Chart Treatment

Keep horizontal reaction bars, but:

- label counts directly
- use a neutral baseline
- avoid animated growth on every render
- show "report mentions in returned records," not an unlabeled risk impression

## 3. FoodRadar

### Keep

- multi-source visibility
- FDA/USDA distinction
- source-specific status
- result sorting
- report download
- lot/code/distribution fields

### Redesign

FoodRadar currently introduces dark source cards and dark limitation panels inside the light application. Convert these into the shared light status-row system.

The source summary should be one compact comparison table:

| Source | Status | Records | Retrieved |
|---|---|---:|---|
| FDA Food Enforcement | Success | N | Time |
| USDA FSIS | Success/Empty | N | Time |

### Report Action

The report action currently appears before results. Move it into the post-search action row so users understand what the report contains before downloading it.

### Result Row Priority

Show:

- product
- agency/source
- class/status
- recall/report date
- review score

Hide:

- quantity
- code details
- distribution text
- complete source endpoint

### Technical Note

The current file references CSS custom properties that are not defined in the shared token system. The modernization should eliminate those token gaps.

## 4. CosmeticSignal

### Keep

- public cosmetic-event search
- top reactions
- result records
- transparent signal score
- causation limitation

### Reframe

CosmeticSignal is a secondary extension module. It should not have equal homepage weight with the core three-module story.

Recommended placement:

- "More modules" menu
- dedicated route
- optional demo extension

### Layout

Reuse DrugSignal's signal-review shell rather than importing its CSS class names directly. Create a shared `SignalReviewLayout` or shared style primitives for:

- score summary
- reaction distribution
- source/evidence
- event records

### Default Density

Show the signal summary and top reactions. Keep individual event records collapsed.

## 5. Ask DAV AI

See the dedicated assistant section below.

## 6. Reports

### Keep

- supported module selection
- role selection
- report style selection
- request review
- PDF download
- explicit no-PHI warning

### Remove or Simplify

- remove sparkle emoji
- remove purple "AI" gradient identity
- remove unavailable profile and weekly-monitor buttons
- do not treat email-intent storage as a completed delivery feature
- reduce the three-step flow to two steps if preview does not render actual report content

### Recommended Flow

1. Configure report
2. Review and download

Use a module-contextual report action:

> Generate report from this RecallRadar result

The standalone report launcher can remain available from an Actions menu, but it should not compete with Ask DAV AI as a second floating button.

### Safety Copy

Keep the no-PHI warning and one acknowledgement. Two long checkboxes plus repeated review and preview warnings are excessive for a public-data-only prototype.

## 7. Audit History

### Keep

- filter controls
- event list
- selected detail
- copy actions
- CSV export
- source-pull summary
- basic/technical toggle
- deep-link support

### Improve

- Reduce the large marketing-style intro card.
- Put "Recent audit events" and filters immediately under the page title.
- Use a compact toolbar for export and reset.
- Preserve the desktop split layout.
- On mobile, replace the wide table with event cards rather than horizontal scrolling.
- Keep technical JSON and identifiers in a monospace evidence section.
- Make the selected row and detail relationship more visually obvious.

### Recommended Visual Role

Audit History should establish the design language for:

- tables
- selected state
- technical metadata
- copy actions
- evidence badges
- status colors

## 8. Saved Monitors

### Keep

- monitor creation
- manual run action
- latest and previous values
- run history
- deterministic insight
- audit links
- explicit production-alert limitation

### Simplify

Each monitor card currently includes:

- header
- action group
- four metric cards
- change pills
- insight card
- run history
- payload change
- multiple audit actions

This is too dense for the default state.

### Recommended Monitor Card

**Collapsed row:**

- name
- module
- query
- latest status
- last checked
- score/record change
- Run check

**Expanded details:**

- insight
- latest/previous metrics
- last three runs
- payload-change status
- audit links
- delete action

### Product Boundary

Label the page:

> Manual monitoring workspace

Avoid language that implies production notifications or automatic user alerts.

## 9. Data Sources

### Keep

- registered sources
- freshness status
- last successful retrieval
- record count
- update cadence
- last error
- endpoint

### Redesign

The current page renders every source as a large card. A source registry is better represented as a compact list or table with expandable details.

Recommended columns:

- source
- module
- freshness
- last success
- last count
- status

Expand a row for:

- endpoint
- description
- cadence
- error detail
- safety note

This improves scanning and reduces card repetition.

## 10. System Status

### Keep

- API state
- database configured
- audit readable
- source count
- freshness counts
- recent audit data quality

### Simplify

System Status currently repeats many of the same full source cards shown on Data Sources.

Recommended structure:

1. top-level health summary
2. service checks
3. data quality summary
4. source freshness counts
5. link to Data Sources for per-source detail

Do not duplicate the complete source registry.

### Status Honesty

Label the page "Environment Status" or "Prototype Operations" if it only reports the currently configured environment. Avoid implying enterprise observability.

## 11. Safety Briefing

### Keep

- deterministic generation
- role selection
- sections for findings, verification, checklist, limitations

### Improve

- Do not render the full briefing automatically after every result.
- Use a clear "Generate briefing" secondary action.
- Present the role selector before generation.
- Keep one section open at a time on mobile.
- Add a copy action.
- Label the output "Deterministic briefing" rather than using version numbers as the main eyebrow.

## 12. Regional Health

### Keep

- clear sample/scaffold labeling
- source and limitation visibility
- controlled options

### Position

Keep this out of the core demo and primary navigation. Mark it with an `Experimental` badge. Its styling should follow the standard module shell rather than maintaining a large separate page-specific system.

---

## Ask DAV AI UX Recommendations

## 1. Reframe It as an Analysis Panel

The current assistant is a drawer labeled as a chatbot. The product behavior is closer to a contextual analyst:

- it uses the current module result
- it has no broad conversation memory
- it is bounded by supplied context
- it returns evidence and limitations

Recommended name in the UI:

> Ask DAV AI  
> Contextual analysis for the selected result

Avoid message bubbles and avatar conventions.

## 2. Toggle and Placement

Replace the separate floating chat and report controls with one contextual action group.

Desktop:

- fixed compact utility rail, or
- actions in the result summary header

Mobile:

- one bottom action bar with `Ask`, `Report`, and `Save`
- actions collapse into a sheet when space is limited

The Ask action should display whether context exists:

- green dot + "RecallRadar context ready"
- neutral dot + "Run a search to enable"

## 3. Drawer Structure

Recommended drawer width: 420-480px desktop.

### Header

- Ask DAV AI
- current module badge
- selected query
- close button

### Context Card

Show:

- Module: RecallRadar
- Query: metformin
- Source: openFDA Drug Enforcement
- Retrieved: timestamp
- Audit ID: shortened, with copy action
- Context records: count

This makes grounding visible before the user asks a question.

### Prompt Area

Use 3-4 module-specific prompts rather than one growing shared list.

**RecallRadar:**

- Explain the highest review score
- What product details should I verify?
- Summarize the official-source evidence

**DrugSignal:**

- Explain this reporting pattern
- What does FAERS not prove?
- What changed from the previous result?

**FoodRadar:**

- Compare the FDA and USDA findings
- What lot or package details should I check?
- Explain why this result ranked highest

**CosmeticSignal:**

- Summarize the top reaction pattern
- What does this cosmetic report not prove?
- What official details should I verify?

## 4. Answer Format

Replace one paragraph plus a generic bullet list with:

1. **Summary**
2. **What to verify**
3. **Evidence used**
4. **Limitations**

Use restrained dividers, not chat bubbles.

### Evidence Used

Each citation should show:

- source label
- retrieval timestamp
- audit ID
- copy or open-audit action

Long identifiers should be shortened visually while preserving full accessible text and copy behavior.

## 5. Limitations

Do not print every limitation as multiple full paragraphs by default.

Show:

> Safety boundary: Public-data explanation only. No diagnosis, treatment, personal risk, or causation claims.

Add an expandable "View all limitations" control for module-specific detail.

## 6. Empty State

Current empty state explains that a search is required. Improve it by making the action explicit:

> No result selected  
> Run a RecallRadar, DrugSignal, FoodRadar, or CosmeticSignal search. DAV AI will use that result, source, and audit ID as its complete answer context.

Include links or buttons to the core modules.

## 7. Loading and Error States

Loading:

- show a compact skeleton or progress row
- state "Reviewing current result context"
- do not imply external browsing

Error:

- explain whether context is missing or backend assistant is unavailable
- preserve the question
- provide Retry
- avoid clearing a valid previous answer unless a new result context is selected

## 8. Context Changes

When the user runs a search in another module:

- update the context badge immediately
- clear or archive the previous answer
- show "Context changed from RecallRadar to FoodRadar"

This prevents an answer from appearing to reference the wrong module.

## 9. Dialog Accessibility

The drawer should add:

- `aria-modal="true"` when modal behavior is intended
- initial focus on the heading or input
- Escape-to-close
- focus containment
- focus restoration to the trigger
- visible label association for context and prompt areas
- non-color context status

---

## Animation and Icon System Recommendations

## Animation Principles

Motion should explain:

- a state changed
- a panel opened
- data loaded
- a result became available
- a status requires attention

Motion should not continuously decorate the page.

### Recommended Timing Tokens

| Token | Duration | Use |
|---|---:|---|
| Fast | 120ms | button press, icon shift |
| Standard | 180ms | hover, selected state |
| Panel | 220-260ms | drawer, accordion, sheet |
| Data reveal | 300ms | one-time result appearance |

### Recommended Easing

- standard: `cubic-bezier(0.2, 0, 0, 1)`
- exit: `cubic-bezier(0.4, 0, 1, 1)`

## Keep

- subtle button elevation
- chevron rotation for expanded details
- assistant drawer transition
- one-time result reveal
- loading skeleton shimmer when reduced motion is not requested

## Remove or Reduce

- continuously rotating radar sweeps in multiple sections
- floating capsule icons
- floating summary shields
- persistent glowing dots on static operational cards
- repeated pulsing arrows
- large scroll reveal movement
- infinite glass scan sweep
- decorative floating hero cards

The product should not appear to be processing data when it is idle.

## Loading States

Use module-specific skeletons:

- source summary skeleton
- result-row skeleton
- score placeholder
- evidence-line placeholder

Avoid plain paragraphs such as "secure backend wakes up." Loading messages should describe the actual task:

- "Querying openFDA recall records"
- "Normalizing FDA and USDA results"
- "Loading audit history"

## Score Transitions

If a score animates:

- animate once after a new response
- transition color and bar width in 250-350ms
- keep the number immediately available to assistive technology
- do not count from zero if it delays understanding

## Source and Audit Status

Use a pulse only for:

- actively loading
- an in-progress monitor run
- a reconnecting service

Use static badges for:

- success
- empty
- stale
- error
- recorded

## Reduced Motion

Keep the existing global reduced-motion rule, but also:

- avoid relying on animation to reveal content
- remove transforms from selected/focused states under reduced motion
- ensure drawers appear immediately
- ensure progress states include text

## Icon System

Use one icon family with:

- 1.75-2px stroke
- rounded line caps
- no filled cartoon illustrations
- 16px, 20px, and 24px sizes
- 32-40px icon containers only for module launchers

A lightweight package such as `lucide-react` is reasonable if it replaces many duplicated inline SVGs. A local typed `Icon` component is also appropriate and avoids a dependency.

### Suggested Mapping

| Concept | Icon |
|---|---|
| Public source | Database or globe |
| Source verified | Badge check |
| Audit trail | Git branch, history, or fingerprint |
| Retrieval timestamp | Clock |
| Report generated | File text |
| Monitor saved | Bookmark or radar |
| Manual run | Play circle |
| Warning/limitation | Triangle alert |
| Bounded assistant | Sparkle inside document or message-square-code |
| RecallRadar | Radar |
| DrugSignal | Capsule |
| FoodRadar | Package search or utensils with search |
| CosmeticSignal | Droplet or package |
| FDA/openFDA | Neutral government-building/database icon plus text |
| USDA FSIS | Neutral source/database icon plus text |

Do not imitate official agency logos without confirming appropriate usage. Source text is more important than a decorative logo.

---

## Copy and Safety Boundary Cleanup

## 1. Create a Safety Communication Hierarchy

### Level 1: Persistent Product Boundary

Display once in the application shell or page header:

> Public data only | No PHI | Informational, not medical advice

### Level 2: Module-Specific Boundary

Display near the search control:

**RecallRadar**

> Recall matches require verification against official product, lot, and agency details.

**DrugSignal**

> FAERS reports show reporting patterns and do not prove causation or incidence.

**FoodRadar**

> Verify exact package, lot, establishment, and official FDA/USDA notice.

**CosmeticSignal**

> Cosmetic-event reports can be incomplete or duplicated and do not prove product harm.

### Level 3: Result-Specific Limitation

Show only when relevant:

- source returned no records
- source was unavailable
- score confidence is limited
- trend lacks history
- one source failed while another succeeded

### Level 4: Full Technical/Legal Detail

Place in:

- expandable Limitations panel
- report footer
- About/Help documentation

## 2. Remove Repetitive Generic Cards

The Safe Insight Cards repeat:

- source visibility
- review signal
- safety boundary

These are useful ideas, but they do not need a titled three-card section after every query.

Replace with a compact evidence bar:

```text
Source: openFDA | Retrieved: 10:42 AM | 5 records | Review score: High | View evidence
```

Then show one concise module-specific boundary below it.

## 3. Standardize Empty-State Copy

Use a consistent structure:

1. No matching records returned
2. What that means
3. What to try next

Example:

> No matching FDA recall records were returned for this query. This is not a safety determination. Try the brand, product, ingredient, or recall number.

## 4. Standardize Error Copy

Avoid exposing implementation instructions such as "Make sure the FastAPI backend is running on port 8000" in the portfolio UI.

Use:

> DAV AI could not reach the recall service. Retry the request or check Environment Status.

Development-specific troubleshooting can remain in local logs or documentation.

## 5. Remove Vague AI Language

Prefer:

- deterministic score
- source-grounded explanation
- current-result context
- rule-based classification
- public reporting pattern

Avoid:

- smart insights
- AI-powered safety
- intelligent prediction
- risk detection
- live intelligence

unless the exact behavior is defined next to the term.

## 6. Standardize Product Name

Use **DAV AI** consistently in:

- headings
- loading copy
- reports
- assistant
- page titles
- accessibility labels

---

## Accessibility and Performance Notes

## Accessibility

### Focus and Keyboard

- Preserve the global `focus-visible` system.
- Ensure custom cards that behave like links remain actual buttons or links.
- Add Escape-to-close and focus restoration to both drawers.
- Avoid nested interactive elements inside clickable cards.
- Maintain logical heading levels after homepage sections are removed.
- Ensure all `summary` elements have visible focus and adequate touch height.

### Color and Status

- Never communicate freshness, score, or error by color alone.
- Include text labels and icons.
- Verify text contrast on green, amber, and purple-tinted surfaces.
- Avoid light gray metadata below 4.5:1 contrast at small sizes.

### Motion

- Centralize reduced-motion behavior.
- Remove non-essential infinite animation.
- Keep content present even when animation is disabled.

### Forms

- Maintain explicit labels.
- Add concise field-level error text.
- Use `aria-describedby` for helper and error text.
- Do not require two long acknowledgement controls when one concise acknowledgement is sufficient.
- Ensure all touch targets are at least 44px.

### Tables

- Audit and source tables need accessible captions or headings.
- On mobile, convert dense tables into labeled cards.
- Preserve table semantics on desktop.
- Do not rely only on sticky headers for context.

### Drawers

- Add dialog focus management.
- Prevent background scrolling when a modal drawer is open.
- Do not let the report and assistant drawers overlap.

## Responsive Behavior

Test at:

- 360x800
- 390x844
- 768x1024
- 1024x768
- 1280x800
- 1440x900

Key responsive goals:

- no horizontal navigation grid covering excessive vertical space
- no fixed actions obscuring content
- no truncated audit IDs without copy access
- no source endpoint overflow
- result summaries remain scannable
- mobile module actions remain above technical details

## Performance

### Reduce Paint Cost

The application uses many:

- backdrop filters
- large blurred shadows
- radial gradients
- fixed grid overlays
- infinite animations

Reduce these, especially on:

- long module pages
- scrolling result lists
- mobile devices

### CSS

- consolidate shared tokens and component primitives
- remove duplicate selector definitions
- eliminate undefined CSS variables
- prefer transform and opacity for necessary motion
- avoid animating box-shadow continuously

### React

Future restructuring can:

- route secondary modules instead of rendering all homepage modules at once
- lazy-load operations pages and secondary modules
- mount drawers only when opened
- avoid regenerating identical assistant context callbacks
- keep module state local but share visual primitives

No backend API contract change is required for the visual modernization.

---

## Phased Implementation Roadmap

## Phase 1: Quick Polish, Low Risk, High Visual Impact

**Goal:** Remove the strongest credibility and consistency problems without changing application structure.

### Tasks

1. Standardize product naming to DAV AI.
2. Remove the hero sample score, decorative chart, orbs, and floating cards.
3. Replace the hero visual with the evidence workflow preview.
4. Keep either Hero module cards or Safety Workspace, not both.
5. Remove or relocate Signals.
6. Remove "Live data flow" language and persistent operational glow effects.
7. Restyle FoodRadar source and limitation cards to match the shared light system.
8. Restyle the report launcher using the teal product palette.
9. Remove sparkle emoji and unavailable report actions.
10. Add explicit styling for all navigation groups.
11. Resolve undefined CSS custom properties.
12. Replace development-specific backend error messages with product-level errors.
13. Consolidate each module's initial safety copy to one boundary.

### Likely Files

- `frontend/src/App.css`
- `frontend/src/App.tsx`
- `frontend/src/components/Hero.tsx`
- `frontend/src/styles/hero.css`
- `frontend/src/components/SafetyWorkspace.tsx`
- `frontend/src/styles/safety-workspace.css`
- `frontend/src/components/OperationalOverview.tsx`
- `frontend/src/styles/operational-overview.css`
- `frontend/src/components/Signals.tsx`
- `frontend/src/styles/signals.css`
- `frontend/src/components/Navbar.tsx`
- `frontend/src/styles/navbar.css`
- `frontend/src/styles/foodradar.css`
- `frontend/src/components/FloatingSafetyReportIntake.tsx`
- `frontend/src/styles/floating-safety-report-intake.css`
- `frontend/src/components/AskDavAIChat.tsx`
- `frontend/src/styles/ask-dav-ai.css`

### Phase 1 Exit Criteria

- no fake/sample analytical metric appears above the fold
- only one core-module launcher appears on the homepage
- no unavailable action appears as an enabled or disabled primary control
- navigation groups have consistent styling
- FoodRadar visually belongs to the same product
- no undefined shared CSS variables remain

## Phase 2: Layout Restructuring and Component System Cleanup

**Goal:** Build one maintainable workspace system and reduce module-level repetition.

### Tasks

1. Create shared design tokens.
2. Create shared button, form, status, evidence, result-row, and boundary styles.
3. Introduce a reusable `ModuleShell`.
4. Introduce a reusable `SearchPanel`.
5. Introduce a reusable `EvidenceBar`.
6. Replace Safe Insight Cards with the evidence bar and one boundary message.
7. Create shared signal-review primitives for DrugSignal and CosmeticSignal.
8. Restructure homepage modules into routes or workspace views.
9. Simplify System Status and link to Data Sources rather than repeating source cards.
10. Convert Data Sources into a list/table with expandable rows.
11. Convert Saved Monitor cards to collapsed summaries with expandable details.
12. Add mobile card treatment for Audit History.

### Likely Files

- `frontend/src/styles/tokens.css` (new)
- `frontend/src/styles/base.css` (new or extracted)
- `frontend/src/styles/layout.css` (new)
- `frontend/src/styles/components/forms.css` (new)
- `frontend/src/styles/components/buttons.css` (new)
- `frontend/src/styles/components/status.css` (new)
- `frontend/src/components/ui/ModuleShell.tsx` (new)
- `frontend/src/components/ui/SearchPanel.tsx` (new)
- `frontend/src/components/ui/EvidenceBar.tsx` (new)
- `frontend/src/components/ui/BoundaryNotice.tsx` (new)
- `frontend/src/components/RecallRadar.tsx`
- `frontend/src/components/DrugSignal.tsx`
- `frontend/src/components/FoodRadar.tsx`
- `frontend/src/components/CosmeticSignal.tsx`
- `frontend/src/components/AuditHistoryPage.tsx`
- `frontend/src/styles/audit-history.css`
- `frontend/src/components/SavedMonitorsPage.tsx`
- `frontend/src/components/SavedMonitorsPage.css`
- `frontend/src/components/DataSourcesPage.tsx`
- `frontend/src/components/SystemStatusPage.tsx`
- `frontend/src/styles/datasources.css`

### Phase 2 Exit Criteria

- all core modules share the same page header, search, result summary, and evidence patterns
- no feature CSS depends on another feature's private class names
- shared selectors are defined once
- module default states contain no more than one major elevated panel
- Audit, Sources, and System use one operations design language
- 360px layouts have no horizontal overflow

## Phase 3: Animation and Icon System

**Goal:** Add restrained polish after layout and hierarchy are stable.

### Tasks

1. Establish motion duration and easing tokens.
2. Remove unnecessary infinite animations.
3. Add assistant/report drawer transitions.
4. Add result skeletons.
5. Add one-time result-row reveal.
6. Add clear in-progress monitor state.
7. Add consistent icon component or lightweight icon package.
8. Replace duplicated inline SVG implementations.
9. Add status icons to freshness, audit, source, report, and monitor states.
10. Verify reduced-motion behavior for every animated component.

### Likely Files

- `frontend/src/styles/animations.css`
- `frontend/src/styles/tokens.css`
- `frontend/src/components/ui/Icon.tsx` (new), or icon-package integration
- `frontend/src/components/Hero.tsx`
- `frontend/src/components/RecallRadar.tsx`
- `frontend/src/components/DrugSignal.tsx`
- `frontend/src/components/FoodRadar.tsx`
- `frontend/src/components/CosmeticSignal.tsx`
- `frontend/src/components/AskDavAIChat.tsx`
- `frontend/src/components/FloatingSafetyReportIntake.tsx`
- corresponding module CSS files

### Phase 3 Exit Criteria

- idle pages contain no continuous decorative motion
- loading, success, warning, and error states use both icon and text
- all motion respects reduced-motion preferences
- one icon family is used throughout
- drawer transitions remain responsive on low-power mobile devices

## Phase 4: Deeper Product Polish for Demo and Interviews

**Goal:** Make the primary story easy to demonstrate in three to four minutes.

### Tasks

1. Add a guided core demo path:
   - RecallRadar
   - evidence
   - audit
   - Ask DAV AI
   - report or monitor
2. Make the active result context visible globally.
3. Add contextual actions instead of separate floating buttons.
4. Add direct "Open audit" links from every core module.
5. Add report success state with filename and source scope.
6. Add copy actions for briefing, assistant answer, and evidence summary.
7. Add a compact architecture/engineering page for portfolio reviewers.
8. Add a truthful project badge:
   - Graduate portfolio prototype
   - Deterministic scoring
   - Public sources
   - No production ML claim
9. Complete keyboard and screen-reader review.
10. Perform responsive visual regression review.

### Likely Files

- `frontend/src/App.tsx`
- `frontend/src/components/Navbar.tsx`
- core module components
- `frontend/src/components/AskDavAIChat.tsx`
- `frontend/src/components/FloatingSafetyReportIntake.tsx`
- `frontend/src/components/AuditHistoryPage.tsx`
- `frontend/src/components/AboutPage.tsx`
- relevant tests for interaction and accessibility behavior

### Phase 4 Exit Criteria

- a reviewer understands the product in 10 seconds
- a live demo reaches provenance in under 90 seconds
- Ask DAV AI always displays current source and audit context
- unavailable roadmap features are not presented as product controls
- every major claim can be tied to visible application behavior or repository evidence

---

## Suggested Acceptance Criteria

## Product Clarity

- [ ] The hero states what DAV AI does in one sentence.
- [ ] The hero communicates public sources, provenance, and auditability above the fold.
- [ ] No fake user, adoption, accuracy, risk, or production metric is displayed.
- [ ] ProductScan/OCR is not represented as implemented.
- [ ] Regional Health is visibly labeled experimental/sample when shown.
- [ ] Deterministic scoring is described as a review heuristic, not a prediction.

## Homepage

- [ ] Only one core-module launcher is present.
- [ ] The default homepage has no more than five major sections.
- [ ] The hero visual uses real product concepts rather than a decorative sample dashboard.
- [ ] Engineering credibility is visible without turning the homepage into a resume.
- [ ] Secondary modules do not interrupt the primary RecallRadar -> DrugSignal -> FoodRadar story.

## Visual System

- [ ] One token file defines colors, spacing, radii, shadows, typography, and motion.
- [ ] No undefined CSS custom properties are used.
- [ ] Standard cards use a consistent radius and border treatment.
- [ ] Pills are reserved for compact status and filters.
- [ ] Purple is not used as a competing primary brand color.
- [ ] Dark cards are used only for intentionally technical content, such as JSON/code.
- [ ] Feature styles do not redefine unscoped global selectors.

## Module UX

- [ ] Every core module follows the same high-level order: search, summary, results, actions, evidence.
- [ ] Source, retrieved time, record count, and audit link are visible after a successful query.
- [ ] Technical metadata is available but collapsed by default.
- [ ] Empty states explain both meaning and next action.
- [ ] Error states avoid local-development instructions.
- [ ] Result lists remain usable at 360px without horizontal scrolling.

## Safety Copy

- [ ] A persistent product boundary appears once per page or shell.
- [ ] Each module has one concise module-specific limitation near the search.
- [ ] Full limitations remain available through progressive disclosure.
- [ ] "Not medical advice" is not repeated in more than two simultaneously visible locations.
- [ ] FAERS and cosmetic causation boundaries remain explicit.
- [ ] Official-source verification language remains available where action could follow.

## Ask DAV AI

- [ ] The current module, query, source, retrieval time, and audit ID are visible in the drawer.
- [ ] Prompt chips are module-specific.
- [ ] Answers are organized into summary, verification, evidence, and limitations.
- [ ] Context changes invalidate or clearly separate the previous answer.
- [ ] Empty state links to an action that creates context.
- [ ] Error state supports retry without losing the question.
- [ ] Drawer supports Escape, focus containment, and focus restoration.

## Reports

- [ ] PDF download is the clear primary completion action.
- [ ] Unimplemented email/profile/weekly actions are not rendered as controls.
- [ ] The report flow uses the DAV AI primary visual system.
- [ ] No-PHI guidance remains visible.
- [ ] Report source scope is shown before download.

## Audit and Operations

- [ ] Audit History retains desktop list/detail behavior.
- [ ] Audit History uses mobile event cards instead of a wide table.
- [ ] Data Sources can be scanned without opening every source card.
- [ ] System Status does not duplicate the full source registry.
- [ ] Saved Monitors are clearly labeled manual/foundation behavior.
- [ ] Operational status language does not imply production SLOs or alerting.

## Accessibility

- [ ] All controls are keyboard reachable.
- [ ] All focus states are clearly visible.
- [ ] Touch targets are at least 44px.
- [ ] Status is not communicated by color alone.
- [ ] Drawer focus and background-scroll behavior are correct.
- [ ] Reduced-motion mode removes non-essential motion.
- [ ] Heading hierarchy is valid on every page.
- [ ] Contrast meets WCAG AA for body and metadata text.

## Performance

- [ ] Infinite decorative animation is removed.
- [ ] Large backdrop blurs are limited to navigation and drawers.
- [ ] Secondary routes/modules can be lazy-loaded.
- [ ] No animation causes layout shift.
- [ ] Core mobile pages remain responsive on mid-range hardware.
- [ ] Performance and accessibility Lighthouse targets are at least 90 for the primary demo route, subject to upstream API behavior.

## Demo Readiness

- [ ] One stable demo query is prepared for RecallRadar.
- [ ] One stable demo query is prepared for FoodRadar or DrugSignal.
- [ ] The demo reaches an audit record and provenance evidence.
- [ ] Ask DAV AI visibly uses the selected result context.
- [ ] A PDF report can be generated without exposing unavailable features.
- [ ] The complete demo can be delivered in under four minutes.

---

## Final Recommendation

DAV AI does not need more visual spectacle. It needs stronger editing.

The project already contains the material needed for a compelling 2026 portfolio presentation:

- real public sources
- full-stack workflows
- deterministic and explainable logic
- typed frontend/backend contracts
- bounded AI behavior
- reports
- audit-linked provenance
- monitoring foundations
- operational transparency

The modernization should make those engineering decisions easier to see. The best final product will use fewer homepage sections, fewer repeated cards, fewer gradients, fewer warnings shown at once, and fewer floating controls. In exchange, it should provide clearer hierarchy, a consistent evidence model, stronger module layouts, and more deliberate progressive disclosure.

The intended impression should be:

> This graduate student understands how to turn uncertain public data into a usable, inspectable, responsibly bounded software system.

That is a stronger portfolio claim than looking like a generic AI startup landing page.
