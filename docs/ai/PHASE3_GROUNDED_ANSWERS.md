# Phase 3: optional grounded answer prototype

**Implementation and automated verification complete. Independent claim-support
and question-relevance review remain PENDING**, explicitly including g03 and h01.
No generated claim is classified as human-supported in this report. Citation
resolution and exact-source checks are measured separately from semantic support.

## Behavior and scope

The existing deterministic research workflow still retrieves and validates the
requested source cards first. New request flag `synthesize: true` opts into a
separate local Ollama step; its default is false. Existing clients and research
requests work without opting in. Both Everyday and Research Pro have an unchecked
opt-in control and display the optional answer above the evidence cards.

This bounded version implements **extractive synthesis**, not unrestricted medical
paraphrasing. The model proposes one to three complete, concise statements from a
server-prepared list of admitted label statements. Each displayed statement must
match its authorized source unit exactly. The server adds attribution and citation
markers; it does not display any other model prose. Output is limited to three
punctuation-delimited source statements and 1,200 characters. Source units are at
most 280 characters, without truncation, normalized rewriting, or RAG chunk
fragments. Conservative splitting can reject useful source text with headings or
complex punctuation rather than manufacture a shorter statement.

The source authority is the existing validated, exact-product SQL label card,
including READY section states. It is not a vector score or the RAG `supported`
flag. Explicit sections use the existing conservative section-name mapping.
`candidate_only` and insufficient RAG outcomes cannot authorize an answer; RAG
passages are never copied into the synthesis prompt. Missing/unconfigured RAG can
still use an admitted SQL section. Questions outside a literal section request,
missing sections/labels, personalized advice, FAERS causality and recall-scope
conclusions receive an insufficient-evidence response with the source cards intact.
FAERS and recall synthesis are intentionally unsupported in this first version;
their structured cards and disclosures remain available.

Within requested sections, a conservative lexical filter removes units without a
specific question-term match, followed by deterministic overlap/offset ordering
and a bounded prompt list (six per source section, twelve total). This is a
context filter, **not** a factual-support/relevance classifier. Shared words,
omitted context and contradictory versions still require human review. Questions
with a conflicting literal NDC are rejected; this is not a general drug-name
entity-resolution service. The confirmed reference/NDC binding remains the
existing server-owned session, never something a model may choose or change.

All evidence and questions are JSON-encoded untrusted data. The system prompt
prohibits following embedded instructions. Recognizable source instruction attacks
are rejected before inference. The model has no tools in this call, no authority
to fetch more evidence, and no ability to add free-form text. The injection regex
is an additional heuristic, not a claim to detect every attack. Text in the UI is
React-escaped, with only server-provided evidence IDs rendered as internal links.

## Contract and validation

The optional `ResearchBriefing.answer` defaults to null. Its fields are:

- `status`: `generated`, `insufficient_evidence`, `unavailable`, or `invalid_output`.
- `reason`: stable fallback/validation reason.
- `text`: attributed quoted statements with `[E1]`-style markers, or null.
- `product_ref`: the opaque confirmed-product reference.
- `citations`: evidence ID, labels-only category, product reference, official
  source URL/record, label set/version, section, original character start/end,
  SHA-256 of quoted text, source snapshot date, and release ID. These nested
  fields are the evidence provenance; no private product/formulation IDs are added.
- `method`: `local_model_extractive`.
- `limitations`: source, relevance, scope and medical-use disclosures.

Ollama's JSON-schema response format constrains the proposal shape. Validation
still independently requires complete assistant responses, the exact product
reference and NDC list, strict types, no extra fields, at most three claims,
unique/resolving evidence IDs, and exact source-unit text. Missing citations,
changed text (including changed whitespace), unsupported categories, extra prose,
empty/oversized outputs, markdown, duplicate JSON keys, tool calls and nonempty
thinking output are rejected. A model's `supported` proposal flag is untrusted
and is **not** a human support judgment. The public answer status is `generated`,
not `verified` or `supported`.

Generation uses the existing fixed-loopback Ollama transport and approved model
allowlist. It has no cloud service, pull endpoint, new framework or package
requirement. Temperature 0, seed 7, context 4,096 tokens and at most 512 predicted
tokens are retained. Each synthesis attempt is bounded by the smaller of 15
seconds and the existing model timeout, inside the existing overall run deadline.
Prompt/response/briefing byte limits remain enforced. If optional output cannot
fit the briefing bound, it is omitted rather than stopping the source briefing.

Validation failure discards model text and returns `invalid_output`; a timeout or
unavailable model returns `unavailable`; unsupported evidence or model abstention
returns `insufficient_evidence`. Structured evidence/statuses remain unchanged.
Session authorization, exact identity checks, cancellation, expiry, deployment
restrictions and product re-verification still apply. Actual session expiry or
binding failure still stops/discards the result rather than exposing stale output.

Citation links in both experiences open/focus the exact source section identified
by public source record, label set/version and section. Summaries are labeled
AI-selected quoted statements, separate from the original FDA source cards.
Fallbacks explicitly retain and direct users to those cards. Older briefings with
no answer field remain renderable; generated TypeScript marks the additive answer
field optional.

## Evaluation methodology and measured results

The checked-in development set contains 16 fixed questions; the separate six-case
question holdout covers additional label facts, absent evidence, conflicting
formulations, unsupported topics and FAERS causality. Across both sets are label,
combination-drug, missing-label/section, personalized-advice, recall-scope,
source-injection, fabricated-citation and model-identity-conflict cases. The latter
two deliberately mutate an otherwise shaped response, and the document injection
modifies only an in-memory test copy. None mutate the pharmaceutical database.

Annotations were selected from source text before each set's initial generation
and contain source-record/section/offset/hash support spans or a documented
negative rationale. They are single-assessor annotations. Human support/relevance
fields remain null/PENDING; there is no independently reviewed clinical accuracy
claim. The original 21-question RAG annotations and both new generation annotation
files were preserved unchanged during evaluation.

An initial development run found that three citations could all resolve while one
statement came from an unrelated part of the same section. That finding motivated
a narrower lexical context filter. JSON-schema output was also added without
relaxing strict type/text validation. A final conjunction-stopword bug fix was
retested on the unchanged datasets. All initial, follow-up and final artifacts
are retained. Accordingly, the final held-out rerun is a **regression check on a
previously observed small pilot**, not pristine external validation. No benchmark
annotation or human judgment was adjusted to improve a score.

Final real-model measurements:

| Measurement | Development (16 cases) | Question holdout (6 cases) |
|---|---:|---:|
| Questions annotated as answerable | 5 | 2 |
| Generated answer objects | 1 | 1 |
| Generation yield on answerable questions | 1/5 | 1/2 |
| Citations resolving to exact admitted source spans | 2/2 | 3/3 |
| Insufficient-evidence fallbacks | 12 | 4 |
| Invalid-output fallbacks | 3 | 1 |
| Annotated gate outcomes matched | 12/16 | 5/6 |
| Independent human-reviewed claims | 0 | 0 |
| Human claim support | **PENDING** | **PENDING** |
| Human question relevance | **PENDING** | **PENDING** |

Citation resolution is **5/5 across the two generated answers**, not 100% factual
accuracy. There are seven source-annotated answerable questions: five fall back
rather than generating. The 15 negative/adversarial cases all produced no answer
text, but this tiny constructed sample is not a safety guarantee. Expected gate
agreement includes deliberately adversarial invalid-output tests and is not a
clinical accuracy metric. All human-reviewed claim-support denominators are zero;
no support percentage is computed.

The generated cases are **g03** (Jardiance/lithium, two statements) and **h01**
(Trulicity contraindications, three statements). Their claim support, relevance
and missing qualifiers are PENDING. g01 is rejected because the model changes
source whitespace; h02 is rejected because it drops the whitelisted statement's
heading. g02 and the two combination-drug questions g04/g05 trigger model
abstention despite source-annotated evidence. These conservative fallbacks show
that this model/protocol has low generation yield; validation was not loosened
to make the benchmark look better.

Final generated-response latency was 2.944 s for g03 and 4.341 s for h01. Other
model attempts ranged from 0.836–4.869 s in the development run; no-model gates took
approximately a millisecond or less. These are single-run observations with local
files/model caches, not controlled performance comparisons. There were seven
model calls in development and two in the held-out rerun.

The user explicitly directed that independent review remain PENDING and that both
follow-up review packets be preserved. They remain byte-identical, with preserved
hashes recorded in `final/preserved-review-packets.json`:

- `/private/tmp/dav-ai-phase3/followup/independent-review-packet.json`
- `/private/tmp/dav-ai-phase3/followup/heldout/independent-review-packet.json`

Final run outputs and additional pending-review packets:

- `/private/tmp/dav-ai-phase3/final/development/evaluation-results.json`
- `/private/tmp/dav-ai-phase3/final/heldout/evaluation-results.json`
- `/private/tmp/dav-ai-phase3/final/development/independent-review-packet.json`
- `/private/tmp/dav-ai-phase3/final/heldout/independent-review-packet.json`

Temporary artifact paths can be reclaimed by the OS. Preserve this external
experiment directory if retaining the run. No generated model/index artifacts
were added to the source tree or frozen release.

## Reproducibility

The real evaluation used the already installed `llama3.2:3b`, 3.2B GGUF Q4_K_M,
model digest `a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72`,
on local Ollama 0.40.6 / Apple M4 / Python 3.13.7. There were no package installs
or model downloads. Ollama was initially stopped; an ephemeral service was started
on `127.0.0.1:11434` with cloud disabled for evaluation and stopped afterward,
restoring the prior state. No deployment or authorization configuration changed.
The main application's preinstalled approved model allowlist remains unchanged.

Fingerprints:

- Synthesis code SHA-256:
  `b42658871e9f3044d7ef7b1483a0d751d24a9261b14a725398360edbde4d8b35`.
- Model transport code SHA-256:
  `224c866b942ea27aadad7f0216a44428317a85ea1b023acb87bb79b3b0d761dd`.
- Generation development dataset SHA-256:
  `7f84ac8b8b6810cbffe622464056ef5d54d33dd77c2e8711ecccc436728e8ec6`.
- Generation held-out dataset SHA-256:
  `87cb4f265e33c394af494e1da461edf7d04b639de4cc52a8db4b020f37534aea`.
- Original RAG benchmark SHA-256, unchanged:
  `953a7623d291a487125b20d0079bba75a952401932857b4bd06f313e29ad4f33`.

With the already provisioned external corpus and local Ollama service running,
reproduce from the repository root (the evaluation scripts only write their own
external output files; copy scripts/use fresh external output paths to preserve
this run):

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend .venv/bin/python \
  /private/tmp/dav-ai-phase3/final/development/evaluate.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend .venv/bin/python \
  /private/tmp/dav-ai-phase3/final/heldout/evaluate.py
```

The scripts check dataset/code freezes, reuse the read-only release repository,
existing product projection, `validate_card`, `build_briefing` and local transport,
and record raw proposals, final answers, gate outcomes, exact citation checks and
pending review fields separately. Source injections/citation substitutions are
explicit synthetic mutations. The scripts and artifacts remain outside the repo;
they require the documented local corpus from prior phases.

## Automated verification

- Final backend suite: **1,070 passed, 29 skipped**, one pre-existing
  Starlette/httpx deprecation warning. Seven optional release checks passed; this
  does not authorize deployment or turn them into a required deployment gate.
- New synthesis suite: **39 tests**, included in the backend run (38 standalone
  checks plus the loopback API integration test).
- Real-FAISS RAG suite in the existing isolated environment: **47 passed**.
- Frontend: **78 passed** across ten test files; lint passed; TypeScript/Vite build
  passed. The 13 new component checks cover both modes, source navigation,
  stale identities, optional fields and fallbacks.
- Playwright: **3 passed** (both new generated/unavailable answer journeys and the
  existing dual-mode product-switching journey). These use browser/API fixtures;
  the real model evaluation above is separate. Browser test sockets required
  permission to bind loopback in this environment.
- The first Playwright command was invoked from the repository root and failed
  to load the frontend configuration (invalid relative URL). The corrected run
  from `frontend` passed. Only this task's misplaced failure artifacts were moved
  to `/private/tmp/dav-ai-phase3/incorrect-cwd-playwright/`; no unrelated files
  were deleted. A frontend lint export issue was corrected before the final pass.

Re-run tests:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest backend/tests -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend \
  /private/tmp/dav-ai-rag-phase1b/venv/bin/python -m pytest backend/tests/rag -q
cd frontend
npm run lint
npm test -- --run
npm run build
npx playwright test e2e/grounded-answer.spec.ts e2e/dual-mode.spec.ts
```

## Remaining limitations

Keep synthesis opt-in and experimental. Exact source copying protects against
new model-authored factual claims but does not establish question relevance,
clinical completeness, qualifier preservation across context, or independent
claim support. Lexical filtering and instruction-pattern detection are incomplete.
The small local model often abstains or fails literal-copy validation on source-
annotated questions. Open-ended/non-label synthesis is outside this bounded
implementation. General prose paraphrasing, wider recall/FAERS narratives and any
claim of validated clinical answer quality require separate work and independent
review; they are not delivered or implied here. The existing structured briefing
remains the primary evidence experience.

## Exact changed files for this task

The worktree already contained prior-phase/unrelated changes. This list was
computed against a start-of-task file fingerprint snapshot, not against git HEAD;
pre-existing changes were preserved. `briefing.py` and `rag_adapter.py` were
inspected/reused but were not changed in this phase.

- `backend/app/agent/evaluation/grounded_answers_heldout_v1.json`
- `backend/app/agent/evaluation/grounded_answers_v1.json`
- `backend/app/agent/model.py`
- `backend/app/agent/orchestrator.py`
- `backend/app/agent/research_contracts.py`
- `backend/app/agent/synthesis.py`
- `backend/app/agent/workflow.py`
- `backend/app/local_research/api.py`
- `backend/app/local_research/export_types.py`
- `backend/tests/agent/test_synthesis.py`
- `backend/tests/agent/test_transport.py`
- `docs/ai/PHASE3_GROUNDED_ANSWERS.md`
- `frontend/e2e/grounded-answer.spec.ts`
- `frontend/src/research/EverydayEvidence.tsx`
- `frontend/src/research/EverydayWorkspace.tsx`
- `frontend/src/research/Evidence.tsx`
- `frontend/src/research/GroundedAnswer.test.tsx`
- `frontend/src/research/GroundedAnswer.tsx`
- `frontend/src/research/ResearchProWorkspace.tsx`
- `frontend/src/research/SynthesisOption.tsx`
- `frontend/src/research/Workspace.test.tsx`
- `frontend/src/research/Workspace.tsx`
- `frontend/src/research/briefing.fixture.json`
- `frontend/src/research/client.ts`
- `frontend/src/research/contracts.ts`
- `frontend/src/research/evidenceAnchors.ts`
