# Phase 1C experiment record

**Decision: REVISE before application integration.** Literal section availability
fixes the missing-section substitution defect. Routing preserves the original
benchmark's six semantic paraphrase recoveries and fixes both BGE summary misses.
Held-out recall improves over SQL keyword retrieval but equals BGE. Open-ended
unsupported questions can still retrieve irrelevant candidates. No retrieved text
is a verified answer; there is no generator or active application integration.

## Changed files in this phase

- `backend/app/agent/rag/index.py`: optional section filter, applied together with
  exact product membership **before** FAISS ranking; independent cached shards.
  Default behavior and persisted index format remain unchanged.
- `backend/app/agent/rag/hybrid.py`: isolated decision layer and fixed RRF ablation.
- `backend/app/agent/rag/hybrid_evaluation.py`: source-judgment validation and
  separately denominated ranking, abstention, and containment measurements.
- `backend/app/agent/rag/heldout_v1.json`: new frozen source-span questions.
- `backend/tests/rag/test_hybrid.py`: synthetic regression and evaluator tests.
- `backend/app/agent/rag/PHASE1C.md`: this report and reproduction instructions.

Previous-phase files and unrelated working-tree changes are preserved. The
original `questions_v1.json`, corpus text/chunk IDs, vectors, model, frozen release,
application APIs/workflow/frontend and authorization/deployment gates are unchanged.
No packages were installed and no model was downloaded in this phase.

## Decision layer

Inputs are a previously selected **exact product ID**, a question, a validated
corpus, and optional read-only index/local embedder. This offline interface is
not an authorization API. It does not resolve names or create/replace confirmed
sessions and must not be exposed directly as an HTTP/model-facing tool.

1. Validate the question and exact sampled product. Reject a conflicting literal
   NDC. Name ambiguity is not treated as permission to switch products.
2. Reject a small documented set of obvious requests outside the frozen-label
   scope: current/future information, fabricated claims, individual risk/dose,
   and personal treatment decisions. These lexical guards are intentionally
   incomplete and are **not** a general medical safety classifier.
3. Re-read admitted SQL evidence through `get_drug_label_evidence`. Require exact
   product/NDCs, admitted label membership, full `LabelRecord` and `ReleaseInfo`
   equality with the corpus, including source identity/provenance and section
   states. Source failure/inconsistency yields structured insufficient evidence.
4. Recognize only literal section names: boxed/black-box warning;
   contraindications; drug interactions/interactions section; adverse reactions;
   warnings and precautions/precautions section; warnings section. The regexes
   in `SECTION_ALIASES` are the complete mapping. Clinical concepts such as family
   cancer history, allergy, or side effects alone do not imply a named section.
5. Check all explicitly requested sections before calling embeddings. An absent
   section or admitted label yields `insufficient_evidence`, a reason and missing
   section list, with no substituted passages. Absence refers only to this frozen
   admitted evidence, not to all possible medical knowledge or label versions.
6. **Primary hybrid (`route`)**: explicit sections use their deterministic SQL
   chunk order, capped at five. Multiple explicit sections are interleaved fairly.
   Open-ended questions use exact-product BGE top five. There is no calibrated
   similarity threshold: all hits are `candidates`, `verified_answer=false`,
   `confidence=uncalibrated`, requiring relevance review.
7. **Ablation (`rrf`)**: equal reciprocal rank fusion, constant 60, depth 20 per
   channel, stable chunk-ID tiebreak. Its SQL channel uses explicit section order
   or the original fixed section order for open questions. Semantic rows are
   restricted to product and requested sections before ranking. It is not a
   BM25/full-text lexical engine; no such architecture was introduced.

Missing/corrupt index or unavailable embeddings allow deterministic, validated SQL
fallback only for explicit sections. Open-ended queries fail closed. Invalid
model/corpus metadata, nonfinite/unknown/duplicate hits or any foreign-product hit
invalidate the whole semantic result. Existing opaque application session
references and confirmation controls remain outside this experiment and unchanged.

## Held-out annotation protocol

`heldout_v1.json` contains **32 questions: 20 positive, 12 negative**. Explicit
and semantic groups each contain 10 positives and 6 negatives. The positives
cover ten new facts with paired literal-section and paraphrased wording. They
exercise thyroid-symptom warnings, allergy contraindications, renal injury,
digoxin, age-related muscle injury, cholestatic jaundice, probenecid, ES-600 adverse
reactions, and Jardiance volume depletion/ketoacidosis. Similar combination brands
and two Zepbound strengths retain their separate NDC/product bindings.

Negative cases comprise four absent boxed warnings, two no-admitted-label Xanax
queries, a fabricated warning request, a conflicting formulation NDC, current
recalls, an individual-risk request, and two unsupported medical topics (migraine
aura prevention with Lipitor and methemoglobinemia with Jardiance). The last two
are deliberate challenges to generic nearest-neighbor search; they contain no
lexical out-of-scope marker recognized by the policy.

Settings/code hashes were frozen at **2026-10-24 03:50:17 UTC**, before held-out
annotation and retrieval. Annotations were authored by direct source reading,
using source-record/section/character spans and text SHA-256; unsupported-topic
terms are checked absent in every indexed section of the exact product. The
complete dataset was then hashed before its first evaluation. No thresholds were
tuned and no settings or annotations were changed after seeing held-out results.

**Limitation:** these are single-assessor, retrieval-blind annotations, not
independent human/clinical review. The original 21 questions are unchanged and
separate. This is question holdout on the same corpus, not unseen-product/source
validation. Paired positive questions share facts; 20 questions are not 20
independent clinical facts. Minimal support spans are not exhaustive relevance
judgments, so reported precision is annotation-set precision. Topic absence checks
do not establish the clinical absence of an effect. Independent relevance review
remains necessary before integration or strong academic claims.

## Measured comparisons

Real, already cached BGE + FAISS; three trials with identical ranked IDs, without
network access. Recall, precision and MRR are macro means over positives only;
MRR is truncated at five and precision always divides by five. SQL native is a
first-five projection of an API that actually returns full sections, not a score
of full API evidence coverage. The SQL keyword baseline is unchanged, including
its narrower spelling support (`black-box` does not match its `black box` rule).

Original benchmark: **19 positive, 2 negative**.

| Method | Recall@5 | Precision@5 | MRR@5 | Exact-product results | Negative abstentions |
|---|---:|---:|---:|---:|---:|
| SQL native | 0.1053 | 0.0211 | 0.1053 | 100/100 | 1/2 |
| SQL keyword | 0.6842 | 0.1368 | 0.5789 | 68/68 | 2/2 |
| BGE | 0.8947 | 0.1789 | 0.6667 | 100/100 | 1/2 |
| Hybrid routing (primary) | **1.0000** | **0.2000** | **0.8158** | 68/68 | 2/2 |
| Hybrid RRF (ablation) | 0.8947 | 0.1789 | 0.5140 | 68/68 | 2/2 |

Held-out benchmark: **20 positive, 12 negative**.

| Method | Recall@5 | Precision@5 | MRR@5 | Exact-product results | Missing-section abstention | False abstention | Unsupported candidates |
|---|---:|---:|---:|---:|---:|---:|---:|
| SQL native | 0.2500 | 0.0500 | 0.2000 | 150/150 | 1/5 | 0/20 | 6/6 |
| SQL keyword | 0.6000 | 0.1300 | 0.5500 | 129/129 | 1/5 | 0/20 | 5/6 |
| BGE | 0.9000 | 0.2000 | 0.7917 | 150/150 | 1/5 | 0/20 | 6/6 |
| Hybrid routing (primary) | **0.9000** | **0.2000** | **0.7917** | 94/94 | **5/5** | **0/20** | **2/6** |
| Hybrid RRF (ablation) | 0.9000 | 0.1900 | 0.6725 | 94/94 | 5/5 | 0/20 | 2/6 |

Missing-section abstention measures the four direct missing-boxed-warning
requests plus the explicit no-label Xanax request. The fabricated-warning request
is scored under unsupported scope, to keep denominators disjoint. False abstention
means empty retrieval on a positive question; it does **not** mean correct passage
retrieval. Unsupported-evidence acceptance is a conservative **retrieval proxy**:
any nonempty candidate set on an annotated unsupported scope/topic or foreign-product
question counts as acceptance, even when explicitly marked unverified. Thus the
primary hybrid's rate is **33.33% (2/6)**. Across *all* negative questions, its
candidate return rate is **16.67% (2/12)**, versus SQL native 10/12, SQL keyword
9/12 and BGE 10/12. No method generates verified answers in this experiment;
that structural property is not counted as perfect relevance or abstention.

Held-out positive subgroup metrics (ten questions per group):

| Method | Explicit R/P/MRR@5 | Semantic R/P/MRR@5 |
|---|---|---|
| SQL native | 0.2000 / 0.0400 / 0.1500 | 0.3000 / 0.0600 / 0.2500 |
| SQL keyword | 0.9000 / 0.2000 / 0.8500 | 0.3000 / 0.0600 / 0.2500 |
| BGE | 0.9000 / 0.2000 / 0.8500 | 0.9000 / 0.2000 / 0.7333 |
| Hybrid routing | 0.9000 / 0.2000 / 0.8500 | 0.9000 / 0.2000 / 0.7333 |
| Hybrid RRF | 1.0000 / 0.2200 / 0.9333 | 0.8000 / 0.1600 / 0.4117 |

All groups/methods have 100% returned-product containment and zero positive
false abstentions. For the six explicit negatives, the five missing-section cases
are handled by the primary hybrid, as is the one fabricated-warning case. In the
semantic group, two of five unsupported requests return candidates (40%); the
sixth negative is no-label Xanax and correctly returns none. The original-set
subgroup and all per-question results are in the external JSON/CSV artifacts.

## Regression and error analysis

- Original **q06 Trulicity summary**: BGE gold rank 35/38 globally, 18/19 within
  adverse reactions; keyword and primary hybrid rank 2. Postmarketing/table
  passages outrank the annotated common-event summary. Section restriction alone
  is insufficient, and equal RRF still excludes that summary from its top five.
- Original **q09 Lipitor summary**: BGE gold rank 6/38 globally and 6/11 within
  adverse reactions; keyword and primary hybrid rank 1, RRF rank 3. No annotation
  was expanded to make BGE score better.
- Primary hybrid retains all six original paraphrase hits at ranks 1,1,2,2,1,2.
  RRF loses q18 and lowers semantic reciprocal ranks. There is no evidence for
  selecting equal-weight RRF over primary routing.
- Held-out primary misses **h04** (kidney-injury explanation occurs late in the
  long Trulicity warnings section, outside SQL's first five passages) and **h11**
  (Zepbound throat/voice symptoms). BGE misses h09 and h11; the primary hybrid
  exchanges BGE's adverse-event miss for a late-section miss. RRF improves explicit
  retrieval but loses semantic cases h12/h13. No post-test tuning was applied.
- Held-out **h30/h31** return Lipitor/Jardiance passages without supporting the
  requested migraine/methemoglobinemia topics. Correct product containment does
  not imply question relevance. These remain unverified candidates, but a future
  answer-producing integration must abstain or verify support before using them.

## Latency, memory and artifacts

Warm wall-clock query latency, pooled across three trials (96 held-out queries
per method), median / nearest-rank p95. It includes SQL/source validation in the
hybrid, plus model inference where used. Negative guard requests are included;
this distribution differs from the positives-only model workload.

| Method | Original median / p95 ms | Held-out median / p95 ms |
|---|---:|---:|
| SQL native | 2.023 / 3.387 | 2.037 / 2.460 |
| SQL keyword | 1.940 / 2.081 | 1.998 / 2.232 |
| BGE | 6.470 / 8.062 | 6.033 / 7.949 |
| Hybrid routing | 2.091 / 9.694 | 2.210 / 10.316 |
| Hybrid RRF | 8.656 / 10.443 | 8.347 / 10.917 |

RSS before model: **98.22 MiB**; after model/index loading: **315.94 MiB**;
sampled and OS lifetime peak: **333.59 MiB (349,798,400 bytes)**. Sampling interval
10 ms; this is one shared process running all methods/trials, not isolated
per-method memory or an allocation estimate. Load time was 0.2024 s, with cached
local files. The unchanged persisted index occupies **911,051 bytes**, including
corpus, vectors and manifest. No new index/model artifacts were written inside
the repository or release. No performance claim beyond this small warmed run.

External artifacts: `/private/tmp/dav-ai-rag-phase1c/results-v1/` contains
`original.json`, `heldout.json`, all three trials, both per-question CSVs,
`failure-analysis.json`, `reproducibility.json` and `requirements.lock`.
`/private/tmp/dav-ai-rag-phase1c/` also contains the pre-run policy/dataset freeze,
source annotation review, annotation-construction script and experiment runner.
These are local experiment artifacts; temporary directories can be reclaimed by
the operating system. Preserve them externally if retaining the run is important.

## Reproduce with the provisioned environment

Run from the repository root; output must be a **new** external directory:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend \
  /private/tmp/dav-ai-rag-phase1b/venv/bin/python \
  /private/tmp/dav-ai-rag-phase1c/run_experiment.py \
  --out /private/tmp/dav-ai-rag-phase1c/results-repeat

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend \
  /private/tmp/dav-ai-rag-phase1b/venv/bin/python \
  -m pytest backend/tests/rag -q

PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest backend/tests -q
```

The runner reuses the Phase 1B local `fastembed_adapter.py`, pinned model manifest
and read-only index. It forbids Python socket connects, enables Hugging Face
offline/local-files-only mode, validates the policy/code/dataset freeze and index
checksums, validates all gold spans before retrieval, runs three identical-ranking
trials, and records exact dependency/model/index metadata. There is no install or
model-pull step. A different machine needs those already provisioned external
artifacts; the Phase 1 corpus CLI documented in README regenerates the same sample
without changing the release. The index is reused, not unnecessarily rebuilt.

Key reproducibility identifiers:

- Python 3.13, macOS ARM64; FAISS 1.15.1, FastEmbed 0.9.0, ONNX Runtime 1.31.0,
  NumPy 2.5.4, Tokenizers 0.23.3, Pydantic 2.13.3. Full exact environment is locked
  in the external report. Existing main environment is untouched.
- Model `BAAI/bge-small-en-v1.5`, FastEmbed's **quantized ONNX Qdrant export**
  `Qdrant/bge-small-en-v1.5-onnx-Q`, revision
  `aa8f8b060edb00e03bfdd08813a2949946c8ba55` (same as Phase 1B).
  CPU provider, one thread, CLS pooling, normalized float32 vectors, query prefix
  `Represent this sentence for searching relevant passages: `, 512-token budget.
- Index `product-flat-ip-v1`, exact `IndexFlatIP`, no ANN training, product/section
  membership selected before scoring, stable chunk-ID tie-break. Python/NumPy/ORT
  seeds 0; no random index seed required.
- Corpus SHA-256:
  `2e05404bc7daff640b8bb85ab98de7c5358924558ae0063910bbb762fe0cf166`.
- Index ID:
  `39ca55fefa5c1d069262636258741e5103ee242ab35b5358635cf8ccb7bec59f`.
- Original 21-question file SHA-256 (unchanged):
  `953a7623d291a487125b20d0079bba75a952401932857b4bd06f313e29ad4f33`.
- Held-out file SHA-256:
  `cd73389a8a78deab003f6957007e139365c460cb2f839dc66e3fc7917449f319`.
- Policy SHA-256:
  `e50d51542b9f58de698945760d23dc006f87819469086e4cc0d4f79a9f43f735`.

## Verification and integration decision

- Isolated real-FAISS RAG suite: **43 passed**, including 21 new tests covering
  missing boxed warnings/no label, section-before-ranking starvation, product and
  formulation containment, source/index/model metadata inconsistency, corruption,
  missing index/embeddings, deterministic fallback/fusion, multi-section requests,
  annotation validation and honest unsupported-candidate scoring.
- Broad backend suite: **1,019 passed, 29 skipped**, one existing Starlette/httpx
  deprecation warning. Seven optional frozen-release integration checks passed;
  this is not a deployment/required-integration gate.
- The initial sandboxed broad run had 26 `PermissionError` failures from denied
  localhost binds (988 passed, 29 skipped at that point, before five final added
  tests). The final full rerun with temporary localhost permission passed.
  Two real-FAISS tests are among the main environment skips; all run in the
  isolated RAG environment. No frontend code changed in this phase.

**REVISE**: retain this offline routing prototype. It earns further study over
keyword-only retrieval, but held-out evidence does not show a ranking gain over
BGE alone, equal RRF is unhelpful overall, and unsupported semantic topics still
return irrelevant text. Before integration, obtain independent relevance review
and evaluate a support/abstention check on a separate development set, then freeze
it before a new held-out evaluation. Do not tune on `heldout_v1.json` or claim that
an uncalibrated cosine score verifies an answer. Existing application research
continues to use its established workflow.
