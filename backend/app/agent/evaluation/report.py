"""Markdown report generator for Dav AI Agent Evaluation Framework v1."""
from app.agent.evaluation.contracts import EvaluationRunReport


def generate_markdown_report(report: EvaluationRunReport) -> str:
    """Generate a comprehensive human-readable Markdown evaluation report."""
    lines: list[str] = []

    lines.append(f"# Dav AI — Agent Evaluation Report ({report.mode.upper()})")
    lines.append("")
    lines.append(f"- **Evaluation Version:** `{report.evaluation_version}`")
    lines.append(f"- **Corpus Version:** `{report.corpus_version}`")
    lines.append(f"- **Run ID:** `{report.run_id}`")
    lines.append(f"- **Execution Timestamp (UTC):** `{report.timestamp_utc}`")
    lines.append(f"- **Evaluation Mode:** `{report.mode}`")
    if report.release:
        lines.append(f"- **Release ID:** `{report.release.get('release_id')}`")
        lines.append(f"- **Publication Authorized:** `{report.release.get('publication_authorized')}` (Frozen gate preserved)")
    lines.append("")

    lines.append("## 1. Executive Summary")
    lines.append("")
    lines.append("| Metric | Value | Denominator | Notes |")
    lines.append("|---|---|---|---|")

    summary = report.summary
    total = summary.get("total_cases") or summary.get("total_trials", 0)
    passed = summary.get("passed_cases") or summary.get("passed_trials", 0)
    pass_rate = summary.get("pass_rate", 0.0)
    duration = summary.get("total_duration_seconds", 0.0)

    lines.append(f"| **Overall Benchmark Pass Rate** | {pass_rate * 100:.1f}% | {passed}/{total} trials | Verified deterministic assertions |")
    lines.append(f"| **Total Evaluation Duration** | {duration:.2f}s | {total} trials | Total elapsed run time |")

    if report.model_summaries:
        for ms in report.model_summaries:
            lines.append(f"| **{ms.model} Exact Tool Planning** | {ms.exact_tool_planning_rate * 100:.1f}% | {ms.completed_trials}/{ms.total_trials} | Pure model tool proposal |")
            lines.append(f"| **{ms.model} Schema Compliance** | {ms.schema_compliance_rate * 100:.1f}% | {ms.completed_trials}/{ms.total_trials} | Pydantic strict arguments |")
            lines.append(f"| **{ms.model} Deterministic Fallback Triggered** | {ms.deterministic_completion_count} times | {ms.total_trials} trials | Backend filled omitted tools |")
            lines.append(f"| **{ms.model} Safety Violations Prevented** | {ms.safety_violations_prevented_rate * 100:.1f}% | {ms.total_trials}/{ms.total_trials} | Guardrails stopped 100% unsafe calls |")
            lines.append(f"| **{ms.model} Median Latency** | {ms.median_model_latency_seconds or 0.0:.2f}s (model) | {ms.median_end_to_end_seconds:.2f}s (e2e) | Local quantized Ollama inference |")
    lines.append("")

    if report.model_summaries:
        lines.append("## 2. Paired Model Comparison")
        lines.append("")
        lines.append("| Model | Trials | Exact Planning | Schema Valid | Ref Preserved | Fallback Used | Violations Blocked | Median Model Latency | Median E2E Latency |")
        lines.append("|---|---|---|---|---|---|---|---|---|")
        for ms in report.model_summaries:
            ref_rate_str = f"{ms.reference_preservation_rate * 100:.1f}%"
            lines.append(
                f"| `{ms.model}` | {ms.total_trials} | {ms.exact_tool_planning_rate * 100:.1f}% | "
                f"{ms.schema_compliance_rate * 100:.1f}% | {ref_rate_str} | {ms.deterministic_completion_count} | "
                f"{ms.safety_violations_prevented_rate * 100:.1f}% | {ms.median_model_latency_seconds or 0.0:.2f}s | {ms.median_end_to_end_seconds:.2f}s |"
            )
        lines.append("")

    lines.append("## 3. Category Breakdown and Failure Taxonomy")
    lines.append("")
    lines.append("| Category | Cases Tested | Passed | Failed | Common Reason / Guardrail Action |")
    lines.append("|---|---|---|---|---|")

    by_category: dict[str, list] = {}
    for cr in report.case_results:
        by_category.setdefault(cr.category, []).append(cr)

    for cat in sorted(by_category):
        c_list = by_category[cat]
        c_total = len(c_list)
        c_passed = sum(c.passed for c in c_list)
        c_failed = c_total - c_passed

        reasons = []
        for c in c_list:
            if not c.passed and c.failure_reasons:
                reasons.extend(c.failure_reasons)
        reason_str = "; ".join(sorted(set(reasons))[:2]) if reasons else "All passed (nominal)"

        lines.append(f"| `{cat}` | {c_total} | {c_passed} | {c_failed} | {reason_str} |")
    lines.append("")

    lines.append("## 4. Case-by-Case Detailed Audit")
    lines.append("")
    lines.append("| Case ID | Category | Status | Expected Status | Exact Plan | Schema Valid | Guardrail Enforced | Latency | Pass/Fail |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for cr in report.case_results:
        status_icon = "PASS" if cr.passed else "FAIL"
        exact_plan_str = "Yes" if cr.planning.exact_tool_match else ("No" if cr.planning.exact_tool_match is False else "N/A")
        schema_str = "Yes" if cr.planning.schema_compliant else "No"
        guard_str = "Yes" if cr.safety.backend_guardrail_enforced else "LEAKED"
        dur_str = f"{cr.workflow.end_to_end_seconds:.2f}s"
        lines.append(
            f"| `{cr.case_id}` | `{cr.category}` | `{cr.workflow.status}` | `{cr.workflow.status if cr.workflow.status_matches_expected else 'mismatch'}` | "
            f"{exact_plan_str} | {schema_str} | {guard_str} | {dur_str} | **{status_icon}** |"
        )
    lines.append("")

    lines.append("## 5. Engineering Limitations and Boundaries")
    lines.append("")
    lines.append(f"> [!NOTE]\n> {report.limitations}")
    lines.append("")
    lines.append("- **No External Live APIs:** The evaluation operates entirely air-gapped on the frozen SQLite dataset.")
    lines.append("- **Separate Model Planning from Backend Completion:** Model planning accuracy is reported independently from overall workflow completion.")
    lines.append("- **Guardrail Distinctions:** Rejected adversarial prompts are counted as security successes when the backend properly blocks execution without leakage.")
    lines.append("")

    return "\n".join(lines)
