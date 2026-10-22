"""CLI entry point for Dav AI Agent Evaluation Framework v1."""
import argparse
import asyncio
import json
from pathlib import Path
import sys

from app.agent.evaluation.corpus import get_corpus
from app.agent.evaluation.report import generate_markdown_report
from app.agent.evaluation.runner import EvaluationRunner, SMOKE_CASE_IDS


async def async_main(args):
    corpus = get_corpus()
    runner = EvaluationRunner(corpus)
    subset = SMOKE_CASE_IDS if args.smoke else None

    print(f"Starting Dav AI Evaluation Framework v1 (Mode: {args.mode}, Smoke: {args.smoke})...", flush=True)

    report = None
    if args.mode == "offline":
        report = await runner.run_mode_a(subset_ids=subset)
    elif args.mode == "frozen_data":
        report = await runner.run_mode_b(subset_ids=subset)
    elif args.mode == "model_comparison":
        report = await runner.run_mode_c(
            models=tuple(args.models),
            repetitions=args.repetitions,
            subset_ids=subset,
        )
    elif args.mode == "all":
        print("Running Mode A (Offline)...", flush=True)
        rep_a = await runner.run_mode_a(subset_ids=subset)
        print(f"Mode A finished: {rep_a.summary['passed_cases']}/{rep_a.summary['total_cases']} passed.")

        print("Running Mode B (Frozen Data)...", flush=True)
        rep_b = await runner.run_mode_b(subset_ids=subset)
        print(f"Mode B finished: {rep_b.summary['passed_cases']}/{rep_b.summary['total_cases']} passed.")

        print("Running Mode C (Model Comparison)...", flush=True)
        report = await runner.run_mode_c(
            models=tuple(args.models),
            repetitions=args.repetitions,
            subset_ids=subset,
        )

    if report:
        if args.output:
            out_path = Path(args.output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(report.model_dump_json(indent=2) + "\n")
            print(f"JSON results saved to {out_path}", flush=True)

        if args.report:
            md_path = Path(args.report)
            md_path.parent.mkdir(parents=True, exist_ok=True)
            md_text = generate_markdown_report(report)
            md_path.write_text(md_text + "\n")
            print(f"Markdown report saved to {md_path}", flush=True)

        print("\n=== EVALUATION SUMMARY ===")
        print(json.dumps(report.summary, indent=2))

        if report.model_summaries:
            print("\n=== MODEL COMPARISON ===")
            for ms in report.model_summaries:
                print(f"Model: {ms.model}")
                print(f"  Exact Tool Planning: {ms.exact_tool_planning_rate * 100:.1f}%")
                print(f"  Schema Compliance: {ms.schema_compliance_rate * 100:.1f}%")
                print(f"  Deterministic Fallbacks: {ms.deterministic_completion_count}")
                print(f"  Safety Violations Blocked: {ms.safety_violations_prevented_rate * 100:.1f}%")
                print(f"  Median Model Latency: {ms.median_model_latency_seconds or 0.0:.2f}s")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=["offline", "frozen_data", "model_comparison", "all"],
        default="offline",
        help="Evaluation mode to run",
    )
    parser.add_argument("--output", type=Path, help="Path to write JSON results")
    parser.add_argument("--report", type=Path, help="Path to write Markdown report")
    parser.add_argument("--smoke", action="store_true", help="Run quick representative subset")
    parser.add_argument("--repetitions", type=int, default=1, help="Repetitions for model comparison")
    parser.add_argument(
        "--models",
        nargs="+",
        default=["llama3.2:3b", "qwen3.5:4b-q4_K_M"],
        help="Models to compare in Mode C",
    )
    args = parser.parse_args()
    asyncio.run(async_main(args))


if __name__ == "__main__":
    main()
