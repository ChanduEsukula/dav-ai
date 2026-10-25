# Phase 5 — final verification and student release candidate

Verified October 24, 2026, America/Chicago. **GO for a scoped local student
portfolio demonstration.** This is not a production, clinical or publication
approval. Optional semantic retrieval and unavailable browser engines must not be
presented as exercised on this host.

The core application was exercised against the real frozen release and local
Ollama. Its original aqua/mint landing, teal typography, SVG workflow graphics,
About/FAQ banners and both research experiences were preserved. Only one reproduced
application boundary issue was fixed; no model/retrieval architecture was expanded.

## Repository state and preserved work

Branch: `feat/private-staging-authorization`. HEAD remains `eda4886`
(`feat(ai): integrate hybrid RAG and grounded answers`). No subsequent commits exist.
Phase 3B, the UI refinement, and Phase 5 changes are **uncommitted**; nothing is staged.

The initial tracked delta from `eda4886` covered synthesis/tests, the historical
Phase 3 pointer, UI code and two intentionally modified screenshots. Untracked
Phase 3B runner/evaluations and restored portfolio UI also existed. Historical
untracked ingestion, research, migration and documentation files were already
present. At Phase 5 start, 507 modified/untracked files were fingerprinted.

All of those files remain present. The two historical Research Pro screenshots
and all original Phase 3B JSON results/review packets remain byte-identical to their
Phase 5 start fingerprints. Existing Phase 3B production synthesis/model code was
not changed. No release/database/publication metadata, authorization or deployment
configuration was modified. There was no cleanup, stash, staging, commit, push,
PR, merge or deployment.

The [actual final Git status](evaluation/phase5-v1/git-status.txt) records the full
working tree, including unrelated historical files. The
[Phase 5 change inventory](evaluation/phase5-v1/changed-files.json) separates this
phase's modifications from the pre-existing delta. A clean clone does not yet
contain this uncommitted release candidate; manual review/commit remains necessary.

## Feature verification matrix

| Capability | Verification | Result / limit |
|---|---|---|
| Home, Overview, About, FAQ | Current Chromium rendering plus 1440/768/390 px mocked-suite navigation | PASS; original design retained |
| Mobile navigation / FAQ keyboard use | Enter/Space disclosures, Escape/focus restoration, active links and main landmarks | PASS |
| Motion / reduced motion | Normal landing settles; no perpetual hero motion; reduced animations disabled | PASS in Chromium; unsupported CSS enhancements have native/static fallbacks |
| Explorer search and formulation selection | Real frozen API search; select actual returned product and review identity | PASS; no mocked API in real-release journey |
| Recall / FAERS / provenance | Real Explorer and real Xanax research; source availability/limitations inspected | PASS; Xanax has unavailable labels, incomplete recalls, available FAERS |
| Source links | Existing URL-policy tests, real source URL/provenance rendering, exact internal citation targets | PASS for binding/allowlist/navigation; remote FDA uptime/content was not fetched |
| PDF report | Real outbound-blocked API: generate and download PDF; fixture tests cover dialog cancellation/focus | PASS |
| Everyday identity confirmation | Real Zepbound `0002-0152` search, selection and explicit confirmation | PASS; no auto-confirmation |
| Everyday grounded answer | Real default Llama 3.2, deterministic tool planning, exact source reconstruction | PASS; two cited statements; human semantic support PENDING |
| Research Pro cohort and A → B | Real directory selection, fresh pairing, Lipitor `58151-155` re-resolution/confirmation | PASS after minimal session-boundary fix |
| Old-session isolation | Actual old session result request after A closes | PASS: HTTP **410**; no reused A credential |
| Native local tool planning | Real Llama 3.2 proposes Lipitor label retrieval; no backend completion | PASS: routing `model`, one planned label tool |
| Research Pro grounded answer | Real Lipitor digoxin question and source citation | PASS; one cited statement; human semantic support PENDING |
| Deterministic fallback | Real fresh Xanax `0009-0029` with synthesis requested | PASS: `insufficient_evidence / no_admitted_label`, source cards retained |
| Citation focus / layout | Real generated answers in both modes at 1440 and 390 px | PASS: targets focus/open below sticky navigation; no horizontal overflow |
| RAG unavailable state | Real API results with corpus/index absent | PASS: `not_configured / rag_artifacts_unavailable`; admitted SQL fallback retained |
| Candidate-only exclusion | Backend agent/RAG tests and unchanged Phase 3B adversarial case | PASS mechanically; candidates cannot authorize answers |
| Live BGE/FAISS passages | Existing semantic model, corpus and index absent | NOT RUN; no substitute mock index or model download |
| Cancellation / expiry / foreign identity | Backend and mocked frontend/browser regression tests | PASS; not all were repeated as live browser timing scenarios |

The ordinary Playwright suite uses intercepted API fixtures. The separate Explorer
journey uses the actual read-only release API with outbound HTTP blocked. The real
research harness uses the actual secured socket-bound API, killable repository
workers, frozen release and installed Ollama. Its route handler blocks external
browser requests; it does not fulfill synthetic API responses.

Real research receipts: [summary](evaluation/phase5-v1/real-research-summary.json).
Detailed public briefings and temporary captures remain under
`/private/tmp/dav-ai-phase5/real-research-v4/`. Pairing/session credentials are never
serialized into those results, URLs or browser storage. The harness confirmed
registry/task cleanup and stopped its own research server. Existing preview
frontend/offline Explorer services were left running as found.

## Minimal reproduced fix

After A was confirmed/researched, Research Pro's cohort directory search reused
A's locked session. The real backend correctly returned `selected_product_locked`;
the permissive mocked journey had allowed it. The frontend now closes that session,
clears the old result and requires fresh pairing **before** issuing another
resolution request. The search text and cohort remain. The pairing panel now
shows the explanatory message and pairing errors.

The backend product lock was not weakened. Existing cohort tests were corrected
to populate multiple products before confirmation or re-pair before a new search.
A new regression verifies that no resolver call is made with the locked session,
the old result disappears, and the next search uses the new session. The real
A → B journey confirms the old credential receives HTTP 410.

The real-browser harness was also brought up to date: fresh output directories,
no historical screenshot writes, optional reuse of an existing frontend, actual
Everyday controls, Research Pro model planning, three live research stages,
source-hash/citation checks, product-switch checks and explicit cleanup. Source-read
assertions now use a bounded 25-second wait consistent with existing API limits;
production deadlines were not changed.

## AI evaluation audit and human review

The original development/holdout questions and annotations were not edited. The
recorded Phase 3B result remains **7/7 accepted answerable cases**, versus the
historical **2/7** copying-protocol result. All fifteen negative/adversarial cases
have no answer text; thirteen reject before inference and two simulate invalid
model output. These are distinct from clinical support judgments.

Phase 5 re-resolved each stored answer citation against the **current frozen SQL
source**, checking record, label set/version, official URL, release/snapshot,
original offsets, SHA-256 and displayed exact source text. Results:

- Accepted recorded answers: **7/7**.
- Frozen annotated support span covered: **7/7** (mechanical selection proxy).
- Citation resolution, exact source text and product consistency: **12/12 each**.
- Negative/adversarial answers with no text: **15/15**.
- Independently reviewed claims: **0**; support/relevance judgments remain **PENDING**.

[Read-only revalidation receipt](evaluation/phase5-v1/phase3b-revalidation.json)
contains every case status/reason and preserved original artifact hashes. This
was a source audit, **not** a new 22-case model benchmark. Separately, the live UI
journey generated two answers with three exact citations and exercised one fallback;
those small integration observations do not establish general model accuracy.

The original g03/h01 independent reviews remain PENDING, as do the seven Phase 3B
packet reviews. The new [human-review checklist](INDEPENDENT_REVIEW_CHECKLIST.md)
covers every claim, citation identity, question relevance, omitted medical
qualifiers and FAERS/recall scope. It requests a real independent reviewer and
separately versioned judgments. No packet or reviewer field was filled automatically.

## Cross-browser and accessibility

| Engine | Availability / execution |
|---|---|
| Chromium 148.0.7778.96 | Executed: full mocked suite, real Explorer/PDF, real Ask/Research Pro, desktop/mobile, reduced motion and source focus |
| Firefox | NOT RUN: Playwright executable absent; actual launch availability check recorded |
| WebKit / Safari-compatible Playwright | NOT RUN: executable absent; actual launch availability check recorded |

[Browser availability receipt](evaluation/phase5-v1/browser-availability.json).
No browser engines were downloaded. This is not a claim that Firefox, native
Safari, WebKit rendering or assistive-technology behavior has been certified.
No reproducible Chromium visual defect required a redesign. The setup keeps CSS
view transitions, scroll timelines and intrinsic disclosure transitions progressive.

## Actual quality gates

| Check | Current result | Evidence |
|---|---|---|
| Full backend | **1,087 passed, 29 skipped**, one existing deprecation warning | [log](evaluation/phase5-v1/backend-tests.txt) |
| Agent/synthesis subset | **241 passed** | [log](evaluation/phase5-v1/agent-tests.txt) |
| Focused RAG | **45 passed, 2 skipped** | [log](evaluation/phase5-v1/rag-tests.txt) |
| Required release gate | **7 passed, 370 deselected**, one existing warning | [log](evaluation/phase5-v1/release-tests.txt) |
| Frontend | **86 passed across 11 files** | [log](evaluation/phase5-v1/frontend-tests.txt) |
| Mocked Playwright | **11 passed** | [log](evaluation/phase5-v1/playwright-mocked.txt) |
| Real Explorer/PDF | **1 passed** | [log](evaluation/phase5-v1/playwright-real-explorer.txt) |
| Real research harness | **PASS: three real stages** | [receipt](evaluation/phase5-v1/real-research-summary.json) |
| ESLint / TypeScript / Vite | **PASS** | [lint](evaluation/phase5-v1/lint.txt), [build](evaluation/phase5-v1/build.txt) |
| Python dependency consistency | `pip check`: **No broken requirements found** | Host verification |
| Git whitespace / local doc links | **PASS** | Final local checks |

Agent and release counts overlap the backend suite and must not be added to it.
The full backend skips are **27 PostgreSQL-dependent tests** without an explicitly
configured test server and **2 FAISS tests**. The focused RAG skips are those same
two tests, not two additional failures. Required-release deselection is the
intentional marker filter, not a skipped critical release check.

### Unavailable FAISS/BGE verification

The earlier temporary FAISS environment and semantic artifacts are absent.
A bounded isolated `/tmp` wheel-provisioning attempt could not resolve/download
FAISS; direct PyPI metadata retrieval also timed out. No application dependency
was installed or changed. A compatible macOS/Python wheel exists in
[PyPI's published files](https://pypi.org/project/faiss-cpu/1.12.0/), but that does
not establish availability or successful execution on this host. Accordingly the
compatible-FAISS test gate is **not completed**, and the 45-test run is not presented
as a 47-test real-FAISS pass. No model, mock semantic artifact or cloud service was
introduced to make this gate appear green.

### Failures encountered and resolved

- The initial real harness looked for an obsolete Everyday model selector. It now
  reads the real session's installed models and exercises planning in Research Pro.
- Real cohort search reproduced the locked-session bug described above; fixed
  without weakening authorization and verified by live HTTP 410 plus regression tests.
- One real-harness assertion used a five-second fixture-style wait while source
  resolution was still running. Its explicit wait now matches the bounded API read.
- The new unit initially could not see its message because the unpaired Pro panel
  hid errors. That panel now exposes the message; **86/86** tests pass.
- A verification command invoked npm/Node from the repository root rather than
  `frontend`; corrected working-directory commands passed.
- FAISS provisioning and two browser-engine availability checks remain unavailable,
  as explicitly recorded above. There are no remaining failures in executed final suites.

## Demo and portfolio readiness

The [updated demo guide](LOCAL_DEMO_GUIDE.md) describes all three services, locked
Python/frontend setup, required external release, private pairing, deterministic
planning, separate generation opt-in, approved preinstalled models, model/index
unavailability and optional local-only FAISS/BGE preparation. It uses environment
paths rather than one developer's temporary artifact locations. The current
Python environment passed dependency consistency checks. A fresh installation and
large optional model provisioning were not performed; optional RAG requires the
separately provisioned compatible environment described in that guide.

The README now includes the problem statement, actual page map, technology stack,
Hybrid RAG/agent/statement-ID architecture diagram, measured acceptance versus
human support, current results, limitations and demonstration commands. Current
screenshots are in a **new** [Phase 5 folder](screenshots/phase5): landing desktop /
mobile, Overview, and two real-API research result captures. Historical images
were not overwritten. The old RAG README is labeled as a historical report rather
than silently rewriting its original measurements.

## Remaining tasks and verdict

- **P0: none found** for the tested, scoped local demonstration.
- **P1 before claiming live semantic retrieval:** restore the already provisioned
  BGE model/corpus/index and a compatible FAISS environment; rerun the two skipped
  vector-engine checks and one real semantic passage journey. Current demos must
  label this feature optional/unconfigured and use the documented SQL route.
- **P1 before claiming reviewed factual support:** obtain independent judgments
  using the checklist. PENDING status is acceptable for the disclosed student
  prototype; a clinical accuracy claim is not.
- **P2:** smoke-test Firefox/WebKit when available; review the uncommitted delta
  and historical untracked files manually; retain demo artifacts outside temporary
  storage; select/commit only intended files after review.

**Final decision: GO for the bounded local student portfolio release candidate,
with the exclusions above.** Do not call every optional gate complete, describe
7/7 acceptance as clinical validation, distribute the frozen dataset, or deploy.
No additional architecture, dashboards, models or engineering phase is recommended.

## Exact files changed in Phase 5

Modified:

- `README.md`
- `backend/app/agent/rag/README.md`
- `docs/README.md`
- `docs/ai/LOCAL_DEMO_GUIDE.md`
- `frontend/e2e/dual-mode.spec.ts`
- `frontend/e2e/verify-local-research.mjs`
- `frontend/src/research/ResearchProWorkspace.tsx`
- `frontend/src/research/Workspace.test.tsx`
- `frontend/src/research/Workspace.tsx`
- `scripts/verify_ask_research.py`

Created:

- `docs/ai/INDEPENDENT_REVIEW_CHECKLIST.md`
- `docs/ai/PHASE5_RELEASE_CANDIDATE.md`
- `docs/ai/evaluation/phase5-v1/agent-tests.txt`
- `docs/ai/evaluation/phase5-v1/backend-tests.txt`
- `docs/ai/evaluation/phase5-v1/browser-availability.json`
- `docs/ai/evaluation/phase5-v1/build.txt`
- `docs/ai/evaluation/phase5-v1/changed-files.json`
- `docs/ai/evaluation/phase5-v1/frontend-tests.txt`
- `docs/ai/evaluation/phase5-v1/git-status.txt`
- `docs/ai/evaluation/phase5-v1/lint.txt`
- `docs/ai/evaluation/phase5-v1/phase3b-revalidation.json`
- `docs/ai/evaluation/phase5-v1/playwright-mocked.txt`
- `docs/ai/evaluation/phase5-v1/playwright-real-explorer.txt`
- `docs/ai/evaluation/phase5-v1/rag-tests.txt`
- `docs/ai/evaluation/phase5-v1/real-research-summary.json`
- `docs/ai/evaluation/phase5-v1/release-tests.txt`
- `docs/ai/evaluation/phase5-v1/verification.json`
- `docs/ai/screenshots/phase5/everyday-real-desktop.png`
- `docs/ai/screenshots/phase5/landing-desktop.png`
- `docs/ai/screenshots/phase5/landing-mobile.png`
- `docs/ai/screenshots/phase5/overview-desktop.png`
- `docs/ai/screenshots/phase5/research-pro-real-desktop.png`
