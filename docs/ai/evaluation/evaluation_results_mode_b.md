# Dav AI — Agent Evaluation Report (FROZEN_DATA)

- **Evaluation Version:** `agent-eval-v1`
- **Corpus Version:** `1.0.0`
- **Run ID:** `run_mode_b_1792700490`
- **Execution Timestamp (UTC):** `2026-10-22T20:17:34.372429+00:00`
- **Evaluation Mode:** `frozen_data`
- **Release ID:** `dav-ai-pharma-v1-phase4b-communications-20261006`
- **Publication Authorized:** `False` (Frozen gate preserved)

## 1. Executive Summary

| Metric | Value | Denominator | Notes |
|---|---|---|---|
| **Overall Benchmark Pass Rate** | 100.0% | 23/23 trials | Verified deterministic assertions |
| **Total Evaluation Duration** | 236.55s | 23 trials | Total elapsed run time |

## 3. Category Breakdown and Failure Taxonomy

| Category | Cases Tested | Passed | Failed | Common Reason / Guardrail Action |
|---|---|---|---|---|
| `ambiguous_search` | 2 | 2 | 0 | All passed (nominal) |
| `empty_unavailable_evidence` | 3 | 3 | 0 | All passed (nominal) |
| `exact_ndc_resolution` | 2 | 2 | 0 | All passed (nominal) |
| `incomplete_plan_completion` | 1 | 1 | 0 | All passed (nominal) |
| `missing_exact_label` | 1 | 1 | 0 | All passed (nominal) |
| `multi_ingredient_product` | 1 | 1 | 0 | All passed (nominal) |
| `partial_recall_coverage` | 2 | 2 | 0 | All passed (nominal) |
| `same_ingredient_different_ndc` | 1 | 1 | 0 | All passed (nominal) |
| `single_source_faers` | 2 | 2 | 0 | All passed (nominal) |
| `single_source_label` | 2 | 2 | 0 | All passed (nominal) |
| `single_source_recall` | 2 | 2 | 0 | All passed (nominal) |
| `three_source` | 2 | 2 | 0 | All passed (nominal) |
| `two_source` | 2 | 2 | 0 | All passed (nominal) |

## 4. Case-by-Case Detailed Audit

| Case ID | Category | Status | Expected Status | Exact Plan | Schema Valid | Guardrail Enforced | Latency | Pass/Fail |
|---|---|---|---|---|---|---|---|---|
| `case_01_exact_ndc_xanax` | `exact_ndc_resolution` | `confirmation_required` | `confirmation_required` | Yes | Yes | Yes | 5.26s | **PASS** |
| `case_02_exact_ndc_zepbound` | `exact_ndc_resolution` | `confirmation_required` | `confirmation_required` | Yes | Yes | Yes | 4.37s | **PASS** |
| `case_03_ambiguous_brand_xanax` | `ambiguous_search` | `confirmation_required` | `confirmation_required` | Yes | Yes | Yes | 4.56s | **PASS** |
| `case_04_ambiguous_brand_strength_xanax` | `ambiguous_search` | `confirmation_required` | `confirmation_required` | Yes | Yes | Yes | 4.30s | **PASS** |
| `case_05_same_ingredient_diff_ndc_alprazolam` | `same_ingredient_different_ndc` | `confirmation_required` | `confirmation_required` | Yes | Yes | Yes | 3.26s | **PASS** |
| `case_06_single_source_label_zepbound` | `single_source_label` | `partial` | `partial` | Yes | Yes | Yes | 9.89s | **PASS** |
| `case_07_single_source_label_trulicity` | `single_source_label` | `partial` | `partial` | Yes | Yes | Yes | 10.43s | **PASS** |
| `case_08_single_source_recall_xanax` | `single_source_recall` | `partial` | `partial` | Yes | Yes | Yes | 10.85s | **PASS** |
| `case_09_single_source_recall_trulicity` | `single_source_recall` | `partial` | `partial` | Yes | Yes | Yes | 12.26s | **PASS** |
| `case_10_single_source_faers_alprazolam` | `single_source_faers` | `completed` | `completed` | Yes | Yes | Yes | 10.07s | **PASS** |
| `case_11_single_source_faers_dulaglutide` | `single_source_faers` | `partial` | `partial` | Yes | Yes | Yes | 9.16s | **PASS** |
| `case_12_two_source_labels_recalls_trulicity` | `two_source` | `partial` | `partial` | Yes | Yes | Yes | 13.10s | **PASS** |
| `case_13_two_source_recalls_faers_xanax` | `two_source` | `partial` | `partial` | Yes | Yes | Yes | 15.35s | **PASS** |
| `case_14_three_source_trulicity` | `three_source` | `partial` | `partial` | Yes | Yes | Yes | 19.21s | **PASS** |
| `case_15_three_source_xanax` | `three_source` | `partial` | `partial` | Yes | Yes | Yes | 17.73s | **PASS** |
| `case_16_missing_exact_label_xanax` | `missing_exact_label` | `partial` | `partial` | Yes | Yes | Yes | 8.25s | **PASS** |
| `case_17_partial_recall_coverage_xanax` | `partial_recall_coverage` | `partial` | `partial` | Yes | Yes | Yes | 8.28s | **PASS** |
| `case_18_partial_recall_coverage_trulicity` | `partial_recall_coverage` | `partial` | `partial` | Yes | Yes | Yes | 9.09s | **PASS** |
| `case_19_empty_recall_coverage_zepbound` | `empty_unavailable_evidence` | `partial` | `partial` | Yes | Yes | Yes | 10.84s | **PASS** |
| `case_20_empty_faers_analytics_zepbound` | `empty_unavailable_evidence` | `partial` | `partial` | Yes | Yes | Yes | 10.25s | **PASS** |
| `case_21_empty_label_and_recall_emgality` | `empty_unavailable_evidence` | `partial` | `partial` | Yes | Yes | Yes | 16.29s | **PASS** |
| `case_22_multi_ingredient_janumet_xr` | `multi_ingredient_product` | `completed` | `completed` | Yes | Yes | Yes | 8.85s | **PASS** |
| `case_34_incomplete_plan_auto_mode` | `incomplete_plan_completion` | `partial` | `partial` | Yes | Yes | Yes | 12.40s | **PASS** |

## 5. Engineering Limitations and Boundaries

> [!NOTE]
> Mode B performs direct read-only fidelity checks between agent evidence cards and SQLite stored records. Does not call external FDA APIs.

- **No External Live APIs:** The evaluation operates entirely air-gapped on the frozen SQLite dataset.
- **Separate Model Planning from Backend Completion:** Model planning accuracy is reported independently from overall workflow completion.
- **Guardrail Distinctions:** Rejected adversarial prompts are counted as security successes when the backend properly blocks execution without leakage.

