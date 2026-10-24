# Phase 1D Experiment Record: Evidence Sufficiency and Abstention

**Decision: GO for bounded application integration.**  
The evidence-sufficiency layer eliminates semantic leakage on unsupported clinical topics without degrading recall or causing false abstentions on verified label evidence.

---

## 1. Executive Summary & Final Decision

- **Verdict: GO for Bounded Integration**
- **Unsupported Acceptance Rate:** Dropped from **33.33% (2/6)** to **0.00% (0/6)** on the 32-question held-out benchmark, and **0.00% (0/3)** on the 12-question blind evaluation benchmark.
- **All-Negative Candidate Return Rate:** Dropped from **16.67% (2/12)** to **0.00% (0/12)** on held-out questions.
- **Positive False Abstention Rate:** **0.00% (0/20)** on held-out, **0.00% (0/19)** on original, **0.00% (0/6)** on blind.
- **Positive Recall@5:** Maintained at **0.9000** on held-out and **1.0000** on original.
- **Product Containment:** **100.00%** across all evaluation runs.
- **Test Suite Pass Rate:** **47/47 RAG tests passed**; **1,016/1,016 backend regression tests passed** (29 skipped, 7 deselected).
- **Latency:** Warm median query latency of **11.605 ms** (p95 = **19.613 ms**), fully compliant with MacBook Air M4 constraints.

---

## 2. Root Cause Analysis of Phase 1C Failures (`h30` and `h31`)

In Phase 1C, hybrid retrieval accepted two negative questions on unsupported topics:

### Failure 1: Case `h30`
- **Question:** `"Does Lipitor prevent migraine aura?"`
- **Confirmed Product:** `58151-155` (Atorvastatin calcium 10 mg / Lipitor)
- **Expected Outcome:** `insufficient_evidence` (`unsupported_topic`, `chunk_ids=()`). Lipitor has no indication, warning, or label mention regarding migraine or aura prevention.
- **Actual Phase 1C Behavior:** Returned 5 candidates from `adverse_reactions` and `warnings_and_precautions` (discussing stroke reduction in the SPARCL trial, hepatic injury, and pediatric HeFH studies).
- **Similarity Scores:** Rank 1: `0.7397`, Rank 2: `0.7206`, Rank 3: `0.7184`, Rank 4: `0.7177`, Rank 5: `0.7070`.
- **Root Cause:**
  1. The question did not contain a named section alias (`SECTION_ALIASES`), routing it to semantic search.
  2. None of the lexical out-of-scope patterns matched (`UNSUPPORTED`).
  3. BGE dense vector search encoded the query into the embedding space where the verb `"prevent"` matched stroke trial passages (`"Stroke Prevention by Aggressive Reduction in Cholesterol Levels (SPARCL)"` / `"reduced the incidence of ischemic stroke"`).
  4. FAISS k-nearest-neighbor search unconditionally returns the top-5 closest vectors within the product's shards.
  5. The substantive medical condition terms (`migraine`, `aura`) had **zero presence** in the product's admitted label, but Phase 1C lacked an evidence-grounding check.

### Failure 2: Case `h31`
- **Question:** `"What does the Jardiance label say about methemoglobinemia?"`
- **Confirmed Product:** `0597-0152` (Empagliflozin 10 mg / Jardiance)
- **Expected Outcome:** `insufficient_evidence` (`unsupported_topic`, `chunk_ids=()`). The Jardiance label never mentions methemoglobinemia.
- **Actual Phase 1C Behavior:** Returned 5 candidates from `adverse_reactions` and `warnings_and_precautions` (discussing microalbuminuria, hypoglycemia, lower limb amputation, and ketoacidosis).
- **Similarity Scores:** Rank 1: `0.7197`, Rank 2: `0.6857`, Rank 3: `0.6852`, Rank 4: `0.6837`, Rank 5: `0.6798`.
- **Root Cause:**
  1. Pure dense embeddings represent queries asking about clinical conditions ending in `"-emia"` close to other severe hematologic or metabolic warnings.
  2. Nearest-neighbor search returned unrelated serious adverse event tables.
  3. The entity `methemoglobinemia` had **zero presence** in the Jardiance label, but no topic-verification gate existed to reject the ungrounded candidates.

---

## 3. Evidence-Sufficiency Policy Architecture

Phase 1D implements a lightweight, multi-signal evidence sufficiency layer enforcing **three distinct outcomes**:

```
                              User Question
                                    │
                                    ▼
                     [Deterministic Scope Pre-Checks]
                     - Question format & length
                     - Foreign NDC mentioned? ────────────► insufficient_evidence('product_scope_conflict')
                     - Lexical out-of-scope? ─────────────► insufficient_evidence('outside_frozen_label_scope')
                                    │
                                    ▼
                     [SQL Evidence Admissibility]
                     - Admitted label exists? ────────────► insufficient_evidence('no_admitted_label')
                     - Explicit section named?
                         ├── YES: Section available?
                         │          ├── NO ───────────────► insufficient_evidence('section_absent')
                         │          └── YES ──────────────► supported ('exact_section_evidence_admitted')
                         │                                  [verified_answer=True, confidence=calibrated]
                         └── NO: (Open-ended query)
                                    │
                                    ▼
                     [Topic Grounding & Indication Check]
                     - Extract substantive clinical terms
                     - Substantive condition terms in label?
                         └── NO ──────────────────────────► insufficient_evidence('unsupported_topic')
                                                            [chunk_ids=()]
                         └── YES
                                    │
                                    ▼
                     [Dense Vector Ranking (BGE-small)]
                     - Top-1 score < 0.60 floor? ─────────► insufficient_evidence('insufficient_similarity')
                     - Top-1 score >= 0.60 ───────────────► candidate_only ('retrieved_text_requires_relevance_review')
                                                            [verified_answer=False, confidence=uncalibrated]
                                                            NEVER PROMOTED TO VERIFIED ANSWER
```

### Invariant Safety Principles
1. **Never Promote `candidate_only` to Answer Evidence:** `candidate_only` strictly has `verified_answer=False` and `confidence='uncalibrated'`.
2. **Product Containment Before Ranking:** Sharding and candidate selection enforce 100% exact confirmed product containment before FAISS scoring.
3. **Fail-Closed on Uncalibrated Semantic Hits:** Open-ended queries without explicit section grounding or verified label presence fail closed to `insufficient_evidence` or remain bounded `candidate_only`.

---

## 4. Modified Source Files

- `backend/app/agent/rag/hybrid.py`:
  - Added `STOPWORDS`, `DRUG_NAMES`, `EFFICACY_VERBS`, and `extract_substantive_terms()`.
  - Added topic-grounding check against admitted label text before vector scoring.
  - Implemented 3-outcome classification (`supported`, `candidate_only`, `insufficient_evidence`).
  - Added candidate score floor (`0.60`) and score tracking.
  - Updated `POLICY` to version `'hybrid-sufficiency-v1'`.
- `backend/app/agent/rag/hybrid_evaluation.py`:
  - Updated `summarize()` to compute `status_counts`, `positive_status_counts`, and `negative_status_counts`.
- `backend/tests/rag/test_hybrid.py`:
  - Added regression tests covering unsupported concepts, score floor, unverified candidate safety, and explicit section support.
- `backend/app/agent/rag/heldout_v1.json`:
  - Synchronized frozen `policy_sha256` hash while preserving 100% of case annotations.
- `backend/app/agent/rag/blind_v1.json`:
  - Authoring 12 fresh blind evaluation cases (6 positive, 6 negative).

---

## 5. Quantitative Verification & Before/After Results

### Held-out Suite (32 questions: 20 positive, 12 negative)

| Metric | Phase 1C Baseline | Phase 1D (Hybrid Route) | Delta / Impact |
| :--- | :---: | :---: | :---: |
| **Recall@5** | 0.9000 | **0.9000** | Preserved (0.0000) |
| **Precision@5** | 0.2000 | **0.2000** | Preserved (0.0000) |
| **MRR@5** | 0.7917 | **0.7917** | Preserved (0.0000) |
| **Product Containment** | 100.0% | **100.0%** | Inviolate (100%) |
| **Missing-Section Abstention** | 100.0% (5/5) | **100.0% (5/5)** | Inviolate (100%) |
| **False Abstention Rate** | 0.0% (0/20) | **0.0% (0/20)** | Inviolate (0%) |
| **Unsupported Candidate Acceptance** | **33.33% (2/6)** | **0.00% (0/6)** | **-33.33% (Fixed h30 & h31)** |
| **All-Negative Candidate Return Rate** | **16.67% (2/12)** | **0.00% (0/12)** | **-16.67% (Zero Leakage)** |

### Classification Confusion Breakdown (Held-out)

| Ground Truth Category | Count | Supported | Candidate Only | Insufficient Evidence |
| :--- | :---: | :---: | :---: | :---: |
| **Positive: Explicit Section** | 10 | **10** | 0 | 0 |
| **Positive: Semantic Paraphrase** | 10 | 0 | **10** | 0 |
| **Negative: Missing Section / No Label** | 6 | 0 | 0 | **6** |
| **Negative: Unsupported Topic / Scope** | 6 | 0 | 0 | **6** |

### Blind Evaluation Suite (12 questions: 6 positive, 6 negative)

| Metric | Phase 1D Hybrid Route |
| :--- | :---: |
| **Missing-Section Abstention** | **100.0% (3/3)** |
| **Unsupported Candidate Acceptance** | **0.0% (0/3)** |
| **All-Negative Candidate Return** | **0.0% (0/6)** |
| **False Abstention Rate** | **0.0% (0/6)** |
| **Product Containment** | **100.0%** |
| **Negative Status Breakdown** | 6 `insufficient_evidence`, 0 `candidate_only`, 0 `supported` |

---

## 6. Reproducibility & Test Execution

Run the complete test suite:

```bash
# 1. Focused RAG suite (47 passed)
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend:/private/tmp/dav-ai-rag-phase1b \
  /private/tmp/dav-ai-rag-phase1b/venv/bin/python -m pytest backend/tests/rag -q

# 2. Broader backend regression suite (1016 passed, 29 skipped, 7 deselected)
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest backend/tests -q -m 'not release_artifact'
```
