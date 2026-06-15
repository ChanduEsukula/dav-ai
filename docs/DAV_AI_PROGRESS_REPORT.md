# Dav AI Progress Report — Student Project, Engineering Review, Product Use Case, and UX Risk Audit

**Review date:** June 14, 2026  
**Reviewed branch:** `feature/universal-safety-search` at `20bcbb5`  
**Review mode:** Read-only repository audit. No application code was changed.  
**Overall portfolio grade:** **B+ (87/100)**  
**Realistic signal:** **Entry-level-ready full-stack engineer; AI-adjacent entry-level candidate; not yet mid-level or production-ready.**

## 1. Executive Summary

- Dav AI is a full-stack public-data review workspace for drug recalls, adverse-event reports, food recalls, cosmetic events, source provenance, audits, monitors, and PDF reports.
- It is substantially above average for a master's student portfolio because it includes real APIs, persistence design, migrations, audit metadata, deterministic scoring, CI, tests, and safety boundaries.
- The use case is worth building when positioned as a public-record verification and review tool, not as an AI system that determines whether a product is safe.
- The strongest engineering work is the provenance layer: source registry, audit events, raw public-source snapshots, SHA-256 payload hashes, request IDs, freshness status, and traceable report inputs.
- The strongest professional signal is disciplined scope language around FAERS causation, medical advice, Regional Health Pulse sample data, and offline-only ML experiments.
- The current branch has a serious integration problem: the richer RecallRadar, DrugSignal, FoodRadar, and CosmeticSignal components still exist, but the routed app now uses consolidated safety pages that omit several of their audit, briefing, semantic, assistant, and report integrations.
- Ask Dav AI is currently visible but nonfunctional in the routed application because `assistantContext` is permanently initialized to `null` and has no setter.
- The checked-in Playwright smoke test fails because it expects the old standalone module pages while navigation now opens the consolidated pharmacy and food pages.
- Saved Monitors advertises CosmeticSignal support, but the database constraints omit `cosmeticsignal` and the manual run route does not implement it.
- Static homepage metrics such as `24.6K Records scanned`, `1.2K New this week`, and `98% Traceable` are not backed by code or a data source and weaken trust.
- The project is useful for a prepared portfolio demo and for teaching public-data verification, but it is not ready for uncontrolled public use because it lacks authentication, ownership, rate limiting, retention controls, and explicit persistence-failure behavior.
- The best next move is not another feature. Select one canonical user journey, restore its end-to-end trust features, fix the E2E test, remove unsupported claims, and update the documentation to match the executable branch.

## 2. Student Project Evaluation

### Direct Assessment

| Question | Assessment |
|---|---|
| How are you doing as a student? | Very well on breadth, learning velocity, testing, and responsible framing. Less well on consolidation and maintaining one coherent product contract as the project evolves. |
| Relative level | Above average for a graduate student project. Most student portfolios do not include source provenance, migrations, scheduled-job foundations, PDF generation, audit filters, and 400+ automated tests. |
| Skills demonstrated | React, TypeScript, Vite, FastAPI, Pydantic, PostgreSQL, Alembic, API integration, deterministic scoring, repository design, test automation, CI, product copy, safety boundaries, and technical documentation. |
| Early-engineering weaknesses | Duplicate product surfaces, very large components, hand-rolled routing, stale docs, schema/API drift, inconsistent version labels, silent persistence fallback, and insufficient end-to-end integration tests. |
| Learning ability | Strong. The commit history shows repeated hardening, source expansion, safety copy refinement, testing, and UI iteration. |
| Ownership | Strong. The repository covers product, frontend, backend, persistence, deployment notes, testing, and responsible-AI decisions. |
| Product thinking | Good but overextended. You identify user workflows and safety risks, but the product serves too many personas and modules at once. |
| Testing discipline | Strong at unit/component level. The failing smoke test shows that integration gates are not yet being treated as release blockers. |
| AI engineering judgment | Better than the product name implies. Keeping production behavior deterministic and ML experiments offline is responsible. Calling the overall system "AI" is still broader than the deployed intelligence warrants. |
| Grade | **B+ (87/100).** The technical ambition and evidence are excellent for a student. The grade is held below A by current branch integration regressions, unsupported UI claims, architecture duplication, and production-safety gaps. |

### What Most Clearly Shows Growth

- You moved beyond a CRUD demo into source-aware workflows with auditability.
- You wrote tests around safety language, source failure, monitor history, and request state rather than only happy-path rendering.
- You separated offline ML experiments from production routes.
- You documented what the system must not claim.
- You added migrations and operational surfaces instead of hiding persistence complexity.

### What Still Looks Early-Career

- New UX work sometimes replaces integration rather than extending it.
- Documentation is frequently used as a milestone ledger, producing many stale "current" documents.
- Passing unit tests appears to have outweighed a failing user-journey smoke test.
- Several abstractions are duplicated across components instead of being shared.
- Fail-soft behavior sometimes hides correctness failures rather than exposing degraded state.

## 3. Interviewer Evaluation

| Interviewer | What impresses | What concerns | Likely questions | Demo first | Avoid overclaiming |
|---|---|---|---|---|---|
| NVIDIA senior engineer | Deterministic scoring, versioning intent, offline ML experiments, source lineage, clear separation between experimentation and production. | No deployed ML pipeline, model evaluation system, feature store, GPU work, or measurable model value. Current assistant is unwired. | Why is this called AI? How would you evaluate an NLP model safely? How do you prevent training-serving skew? | Audit/provenance, offline experiment boundaries, one scoring workflow. | Do not call deterministic rules a production ML system or imply GPU/LLM expertise from this project alone. |
| Google senior engineer | Typed frontend, service boundaries, extensive tests, clear APIs, auditability, CI. | Hand-rolled router, duplicate module architectures, N+1 monitor loading, no auth, no pagination, direct database connections, failing E2E. | What invariants failed during the routing redesign? How would this scale to 100,000 monitors? How do you test contracts? | A search request through API, normalization, scoring, audit, and UI. | Do not describe the system as scalable or production-ready. |
| Microsoft senior engineer | End-to-end ownership, practical web stack, operational pages, deployment documentation, accessibility foundations. | Identity and authorization are absent; error handling and degraded-state UX are inconsistent; public mutable endpoints are risky. | How would you add Entra-style identity and resource ownership? What telemetry and SLOs would you add? | System Status, Audit History, Saved Monitor architecture, then a search. | Do not claim enterprise readiness, tenant isolation, or alerting. |
| Apple senior engineer | Attention to copy, source boundaries, privacy warnings, custom UI, and report output. | Dense and visually inconsistent UI, static fake metrics, two floating actions, stale information architecture, no fresh visual regression suite. | Why should a consumer trust each number? What happens with VoiceOver and keyboard-only use? What data remains on device? | A clean consumer search and exact source verification flow. | Do not call the experience polished until mobile, focus management, and unsupported CTAs are fixed. |
| Startup hiring manager | One person built product, frontend, backend, tests, migrations, docs, and deployment foundations. Strong shipping energy. | Too much scope, many large files, unclear primary customer, brittle integrations, and operational/security work deferred. | What would you cut for a four-week launch? Which metric proves value? What is the first paying user? | One problem, one persona, one complete workflow. | Do not demo every page or present the roadmap as already shipped. |

### Hiring Signal

- **Entry-level full-stack roles:** Yes, this project can materially help obtain interviews.
- **Entry-level backend roles:** Yes, especially when you lead with provenance, API workflows, persistence, and testing.
- **Entry-level AI engineer roles:** Some help, but it signals responsible AI/product judgment more than production ML engineering.
- **Internships:** Strong signal.
- **Mid-level roles:** Not by itself. The repository lacks evidence of operating a multi-user production system, making architecture tradeoffs under load, and maintaining team-owned interfaces.
- **Big Tech:** Helpful as a conversation starter, not sufficient alone. Algorithms, fundamentals, collaboration examples, and a concise technical narrative still matter.

### Questions You Should Be Ready to Answer

1. Why did you choose deterministic scores instead of ML?
2. How do you prove an output came from a specific public-source response?
3. Why does the same query's DrugSignal score depend on the fetch limit?
4. What failed when standalone module pages were replaced by combined pages?
5. How would you add user ownership to Saved Monitors?
6. Why is silent in-memory fallback dangerous in production?
7. What does a zero-result response mean, and what does it not mean?
8. How would you evaluate the assistant against fabricated client context?

## 4. Engineering Architecture Review

### Architecture Scorecard

| Area | Score | Review |
|---|---:|---|
| Frontend structure | 7/10 | Clear folders and typed API clients, but routing and module duplication now create drift. |
| Backend structure | 8/10 | Good route/service/scoring/repository separation for a student project. |
| API contracts | 7/10 | Typed and tested, but frontend omits useful FoodRadar normalization fields and feature parity is inconsistent. |
| Provenance/audit | 9/10 | The strongest part of the system. |
| Test strategy | 8/10 | Excellent unit/component breadth; insufficient release-level journey enforcement. |
| Maintainability | 6/10 | Several 600-1,300 line files and duplicated workflows will slow future changes. |
| Scalability | 4/10 | Direct connections, synchronous work, N+1 requests, no caching/rate limits/pagination. |
| Production readiness | 3/10 | No identity, ownership, abuse controls, retention policy, or durable degraded-state guarantees. |

### Frontend Strengths

- React 19, TypeScript strict mode, Vite, Axios, Vitest, Testing Library, and Playwright are appropriate choices.
- API response types make the public-data contracts understandable.
- Request IDs, stale-request protection, URL query state, partial pharmacy results, and accessible loading/error regions show thoughtful implementation.
- New safety pages contain clearer zero-result wording and avoid displaying a numeric cosmetic or pharmacy signal when no records are returned.
- Responsive breakpoints, `focus-visible` rules, semantic `details`, and reduced-motion rules provide a solid accessibility base.

### Frontend Weaknesses and Debt

- `App.tsx` uses query-string state as a hand-built router. This is workable for a small demo but brittle for nested state, stale parameters, deep links, and route-level loading.
- RecallRadar and DrugSignal navigation both open `pharmacy-safety`; FoodRadar and CosmeticSignal open consolidated pages. The rich standalone components remain in the codebase but are not mounted.
- The new pages omit features still advertised elsewhere: audit details, semantic previews, deterministic role briefings, contextual assistant wiring, and direct PDF actions.
- `assistantContext` is always `null`; the visible Ask Dav AI control cannot answer from a current result.
- `OperationalOverview` links to `#recallradar`, but that target is no longer present on the home page.
- Navbar active-state logic checks `activePage === 'home'` for branded modules, so module buttons are not marked active on their actual routed pages.
- `FoodSafetyPage` and `CosmeticSafetyPage` receive old-module navigation props they do not use, a clear sign of transition debt.
- `AuditHistoryPage` is 835 lines, `SavedMonitorsPage` 669, and the three new safety pages are 632-704 lines. They need later extraction by responsibility, not cosmetic splitting.

### Backend Strengths

- FastAPI routes are separated from reusable search workflows.
- Pydantic request and response schemas are explicit.
- Source registry, audit events, source pulls, raw snapshots, stable SHA-256 hashes, and metadata-only provenance reads are unusually strong portfolio features.
- Backend tests isolate the developer's real `DATABASE_URL`.
- Search workflows persist error audit events and expose source-level status.
- FoodRadar includes a useful multi-source abstraction and explicit limitations.
- Offline ML experiments are not mixed into production behavior.

### Backend Weaknesses and Debt

- There is no authentication, authorization, monitor ownership, tenant isolation, or protection for public audit queries.
- `SavedMonitorRepository` silently falls back to process memory after database failures. A request may appear successful while data is non-durable and disappears after restart.
- CosmeticSignal is allowed by Pydantic and the UI, but omitted from SQL monitor constraints and from manual monitor execution.
- Direct `psycopg.connect` per operation has no connection pooling.
- Source calls have timeouts but no retries, backoff, caching, circuit breaker, or upstream rate-limit handling.
- Broad exception handling often maps internal or persistence defects to `502`, obscuring whether the failure is upstream, database, validation, or code.
- Search strings are interpolated into openFDA query syntax without escaping embedded quotes or query operators.
- FoodRadar is fail-soft only when USDA fails. If openFDA Food Enforcement fails first, USDA results are not attempted or returned.
- `reportlab` is unpinned.
- API docs and mutable endpoints are public by default.
- Logger namespaces still use the old `medtrek` name.

### Scoring and Data Contract Risks

- Recall records emit `recall-review-priority-v0.2`, while response-level and audit metadata say `recall-risk-v0.1`.
- FoodRadar repeats the same score-version mismatch.
- DrugSignal's score object says `drug-signal-intelligence-v0.1`, while audit metadata says `drug-signal-score-v0.1`.
- DrugSignal scores depend on the requested result limit. The same query can score differently in a page, monitor, preview, or PDF.
- A zero-record DrugSignal response receives a score of 10 because concentration and confidence components add baseline points.
- Cosmetic concentration divides the top reaction count by record count; repeated terms inside a report can produce a percentage over 100 unless capped.
- Counts represent fetched and capped records, not total source matches.

### What to Refactor Later

1. Introduce a real router and route-level state model.
2. Choose shared search-domain view models for pharmacy, food, and cosmetic pages.
3. Extract result table, source evidence, safety boundary, and query guidance components.
4. Replace repository silent fallback with explicit persistence modes and health status.
5. Add a database pool and transaction boundaries.
6. Centralize score-version constants across output, audit, report, and tests.
7. Add generated OpenAPI contract checks or shared schemas for frontend types.
8. Split the PDF renderer into module-specific document builders and shared layout primitives.

### What Not to Touch Right Now

- Do not rewrite FastAPI or React.
- Do not replace deterministic scores with ML.
- Do not add another data source or module.
- Do not redesign every visual component.
- Do not introduce microservices, Kubernetes, a vector database, or a new state library.
- Preserve the provenance model, safety boundaries, typed clients, and existing focused tests while repairing integration.

## 5. Product Use Case Review

### Is Dav AI Worth Making?

Yes, with narrower positioning. Public FDA and USDA records are fragmented, technical, and easy to misread. A product that helps a reviewer locate likely records, compare exact identifiers, understand source limitations, and preserve an audit trail is useful.

The product is not valuable because it says "AI." It is valuable because it reduces the work required to verify public records while keeping source and uncertainty visible.

### Real Target User

The best initial user is not an average consumer making a medical decision. It is a **public-data reviewer**:

- pharmacy operations or medication-safety staff
- food quality or compliance staff
- university researchers
- public-health analysts
- journalists or nonprofit investigators
- technically confident consumers verifying a known recall notice

Average consumers can benefit from a simplified search and verification experience, but they are a secondary persona because the underlying datasets require exact product, package, lot, date, and manufacturer matching.

### Problem Solved

Dav AI helps users:

- choose the relevant public-data workflow
- search multiple public sources with normalized output
- distinguish recalls from adverse-event reports
- see source, retrieval time, and limitations
- preserve an audit trail
- generate a review report
- repeat selected checks over time

### Problem Not Solved

Dav AI does not:

- determine whether a specific product in a user's possession is safe
- provide medical advice or personal risk
- prove causation or incidence
- replace official recall notices
- guarantee source completeness
- scan labels or automatically match UPC, NDC, or lot identifiers
- provide production alerts or emergency guidance

### Best Product Form

| Form | Fit |
|---|---|
| Broad consumer safety oracle | Poor fit and high misunderstanding risk |
| Consumer verification helper | Reasonable secondary experience |
| Pharmacy/compliance review workflow | Strongest practical fit |
| Public-health dashboard | Plausible later, but current Regional Health data is only sample scaffolding |
| Portfolio project | Excellent fit today |

### One-Line Pitch

> Dav AI helps people find and verify public FDA and USDA safety records across drugs, food, supplements, and cosmetics, with source timestamps and audit trails.

### Recommended Positioning

> **Dav AI is a source-audited public-record verification workspace. It helps reviewers search, normalize, compare, and document public safety records without turning incomplete public data into medical advice or product-safety verdicts.**

### Claims to Avoid

- "Dav AI tells you whether a product is safe."
- "AI predicts safety risk."
- "Real-time monitoring" unless scheduler and delivery are actually operating.
- "Search by UPC, NDC, or lot" until identifier-aware parsing and source-field queries exist.
- "Contextual AI assistant" while the routed app supplies no context.
- "Production-ready healthcare platform."

## 6. Average Consumer Benefit

| Consumer situation | What Dav AI can help verify | What it cannot guarantee | Recommended next step |
|---|---|---|---|
| Searches a drug name | Whether returned public recall records or FAERS-style reports mention the term; source and date. | That their exact medication is affected, that an event was caused by the drug, or what they should do medically. | Match exact label/NDC/strength/manufacturer in the official source; ask a pharmacist or clinician for personal guidance. |
| Searches a recalled food | Product description, firm, recall reason, source, dates, and code information when present. | That the food in their home is included or excluded. | Compare brand, package, UPC, lot/code, establishment number, and official FDA/USDA notice. |
| Searches a cosmetic | Public cosmetic-event reports, product names, reported reactions, outcomes, and source timing. | Product defect, causation, incidence, or personal safety. | Verify the exact product and read the official record; seek medical help separately for symptoms. |
| Searches in the wrong module | Dav AI can suggest pharmacy, food, or cosmetic routing for recognized terms. | Correct classification for unknown brands, abbreviations, or identifiers. | Choose the category based on the product label; retain the original query. |
| Has a lot number or label | Dav AI can display lot/code fields returned in matched food records. | Reliable identifier lookup today; the backend does not search dedicated lot/UPC/NDC fields. | Search the product or brand, then compare the exact identifier in official notices. |
| Sees no results | Dav AI can explain that the exact query returned no records from the checked workflow. | Safety, absence of a recall, source completeness, or correct spelling/category. | Try generic/brand variants and verify official sources directly. |
| Sees reports or a high signal | Dav AI can summarize returned reporting patterns and review priority. | Causation, incidence, severity for the individual, or clinical urgency. | Review source records and consult the appropriate professional for personal decisions. |

### Disclaimer Presentation

Disclaimers should be calm, layered, and actionable:

1. Near the search: "Public records only. Not medical advice or a safety guarantee."
2. Near results: explain the source-specific limitation, such as FAERS non-causation.
3. In expanded evidence: show full technical limitations and source metadata.
4. In zero states: state what was checked and what the user can try next.

Avoid repeating long warnings in every card. Repetition makes users stop reading and can make a normal verification task feel alarming.

## 7. Page-by-Page Review

### Home / Universal Safety Search

- **Purpose:** Introduce the product and route a query to pharmacy, food, or cosmetic workflows.
- **Strengths:** Clear examples, deterministic routing, partial pharmacy preview, responsible preview wording, typo suggestions, and direct workflow choices for ambiguous terms.
- **Gaps:** Only one classified category is searched; arbitrary brands and identifiers become ambiguous. Static homepage metrics are unsupported. The same module story is repeated in Hero, Safety Workspace, Operational Overview, and Signals.
- **Risks:** Users may interpret "Universal" as a comprehensive cross-source search. UPC/NDC/lot claims exceed actual field-aware behavior.
- **Best next improvement:** Rename it "Guided safety search," add identifier detection, remove static metrics, and reduce the homepage to one launcher plus one provenance explanation.
- **Demo-ready:** **Conditional.** Use prepared terms such as Xanax, chicken, sunscreen, or protein powder.

### Pharmacy Safety

- **Purpose:** Compare drug recall records and FAERS-style reporting patterns.
- **Strengths:** Correctly separates the two source types, supports partial source success, protects against stale requests, provides sorting and zero-result guidance.
- **Gaps:** Recall sorting re-fetches DrugSignal unnecessarily. Audit, semantic preview, briefing, assistant context, and report integration from the old modules are absent.
- **Risks:** Nav labels imply separate RecallRadar and DrugSignal destinations, but both land on the same page with no active nav item.
- **Best next improvement:** Make this the canonical pharmacy workspace and restore evidence/assistant/report integrations as collapsible panels.
- **Demo-ready:** **Mostly**, after the navigation and E2E contract are fixed.

### Food & Supplement Safety

- **Purpose:** Review FDA food enforcement and USDA FSIS records.
- **Strengths:** Multi-source status, useful record fields, sorting, strong verification copy, typo flow, and safer no-result language.
- **Gaps:** Frontend types discard backend normalization fields such as `correction_applied` and `suggestion_message`. Search-intent expansion mostly affects post-fetch ranking, not the upstream query.
- **Risks:** OpenFDA failure prevents USDA-only results. UPC/lot wording implies direct lookup that is not implemented.
- **Best next improvement:** Surface backend corrections, make both sources independently fail-soft, and implement identifier-aware search or narrow the copy.
- **Demo-ready:** **Yes with prepared queries**, while clearly describing source coverage.

### Cosmetic Safety

- **Purpose:** Review public cosmetic-event reports and reaction patterns.
- **Strengths:** Multiple records, reaction summaries, product/industry context, source details, and no numeric score when zero reports are returned.
- **Gaps:** No audit panel, assistant context, report action, saved-monitor action, or semantic evidence in the routed page.
- **Risks:** "FDA CAERS-style" and signal scores can sound more authoritative than incomplete voluntary reporting supports.
- **Best next improvement:** Restore audit and report links and explain exactly what the score counts.
- **Demo-ready:** **Conditional**, especially because current worktree changes are not yet represented by a passing E2E path.

### RecallRadar

- **Purpose:** Rich standalone drug recall review.
- **Strengths:** Detailed records, deterministic briefing, score breakdown, audit metadata, semantic preview, and assistant-context builder.
- **Gaps:** It is no longer mounted by `App.tsx`.
- **Risks:** README and demo docs still describe it as a current standalone journey.
- **Best next improvement:** Either integrate its evidence panels into Pharmacy Safety or restore a dedicated route. Do not maintain both indefinitely.
- **Demo-ready:** **No as a standalone page on this branch.**

### DrugSignal

- **Purpose:** Rich standalone FAERS reporting-pattern review.
- **Strengths:** Reaction classification, trend snapshot, score explanation, role briefing, semantic preview, audit metadata, and assistant context.
- **Gaps:** It is no longer mounted; a zero-result response can still carry a backend score of 10.
- **Risks:** The score depends on fetch limit and can be mistaken for medical risk.
- **Best next improvement:** Normalize zero-result scoring and restore the useful evidence panels inside the canonical pharmacy experience.
- **Demo-ready:** **No as a standalone page on this branch.**

### FoodRadar

- **Purpose:** Rich standalone food/supplement recall review and PDF download.
- **Strengths:** Audit/source information, sorting, PDF action, and assistant context.
- **Gaps:** It is no longer mounted. The new Food Safety page duplicates much of it without feature parity.
- **Risks:** Two implementations will continue to diverge.
- **Best next improvement:** Merge the best features into one component hierarchy and retire the other.
- **Demo-ready:** **No as a standalone page on this branch.**

### CosmeticSignal

- **Purpose:** Rich standalone cosmetic reporting review.
- **Strengths:** Assistant-context builder, score limitations, source information, and report-capable backend.
- **Gaps:** It is no longer mounted; it has less evidence UI than older RecallRadar/DrugSignal surfaces.
- **Risks:** Documentation says it has parity while monitor persistence and manual runs do not.
- **Best next improvement:** Make parity an executable contract with route, monitor, report, assistant, audit, and E2E coverage.
- **Demo-ready:** **No as a standalone page on this branch.**

### Saved Monitors

- **Purpose:** Save repeatable searches, run manual checks, compare history, and inspect deterministic insights.
- **Strengths:** Duplicate prevention, run history, previous/latest comparison, audit linking, payload-change status, and schedule foundations.
- **Gaps:** No auth or ownership. Cosmetic creation conflicts with DB constraints; manual cosmetic runs return 422. Initial load performs two additional requests per monitor.
- **Risks:** Silent database fallback can make non-durable data look saved. Failed history/insight calls are hidden as empty data.
- **Best next improvement:** Fix cosmetic end to end or hide it, expose persistence mode, batch detail reads, and require identity before public deployment.
- **Demo-ready:** **Conditional for RecallRadar, DrugSignal, FoodRadar, and sample Regional monitors only.**

### Audit History

- **Purpose:** Inspect query, source, versions, status, request metadata, and source-pull provenance.
- **Strengths:** A real differentiator with filters, detail views, copy/export actions, and payload hashes.
- **Gaps:** CosmeticSignal is absent from the module filter. URL deep links only select an event if it appears in the fetched page even though a detail API exists.
- **Risks:** Clickable table rows lack keyboard interaction. Clipboard failures are not handled. Public audit queries may expose user-entered text.
- **Best next improvement:** Fetch deep-linked IDs directly, add keyboard semantics, include all modules, and establish access/privacy policy.
- **Demo-ready:** **Yes**, with a known recent audit ID.

### Sources

- **Purpose:** Explain registered sources and audit-backed freshness.
- **Strengths:** Transparent endpoints, cadence, last retrieval, record count, and source-error state.
- **Gaps:** The aggregate FoodRadar workflow is counted as a source in addition to its two upstream sources. Error text lacks alert semantics.
- **Risks:** Freshness can be confused with source correctness or data completeness.
- **Best next improvement:** Separate "external sources" from "aggregate workflows" and simplify freshness explanation.
- **Demo-ready:** **Yes.**

### System

- **Purpose:** Show API, database, audit readability, source registry, freshness, and recent audit quality.
- **Strengths:** Valuable operational transparency for a portfolio.
- **Gaps:** `Promise.all` means one failed endpoint blanks the whole page. Latest query/audit information is public.
- **Risks:** "System Status" may be mistaken for production observability despite no metrics, traces, alerts, or SLOs.
- **Best next improvement:** Render each subsystem independently and rename it "Demo system diagnostics" until production monitoring exists.
- **Demo-ready:** **Yes**, if the backend is running.

### Regional Health Pulse

- **Purpose:** Demonstrate how the architecture could support regional public-health signals.
- **Strengths:** Very clear sample-data disclaimers, provenance, deterministic signal explanation, and limited supported combinations.
- **Gaps:** Only MN/CA and three hardcoded combinations; not in primary navigation.
- **Risks:** Any live-surveillance wording would be misleading. The audit link assumes root deployment at `/`.
- **Best next improvement:** Keep it explicitly sample-only and move it to an "Experiments" or "Architecture extensions" area.
- **Demo-ready:** **Yes only as a labeled scaffold.**

### Ask Dav AI

- **Purpose:** Answer bounded questions from current result context.
- **Strengths:** Server-side provider keys, context schema, pre/post guardrails, citations, limitations, and a deterministic mock provider.
- **Gaps:** The current app never supplies context. Client-provided context is trusted rather than independently retrieved by audit ID.
- **Risks:** A malicious client can fabricate source context. Regex guardrails are narrow. Dialog focus management is incomplete.
- **Best next improvement:** Wire it to the canonical result view, retrieve trusted context server-side, and hide the button when no context exists.
- **Demo-ready:** **No.**

### Floating Safety Report Intake

- **Purpose:** Collect a public-data report request and download a PDF.
- **Strengths:** PHI warnings, acknowledgement gates, supported module mapping, local storage that omits email, and real backend PDF download.
- **Gaps:** Report style and region are only placed in `purpose`; the PDF renderer does not use `purpose`, so the output does not actually vary by selected style or region. Email is not saved or sent.
- **Risks:** "Coming next" actions look like product functionality. The modal lacks Escape, focus trap, and focus restoration.
- **Best next improvement:** Remove unsupported controls, make selected options affect output, and complete dialog accessibility.
- **Demo-ready:** **Conditional for PDF download only.**

### PDF / Report Generation

- **Purpose:** Create branded one-page module reports and a two-module recall/drug report.
- **Strengths:** Real PDF bytes, module-specific content, source/audit fields, filenames, disclaimers, and route tests.
- **Gaps:** A 1,371-line renderer is hard to maintain. Report generation performs live source calls and has no rate limiting. `purpose` is ignored.
- **Risks:** Source failure blocks report generation; reports are not persisted; output is not independently visually regression-tested in this review.
- **Best next improvement:** Split module builders, add PDF text/layout assertions or rendered snapshots, and rate-limit the endpoint before public use.
- **Demo-ready:** **Yes with a stable source query and local backend.**

## 8. UI/UX Design Review

### Overall Design Judgment

Dav AI looks modern in components, but not yet coherent as one product. It combines a marketing homepage, glassmorphism, dense operational dashboards, dark source cards, a purple report funnel, and technical audit tables. Each can work independently; together they make the app feel assembled from several design phases.

### Specific Findings

| Area | Finding | Recommended fix |
|---|---|---|
| Visual system | Teal/blue/green is credible, but purple report styling and heavy glass effects introduce competing identities. | Use one evidence-first system: neutral surfaces, teal actions, blue information, green verified, amber caution, red failure. |
| Layout | Long pages and repeated cards create scanning fatigue. | Show one primary task above the fold; move evidence and limitations into predictable expandable panels. |
| Navigation | Too many horizontal items; branded module names no longer map cleanly to routed pages. | Use Workspace, Monitors, Audit as primary navigation and a module selector inside Workspace. |
| Typography | Generally readable, but many eyebrow labels, badges, subtitles, and helper lines compete. | Reduce metadata styles and establish a strict heading/body/label scale. |
| Card hierarchy | Nearly every surface is elevated, rounded, or highlighted. | Reserve elevation for selected/floating content; use borders for normal data cards. |
| Color use | Color is attractive but sometimes decorative rather than semantic. | Tie each status color to a documented meaning and avoid decorative status pulses. |
| Accessibility | Good semantic foundations, but dialogs and clickable table rows need keyboard/focus work. | Add focus trap/return, Escape close, keyboard-selectable audit rows, and automated axe checks. |
| Responsive design | Many breakpoints exist, which is positive. Global `overflow-x: hidden` can hide real layout defects. | Remove masking where possible and test 320, 375, 768, 1024, and zoomed desktop widths. |
| Above the fold | Hero and module marketing delay the actual search. | Put the guided search and source boundary first. |
| Empty states | New safety pages are thoughtful but can show both banner and panel no-result messages. | Use one primary empty state and make secondary panels quiet. |
| Loading states | Text status is accessible, but full panels reset and disappear during searches. | Preserve previous results with an updating state when appropriate. |
| Error states | Pharmacy handles partial failure well; System and other pages collapse too broadly. | Use source-specific error cards and preserve successfully loaded data. |
| Wrong-category suggestions | Useful for recognized terms, weak for unknown brands and no-space strings. | Combine deterministic classification with explicit category choice and identifier detection. |
| Typo suggestions | Helpful but hardcoded and tiny in coverage. | Use backend normalization or a bounded vocabulary/fuzzy matcher with transparent suggestions. |
| CTA clarity | "Analyze," branded nav buttons, "Know more," Ask Dav AI, and report intake compete. | One primary CTA per page; contextual secondary actions after results. |
| Density | Recruiters can see depth, but average users face too much evidence at once. | Progressive disclosure and persona-focused default views. |

### Recruiter Demo Readiness

The visual system is close enough for a recruiter demo, but only after:

- removing static fabricated metrics
- fixing the broken smoke journey
- hiding or wiring Ask Dav AI
- choosing one canonical page per module area
- preparing stable demo queries
- confirming desktop and mobile screenshots

## 9. Trust, Safety, and Wording Review

### What Is Already Good

- Repeated statements that FAERS reports do not prove causation.
- Clear "not medical advice" and "not a medical device" boundaries.
- Regional Health Pulse is explicitly sample data, not live surveillance.
- Zero-result text often says absence does not prove safety.
- Recall scoring comments explicitly define the value as review priority, not medical risk.

### High-Risk Wording

| Current concept | Risk | Better wording |
|---|---|---|
| `risk_score` API field | Developers and users can read it as medical/product risk. | Keep for compatibility internally, display "Review priority" everywhere, and document deprecation. |
| "Universal safety search" | Implies comprehensive coverage across records and identifiers. | "Guided public-record search." |
| "Checks UPC, NDC, or lot number" | Dedicated identifier lookup is not implemented. | "You can include label identifiers, but exact identifier matching is not yet supported." |
| "24.6K Records scanned" | Unsupported metric creates false authority. | Remove, or calculate from audited persisted source pulls and label the time range. |
| "98% Traceable" | Undefined denominator and methodology. | "Results include source and retrieval metadata when available." |
| "AI Monitor Insight" | The insight is deterministic rules over stored history. | "Deterministic monitor summary." |
| Cosmetic "signal score" | Can imply danger or product risk. | "Returned-report review signal." |
| DrugSignal "intelligence score" | Can imply clinical intelligence. | "Returned-report review signal." |
| "No matching records" | Users may hear "safe." | "No records were returned for this exact query from the sources checked." |
| "Real-time" or "monitoring" | Scheduler and alert delivery are not productionized. | "Repeatable manual checks with scheduled-refresh foundation." |

### Recommended Result Boundary

> This result summarizes public records returned for the exact query and sources shown. It does not determine whether a product is safe, whether a report was caused by the product, or whether the result applies to your exact package, lot, label, or medical situation.

### Recommended Zero-Result Copy

> No records were returned for this exact query from the sources checked. Try a generic name, brand variant, or corrected spelling, and verify the official FDA or USDA source. No result is not a safety guarantee.

### Recommended Adverse-Event Copy

> These are public reports of events submitted after product use. They may be incomplete, duplicated, delayed, or influenced by reporting behavior. They do not prove causation or incidence.

## 10. 162 User Issues and Edge Cases

### Search and Typing Issues

1. **An empty search can leave prior result context visible in some flows.** Why it matters: users may believe old records match the blank query. **Fix:** clear or explicitly label retained results whenever input becomes empty.
2. **A one-character query is blocked by backend validation but not explained consistently before submission.** Why it matters: a generic error feels like an outage. **Fix:** enforce and display the same minimum length in every form.
3. **Leading, trailing, and repeated spaces are normalized, but the UI does not always show that normalization.** Why it matters: URL text and result text can appear inconsistent. **Fix:** display the submitted normalized query and preserve raw input only for correction messaging.
4. **Singular and plural terms such as `egg`/`eggs` or `vitamin`/`vitamins` are not handled consistently across all classifiers and sources.** Why it matters: equivalent searches can route or match differently. **Fix:** add bounded morphological normalization and contract tests.
5. **Brand and generic names can produce different routes and records.** Why it matters: consumers may not know both names. **Fix:** show known brand/generic alternatives only when sourced from an authoritative drug-label dataset.
6. **A bare UPC value is not recognized unless the text includes `UPC`.** Why it matters: the homepage promises UPC searches. **Fix:** detect valid UPC-A/EAN lengths and route to an identifier-aware food search.
7. **A bare NDC value is not recognized unless the text includes `NDC`.** Why it matters: pharmacy users commonly paste digits and hyphens. **Fix:** parse standard NDC patterns and query appropriate label/enforcement fields.
8. **A lot code by itself is classified as ambiguous.** Why it matters: users with a recall notice often start with the lot. **Fix:** request product category/brand and support field-specific code matching.
9. **Special characters or quotes can break openFDA query syntax.** Why it matters: real product names contain punctuation. **Fix:** escape or construct source queries with a tested encoder.

### Spelling and Missing-Space Issues

10. **`proteinpowder` is normalized by the backend but classified as ambiguous by Universal Search.** Why it matters: the request never reaches FoodRadar normalization. **Fix:** share correction logic before routing.
11. **`protienpowder` has neither the space nor the correct spelling.** Why it matters: it misses both current frontend and backend correction maps. **Fix:** add bounded fuzzy correction for high-value terms.
12. **`peanutbutter` does not match the phrase `peanut butter`.** Why it matters: common mobile typing fails. **Fix:** compare a no-space normalized form for known multiword terms.
13. **`hairdye` does not match `hair dye`.** Why it matters: cosmetic routing becomes ambiguous. **Fix:** add phrase compaction aliases and tests.
14. **`chees` is not suggested as `cheese`.** Why it matters: a simple typo produces a category-choice dead end. **Fix:** use edit-distance suggestions within the food vocabulary.
15. **`cheesecurd` does not match `cheese` or a known food phrase.** Why it matters: a valid food product is treated as unknown. **Fix:** tokenize known substrings carefully and add compound-food aliases.
16. **`sunscrean` is suggested only after a zero-result request.** Why it matters: an unnecessary API call delays a predictable correction. **Fix:** offer the correction before search while still allowing the original.
17. **`metforimn` is similarly corrected only after zero results.** Why it matters: it causes two pharmacy source calls and two audits before correction. **Fix:** preflight known corrections and record the accepted correction.
18. **`xanex` depends on a tiny hardcoded map.** Why it matters: users may assume general typo support that does not exist. **Fix:** label suggestions as limited and expand through a controlled drug-name index.

### Wrong Module / Wrong Category Issues

19. **An unknown drug brand may be classified as ambiguous.** Why it matters: users cannot tell which workflow to choose. **Fix:** provide simple product-type prompts and optional authoritative label lookup.
20. **A cosmetic brand that is also a common word can route to food or remain ambiguous.** Why it matters: wrong-category guidance becomes unreliable. **Fix:** use explicit category selection when confidence is low.
21. **A supplement containing a drug-like ingredient can match both pharmacy and food.** Why it matters: the user may miss relevant enforcement records. **Fix:** allow multi-area search or explain why both areas are offered.
22. **A product such as medicated shampoo crosses pharmacy and cosmetic categories.** Why it matters: a single route may omit relevant records. **Fix:** offer both workflows and preserve the query.
23. **RecallRadar and DrugSignal nav buttons open the same Pharmacy Safety page without explaining the merge.** Why it matters: navigation feels broken. **Fix:** rename the nav item to Pharmacy Safety or restore separate views.
24. **FoodRadar nav opens Food Safety, while old FoodRadar features are absent.** Why it matters: the branded promise and page capability differ. **Fix:** use one canonical name and feature set.
25. **CosmeticSignal nav opens Cosmetic Safety, while monitor/report parity is incomplete.** Why it matters: users assume parity from the label. **Fix:** align all integrations or mark beta limitations.
26. **Wrong-category suggestions appear only after zero records.** Why it matters: source calls are wasted and users wait for a predictable route hint. **Fix:** show a low-confidence route suggestion before submission.
27. **Changing categories can preserve a stale `audit_id` URL parameter.** Why it matters: a later Audit visit may open unrelated evidence. **Fix:** clear route-specific parameters on every page transition.

### No-Result Issues

28. **A zero-result search can show both a page-level guidance banner and a panel empty card.** Why it matters: duplicate messages make the page feel broken. **Fix:** designate one primary empty-state component.
29. **DrugSignal calculates 10/100 for zero records.** Why it matters: old or future views can display a score despite no evidence. **Fix:** return an explicit unscored state for zero records.
30. **No result does not identify which exact fields were searched.** Why it matters: users cannot judge whether their lot or brand was actually checked. **Fix:** show a concise "searched fields" summary.
31. **No result can be caused by source caps rather than true absence.** Why it matters: only the first 25 upstream records are considered. **Fix:** disclose result caps and use source totals/pagination when available.
32. **No result after typo correction may still be treated as proof the correction was right.** Why it matters: the system can silently redirect intent. **Fix:** show original and corrected terms and allow undo.
33. **No result for a bare identifier provides generic spelling advice.** Why it matters: spelling is not the relevant problem. **Fix:** detect identifiers and provide identifier-specific help.
34. **No result from an ambiguous query performs no source calls but looks like a search outcome.** Why it matters: users may think all sources were checked. **Fix:** label it clearly as "category needed; no source search run."
35. **A zero-record cosmetic response still reports `Limited` confidence.** Why it matters: confidence sounds like a model judgment instead of no evidence. **Fix:** use `Not assessable` when count is zero.
36. **No-result guidance does not offer direct official-source links.** Why it matters: the safest fallback requires extra searching. **Fix:** provide source links with the query where URL formats safely allow it.

### Partial-Result Issues

37. **A pharmacy search can show one source while the other failed, but stale prior results are cleared first.** Why it matters: users lose useful comparison context. **Fix:** preserve old data with an "updating" label until new outcomes arrive.
38. **Partial pharmacy results use one general notice rather than naming the failed source prominently.** Why it matters: users may assume both recall and FAERS coverage. **Fix:** show per-source success/error badges near counts.
39. **FoodRadar handles USDA failure but not openFDA failure symmetrically.** Why it matters: USDA-only records are lost. **Fix:** call sources independently with `gather`/`allSettled` semantics.
40. **An empty source and a failed source can both contribute zero records.** Why it matters: zero is not enough to understand coverage. **Fix:** make status, count, and timestamp separate required fields.
41. **Partial source data can still receive a normal combined review score.** Why it matters: the score may appear complete. **Fix:** attach coverage status and suppress or qualify combined summaries.
42. **A PDF fails entirely if its source retrieval fails.** Why it matters: the report cannot document a degraded search. **Fix:** optionally generate a failure-status report with no safety conclusion.
43. **Saved Monitor insights silently become unavailable when their API request fails.** Why it matters: users cannot distinguish no insight from an outage. **Fix:** display per-monitor error state and retry.
44. **Saved Monitor run history silently becomes an empty list on error.** Why it matters: history loss can be mistaken for no prior runs. **Fix:** preserve existing history and show a fetch error.
45. **System Status uses one `Promise.all`, so one endpoint failure hides successful subsystems.** Why it matters: diagnostics become less useful during partial outages. **Fix:** load and render subsystems independently.

### Source / API Issues

46. **Source calls have no retry or backoff.** Why it matters: transient FDA/USDA failures become user-facing errors. **Fix:** add bounded retries for idempotent requests with jitter and observability.
47. **There is no cache for repeated identical searches.** Why it matters: examples, sort toggles, reports, and monitors repeatedly hit upstream APIs. **Fix:** add short-lived query/source caching with visible retrieval time.
48. **Recall sorting triggers a second DrugSignal fetch.** Why it matters: it wastes latency, source quota, and audit rows. **Fix:** re-fetch only the recall endpoint or sort client-side when valid.
49. **OpenFDA query values are interpolated without escaping.** Why it matters: quotes and Lucene operators can produce invalid or broadened queries. **Fix:** centralize query escaping and tests.
50. **Recall search only targets `product_description`.** Why it matters: brand, firm, NDC, and category claims are broader than implementation. **Fix:** query supported fields or narrow the UI promise.
51. **Food search does not query `code_info`, UPC, or lot fields.** Why it matters: identifier-oriented copy is misleading. **Fix:** add field-specific clauses and exact-match modes.
52. **Counts are capped fetched counts, not total matches.** Why it matters: "reports found" can understate source volume. **Fix:** expose source metadata totals separately from displayed/fetched count.
53. **The aggregate FoodRadar workflow is registered alongside its upstream sources.** Why it matters: source counts can look inflated. **Fix:** classify registry entries as external source or internal aggregate.
54. **Errors often become generic 502 responses.** Why it matters: clients cannot distinguish upstream, database, parsing, and internal failures. **Fix:** define stable error categories and include request ID consistently.

### Route / History Issues

55. **The checked-in E2E test expects old RecallRadar and DrugSignal pages.** Why it matters: CI fails on the current branch. **Fix:** decide the canonical journey and update app plus E2E together.
56. **Browser Back/Forward resets `activeSection` to home even on module pages.** Why it matters: nav state can disagree with the displayed route. **Fix:** derive active navigation entirely from the route.
57. **Page-specific `pushState` calls do not notify App state directly.** Why it matters: consistency depends on local component state and manual popstate dispatches. **Fix:** use a router or centralized navigation function.
58. **A completed equivalent search can reuse old data while displaying newly cased query text.** Why it matters: displayed query and response payload can differ. **Fix:** retain the canonical response query or refresh display metadata together.
59. **`audit_id` is not cleared when moving among non-home pages.** Why it matters: stale deep-link state leaks across pages. **Fix:** explicitly whitelist parameters per route.
60. **Audit deep links fail for records outside the first fetched page.** Why it matters: copied evidence links can open the wrong/default event. **Fix:** call the existing audit-detail endpoint by ID.
61. **Regional Health audit links assume deployment at root `/`.** Why it matters: subpath hosting breaks navigation. **Fix:** construct URLs from the current base path/router.
62. **The Operational Overview CTA targets a missing `#recallradar` anchor.** Why it matters: a primary CTA appears to do nothing. **Fix:** use the canonical route action.
63. **Unknown `page` parameters silently return Home.** Why it matters: broken links are hidden. **Fix:** show a small not-found state or normalize with a clear redirect.

### Mobile Layout Issues

64. **The horizontal navbar contains too many items for a narrow screen.** Why it matters: important destinations may require awkward scrolling. **Fix:** use a compact menu and keep only primary destinations visible.
65. **Large summary grids and record rows can become dense at 320-375px.** Why it matters: values and labels may wrap unpredictably. **Fix:** test real content at narrow widths and stack semantic groups.
66. **Ask Dav AI and Safety Report are both fixed actions.** Why it matters: even when offset, they consume viewport space and can obscure controls. **Fix:** use one contextual action tray or hide unavailable actions.
67. **Global `overflow-x: hidden` can conceal overflow instead of fixing it.** Why it matters: clipped content may be inaccessible. **Fix:** remove masking selectively and repair overflowing components.
68. **Long endpoints and payload hashes can force narrow cards wider.** Why it matters: technical evidence becomes unreadable. **Fix:** use wrapping, copy controls, and expandable technical detail.
69. **Audit tables rely on horizontal scrolling.** Why it matters: row selection and column context are difficult on phones. **Fix:** switch to cards or a master-detail list below tablet width.
70. **The report drawer can occupy most of a small viewport without robust focus behavior.** Why it matters: keyboard and screen-reader users can lose position. **Fix:** implement a tested modal pattern.
71. **Long safety disclaimers dominate mobile result pages.** Why it matters: actual record verification fields move far below the fold. **Fix:** show a short boundary with expandable details.
72. **Many decorative cards and large radii reduce information density on mobile.** Why it matters: the demo requires excessive scrolling. **Fix:** simplify surfaces and reduce vertical padding at mobile breakpoints.

### Accessibility Issues

73. **Ask Dav AI dialog lacks `aria-modal`, focus trap, Escape close, and focus return.** Why it matters: keyboard users can interact behind the dialog or lose their place. **Fix:** implement a standard accessible dialog.
74. **Safety Report has `aria-modal` but still lacks trap, Escape, and focus restoration.** Why it matters: semantics alone do not manage interaction. **Fix:** add focus lifecycle tests.
75. **Audit rows are clickable `<tr>` elements without keyboard semantics.** Why it matters: keyboard users cannot select records equivalently. **Fix:** place a real button/link in the first cell or add full keyboard behavior.
76. **Data Sources errors lack `role="alert"`.** Why it matters: assistive technology may not announce failures. **Fix:** use a shared alert component.
77. **Some loading states are plain paragraphs without live regions.** Why it matters: async changes may not be announced. **Fix:** standardize `role="status"` and polite live behavior.
78. **Color-coded freshness and change pills may rely too much on color.** Why it matters: color-vision differences reduce meaning. **Fix:** retain explicit text/icons and test contrast.
79. **Long horizontal navigation lacks an obvious keyboard scroll affordance.** Why it matters: focused items can be hard to locate. **Fix:** use a menu or ensure focused elements scroll into view.
80. **Clipboard operations have no failure handling.** Why it matters: denied permissions produce no feedback. **Fix:** catch errors and announce copy failure.
81. **No automated accessibility suite is configured.** Why it matters: semantic regressions rely on manual review. **Fix:** add axe-based component tests and keyboard E2E scenarios.

### Wording / Trust Issues

82. **Static homepage metrics imply measured production usage.** Why it matters: unsupported authority damages recruiter and user trust. **Fix:** remove or calculate from auditable data.
83. **"Universal" suggests broader coverage than the finite keyword router.** Why it matters: users overestimate search completeness. **Fix:** call it guided routing or search all selected areas.
84. **"AI Monitor Insight" overstates deterministic comparison rules.** Why it matters: it obscures how the output is produced. **Fix:** label it deterministic and show the version.
85. **"Risk score" remains in API fields.** Why it matters: downstream clients may surface it as medical risk. **Fix:** introduce `review_priority_score` and deprecate the old field.
86. **"Confidence" on cosmetic results can sound like model confidence.** Why it matters: it is currently based on record-count thresholds. **Fix:** say "data volume category" or explain the formula.
87. **"Traceable" is used without defining which results persist successfully.** Why it matters: audit persistence can fail softly. **Fix:** show actual audit/snapshot status per result.
88. **A report preview says the selected style is ready even though output ignores style.** Why it matters: users receive a different product than requested. **Fix:** implement style variants or remove the selector.
89. **"Save email intent" sounds like data was stored.** Why it matters: the handler only displays a message. **Fix:** call it "Email delivery not available" or remove it.
90. **About and FAQ describe modules and sources that no longer match the routed app.** Why it matters: stale trust pages undermine credibility. **Fix:** generate or update current-state content with each release gate.

### Data Quality Issues

91. **Recall score version metadata is inconsistent.** Why it matters: audits cannot reproduce the exact displayed scoring contract. **Fix:** use one exported version constant everywhere.
92. **DrugSignal score version metadata is inconsistent.** Why it matters: report, audit, and response labels can refer to different names. **Fix:** align and migrate documentation.
93. **DrugSignal score changes with request limit.** Why it matters: the same query can look more or less important across pages. **Fix:** score a stable sampling policy or disclose sample size as part of the version.
94. **Recall recency score uses the current clock.** Why it matters: identical historical input changes score over time. **Fix:** include scoring timestamp in audit or score against retrieval time.
95. **Unknown recall classifications/statuses receive default points.** Why it matters: USDA fields may be scored with FDA assumptions. **Fix:** use source-specific scoring adapters and an unknown component.
96. **Distribution scope uses string length and keywords.** Why it matters: verbose text can receive broader-scope points incorrectly. **Fix:** parse source-specific geography or label the heuristic clearly.
97. **Cosmetic concentration can exceed 100 if repeated reaction terms occur within reports.** Why it matters: percentages become nonsensical. **Fix:** deduplicate per report or cap with a documented denominator.
98. **Audit save failure does not prevent returning a generated audit ID.** Why it matters: the UI can display an ID that was never persisted. **Fix:** return explicit audit persistence status and avoid claiming a durable trace.
99. **Raw snapshots have no documented retention, compression, size cap, or deletion policy.** Why it matters: storage and governance risk grow over time. **Fix:** establish lifecycle controls before production.

### Long Text / Truncation Issues

100. **Product descriptions are truncated in summary rows.** Why it matters: distinguishing label details may be hidden. **Fix:** keep full text accessible in expanded detail and via copy.
101. **Long recalling-firm names can overwhelm table columns.** Why it matters: dates/statuses become hard to scan. **Fix:** use responsive column priorities and wrapping.
102. **Long recall reasons create very tall expanded cards.** Why it matters: users lose context between records. **Fix:** add readable line length and optional expansion.
103. **Endpoints are displayed as raw long strings.** Why it matters: they dominate metadata cards. **Fix:** show source label plus copy/open actions.
104. **Audit query parameters can contain large JSON.** Why it matters: technical detail overwhelms basic users. **Fix:** collapse formatted JSON by default.
105. **Payload hashes and UUIDs wrap poorly on narrow screens.** Why it matters: copy mistakes become likely. **Fix:** monospace wrapping with dedicated copy buttons.
106. **Report prepared-for and organization text is truncated to 28 characters in PDF detail rendering.** Why it matters: names can be silently incomplete. **Fix:** wrap or validate to the displayed limit.
107. **Assistant output is character-truncated at 1,200 characters.** Why it matters: it can cut a sentence or limitation. **Fix:** generate within a structured schema and truncate by sections.
108. **README and docs are extremely long and repeat status claims.** Why it matters: reviewers cannot identify the actual source of truth. **Fix:** keep one current status page and archive milestones.

### Sorting / Filtering Issues

109. **Changing recall sort re-fetches unrelated adverse-event data.** Why it matters: slower interaction and duplicate audit noise. **Fix:** isolate sort-dependent requests.
110. **Food "score" sorting combines intent relevance and review score.** Why it matters: users may think it is purely highest safety-review score. **Fix:** label it "Best match" or expose separate sort choices.
111. **Food latest sorting falls back to digit extraction from mixed date formats.** Why it matters: malformed dates can sort incorrectly. **Fix:** normalize dates in source adapters.
112. **DrugSignal alphabetical sort changes reaction order but still creates a new audit/search.** Why it matters: a display preference should not imply new source evidence. **Fix:** sort returned reactions client-side.
113. **Audit module filters omit CosmeticSignal.** Why it matters: cosmetic audits are hard to find. **Fix:** derive filter options from known modules or API data.
114. **Audit filters are not encoded in the URL.** Why it matters: filtered views cannot be shared or restored. **Fix:** synchronize filter state with query parameters.
115. **Audit export contains only the currently loaded limited set.** Why it matters: users may mistake it for a full export. **Fix:** label scope or provide server-side export.
116. **Saved Monitors show only three runs despite the API returning more.** Why it matters: trend context is hidden. **Fix:** add a "View all runs" expansion.
117. **No pagination exists for monitors or source/audit cards beyond fixed limits.** Why it matters: performance and discoverability degrade as data grows. **Fix:** add cursor pagination and server-side filtering.

### Saved Monitor Issues

118. **CosmeticSignal monitor creation conflicts with database constraints.** Why it matters: production persistence fails. **Fix:** add a migration and schema update before exposing the option.
119. **Manual CosmeticSignal monitor runs are unsupported.** Why it matters: the UI promises a Run Check that returns 422. **Fix:** implement the workflow and tests or hide the module.
120. **Database errors silently fall back to memory.** Why it matters: users believe a monitor is durable when it is not. **Fix:** fail explicitly or mark the monitor as temporary/degraded.
121. **A restart loses memory-fallback monitors.** Why it matters: apparent saved data disappears. **Fix:** never use automatic memory fallback in production mode.
122. **List failure can return only process-memory items and hide database items.** Why it matters: the system presents an incomplete monitor set without warning. **Fix:** return a persistence error and preserve last known client data.
123. **All monitors are globally visible and mutable.** Why it matters: one user can view or delete another user's searches. **Fix:** add authentication and owner IDs.
124. **Initial loading makes 2N extra requests for N monitors.** Why it matters: latency and backend load scale poorly. **Fix:** return run summary and insight in a batched list endpoint.
125. **Delete uses browser `confirm`.** Why it matters: styling and accessibility are inconsistent. **Fix:** use an accessible confirmation dialog with monitor name.
126. **No schedule-edit UI exists despite schedule fields.** Why it matters: users may infer automation from backend metadata. **Fix:** keep scheduling hidden until ownership, observability, and delivery are ready.

### Report Intake Issues

127. **Report style selection does not change the PDF.** Why it matters: simple, technical, and pharmacy/clinic choices are misleading. **Fix:** implement templates or remove the field.
128. **Optional region does not change report content.** Why it matters: users expect regional filtering or labeling. **Fix:** render it clearly as context or remove it.
129. **Email is validated only by checking for `@`.** Why it matters: invalid addresses appear accepted. **Fix:** do not collect email until delivery exists; later use robust validation.
130. **Email intent is not saved or sent.** Why it matters: the success-like message is misleading. **Fix:** remove the action until a backend contract exists.
131. **"Save to My Safety Profile" is disabled but advertises a nonexistent account system.** Why it matters: the demo looks unfinished. **Fix:** remove coming-soon controls.
132. **"Monitor this weekly" is disabled while Saved Monitors has no user scheduling UI.** Why it matters: it implies alert functionality. **Fix:** remove until production scheduling is safe.
133. **Local storage retains report topics and region.** Why it matters: users may enter sensitive or private text despite warnings. **Fix:** minimize storage, add clear/delete controls, and reject likely PHI.
134. **Report endpoint is unauthenticated and rate-unlimited.** Why it matters: attackers can trigger repeated upstream calls and PDF generation. **Fix:** add rate limits and abuse controls.
135. **Report generation has no idempotency or cached source snapshot option.** Why it matters: repeated downloads create different audits and source calls. **Fix:** allow generation from a selected audit snapshot.

### Audit / Source Page Issues

136. **An audit ID can be shown even when persistence failed.** Why it matters: copied links may not resolve. **Fix:** expose `audit_persistence_status` in responses.
137. **Audit queries can contain accidental personal or medical information.** Why it matters: the system persists and publicly lists them. **Fix:** add input warnings, server-side detection/redaction, access control, and retention policy.
138. **Audit detail selection defaults to the first row when a deep-linked ID is absent.** Why it matters: users may inspect the wrong evidence. **Fix:** show not found and fetch the ID directly.
139. **Source freshness is based on latest audit activity, not independent source monitoring.** Why it matters: an unused source can look stale even if healthy. **Fix:** describe it as "last observed retrieval" or add scheduled health checks.
140. **Latest source errors can hide an older successful retrieval time.** Why it matters: users need both last attempt and last success. **Fix:** query and display both events.
141. **Aggregate FoodRadar freshness duplicates upstream interpretation.** Why it matters: users may see conflicting statuses. **Fix:** show workflow health separately from source freshness.
142. **System Data Quality exposes latest search query publicly.** Why it matters: it can leak user-entered terms. **Fix:** remove query text from public diagnostics or require admin access.
143. **No source page links directly to official documentation or usage limits.** Why it matters: reviewers cannot understand source semantics. **Fix:** add official documentation links and coverage notes.
144. **The source registry count is described as public sources even though one entry is an internal aggregate.** Why it matters: documentation and UI counts disagree. **Fix:** type and count entries separately.

### Average Consumer Confusion Issues

145. **Consumers may read a high review signal as a high chance of harm.** Why it matters: the score is not clinical risk. **Fix:** avoid standalone numbers or pair them with a plain-language formula and boundary.
146. **Consumers may assume FAERS report count is incidence.** Why it matters: reporting volume lacks exposure denominator. **Fix:** repeat non-incidence wording next to counts.
147. **Consumers may assume a matched recall covers their exact package.** Why it matters: recalls are lot/package/manufacturer specific. **Fix:** make exact-match verification the primary next step.
148. **Consumers may assume no recall means the product is safe.** Why it matters: source coverage and timing are incomplete. **Fix:** use the recommended zero-result copy consistently.
149. **Consumers may not understand the difference between recall and adverse-event data.** Why it matters: one is enforcement action and the other is reporting patterns. **Fix:** include a two-column explainer on Pharmacy Safety.
150. **Consumers may not know whether a supplement belongs in food or pharmacy.** Why it matters: records can exist in different systems. **Fix:** explain regulatory category and offer both where relevant.
151. **Consumers may paste symptoms into Ask Dav AI.** Why it matters: the app could appear to accept personal medical questions. **Fix:** hide chat without record context and provide a clear input boundary.
152. **Consumers may enter PHI into report topic or monitor query fields.** Why it matters: those values can be stored. **Fix:** add server-side PHI heuristics, rejection, and privacy controls.
153. **Consumers may believe source freshness means the product data is complete and correct.** Why it matters: freshness only reflects observed retrieval history. **Fix:** label the metric narrowly and explain limitations.

### Recruiter / Interviewer Demo Issues

154. **The first checked-in E2E journey fails.** Why it matters: a reviewer running CI sees a regression immediately. **Fix:** make the canonical demo path pass before presenting.
155. **Ask Dav AI opens without current context.** Why it matters: a headline feature appears unfinished. **Fix:** wire it or hide it for the demo.
156. **RecallRadar, DrugSignal, FoodRadar, and CosmeticSignal are described as pages but are unreachable as standalone modules.** Why it matters: the spoken demo can contradict the app. **Fix:** update the narrative and docs to the consolidated architecture.
157. **Static metrics look fabricated.** Why it matters: interviewers will question data integrity. **Fix:** remove them before any demo.
158. **About and FAQ are stale.** Why it matters: reviewers often use these pages to understand scope. **Fix:** make them match executable capabilities and current source count.
159. **Cosmetic monitor parity can fail in a live demo.** Why it matters: a visible option triggers a backend/schema defect. **Fix:** do not demo it until fixed.
160. **The homepage is too long for a short interview.** Why it matters: product depth becomes scrolling rather than explanation. **Fix:** use a focused route and a rehearsed three-minute path.
161. **Documentation contains many different "current verified" test counts.** Why it matters: it suggests weak release discipline. **Fix:** keep generated/current verification in one report and archive old checkpoints.
162. **The product name implies more production AI than the app currently uses.** Why it matters: AI interviewers may probe for models that are not deployed. **Fix:** lead with public-data intelligence, deterministic scoring, and responsible restraint.

## 11. Testing and QA Review

### Verification Results From This Audit

| Command | Result |
|---|---|
| Backend `pytest` with bytecode/cache disabled | **276 passed** |
| Frontend Vitest | **17 files, 146 tests passed** |
| Frontend ESLint | **Passed on final run** |
| TypeScript app no-emit | **Passed** |
| TypeScript Vite config no-emit | **Passed** |
| Playwright E2E smoke | **Failed** on expected old RecallRadar heading after navigation |
| `git diff --check` | **Passed** |

The first concurrent lint attempt encountered an `ENOENT` while Playwright was creating/removing `frontend/test-results`; the clean rerun passed. This is a tooling-race observation, not a source lint failure.

### Strong Existing Tests

- Backend routes, scoring, classifiers, audit repository, source pulls, source freshness, request logging, system status, reports, monitors, scheduler locks, and offline ML experiments.
- Frontend component behavior for all major old and new search surfaces.
- Stale-request behavior, query URL synchronization, typo correction, wrong-category suggestions, partial pharmacy results, no-result language, report contract mapping, and monitor interactions.
- CI includes backend tests, frontend lint/test/build, and Playwright.

### Important Missing Tests

- E2E tests for the current canonical consolidated pages.
- App-level test proving result context reaches Ask Dav AI.
- Cosmetic monitor creation against real migration constraints and manual-run route.
- Contract test asserting every `SavedMonitorModule` works through schema, migration, manual execution, scheduled execution, UI, and tests.
- Score-version equality across record, response, audit, monitor, report, and docs.
- Zero-result score invariants.
- Symmetric FoodRadar partial-source failure.
- OpenFDA escaping for quotes and operators.
- Audit deep-link fetch outside the first page.
- Authentication/ownership tests when those features are added.
- Visual PDF regression and accessibility tests.

### Manual Screenshot QA Still Needed

- Home at 1440, 1024, 768, 375, and 320 widths.
- Pharmacy with success, one-source failure, zero records, long product name, and typo suggestion.
- Food with both sources, one source failed, long code info, and no result.
- Cosmetic with many reactions, no product name, and zero reports.
- Audit with long JSON, payload hash, and mobile card behavior.
- Saved Monitors with 0, 1, 10, and 50 cards.
- Ask and Report overlays at 200% zoom and mobile landscape.
- Generated PDFs with long names, long reasons, no results, and non-ASCII product names.

Fresh in-app visual inspection was not possible in this audit because the local in-app browser surface was unavailable. Source/CSS review and the local Chromium E2E run were completed instead.

### Recommended QA Checklist

- [ ] All unit/component suites pass.
- [ ] Lint and both TypeScript no-emit checks pass.
- [ ] Production build passes in CI.
- [ ] Current Playwright desktop journey passes.
- [ ] Add a mobile Playwright project and pass the canonical journey.
- [ ] Back/Forward preserves route, query, selected module, and results correctly.
- [ ] Empty, typo, ambiguous, wrong-category, partial-source, and total-failure states are verified.
- [ ] No zero-record response displays a numeric score.
- [ ] Every visible module option works through API, persistence, and UI.
- [ ] Keyboard-only navigation reaches every control and closes dialogs.
- [ ] Screen-reader labels and live announcements are checked.
- [ ] 200% zoom and reduced-motion mode are checked.
- [ ] No PHI-like text appears in public diagnostics.
- [ ] PDF content is visually reviewed and text-extracted in tests.
- [ ] Deployment smoke uses the exact branch/commit being presented.

## 12. Resume and Portfolio Value

### Best Resume Bullets

- Built a React/TypeScript and FastAPI public-data verification platform integrating FDA/openFDA and USDA safety records across drug, food, supplement, and cosmetic workflows.
- Designed an audit/provenance layer that records source metadata, transform and score versions, request context, raw public-source snapshots, and stable SHA-256 payload hashes.
- Implemented deterministic, explainable review-priority scoring and source-specific safety boundaries for recall and adverse-event data without presenting outputs as medical advice or causation.
- Developed Saved Monitor workflows with run history, previous/latest comparisons, payload-change status, scheduler-lock foundations, and PostgreSQL/Alembic persistence.
- Added 276 backend tests, 146 frontend tests, strict TypeScript checks, linting, and GitHub Actions CI with Playwright smoke coverage.
- Built branded PDF safety reports with module-specific source, audit, and limitation context.

### What Not to Claim

- Production-ready healthcare AI.
- FDA-approved or clinically validated.
- Production ML, RAG, OCR, or real-time outbreak detection.
- Complete UPC/NDC/lot lookup.
- Production alerts, email delivery, or user accounts.
- Scalable multi-tenant monitoring.
- A working contextual assistant on the current branch.

### Roles Supported

- Entry-level full-stack software engineer
- Entry-level backend engineer
- Frontend engineer with data-product focus
- Platform or data-integrations engineer
- Responsible-AI product engineer
- AI engineer internship or entry role when paired with stronger ML projects

### 30-Second Pitch

> Dav AI is a full-stack public-data safety review platform I built with React, TypeScript, FastAPI, and PostgreSQL. It searches FDA and USDA records, normalizes results, applies transparent deterministic review signals, and preserves source provenance through audit events, raw snapshots, and payload hashes. I intentionally kept medical decisions and production ML out of scope, and backed the system with 400-plus automated tests.

### 2-Minute Pitch

> I built Dav AI because public safety data is available but fragmented and easy to misinterpret. The frontend guides a user to drug, food, supplement, or cosmetic workflows. The FastAPI backend calls public FDA/openFDA and USDA sources, normalizes records, calculates explainable review-priority signals, and returns explicit source limitations.
>
> The part I am most proud of is the trust layer. Every workflow can create an audit event with query, source, timestamp, transform version, score version, and upstream status. Where persistence is configured, the system stores raw public-source snapshots and stable SHA-256 payload hashes so a reviewer can trace what produced an output.
>
> I also built repeatable Saved Monitors, system/source diagnostics, PDF reports, CI, and extensive tests. The responsible engineering decision was to keep the current intelligence deterministic and keep ML experiments offline until there is a defensible evaluation and monitoring plan. The project is portfolio-grade, not a clinical or production healthcare system.

### Interview Questions and Strong Answers

| Question | Strong answer |
|---|---|
| Why deterministic scoring? | Public safety data is incomplete and high stakes. Rules are explainable, testable, versionable, and easier to audit. I would require labeled evaluation and rollback before exposing ML. |
| What is the hardest bug you found? | The current routing redesign left rich modules and contextual assistant wiring unreachable while isolated tests still passed. It showed why app-level and E2E contracts matter. |
| How is provenance implemented? | Search workflows create audit metadata, persist source-pull records, store public raw snapshots, hash canonical JSON with SHA-256, and expose metadata-only provenance by audit ID. |
| What would you change for production? | Identity, ownership, retention/deletion, rate limiting, explicit persistence failures, connection pooling, retries, observability, pagination, and a narrower product scope. |
| What does the score mean? | It prioritizes review of returned public records. It is not medical risk, product danger, causation, incidence, or personal urgency. |
| What did you intentionally not build? | Production ML, clinical advice, OCR, live surveillance, and automated alerts because the trust, ownership, and evaluation foundations are not ready. |

## 13. Roadmap

### Must Fix Before Demo

1. Choose the canonical module architecture: consolidated safety pages or standalone branded modules.
2. Restore audit, source, briefing, report, and assistant context to that canonical path.
3. Fix the Playwright smoke test and treat it as a release gate.
4. Wire Ask Dav AI or hide it when context is unavailable.
5. Remove unsupported homepage metrics and the broken RecallRadar anchor.
6. Fix nav naming and active states.
7. Fix CosmeticSignal monitor schema/manual-run parity or remove the option.
8. Make zero-record scores explicitly unscored.
9. Align score-version metadata.
10. Update About, FAQ, README current status, and demo script to match the branch.

### Should Fix Before Applying Widely

1. Add an app-level canonical user-journey test.
2. Make FoodRadar source failures symmetric.
3. Surface backend FoodRadar correction metadata.
4. Narrow UPC/NDC/lot claims or implement field-aware parsing.
5. Fetch audit deep links by ID.
6. Complete dialog and audit-row accessibility.
7. Remove unsupported report style, email, profile, and weekly-monitor controls.
8. Split the largest frontend components and PDF renderer by responsibility.
9. Add one current architecture/status document and archive old checkpoints.
10. Record a short demo video from a verified commit.

### Good Later Improvements

- Real router with typed route/query state.
- Database connection pool.
- Bounded source retries, backoff, and cache.
- Cursor pagination.
- Batched monitor summaries.
- Contract generation from OpenAPI.
- Visual regression tests.
- PDF rendered snapshots.
- Source documentation links.
- Explicit aggregate-workflow registry type.

### Do Not Do Now

- New safety modules.
- ProductScan/OCR.
- RAG or a vector database.
- A more complex scoring model.
- Mobile native app.
- A full visual redesign.
- Live CDC/HHS integration.
- More LLM providers.

### Production-Only Features

- Authentication, authorization, ownership, and tenant isolation.
- Privacy policy, retention, deletion, export, and PHI handling.
- Rate limiting, abuse protection, and quotas.
- Background job queue, idempotency, alert delivery, and retry policy.
- Secrets management, dependency scanning, and hardened CORS/API docs.
- Metrics, traces, structured log aggregation, SLOs, and incident response.
- Database backups, restore testing, migration rollback, and connection pooling.
- Independent safety review and user research.

### Risky Distractions

- Trying to prove "AI" by adding an LLM to every page.
- Rebranding every deterministic rule as intelligence.
- Building more dashboards before validating one user workflow.
- Using polished mock metrics instead of auditable data.
- Optimizing for feature count rather than a passing end-to-end demo.

## 14. Final Verdict

**Is this project good?** Yes. It is technically ambitious, unusually thoughtful about provenance, and clearly above the typical student CRUD portfolio.

**Is it useful?** Yes as a public-record review and verification workspace. Its usefulness drops when it is framed as a consumer safety answer engine.

**Is it too ambitious?** In its current scope, yes. The breadth has created duplicate interfaces, stale docs, and broken integration contracts.

**Is it impressive for a student?** Yes. The backend trust layer, testing breadth, migrations, and responsible boundaries are genuinely impressive.

**Is it enough for Big Tech?** It is enough to earn serious discussion and can help obtain interviews, but it is not a substitute for computer-science fundamentals, coding interviews, collaboration evidence, and a concise explanation of tradeoffs.

**Is it enough for entry-level roles?** Yes, especially full-stack and backend roles, once the current demo path is repaired.

**Single biggest thing to improve next:** **Consolidate the product into one truthful, passing, end-to-end workflow where navigation, search, source evidence, audit, assistant/report actions, tests, and documentation all agree.**

**What should you stop worrying about?** Stop worrying that the project needs more AI, more sources, or more features to be impressive. It already has enough scope. Reliability, coherence, and an honest demo will add more value than another module.

## Final Checklist

- [x] Whole-repository architecture, frontend, backend, tests, styles, docs, configuration, migrations, and history reviewed.
- [x] Current worktree changes inspected without modifying them.
- [x] Backend suite run: 276 passed.
- [x] Frontend suite run: 146 passed.
- [x] Frontend lint and TypeScript no-emit checks passed.
- [x] Playwright smoke test run and current route mismatch documented.
- [x] More than 150 user issues and edge cases documented.
- [x] Product, UX, trust, safety, interview, resume, and roadmap reviews included.
- [x] No application code changed.
- [x] No commit created.
- [ ] Fresh manual screenshot review remains outstanding because the in-app visual browser was unavailable.
- [ ] Production build was not run during this audit to avoid changing generated `dist` artifacts; TypeScript no-emit and the CI build configuration were inspected instead.
- [ ] No live FDA/USDA, deployed-environment, or real-database smoke test was performed.

## Review Evidence

### Files Inspected Summary

- Repository root, Git status/history, `.gitignore`, Docker Compose, Alembic configuration, README, and GitHub Actions workflow.
- Frontend application shell, navigation, old and new module components, API clients, utilities, tests, CSS, Vite/TypeScript/ESLint/Playwright configuration, and E2E spec.
- Backend routes, schemas, search workflows, source clients, scoring, assistant, reports, repositories, jobs, source registry, migrations, SQL schema, configuration, and all backend test areas.
- Current architecture, status, demo, deployment, persistence, provenance, UI/UX, case-study, roadmap, and milestone documentation.

### Commands Run

- `git status --short`
- `git log --oneline` variants
- `git diff --stat`, `git diff --check`, and targeted diff inspection
- `find`, `rg`, `sed`, `wc`, `file`, and targeted configuration/source reads
- `npm run lint`
- `npm test -- --run`
- `npx tsc -p tsconfig.app.json --noEmit`
- `npx tsc -p tsconfig.node.json --noEmit`
- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider`
- `npm run test:e2e -- --reporter=line`
- Local Vite server startup for browser review attempt

### Review Limitations

- Fresh in-app screenshot inspection was unavailable.
- The Playwright test exercised local Chromium but stopped at the first failing assertion.
- No production build was run to preserve the requested report-only workspace outcome.
- No network-dependent live source or deployed-site verification was performed.
- No real database migration or persistence test was run; automated tests deliberately isolate `DATABASE_URL`.
- Uncommitted user changes were reviewed as part of the current worktree and were not altered.
