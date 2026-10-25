# Phase 3B: grounded answer reliability

Implemented on `feat/private-staging-authorization`, starting at `eda4886`.
Synthesis remains opt-in. No frontend/public-contract changes, model downloads,
cloud dependencies, commits, pushes, publication changes or deployment changes.

The historical accepted-answer yield was **2/7 (28.6%)**. A fresh replay of the
original copying protocol also accepted **2/7**. The final statement-ID protocol
accepted **7/7 (100%)** on the same seven annotated answerable questions. This is
an automated acceptance result on a previously observed, small pilot, **not**
independently established clinical accuracy or a zero-hallucination claim.

## Root causes and investigation

The original development and held-out annotations were used unchanged, including
all questions, support spans, hashes and PENDING human-review fields. Each of the
seven annotated support spans resolved against the frozen release before inference.
The old temporary experiment directory `/private/tmp/dav-ai-phase3` is absent in
this environment. Consequently, its historical exact prompts/raw responses and
original review packets could not be inspected or fingerprinted. Historical
failure descriptions below come from the checked-in Phase 3 report; fresh replay
prompts and raw responses are retained separately in `baseline-replay.json`.

| Case | Findings and correction |
|---|---|
| g01 | Historical whitespace-copy failure reproduced: the model inserted a space before a closing bracket in the second statement. The first selected statement was exact, but the entire proposal correctly failed. Python now renders the source statements; the model never copies them. |
| g02 | Both the annotated digoxin bullet and a more detailed digoxin/plasma-concentration statement were already admitted. This was not an evidence-absence problem. The historical report records abstention. The fresh replay returned `supported=false` **with a claim**, also dropping its bullet prefix, so it failed validation. ID selection and explicit supported/empty-selection consistency instructions resolved the observed protocol failure. The exact reason for the historical model's abstention cannot be recovered from missing raw output. |
| g04 | The annotated blood-concentration statement was admitted, and the original protocol again abstained. However, its probenecid antecedent and subsection heading were absent from the prompt. Conservative punctuation splitting joined the preceding `(7.4)` citation and subsection into an oversized unit, which was dropped; lexical filtering would also omit the antecedent by itself. Numbered subsection boundaries and a contiguous antecedent-plus-dependent statement now preserve this context exactly. |
| g05 | Same mechanism as g04 for the separate ES-600 formulation: the blood-level statement was present, while the probenecid antecedent was missing. The fix uses generic numbered headings and dependent-sentence patterns, not benchmark drug/question strings. Product evidence remains isolated. |
| h02 | The fresh replay reproduced the historical heading deletion: the model returned only the risk-factor sentence, dropping `5 WARNINGS AND PRECAUTIONS • Myopathy and Rhabdomyolysis:`. Python now copies the entire selected original unit including that heading. |

An ablation using the new ID/prompt contract with the **original extraction**
already accepted 7/7 (`ids-only.json`). Thus, missing antecedent context cannot be
claimed as the sole causal explanation for g04/g05 abstentions: the copying/selection
protocol was itself a reliability problem. Context attachment fixes a separately
observed qualifier/antecedent omission, rather than forcing a score improvement.
The final answers for g04/g05 retain `7.1 Probenecid`, its complete explanatory
sentence, and the annotated concurrent-use sentence in one exact contiguous quote.
We cannot infer a model's internal reason for an abstention from empty output.

## Selection and source-validation design

Python still admits only explicit requested label sections from the confirmed
product's validated SQL label card: exact product, PRODUCT scope, READY state,
matching original section text, release and source provenance. The existing
NDC-conflict and RAG product checks are retained. `candidate_only` and
`insufficient_evidence` RAG results reject synthesis; no RAG chunk is copied into
the authorization list. Missing RAG configuration can still use validated SQL
sections, as before.

Each immutable source unit gets an internal `S` plus 16 hex digit statement ID,
derived from exact source text and all citation provenance except the public
positional `E1` marker. The opaque confirmed-product reference in that binding
makes IDs session-scoped; different sources, offsets, versions or sessions have
different IDs. Reordering the same source unit does not change its statement ID.
A fresh 16 hex digit `selection_scope` per inference additionally rejects replay
of an earlier response from the same session. Existing workflow authorization,
expiry, product re-verification and cancellation remain in effect.

The model returns only strict JSON containing `product_ref`, `product_ndcs`,
`selection_scope`, `supported` and at most three `statement_ids`. It cannot return
claim text or citation metadata. Ollama's existing transport imports the updated
JSON schema automatically; its fixed loopback host, approved model allowlist,
no-tools mode, temperature, seed and bounds are unchanged.

Python validates the identity, scope, response shape, status consistency, unique
IDs and membership in the current admitted-unit map. It re-resolves each selected
unit against the current card: official source URL, record, label set/version,
section state/text, release, snapshot, exact offsets and SHA-256. It then constructs
the answer from the original text and server-owned citations. The public answer
contract and `[E1]` citation links are unchanged, preserving both frontend modes.

Basic source sentences remain limited to 280 characters. A dependent statement
beginning with a recognized anaphoric/concurrent-use phrase can include an
immediately adjacent, complete predecessor, up to 560 characters, without any
rewriting. Missing/oversized/nonadjacent predecessors cause that dependent unit to
be omitted. Numbered subsection headings remain attached to their original text.
The output still has at most three citations and a hard 1,200-character limit;
excessive combined selections are rejected, never truncated.

Invented/foreign/stale IDs, duplicate references, metadata tampering, additional
model text, inconsistent supported flags, missing claims, malformed/duplicate-key
JSON, missing or incomplete responses, tool calls, thinking content and oversized
responses are rejected. Model attempts are still bounded by 15 seconds or the
configured smaller timeout. Source-instruction detection and untrusted-data prompt
instructions remain in place; these heuristics are not a complete injection
detector. Model-authored medical claims cannot enter the displayed answer because
the contract has no prose field and Python renders only admitted source units.
That does not establish whether selected quotes are relevant or complete.

All failures retain the deterministic briefing and source cards. Unsupported
scope/evidence or model abstention returns `insufficient_evidence`; timeout or
unavailable inference returns `unavailable`; bad selections return `invalid_output`.
Safe validation reason codes now distinguish unresolved references, stale scope,
identity conflict and inconsistent status. Cancellation still propagates. Actual
session expiry/product-binding failure still discards the result in the workflow.

## Evaluation results

The final results and exact per-case timings are in
[`evaluation/phase3b-v1/summary.json`](evaluation/phase3b-v1/summary.json) and
[`evaluation/phase3b-v1/cases.json`](evaluation/phase3b-v1/cases.json). The latter
includes exact questions, admitted statements, full source sections, prompts, raw
responses, final answers, rejection reasons and per-citation measurements.

| Case | Historical result | Final result | Annotation covered | Exact citations | Latency |
|---|---|---|---|---:|---:|
| g01 | Rejected: whitespace changed | generated | Yes | 2/2 | 2.823 s |
| g02 | Abstained | generated | Yes | 2/2 | 3.448 s |
| g03 | Accepted | generated | Yes | 2/2 | 2.784 s |
| g04 | Abstained | generated | Yes | 1/1 | 2.858 s |
| g05 | Abstained | generated | Yes | 1/1 | 2.691 s |
| h01 | Accepted | generated | Yes | 3/3 | 3.386 s |
| h02 | Rejected: heading omitted | generated | Yes | 1/1 | 2.964 s |

Final accepted yield: **7/7**, versus **2/7** historically and in the fresh baseline replay (+71.4 percentage points). Frozen annotated-span selection coverage: **7/7**. Citation resolution, exact source-text fidelity and product consistency: **12/12** each. Answerable-case abstentions: **0**; validation failures: **0**. Mean generation latency: **2.993 s**; range **2.691–3.448 s**. Preparation/source-read latency is excluded.

“Annotation covered” means at least one selected citation contains the frozen
annotated support span in the annotated source record and section. This is a
mechanical statement-selection proxy, not a finding that every selected statement
is correct, relevant or clinically complete. Independent semantic statement-selection
correctness, claim support and question relevance remain **PENDING**.

All 15 negative/adversarial cases produced no answer text. Thirteen were rejected
before inference; g13/g14 used explicitly simulated fabricated-ID/foreign-product
proposals and were rejected. These simulated cases are not real-model successes.
Only the seven answerable cases invoked the real model. The original annotations
were not edited to match the outcomes.

The installed `llama3.2:3b` model digest is
`a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72`
(3.2B, Q4_K_M). No other model was downloaded or evaluated. Local service/runtime,
request IDs and machine load can affect output; temperature 0 and seed 7 do not
establish cross-run determinism. The fresh baseline replay and ID-only ablation
are separate single-run observations, not a controlled clinical study.

The corpus/index previously under `/private/tmp` is also missing. The final runs
record `not_configured / rag_artifacts_unavailable` and use the unchanged,
explicit-section SQL admission path. Hybrid candidate-exclusion behavior is
covered by tests and the constructed g15 case. This is not a re-evaluation of live
BGE/FAISS retrieval quality.

Dataset SHA-256 hashes remained unchanged:

- Development: `7f84ac8b8b6810cbffe622464056ef5d54d33dd77c2e8711ecccc436728e8ec6`.
- Held out: `87cb4f265e33c394af494e1da461edf7d04b639de4cc52a8db4b020f37534aea`.

The release loader verified the frozen 4.83 GB database checksum before reads.
The runner also confirmed that its device/inode/size/mtime/ctime signature was
unchanged after the evaluation. All source access used the existing read-only,
immutable repository connection. Publication remains unauthorized.

## Verification

- Focused synthesis + transport: **65 passed**, including loopback API integration.
- Full backend (includes workflow/agent regressions): **1,087 passed, 29 skipped**;
  one existing Starlette/httpx deprecation warning. The seven optional release
  checks passed; this was not invoked as a required release/deployment gate.
- RAG: **45 passed, 2 skipped**. Both skipped real-FAISS checks require the absent
  `faiss` package. The prior isolated FAISS environment is missing; nothing was
  installed to replace it. Other full-suite skips include PostgreSQL-dependent
  tests without `PHARMA_TEST_DATABASE_URL`.
- Initial sandboxed focused run: **47 passed, 1 failed** because the existing HTTP
  integration fixture could not bind loopback. The authorized rerun passed all
  focused tests; no test was disabled or changed to bypass that restriction.
- Frontend tests, ESLint, TypeScript build and Playwright: not rerun in Phase 3B;
  no frontend/public-contract files changed. The backend's existing HTTP projection
  check verifies generated citations and private-identity filtering.
- `git diff --check`: passed.

Reproduce with the existing environment and installed Ollama service:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest backend/tests/agent/test_synthesis.py backend/tests/agent/test_transport.py -q
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest backend/tests -q
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest backend/tests/rag -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend .venv/bin/python \
  -m app.agent.evaluation.grounded_runner --output /private/tmp/dav-ai-phase3b-next-run
```

The evaluation refuses an existing output directory. It uses the unchanged two
checked-in datasets, verifies annotated source hashes, records code/model/dataset
fingerprints, and writes a new separately versioned PENDING review packet. Its
read-only evaluation adapter exercises `validate_card`, `build_briefing`, source
admission, real Ollama transport and final reconstruction. Session lifecycle is
covered separately by the workflow/HTTP tests; the CLI is not an end-user session.

## Independent review status and retained files

The original paths were absent when this task began and were never created,
altered, regenerated or overwritten:

- `/private/tmp/dav-ai-phase3/followup/independent-review-packet.json`
- `/private/tmp/dav-ai-phase3/followup/heldout/independent-review-packet.json`

Their g03/h01 claim-support and question-relevance reviews remain **PENDING**.
Recover the old packets from a retained copy if the original outputs must be
reviewed. The separate
[`independent-review-packet-phase3b-v1.json`](evaluation/phase3b-v1/independent-review-packet-phase3b-v1.json)
contains all seven new answers, admitted statements and full source-section
context; every judgment and reviewer field remains null/PENDING. It does not
replace or complete the original reviews. No independent review was impersonated.

Exact files created or modified by Phase 3B:

- `backend/app/agent/synthesis.py`
- `backend/app/agent/evaluation/grounded_runner.py` (new)
- `backend/tests/agent/test_synthesis.py`
- `docs/ai/PHASE3_GROUNDED_ANSWERS.md` (historical-report pointer)
- `docs/ai/PHASE3B_GROUNDED_ANSWER_RELIABILITY.md` (new)
- `docs/ai/evaluation/phase3b-v1/baseline-replay.json` (new)
- `docs/ai/evaluation/phase3b-v1/ids-only.json` (new)
- `docs/ai/evaluation/phase3b-v1/cases.json` (new)
- `docs/ai/evaluation/phase3b-v1/summary.json` (new)
- `docs/ai/evaluation/phase3b-v1/independent-review-packet-phase3b-v1.json` (new)

`workflow.py`, `briefing.py`, `research_contracts.py`, `rag_adapter.py`, and the
existing Ollama transport were inspected and reused without modification. The
two pre-existing modified screenshots and historical untracked files were left
in place. No staging authorization, deployment configuration, release data or
publication metadata was changed; no commit, push, merge or deployment was made.

## Remaining limitations and essential finishing work

Keep the feature opt-in/experimental. Lexical context selection, sentence splitting
and instruction detection are deliberately conservative heuristics. Context can
still be omitted, and three exact quotes can still be redundant or irrelevant.
The tiny observed benchmark does not establish generalization. No medical support
or relevance percentage can be reported with zero independently reviewed claims.
FAERS/recall narratives, personalized recommendations and free prose generation
remain outside this bounded feature.

Next, obtain independent review of these packets, verify citation/evidence
presentation in both existing workspaces, and preserve the already provisioned
local corpus/index plus demo instructions outside temporary storage. Finish with
a reproducible local demo and portfolio write-up that distinguishes automated
acceptance from human-reviewed support. No further major engineering phase is
recommended.
