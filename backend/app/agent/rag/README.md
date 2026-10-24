# FDA label passage retrieval — offline Phase 1

This is an isolated graduate-project experiment. Neither application API nor the
research workflow imports this package. No model generation, cloud client, new
agent framework, frontend integration, or deployment change is included.

## Boundaries and data

Extraction reuses `FrozenPharmaReleaseRepository`, `get_drug_label_evidence`, and
`validate_card`. The existing consumer eligibility, exact-product label admission,
section state, official source URL and frozen-release checks remain authoritative.
No query selects arbitrary raw labels or promotes withheld ingredient-context labels.

Default selection (explicit exact NDCs, not first name matches):

| Product | NDC | Purpose |
|---|---|---|
| Zepbound | 0002-0152 | Admitted label, 2.5 mg formulation |
| Zepbound | 0002-0243 | Same brand/source label, distinct 5 mg formulation |
| Trulicity | 0002-1433 | Related class, distinct product/source |
| Lipitor | 58151-155 | Different class; absent boxed-warning section |
| Augmentin suspension | 71297-240 | Combination formulation |
| Augmentin ES-600 | 81964-003 | Similar brand, different combination formulation |
| Jardiance | 0597-0152 | Additional interactions and adverse reactions |
| Xanax | 0009-0029 | No admitted exact-product label in this release |

The default extraction measured **229 passages, seven product-associated label
documents, eight exact products**. The two Zepbound formulations deliberately
retain separate product-associated copies of their shared source label. Missing
labels remain missing; this is not a statement that a medication has no warnings.

Six existing safety fields are chunked independently in fixed order. Paragraph
boundaries are preferred, then whitespace, then a hard character limit. Offsets
partition each section without overlap or whitespace normalization: concatenation
reconstructs the original stored text exactly. Defaults are 750 characters per
passage and an extraction guard of 200–500 passages. No source text is truncated
to meet the passage-count guard; extraction fails if the selection exceeds it.

Each passage points to an immutable document key carrying product/NDC/formulation,
strength, dosage form, ingredients, label ID/set/version, admission status,
source ID/record/URL, effective date, source snapshot and release metadata.
The corpus also records the verified release artifact SHA-256. Chunk IDs hash
that document key, section, ordinal, offsets and original text.

All generated corpus/index/report files must be **outside the repository and
outside the configured frozen-release directory**. These artifacts contain derived
pharmaceutical text and are local/private; do not publish or commit them. Existing
publication metadata is not changed. Writers refuse existing output paths.

## Environment and optional dependencies

The measured root `.venv` is Python 3.13.7 on macOS arm64 with NumPy 2.5.4 and
psutil 7.2.2. FAISS, sentence-transformers, transformers and PyTorch were absent;
there was no standard Hugging Face BGE cache. No dependency was installed and no
model downloaded. The runtime/development locks are unchanged. Minimal CI without
NumPy skips this optional experiment's tests rather than importing it into the
application runtime.

`faiss-cpu` publishes macOS arm64 wheels; a compatible published wheel does not
prove resolution or runtime compatibility in this environment. Actual FAISS/BGE
execution remains unverified until separately approved local provisioning.

The BGE adapter follows the [BAAI model card](https://huggingface.co/BAAI/bge-small-en-v1.5):
384 dimensions, bounded 512-token inputs and a query-only retrieval instruction.
It accepts an existing local model directory, requires local-only loading, disables
remote code and network model access, and requests safetensors. It fingerprints
local model files and records package versions. Overlong tokenized passages fail;
they are never silently truncated. A provisioned model still needs verification
against its expected upstream revision; the file fingerprint records what was
used, not proof of model authenticity.

See [FAISS cosine guidance](https://github.com/facebookresearch/faiss/wiki/MetricType-and-distances),
[package wheels](https://pypi.org/project/faiss-cpu/), and
[SentenceTransformer local-file options](https://sbert.net/docs/package_reference/sentence_transformer/model.html).

## Reproduce without installs or downloads

From the repository root, using new output paths:

```bash
PYTHONPATH=backend .venv/bin/python -m app.agent.rag.cli check

PYTHONPATH=backend .venv/bin/python -m app.agent.rag.cli sample \
  --out /private/tmp/dav-ai-label-rag-demo/corpus.json

PYTHONPATH=backend .venv/bin/python -m app.agent.rag.cli evaluate \
  --corpus /private/tmp/dav-ai-label-rag-demo/corpus.json \
  --out /private/tmp/dav-ai-label-rag-demo/sql-report.json

PYTHONPATH=backend .venv/bin/python -m pytest backend/tests/rag -q
```

The following builds a deterministic **test scaffold, not semantic retrieval**:

```bash
PYTHONPATH=backend .venv/bin/python -m app.agent.rag.cli build \
  --corpus /private/tmp/dav-ai-label-rag-demo/corpus.json \
  --embedding mock --engine numpy-test \
  --out /private/tmp/dav-ai-label-rag-demo/mock-index

PYTHONPATH=backend .venv/bin/python -m app.agent.rag.cli query \
  --index /private/tmp/dav-ai-label-rag-demo/mock-index \
  --ndc 0002-0152 --question 'Find label information about birth-control pills.'
```

`--ndc` is an analyst's exact offline sample selection, not an authorization
capability. This CLI must not be exposed as a model-facing or HTTP API. A future
integration would need to resolve the already confirmed server-owned session
binding, preserving the existing opaque-reference boundary.

Only after dependencies and a local model have been separately provisioned with
approval, run the real experiment (there is deliberately no install/pull command):

```bash
PYTHONPATH=backend .venv/bin/python -m app.agent.rag.cli build \
  --corpus /private/tmp/dav-ai-label-rag-demo/corpus.json \
  --embedding bge --engine faiss \
  --model-dir /absolute/path/to/local/bge-small-en-v1.5 \
  --out /private/tmp/dav-ai-label-rag-demo/bge-index

PYTHONPATH=backend .venv/bin/python -m app.agent.rag.cli query \
  --index /private/tmp/dav-ai-label-rag-demo/bge-index \
  --model-dir /absolute/path/to/local/bge-small-en-v1.5 \
  --ndc 71297-240 --question 'Find label evidence about allopurinol and rash.'

PYTHONPATH=backend .venv/bin/python -m app.agent.rag.cli evaluate \
  --corpus /private/tmp/dav-ai-label-rag-demo/corpus.json \
  --index /private/tmp/dav-ai-label-rag-demo/bge-index \
  --model-dir /absolute/path/to/local/bge-small-en-v1.5 \
  --out /private/tmp/dav-ai-label-rag-demo/comparison.json
```

## Index design

Embeddings use `section + newline + original text`, float32 L2 normalization and
exact inner-product ranking. FAISS receives **only rows belonging to the exact
selected product before ranking**. It scores all eligible rows and uses chunk ID
to break exact ties, avoiding global-top-k filtering starvation.

Persistence consists of canonical corpus JSON, a normalized NumPy matrix and a
checksummed/versioned manifest. Loading maps vectors with `mmap_mode='r'` and
`allow_pickle=False`; no pickled object or native untrusted FAISS binary is loaded.
A product's FAISS `IndexFlatIP` is reconstructed lazily in memory and cached.
Queries do not write the index. This is read-only artifact loading, not a claim
that Python objects form an authorization sandbox. First-query ranking latency
includes lazy index construction. Engine/model versions must match, and all row,
chunk, source, text and ordering mappings are validated on load.

Plain nearest-neighbor search does not infer that an answer is absent. An exact
product with no indexed label returns no hits, but a product with labels and no
boxed-warning section can still return other sections. The negative evaluation
case intentionally tests this limitation; returned passages must not be treated
as proof that a question has an answer. Section-aware abstention remains a later
decision to evaluate, not an unmeasured guarantee of this prototype.

## Evaluation protocol and actual measurements

`questions_v1.json` currently contains corpus **label-questions-v1.1**: 21 questions,
19 positive and two missing-evidence cases. Thirteen positives name a section;
six are natural paraphrases. Coverage includes all requested safety categories,
same-brand strengths and related combination products.

Judgments were selected by direct source reading, independent of retrieval output,
then frozen as source-record/section/character spans and text hashes. The original
15-case SQL pilot was retained separately; six paraphrases were added before any
semantic-model run. These are **single-assessor, minimal support annotations**,
not independent human/clinical review or exhaustive passage relevance judgments.
External review and more complete judgments are needed before strong academic
claims; unannotated supporting passages can depress measured precision.

Comparators:

1. `sql_native_first5`: existing admitted SQL label-section evidence, expanded in
   fixed document/section/chunk order and capped at five **for measurement**. The
   actual application returns full sections, so this is not a score of its full
   evidence coverage or user-facing correctness.
2. `sql_keyword_sections`: an explicitly new, transparent section-keyword router
   over the same SQL evidence. This avoids comparing semantic retrieval only to
   arbitrary passage order. It is not installed in the existing workflow.
3. `faiss_bge`: real local BGE+FAISS, **not run**. The evaluator refuses mock indexes
   as semantic comparison results.

Measured on 2026-10-23; one trial per question, no model inference:

| Method | Recall@5 | Precision@5 | MRR@5 | Product containment | Empty-evidence cases | Median query |
|---|---:|---:|---:|---:|---:|---:|
| SQL native first-five projection | 0.1053 | 0.0211 | 0.1053 | 100% (100 returned passages) | 1/2 | 2.420 ms |
| SQL keyword sections | 0.6842 | 0.1368 | 0.5789 | 100% (68 returned passages) | 2/2 | 2.003 ms |
| FAISS + BGE | Not measured | Not measured | Not measured | Not measured | Not measured | Not measured |

Keyword recall was 13/13 on section-explicit questions and 0/6 on paraphrases.
The first native SQL query took **2.475 s**, including cold release verification;
subsequent measurements used the warmed process. Baselines ran sequentially;
these one-trial latency observations are not controlled performance comparisons.

Metric definitions: positives only for Recall@5, Precision@5 and reciprocal rank
truncated at five; precision always divides by five. Missing-evidence cases are
reported separately, not assigned perfect recall. Product containment counts
correct-product returned passages divided by all returned passages and is not
natural-language product-resolution accuracy. No-result identity is undefined.

Other observed measurements:

- Extraction: **7.810 s**, corpus **558,087 bytes**.
- Mock-only index: **617,323 bytes**, **0.0265 s** initial build; second build had
  byte-identical corpus, normalized vectors and manifest. These are scaffold
  measurements, not BGE timing or semantic index size.
- SQL evaluation process lifetime peak RSS: **66,289,664 bytes**. This includes
  imports, corpus loading and both SQL baselines; no per-method memory claim.
- Semantic query latency, embedding latency, index size and model memory: **not measured**.

Local artifacts from this run are under `/private/tmp/dav-ai-rag-phase1/`:
`corpus-v1.json`, `mock-index-v1/`, and `sql-evaluation-v1.1.json`. They remain
outside source control and are not authorized for publication. Temporary paths
may be removed by the operating system; the commands above regenerate them.

## Recommendation

**Revise/continue the offline evaluation; do not integrate into research yet.**
The paraphrase failures make a bounded semantic comparison worth testing, but
there is no measured semantic improvement. Review the annotations independently,
then, only with provisioning approval, run BGE/FAISS on this fixed question set.
Proceed toward a later hybrid integration only if paraphrase retrieval improves
while exact-product containment and missing-evidence handling remain correct.
Otherwise retain SQL and the simpler section-routing option. No new infrastructure
or generation model is justified by this milestone.
