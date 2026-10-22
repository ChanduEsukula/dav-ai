# Agent v2 — multi-source pharmaceutical research

## Architecture plan from repository audit

Retain the v1 session-owned references, explicit numbered human confirmation, locked exact product identity, strict argument validation and killable read-only workers. Reuse `FrozenPharmaReleaseRepository.safety()` for its admitted product-label selections and unchanged ingredient-level FAERS aggregates; do not reimplement selection, deduplication or counting. Supplement the FAERS projection with an agent-local read-only source-row join because the existing aggregate projection omits provenance. Use `release_metadata()` for exact release/snapshot identity.

Add strict output models and deterministic label/FAERS cards. Keep label linkage product-scoped and FAERS observations ingredient-scoped. Build a typed briefing with one explicit outcome for each requested category, without model-written medical summaries. Add a finite request workflow with session/request/per-tool budgets and no indefinite repeated calls. Separate model-directed routing from explicit-category deterministic execution/fallback and report their measured results separately. Preserve v1 single-source compatibility and extend the existing numbered CLI; no React/HTTP endpoint, new framework, paid API or deployment is planned.

This plan was recorded before the new source/workflow implementation. It follows the actual repository contracts rather than treating all proposals in the feasibility study as implemented or safe. In particular, no raw-ID model arguments, regex-repaired medical narrative, automatic selection, external lookup or free-form factual summary was adopted.

## Result and baseline

2026-10-22 (America/Chicago). Baseline HEAD remains `264f65b` on `feat/private-staging-authorization`. Baseline verification was rerun: **97 agent tests passed** and **852 backend tests passed, 27 skipped, 7 deselected**. Historical v1 reports remain historical; they were not rewritten to imply current results.

**Agent v2 is implemented and ready for engineering review as a local backend milestone.** It produces typed, deterministic multi-source briefings through confirmed product references, with explicit partial/unavailable source outcomes. No React interface, HTTP agent endpoint, authentication provider, deployment or publication authorization was added. No paid service, new dependency, framework or model download was introduced. No Git publication operation occurred.

## Architecture and state transitions

`UNSELECTED → human candidate confirmation → CONFIRMED → PLANNING → EXECUTING → COMPLETE | PARTIAL | STOPPED`

These are bounded request states within a caller-owned session. The selected product remains immutable. A later request can ask for a previously unattempted source while session/request/iteration budgets permit; it cannot reset counters or silently select another product. Failed owned requests update the request state to STOPPED. A foreign owner is rejected before locking or mutating the session. Expiry still denies publication of late results.

The v1 `ResearchAgent.run()` interface remains compatible. The new `ResearchAgent.research(question, session=…, owner_id=…, categories=…, routing=…)` delegates to `ResearchWorkflow`:

1. Authorize the trusted caller/session and validate the bounded question and categories. An unconfirmed product returns a confirmation requirement; unspecified scope returns category clarification instead of a generic chatbot answer.
2. Acquire the session lock under the overall request deadline. Validate remaining session and request budgets before any model or source call.
3. Obtain one bounded model plan, or execute the explicitly selected deterministic mode. The model sees only the user question, selected opaque reference and permitted category tool schemas. No repository product/ingredient IDs or retrieved label text are sent to it.
4. Validate **every call in the batch before dispatching any call**: allowed name, one exact owned selected reference, strict JSON/Pydantic arguments, no extras, no duplicates and no more than the request limit. A valid first call cannot conceal an invalid later call.
5. Reserve source-attempt budget. Execute each requested source once in canonical order, with a fresh product binding check before each source and a killable read-only worker. Validate exact product identity, typed outputs, source scope and provenance. No model writes the source results or the briefing.
6. Preserve verified sources when another source times out, lacks data/provenance, exceeds its byte budget or fails its contract. Ownership, expiry, changed product binding or mixed releases discard the briefing rather than combining incompatible facts.
7. Validate the final typed briefing and byte budget; publish explicit COMPLETE/PARTIAL/STOPPED results. No follow-up medical narrative generation occurs.

### Routing modes and fallback

- **`model`** requires the model's proposed tool set to cover the entire requested set. A missing category stops with `incomplete_model_plan` and no source dispatch.
- **`auto`** validates the entire plan just as strictly. If the model proposes a valid, nonempty subset of the explicitly requested set, Python transparently completes the missing categories. The output says `routing.mode="deterministic_completion"` and records `model_planned_tools` separately from `backend_completed_tools`. Invalid references, unknown tools, duplicate calls, malformed/extra arguments and answers without calls **never** receive this fallback.
- **`deterministic`** executes the caller's explicit category plan without contacting a model. Literal category recognition can also derive the scope from question words; this is a small documented keyword matcher, not semantic medical planning. Callers should supply `categories`/`--categories` for precise intent, especially negated or complex questions.

This fallback is necessary based on the observed Llama multi-source omission described below. It is not presented as autonomous model planning. Even in model-directed mode, backend execution order, evidence verification and briefing formatting remain deterministic.

### Budgets and failure boundaries

Existing defaults remain: four session iterations, four session tool attempts, 45-second model requests, 20-second repository operations, 70-second overall runs (including lock wait), 600-second session lifetime, 65,536-byte source/result limits, 12,288-byte prompt limit, 4,096-token context and 512 generation tokens. V2 adds:

- At most **three evidence tools per request**.
- At most **one actual attempt per evidence category per selected session** by default, including failed source attempts.
- A separately bounded **262,144-byte assembled briefing**; each source remains independently bounded.

Resolution through a model consumes the existing session budget too; one resolver plus three evidence tools fits the default four-tool budget. Invalid model proposals consume budget. Reserved failed/repeated attempts do not reset counters; a fresh product/session requires renewed human confirmation. There is no indefinitely repeated tool loop or unbounded model repair loop.

Source timeouts can preserve already validated sources. Overall deadline exhaustion marks remaining categories failed and can return a partial briefing only while the owned session is still valid. External cancellation propagates through the existing worker kill/reap path. No worker can later mutate parent session state. Oversized source/briefing data fails explicitly; no warning text is silently truncated in the machine-readable cards. The redundant labels `latest_records` compatibility alias is omitted by the new adapter because it repeats the canonical `records`, not because any admitted label was removed.

## Tool specifications and evidence contracts

All three evidence tools accept exactly `{"product_ref": "p_…"}` using the existing strict reference argument model. Their schema includes an enum of the one human-confirmed reference. Internal worker adapters resolve that reference to the private exact database ID; raw IDs are not model arguments. Product resolution remains the only pre-confirmation model tool.

| Tool | Existing logic reused | Validation/output |
|---|---|---|
| `get_drug_label_evidence` | `FrozenPharmaReleaseRepository.safety()['labels']`, including `_consumer_labels`, sealed selection decisions and `_section_text` | `LabelCard`: exact product-linked scope, admitted selection status, label set/version/effective date, matching method/value, source record/URL, snapshot date, full section states/text, missing sections, coverage/limitations. No ingredient-label substitution. |
| `search_historical_recalls` | v1 recall adapter and v1 deterministic card validator | Typed `RecallCard` adds exact release metadata while preserving classification, reason, firm, applicability, matched NDC/method, lot scope, source record/URL/date, counts and truncation. Existing package/product applicability checks remain. |
| `get_faers_reporting_evidence` | `safety()['adverse_events']`, existing `_adverse_events` aggregation output | `FaersCard`: `INGREDIENT_LEVEL_REPORTING_EVIDENCE`, one row per exact selected ingredient, unchanged analytics/reactions/months/summary and explicit source provenance. Product reference is selection context, not an observation scope. |

### Labels

The repository already filters for consumer-eligible, exact-product, product-scoped, ingredient/formulation-verified, conflict-free, valid-dated extracted labels, including explicitly marked EARLIER_STORED evidence. The agent does not reselect withheld labels or implement alternate pharmaceutical matching logic. It preserves independent label sets and their versions. READY text must agree with the section-state text; a missing/unavailable section remains missing, never “no warnings.” Earlier stored evidence, missing sections or non-READY coverage makes the source incomplete. Missing exact linkage yields an unavailable label section with its actual repository reason and limitations.

The CLI displays labeled source excerpts of up to 800 characters per label field, with an explicit full-text/`--json` notice. The underlying typed card retains the complete admitted source text within byte budgets. There is no model ranking of “major” warnings, severity, contraindications or interactions.

### FAERS and provenance

The existing repository projection contains validated aggregates but omits the aggregate source row. `source_tools.faers_sources()` adds a single **read-only provenance join** from the selected product's ingredient memberships through `ae_summary.source_id` to `sources`. It performs no counting, aggregation, deduplication, normalization or medical interpretation. No core repository or pharmaceutical service was changed.

The card checks the exact ingredient-ID set and names against the confirmed product projection, including newly preserved ingredient IDs; ingredient coverage must identify the same ingredient. Present analytics require the actual `openfda_drug_event` source ID, allowlisted official HTTPS URL and export date matching the ingredient coverage snapshot. The original count unit (`deduplicated ingredient-report associations`), date basis, source reporting period, reaction co-report activity and monthly rows are preserved. Missing bins are not filled with zero. Product totals remain `null`, never a sum across ingredients.

Seriousness/outcome fields already supported by the repository are typed and retained. No age/sex breakdown, denominator, risk probability, comparative safety score or signal classification was invented. Missing analytics remain `null` and make the source unavailable/incomplete as appropriate. FAERS observations remain ingredient-level and are never evidence that a particular NDC caused an event. Non-causality, non-incidence, non-comparative-safety, non-individual-risk and no-summing limitations are mandatory.

### Typed briefing schema

`research_contracts.py` uses strict Pydantic output contracts with extra fields forbidden, nonnegative count types and discriminated evidence-card types. Public identity includes the opaque reference, exact NDCs/formulation, ingredients, strength/form, routes and source identity. All present source cards retain exact release/contract/policy/schema/build/snapshot identity; mixed releases are rejected.

The machine-readable result contains:

```text
ResearchBriefing
  schema_version: "agent-research-v2"
  status: completed | partial | stopped
  workflow_state: COMPLETE | PARTIAL | STOPPED
  medication: MedicationIdentity
  requested_categories: [labels | recalls | faers]
  routing:
    mode: model | deterministic | deterministic_completion
    model_planned_tools: [...]
    backend_completed_tools: [...]
    discarded_model_content: boolean
  sections: exactly one entry per category
    category
    status: not_requested | available | incomplete | unavailable | failed
    reason: fixed failure code or null
    evidence: LabelCard | RecallCard | FaersCard | null
  limitations: deterministic deduplicated source/general limitations
```

“Completed” means all requested sections were available under their returned contracts; it does not assert comprehensive regulatory coverage or clinical safety. “Partial” retains honest missing fields, incomplete coverage or unavailable/failed sources. A source can be available for the supported frozen reporting window while still carrying the limitations of spontaneous reporting. No free-form model medical advice or FDA endorsement is emitted. Early authorization/planning/timeout failures return a small stopped result with no evidence; absent scope/selection returns clarification requirements.

## Exact files modified

Only Agent v2 implementation, tests and engineering evidence changed:

| Path | Purpose |
|---|---|
| `backend/app/agent/contracts.py` | New request/per-tool/briefing limits; state-aware schemas for the three evidence tools. |
| `backend/app/agent/orchestrator.py` | Preserve v1 interface; expose `research()` and reuse strict proposal validation for permitted v2 names. |
| `backend/app/agent/state.py` | Per-category attempt counters and explicit request state; selected-product/owner rules remain. |
| `backend/app/agent/tools.py` | Preserve exact ingredient IDs in the product binding for FAERS scope checks. |
| `backend/app/agent/worker.py` | Three fixed v2 source dispatch operations through existing bounded subprocess handling. |
| `backend/app/agent/cli.py` | Numbered confirmation retained; readable source/status/excerpt output, explicit scope/routing flags, clean JSON debugging output and truncation notice for limited candidate searches. |
| `backend/app/agent/source_tools.py` (new) | Read-only repository adapters, release metadata and missing FAERS source-row linkage. |
| `backend/app/agent/research_contracts.py` (new) | Strict identity, release, coverage, source, section, aggregate, card, routing and briefing models. |
| `backend/app/agent/briefing.py` (new) | Domain/scope/provenance checks and deterministic partial/completed briefing assembly. |
| `backend/app/agent/workflow.py` (new) | Finite scoped planning/validation/execution workflow and transparent deterministic modes. |
| `backend/app/agent/research_evaluation.py` (new) | Opt-in real-data corpus verification and paired installed-model evaluation. |
| `backend/tests/agent/test_research.py` (new) | Synthetic source fixtures, provenance/contracts, scope, batching, limits, failures, CLI and fallback regressions. |
| `docs/ai/agent-v2-evaluation.json` (new) | Measured real-data/model outputs, native plans, paired prompt hashes, settings, model digests, verification comparisons and raw bounded responses. |
| This report (new) | Architecture plan, results, exact commands and review limitations. |

No dependency files, core data repository/services, database, manifest, existing v1 report/evaluation, frontend, Vercel/Render configuration, authorization/security modules or unrelated research/ingestion files changed.

## Automated verification

Executed with the existing root `.venv`, Python 3.13.7. Ordinary tests use synthetic repository/source fixtures and fake model/HTTP responses; they do not read the real frozen release or require Ollama. Existing subprocess tests retain their no-fixture behavior. Real-data checks are opt-in through the evaluator and the existing mandatory release gate.

| Required check | Observed result |
|---|---|
| `PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/agent -q` | **144 passed**, zero failed/skipped. All 97 baseline agent tests remain passing; 47 v2 cases were added. |
| `PYTHONPATH=backend .venv/bin/python -m pytest backend/tests -m 'not release_artifact' -q` | **899 passed, 27 skipped, 7 deselected**, zero failures; one existing warning. |
| `PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/security -q` | **246 passed**, zero failures/skips (0.43 s). |
| `PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/pharma_release -m release_artifact --require-pharma-artifact -q` | **7 passed, 370 deselected**, zero failures/skips; one existing warning (19.31 s, concurrent with read-only evaluation). Required artifact verification passed. |
| `git diff --check`, new-file whitespace checks, Python compile checks | Passed. |

New tests cover source retrieval, typed multi-source aggregation, exact product identity, product-vs-ingredient scope, cross-session/unknown/raw-ID references, unknown tools, malformed/duplicate JSON, extra arguments, duplicate/oversized batches, complete validation before dispatch, missing source ID/URL/date, wrong ingredient coverage, unsupported scope/count units/product totals, missing labels/analytics, partial coverage, label section-state mismatch, source/model/overall timeouts, lock waits, expiry, repeated attempts, session/request budgets, changed identity, mixed releases, oversized source/briefing results, fabricated model content, no tools/no evidence, deterministic completion versus native planning, numbered CLI/JSON output and deployed-mode denial.

The 27 skips remain optional PostgreSQL ingestion fixtures without a disposable `PHARMA_TEST_DATABASE_URL`; no PostgreSQL server was started. Seven release checks were intentionally deselected from artifact-independent regression, then passed separately as the required gate. The preexisting Starlette TestClient/httpx deprecation warning remains. Frontend tests were not rerun because no frontend or shared application API behavior changed.

An intermediate **real-data** check found an introduced strict-output mismatch: ingredient coverage includes an `ingredient_id` omitted from the first Coverage model. The early Xanax and Zepbound checks returned explicit failed FAERS sections (`invalid_source_contract`), without fabricated evidence. The model comparison was interrupted during fixture preparation, before model trials, to fix this. The field is now retained, its ingredient binding is validated, fixtures cover it, and all subsequent corpus checks passed. No final automated check failed.

## Real-data integration evidence

The evaluator derives expected records from fresh guarded reads using the existing repository/service contracts; it does not hardcode supposed label warnings or expected counts. Its worker executions are separately compared to those projections for record IDs, source text/version/date, exact counts/reactions/months, coverage and FAERS summary. This establishes fidelity to the sealed release, not independent clinical correctness or live FDA status.

Frozen release:

- Release ID: `dav-ai-pharma-v1-phase4b-communications-20261006`
- Contract/policy: `dav-ai-pharma-release-v1` / `1.0.0`
- Build: `phase4b-communications-0.1.0`, `2026-10-06T22:12:24.015723+00:00`
- Artifact bytes: **4,825,108,480**
- SHA256: `87779eda6b06c75f10603762b18f8c66a5cb7b12ed37d47ab1bf9b4825639c71`
- Identity observation: **2026-09-26**; label/enforcement snapshot: **2026-09-25**; FAERS export: **2026-09-23**, reporting window **2020-01-01 through 2026-06-30**.

All **six deterministic corpus checks passed**:

| Case | Verified local behavior |
|---|---|
| Historical recall: Xanax product NDC `0009-0029` | D-0161-2016; Class II; Subpotent Drug; AFFECTED_PACKAGE; EXACT_PACKAGE_NDC; UNKNOWN lot scope. Source remains incomplete because recall coverage is PARTIAL. |
| Exact label: Zepbound product NDC `0002-0152` | One admitted product-linked label, version **40**, effective **2026-08-28**, SELECTED_STORED. Full text matched the repository. The separate `warnings` field is unavailable while warnings/precautions and other sections exist, so the label result is incomplete rather than “no warnings.” |
| FAERS: confirmed Xanax selection, ingredient alprazolam | **18 deduplicated ingredient-report associations**, **6 marked serious**, with original ranked reaction co-report activity and monthly rows. These are ingredient-level associations, not NDC-specific observations or patient risk. |
| Ambiguous `Xanax 0.25 mg` search | Two candidates; no selected product. The harness does not ask a model to confirm one. |
| Missing exact Xanax label | Zero consumer-admitted label records with the actual STRICT_PRODUCT_NDC_REJECTION coverage reason. No alternate alprazolam label was substituted. |
| Multi-source Xanax question | Label unavailable, recall incomplete, FAERS reporting available for its supported window; overall **PARTIAL** with all three outcomes explicitly disclosed. |

The real numbered CLI was also executed with an explicitly scripted `1` selection for the sole exact `0009-0029` candidate, deterministic categories and `--json`. Its stdout parsed directly as `ResearchBriefing`; the readable formatter showed exact NDCs, D-0161-2016, ingredient-only reporting and category statuses. This verifies a complete local human-selection-to-briefing path without requiring a model to select a product.

## Llama/Qwen comparison

Both requested models were already installed and reachable through the existing loopback Ollama service. No server, model download or paid endpoint was created. The comparison uses the same six cases, one fixed-order trial per model: **12 trials total**. Each model is warmed once before scoring. Both use temperature 0, seed 7, thinking disabled, 4,096 context tokens, 512 generation tokens and the same time/byte limits.

Evaluation-only fresh copies of already verified fixture sessions give both models the same opaque references with independent counters; they are not a production session-cloning API. Within-run prompt/schema SHA256 equality is checked for each paired case. Raw model responses, native plans, source verification comparisons, model digests, settings and warm-up measurements are retained in [agent-v2-evaluation.json](agent-v2-evaluation.json).

| Measured metric | Llama `llama3.2:3b` | Qwen `qwen3.5:4b-q4_K_M` |
|---|---:|---:|
| Exact expected tool set selected natively | **5/6** | **6/6** |
| Schema-compliant proposals | 6/6 | 6/6 |
| Selected reference preserved | 5/5 eligible | 5/5 eligible |
| Correct full multi-source plan | **0/1** | **1/1** |
| Overall corpus workflows verified, including clarification | 6/6 | 6/6 |
| Selected-product evidence workflows matched the repository | 5/5 | 5/5 |
| Deterministic plan completion used | **1** | **0** |
| Free-form content / answers without tools | 0/6 / 0/6 | 0/6 / 0/6 |
| Timeouts or unverified workflows | 0 / 0 | 0 / 0 |
| Median model request latency | **1.144 s** | **3.024 s** |
| Median end-to-end latency | **6.556 s** | **9.367 s** |
| Multi-source end-to-end latency | **17.02 s** | **23.42 s** |

In the multi-source case, **Llama proposed only `get_drug_label_evidence`**; backend `auto` mode explicitly completed the requested recall and FAERS tools. Qwen proposed all three. Llama's verified final briefing is therefore not evidence that it planned the full workflow. Both final multi-source briefings remained partial because of actual data limitations, not failed tool execution.

Single-category cases offer only their requested tool and primarily measure constrained routing/schema compliance, not unrestricted medical planning. A six-case, fixed-order sample is not a reliability guarantee or broad hallucination evaluation. “Free-form content attempt” means any nonempty assistant content; it is not a semantic detector of every unsupported factual assertion. No such content was observed here, and any future content is discarded regardless. End-to-end measurements include cold subprocess artifact checks; some checks ran concurrently with regression/release verification. They are observed local latencies, not isolated inference or load-test benchmarks. No new peak-memory measurement or model superiority claim is made.

## Security, failures and remaining limitations

- Existing `is_deployed_environment()` behavior and unconditional hosted denial in `connect_release()` are unchanged. All new source operations still cross that guard; parent session authorization also denies staging/production before model calls. Tests cover both prototype and worker denial paths.
- Product confirmation remains outside the model. Session scope/ownership, exact NDC/formulation/ingredient binding, expiry, response bounds and cancellation are retained. There is still no authenticated HTTP/session provider; an embedding caller must derive owner identity from trusted authentication context, never model/request-body assertions.
- The only runtime HTTP destination is the existing fixed loopback Ollama transport. Source URLs are provenance strings, never runtime pharmaceutical API fetches. Models have no shell, SQL, filesystem or arbitrary HTTP tool.
- Retrieved label text is never sent back to the model. Source text cannot instruct the model to dispatch another tool. Model-written facts, advice, invented citations, all-lot inferences or causality assertions cannot become briefing facts merely by accompanying a valid call.
- The source adapter supplements provenance only; validated label admission and FAERS deduplication/aggregation remain in the existing repository/build contracts. No alternate truth source, clinical scoring or model-generated summary was introduced.
- Sessions are ephemeral and process-local. Per-tool attempts default to one; refreshing a source requires an explicitly new session and human confirmation. No pagination, distributed state, global admission/rate limiter, production audit store or target infrastructure qualification is included.
- Source text is not summarized/ranked. Long sources can exceed byte limits and are explicitly failed; the CLI's clearly marked excerpts are a display convenience, not the full research record. Demographic fields absent from existing aggregates remain unsupported.
- Exact label coverage is limited: the common Xanax example cannot safely satisfy a request for label text from this release. Its honest unavailable section is the intended result, not a reason to weaken label admission.
- Scope recognition is literal, not semantic. Use explicit categories for negation, comparisons, vague “safety” questions or complex intent. Neither a selected-product briefing nor a completed workflow establishes comprehensive safety or provides individualized advice.

## Exact local demonstration commands

Use the existing root Python environment and local Ollama installation. Do not clear hosted markers or force local mode on a hosted application. No `ollama pull` is required or performed.

Normal numbered selection and readable multi-source briefing:

```sh
PYTHONPATH=backend .venv/bin/python -m app.agent.cli \
  --model llama3.2:3b \
  --query 'Xanax 0.25 mg' \
  --question 'What are the major safety warnings, historical recalls, and reported adverse events associated with the product I confirm?' \
  --categories labels recalls faers --routing auto
```

Inspect the exact product and package NDCs, then enter `1`, `2`, etc.; Enter cancels. The two candidates are never selected automatically. A generic question without `--query` first uses the v1 model resolver and then the same human confirmation boundary.

Model-independent demonstration for an explicitly confirmed exact NDC:

```sh
PYTHONPATH=backend .venv/bin/python -m app.agent.cli \
  --query '0009-0029' --question 'Warnings, historical recalls, and reported adverse events' \
  --categories labels recalls faers --routing deterministic
```

Exact-label demonstration:

```sh
PYTHONPATH=backend .venv/bin/python -m app.agent.cli \
  --query '0002-0152' --question 'Show the admitted product label warnings and interactions' \
  --categories labels --routing deterministic
```

Use `--routing model` to require a complete native plan, or `--model qwen3.5:4b-q4_K_M` for Qwen. Add `--json` for the full typed result; candidate/prompt text goes to stderr so stdout can be redirected to a JSON file. No silent fallback from invalid proposals occurs.

Reproduce opt-in real-data verification and model comparison:

```sh
PYTHONPATH=backend .venv/bin/python -m app.agent.research_evaluation \
  --output /tmp/davai-agent-v2-real-data.json

PYTHONPATH=backend .venv/bin/python -m app.agent.research_evaluation \
  --models --output /tmp/davai-agent-v2-model-comparison.json
```

The first command does not contact Ollama. The second requires the two existing models; missing models are reported without downloading. Both read the sealed release. The evaluator exits nonzero if deterministic real-data facts do not match. Model deficiencies remain recorded separately, rather than being replaced with assumed outcomes. Loopback access required sandbox escalation for model comparisons; no network-facing application listener was started.

## Next steps toward a React research interface

1. Review these source contracts and the conservative partial-result semantics, especially label availability and FAERS scope, before adding UI behavior.
2. Define a local/backend API boundary that derives authenticated owner context, retains session references server-side, distinguishes user confirmation from model proposals and enforces admission/rate/timeout/privacy controls. Preserve hosted denial until independent deployment authorization work is completed.
3. Build source-specific React panels from the typed JSON: exact identity/numbered confirmation, label quotations with version/snapshot, recall applicability/lot limitations, ingredient-only reporting, explicit unavailable/failed/incomplete states and visible routing/fallback provenance. Do not add free-form medical summaries by default.
4. Expand paired evaluations with additional NDCs, combination products, missing-provenance/oversized sources, repeated runs, prompt variations and load/cancellation tests. Report native planning separately from deterministic completion and data availability. Measure latency without concurrent artifact work before optimizing worker reuse; retain hard cancellation and integrity checks.

## Preservation and completion disposition

Before/after checks confirmed unchanged frozen database inode, byte count, modification/change timestamps, read-only permissions and release-metadata SHA256. The mandatory gate verified the exact sealed hash. `publication_validated=false` remains unchanged. Release manifest, core serving gate, Vercel Authentication, Render Maintenance Mode, frontend and unrelated untracked research/ingestion files remain intact. No wildcard Git staging/cleanup, commit, push, merge, PR or deployment was performed.

**Completion: the requested local backend milestone is complete and reviewable.** Exact product selection, all three supported evidence tools, typed deterministic briefing generation, explicit uncertainty/partial success, offline regression/security checks and real-data end-to-end verification all succeeded. Private staging and production serving remain denied; these results do not authorize deployment.
