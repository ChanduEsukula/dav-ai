# Agent v1: secure tool calling and product state

2026-10-22 (America/Chicago). Branch `feat/private-staging-authorization`, baseline HEAD `542bf37`. **Local backend milestone ready for engineering review; staging/production serving and deployment remain unauthorized.** No frontend or HTTP agent endpoint was added. No commit, push, merge, PR, paid API, model download or cloud configuration change occurred.

## Audit and architecture decisions

The manual `app/agent/tools.py` already delegated to `FrozenPharmaReleaseRepository`, which opens only the sealed read-only release through the existing deployed-denial gate. It did not maintain a user/session selection. Models were therefore expected to reproduce a long structured database ID; an incomplete but plausible suffix was correctly rejected. A model answering without executing a tool had no grounded evidence boundary.

The resolver also checked `len(products) == 100` **after** strength filtering, hiding possible truncation and allowing a filtered singleton to appear fully resolved. The original mg filter could treat a concentration denominator as a comparable dose, and candidate projections omitted formulation/provenance information needed to bind a choice. Recall projections retained useful scope fields but did not expose the source snapshot date.

The implementation is deliberately a single-step, bounded tool router with a human pause, rather than an autonomous search/selection loop:

1. A trusted embedding caller creates one `ProductSession(owner_id, backend=ProcessBackend())` per conversation. There is no module-level selected-product registry.
2. Before selection, the model sees only the resolver schema. The resolver delegates to the existing repository, projects actual candidates and replaces database IDs with random session-local `p_…` references. The map remains private to the Python session object.
3. Candidate results always require explicit human confirmation, including singleton results. Ambiguous strengths/NDCs are never selected automatically. A limited search is flagged even if filtering leaves only one candidate.
4. `confirm(reference, owner_id=…)` is a trusted caller method, **not a model tool**. It checks ownership, membership, session lifetime and a fresh repository projection before committing selection. Product NDCs, package NDCs, formulation ID, strength, dosage form, routes, ingredients, names and provenance must still match. Selection is immutable for that session; a different product requires a new session.
5. After confirmation, the only model tool is `search_historical_recalls(product_ref=…)`. Its JSON schema contains an enum of exactly the selected reference. Server validation independently checks the reference. Full or incomplete product IDs, foreign session references, extra scope/lot fields and unknown tools cannot dispatch a repository operation.
6. Python resolves the reference to the stored database ID, rechecks the product binding, executes the guarded recall function, validates provenance/applicability and returns a deterministic evidence card. The model receives no database ID, evidence-generation authority, SQL, shell, filesystem or external HTTP tool.

`ResearchAgent.run` performs at most one model proposal per call. It pauses immediately for clarification or returns evidence and stops; it never asks the model to rewrite evidence into a final answer. Caller resumptions share session counters. Invalid proposals fail closed rather than triggering an unbounded model repair loop. Model prose/thinking is never copied into candidate/evidence results, even when it accompanies a valid tool call.

### Trust and ownership boundary

The owner ID is a **trusted caller input**, never an LLM argument or a credential supplied by the model. Ownership and session-local reference membership are both checked. An embedding server must derive owner identity from its authenticated request context and retain the actual session object under that owner; this phase does not invent an authentication provider or HTTP session manager. It would be unsafe to expose construction, `confirm`, backend injection or the raw `owner_id` as unauthenticated model-controlled API parameters. Python access to private session internals is outside the untrusted-model boundary.

The CLI generates a fresh local owner token and obtains confirmation through terminal input outside the model executor. No mapping persists across processes. References are random rather than predictable ordinals; even two sessions with the same owner cannot use each other's references. A lock serializes state changes. The overall run deadline includes waiting for that lock; a foreign caller is rejected before it can close a busy session. Expiry is rechecked after reads and before publishing/committing late results.

### Resource and execution boundaries

Defaults are configurable through the frozen `Limits` object:

| Limit | Default |
|---|---:|
| Model iterations / session | 4 |
| Model tool-call attempts / session | 4 |
| Calls accepted from one response | Exactly 1 |
| Candidate search size | 100, with original-search truncation flag |
| Recall records returned | 10, with original count/truncation preserved |
| Model response | 65,536 bytes |
| Serialized prompt budget | 12,288 bytes |
| Tool result / published result budget | 65,536 bytes |
| Private worker envelope | 262,144 bytes |
| Model request deadline | 45 seconds |
| Each repository worker operation | 20 seconds |
| Overall run, including lock wait | 70 seconds |
| Session lifetime | 600 seconds |
| Ollama context / generation budgets | 4,096 / 512 tokens |

Prompt byte bounds and Ollama's token bounds are separate; there is no claim of tokenizer equivalence between models. Oversized results stop explicitly instead of silently selecting/truncating candidates. The installed models are the only allowed model names. The transport uses fixed `http://127.0.0.1:11434`, disables environment proxies and redirects, bounds streamed response bytes and the whole request deadline, and exposes no model-pull endpoint. Existing development dependency `httpx==0.28.1` is reused; no dependency manifest changed. The existing API runtime remains independent of this local development transport.

Actual repository operations run in a fixed Python subprocess, with fixed operation dispatch and bounded JSON input/output, not shell interpolation. Timeout/cancellation kills and reaps the worker. Read-only work cannot later update parent session state. This is stronger than abandoning a running thread, but is not an OS sandbox against a malicious repository, host or Python installation. The release gate, filesystem ownership and trusted dependency assumptions still apply. A fresh worker cold-hashes the large artifact, trading latency for simple hard cancellation; no authorization/hash bypass or persistent background worker was added.

### Pharmaceutical evidence rules

Cards preserve recall number/classification/status/reason, firm, dates, lot text/scope, applicability, match method/value, record ID, source record ID, source URL, source snapshot date, full coverage metadata, count/truncation and limitations. They never infer all-lot scope from an unknown lot scope. Package/product applicability must match the corresponding exact NDC and matching method. Unknown/unsupported linkage classes or methods deny rather than being upgraded to a verified association. Required identity/recall provenance and snapshot dates must be present; URLs use the existing HTTPS FDA-host allowlist.

A partial empty recall collection remains a partial collection, with an explicit warning that it cannot establish no historical recalls. Shared limitations retain FAERS causality and ingredient-count restrictions; Agent v1 exposes no FAERS analysis tool. The model cannot override scope fields through arguments. Even a fabricated narrative attached to a valid tool call is discarded. There is no generated narrative presented as independently verified evidence.

The strength shorthand remains intentionally narrow: a single-ingredient mg amount or mg/1 value can be refined, but concentration conversions, combination products and release-form equivalence are not inferred. Names including XR remain intact when delegated to repository search; distinct strengths/NDCs/formulation IDs remain distinct candidates.

## Files changed

The existing agent directory and manual tool file were untracked at task start; their contents were preserved and extended without staging. The preexisting feasibility study was not modified.

| File | Purpose |
|---|---|
| `backend/app/agent/tools.py` | Fix original-limit truncation; require clarification for a limited singleton; preserve formulation/NDC/provenance/snapshot fields; narrow unsafe strength equivalence. |
| `backend/app/agent/contracts.py` | Strict extra-forbidding Pydantic argument models, tool schemas, configurable bounds and strict bounded JSON. |
| `backend/app/agent/state.py` | Caller-owned session, opaque references, owner checks, explicit confirmation, product binding and selection lock. |
| `backend/app/agent/backend.py`, `worker.py` | Killable fixed read-only repository dispatch with bounded envelopes and no fallback. |
| `backend/app/agent/evidence.py` | Deterministic evidence validation/cards and pharmaceutical limitations. |
| `backend/app/agent/model.py` | Restricted local Ollama chat/metadata transport, no proxies/redirects/model pulls. |
| `backend/app/agent/orchestrator.py` | Bounded model proposal validation, state-aware whitelist, timeouts, budgets, failure handling and narrative exclusion. |
| `backend/app/agent/cli.py` | Local terminal interface with explicit out-of-model user confirmation. |
| `backend/app/agent/benchmark.py` | Installed-model checks, identical prompt/reference reuse, warm-ups, telemetry and reproducible per-trial scoring. |
| `backend/tests/agent/` | Package marker and tool, orchestrator, transport/worker and benchmark-metric regressions using synthetic data/mock model responses. |
| `docs/ai/agent-v1-benchmark.json` | Actual 24 measured trials, raw bounded model responses, model digests/options, prompt hashes, warm-up data, latency and memory telemetry. |
| This report | Architecture, exact commands, evidence, results and limitations. |

No frozen database, release manifest, deployment guard, publication flag, frontend, Vercel/Render configuration, unrelated research/ingestion source or dependency pins changed.

## Offline and regression tests

All automated agent tests run without Ollama; they use mock model responses, synthetic repository results and HTTP transport mocks. Worker tests also exercise the real subprocess entrypoint without a pharmaceutical fixture and simulate kill/reap behavior on timeout.

| Check | Final result |
|---|---|
| `PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/agent -q` | **73 passed**, zero skipped/failed (0.43 s). |
| `PYTHONPATH=backend .venv/bin/python -m pytest backend/tests -m 'not release_artifact' -ra` | **828 passed, 27 skipped, 7 deselected**, one existing warning (10.02 s). |
| `PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/security -q` | **246 passed**, no skips/failures (0.24 s). |
| `PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/pharma_release -m release_artifact --require-pharma-artifact -ra` | **7 passed, 370 deselected**, no skips/failures; one existing warning (20.66 s, while benchmark reads were also running). Required integrity gate passed. |
| `.venv/bin/python -m compileall -q backend/app/agent backend/tests/agent` | Passed. |
| `git diff --check` plus explicit whitespace checks for new/untracked changed files | Passed. |

Coverage includes empty/missing queries and products; delegated exact NDC lookup; brand/strength ambiguity; same strength across NDCs; XR vs immediate-release preservation; limited search before strength filtering; unsafe concentration comparisons; invalid/incomplete IDs; missing evidence; valid routing; absent/unknown/malformed/duplicate-field/extra-field tool calls; incomplete model responses; full/incomplete IDs used as references; cross-session and foreign-owner misuse; model attempts to confirm/replace a product; binding changes before confirmation/use; unsupported applicability/matched NDC/lot scope; missing source ID/URL/date/coverage; partial empty results; hallucinated narrative without tool execution and attached to valid calls; response limits; worker/model timeouts; lock deadlines; session expiry during confirmation; repeated-call budgets; hosted-denial preservation and benchmark metric classification.

The first expanded mock run was **51 passed, 1 failed**: the test tried a foreign reference against an already selected session, so the stronger selection-lock rejection occurred first. The test now separates foreign-reference and locked-selection boundaries. Intermediate runs expanded from 65 to 73 tests as transport, deadline and expiry cases were added. No final failures remain. The 27 skips require optional disposable PostgreSQL ingestion fixtures; no server was started. The existing Starlette TestClient/httpx deprecation warning remains. Frontend suites were not rerun because no frontend code or API contract changed.

## Real-model benchmark findings

Both requested models were found in the existing Ollama installation. No model was downloaded. API shapes follow the official [chat endpoint](https://docs.ollama.com/api/chat), [tool-calling documentation](https://docs.ollama.com/capabilities/tool-calling) and [running-model telemetry](https://docs.ollama.com/api/ps).

The evaluation uses six questions (brand ambiguity, strength ambiguity, confirmed recall lookup, incomplete-ID bait, fabricated-recall/all-lot bait and causality boundaries), repeated twice per model: **12 trials per model, 24 total**. Four scenarios per repetition have an explicitly scripted human selection of the sole exact `0009-0029` candidate. This fixture preparation is outside the model; ambiguous search scenarios are never automatically confirmed.

Equivalent cases use the **same live session reference across both models**, rather than giving models different opaque strings. Prompt/schema SHA256 equality is checked per case/repetition. Both models use temperature 0, seed 7, 4,096 context tokens, 512 generation tokens, thinking disabled and the same deadlines. One completed warm-up per model is excluded from trial metrics. Warm-up latency was 3.24 s for Llama and 5.31 s for Qwen; per-trial load-duration telemetry is retained in the raw file. Sequential model blocks reduce repeated cold loading, but do not provide randomized order or an isolated-memory laboratory.

| Measured metric | Llama `llama3.2:3b` | Qwen `qwen3.5:4b-q4_K_M` |
|---|---:|---:|
| Valid tool calls | 12/12 | 12/12 |
| Correct permitted tool selected | 12/12 | 12/12 |
| Argument schema compliance | 12/12 | 12/12 |
| Exact selected reference preserved | 8/8 eligible trials | 8/8 eligible trials |
| Tool execution succeeded | 12/12 | 12/12 |
| Unsupported recall-ID claims in model content | 0/12 | 0/12 |
| Answer attempts without tool execution | 0/12 | 0/12 |
| Median model-request latency | **0.947 s** | **2.446 s** |
| Median end-to-end latency including real workers | 6.089 s | 8.519 s |
| Sampled Ollama `size` / `size_vram` | 2,561,000,078 / 2,561,000,078 bytes | 3,152,229,169 / 3,152,229,169 bytes |

Memory fields are Ollama-reported loaded-model values, **not process RSS, system peak memory or independent hardware measurement**. They should not be added together as an asserted system footprint on unified memory. The native prompt counts were below the configured context ceilings (maximum reported 362 for Llama, 500 for Qwen).

"Hallucinated answer frequency" is operationalized narrowly here: unsupported FDA-style recall IDs in response content, plus separately counted unverified answer attempts without tools. The allowed recall number is independently known from the real fixture. This is **not** semantic validation of every possible medical assertion, lot inference or causal claim. Any such narrative would still be excluded from application output. Zero observed proxy failures in 12 trials is not proof of hallucination-free behavior. The mocked adversarial cases enforce failure handling regardless of these measured model successes.

The evidence supports equal routing reliability on this small corpus and lower observed latency for Llama under these settings; it does not establish general model superiority. Llama remains the requested starting default. Both achieved real guarded database execution; cold checks substantially contribute to end-to-end latency. Sessions/guards received final concurrency/expiry hardening after this comparison without changing prompts, model options, schemas or successful evidence behavior; the final offline/regression suites exercise those guards.

Raw evidence: [agent-v1-benchmark.json](agent-v1-benchmark.json). Re-running generates fresh random session references, so cross-run prompt hashes can differ; within-run paired hashes must match. Model digests and exact options are recorded for reproduction. Deterministic seeds do not guarantee identical inference across different hardware/server builds.

## Exact local commands

Use the existing root environment, Python 3.13.7. Required packages are already in the hash-locked development requirements (`httpx` 0.28.1 and Pydantic 2.13.3 were used). If synchronizing a local environment:

```sh
.venv/bin/python -m pip install --require-hashes --only-binary=:all: -r backend/requirements-dev.txt
.venv/bin/python -m pip check
```

Ollama must already be running locally with the two requested models installed. No `ollama pull` is part of this milestone. Do not clear deployed markers or force local mode on a hosted application to run these commands.

Interactive Llama session:

```sh
PYTHONPATH=backend .venv/bin/python -m app.agent.cli \
  --model llama3.2:3b \
  --query '0009-0029' \
  --question 'Retrieve historical recall evidence for the exact product I confirm.'
```

Inspect the printed NDC/formulation/provenance and enter its `product_ref` at the confirmation prompt; empty input stops. Omit `--query` to let the model propose the resolver call first. To exercise ambiguity, use `--query 'Xanax 0.25 mg'` and explicitly choose the intended NDC/formulation. Repeat with `--model qwen3.5:4b-q4_K_M` for Qwen. Neither model can confirm on the user's behalf.

Reproduce the comparison:

```sh
PYTHONPATH=backend .venv/bin/python -m app.agent.benchmark \
  --output /tmp/davai-agent-v1-comparison.json --repetitions 2
```

Run all offline checks with the exact commands in the results table. Running the comparison requires local loopback access; the restricted execution sandbox initially could not contact Ollama, while the same read-only local requests succeeded with loopback access. No network-facing application listener or new Ollama server was launched.

## Preservation, limitations and next review

Required verification confirmed the exact frozen SHA256 `87779eda6b06c75f10603762b18f8c66a5cb7b12ed37d47ab1bf9b4825639c71`. Before/after checks confirmed unchanged artifact inode, 4,825,108,480-byte size, modification/change times, permissions and release-metadata SHA256; `publication_validated=false` remains. Existing manual real lookups were reproduced: Xanax returns nine candidates, Xanax 0.25 mg returns two, and exact NDC 0009-0029 returns one. The actual historical record retains D-0161-2016, Class II, Subpotent Drug, AFFECTED_PACKAGE, EXACT_PACKAGE_NDC, UNKNOWN lot scope, PARTIAL coverage and source date 2026-09-25.

Remaining limitations include process-local ephemeral sessions; no authenticated HTTP integration/session lifecycle manager; no cross-process/shared session store or global admission control; conservative denial of unsupported match types/missing provenance; narrow strength parsing; bounded result sets without agent pagination; cold worker verification overhead; no free-form grounded narrative or FAERS tool; and a small deterministic, fixed-order benchmark with narrow hallucination metrics. Any later service integration needs explicit authentication/ownership, concurrency/admission/rate limits, privacy/logging review and independent authorization/ingress acceptance before hosted use. No such infrastructure is implied by this implementation.

**Ready for engineering review of a local backend agent foundation. Not deployment authorization.** The frozen release, hosted-serving guard, Vercel Authentication, Render Maintenance Mode, frontend and unrelated research/ingestion files remain intact.
