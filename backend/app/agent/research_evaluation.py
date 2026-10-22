"""Opt-in real-release verification and paired local-model research evaluation."""
import argparse
import asyncio
from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import statistics
import time

from app.agent.backend import ProcessBackend
from app.agent.benchmark import RecordingClient
from app.agent.briefing import LABEL_FIELDS
from app.agent.contracts import AgentRejected, Limits, tool_schema
from app.agent.model import MODELS, OllamaClient
from app.agent.orchestrator import ResearchAgent, parse_proposal
from app.agent.research_contracts import TOOLS
from app.agent.state import ProductSession
from app.agent.workflow import RESEARCH_PROMPT, parse_plan
from app.db.pharma.release_repository import FrozenPharmaReleaseRepository
from app.services.pharma.evidence import release_metadata

CASES = (
    {"id": "recall_xanax", "query": "0009-0029", "categories": ["recalls"], "question": "Retrieve historical recalls for my confirmed product."},
    {"id": "label_zepbound", "query": "0002-0152", "categories": ["labels"], "question": "Retrieve exact-product label warnings, contraindications and interactions."},
    {"id": "faers_alprazolam", "query": "0009-0029", "categories": ["faers"], "question": "Retrieve ingredient-level FAERS reporting evidence, not causal NDC observations."},
    {"id": "ambiguous_xanax", "query": "Xanax 0.25 mg", "categories": [], "question": "Find Xanax 0.25 mg products. Ask me to choose an exact formulation."},
    {"id": "missing_exact_label", "query": "0009-0029", "categories": ["labels"], "question": "Retrieve product-linked label warnings; disclose unavailable exact linkage."},
    {"id": "multisource_xanax", "query": "0009-0029", "categories": ["labels", "recalls", "faers"],
     "question": "What are the major safety warnings, historical recalls, and reported adverse events associated with my confirmed Xanax 0.25 mg?"},
)
OWNER = "scripted-local-evaluation-user"


def compare_evidence(result, expected, categories):
    """Compare displayed facts to independently read repository projections, not invented counts."""
    comparisons = {}
    sections = {section["category"]: section for section in result.get("sections", [])}
    for category in categories:
        section = sections.get(category)
        if not section or not section.get("evidence"):
            comparisons[category] = False
            continue
        card = section["evidence"]
        source = expected[{"labels": "labels", "recalls": "recalls", "faers": "adverse_events"}[category]]
        expected_records = source["records"][:10] if category == "recalls" else source["records"]
        valid = len(card["records"]) == len(expected_records)
        for actual, original in zip(card["records"], expected_records):
            if category == "labels":
                keys = ["id", "label_set_id", "label_version", "effective_date", "applicability_class",
                        "selection_status", "source_url", "source_record_id", *LABEL_FIELDS]
                valid &= all(actual[key] == original[key] for key in keys)
            elif category == "recalls":
                valid &= all(value == original.get(key) for key, value in actual.items())
            else:
                valid &= all(actual[key] == original[key] for key in (
                    "ingredient_id", "ingredient_name", "scope", "analytics", "top_reported_reactions", "monthly"))
                valid &= actual["source"] is not None if actual["analytics"] is not None else True
        valid &= all(card["coverage"][key] == value for key, value in source["coverage"].items())
        if category == "faers":
            valid &= card["summary"] == source["summary"] and card["scope"] == "INGREDIENT_LEVEL_REPORTING_EVIDENCE"
        if category == "labels" and not expected_records:
            valid &= section["status"] == "unavailable"
        comparisons[category] = bool(valid)
    return comparisons


def score_response(response, reference, categories, limits):
    message = response.get("message", {}) if isinstance(response, dict) else {}
    if not isinstance(message, dict):
        message = {}
    raw_calls = message.get("tool_calls")
    calls = raw_calls if isinstance(raw_calls, list) else []
    expected = [TOOLS[c] for c in categories] if categories else ["resolve_drug_product"]
    try:
        if reference:
            names, _ = parse_plan(response, reference, list(TOOLS.values()), limits)
        else:
            name, _ = parse_proposal(response, selected_ref=None, limit=limits.max_response_bytes)
            names = [name]
        compliant = True
    except (AgentRejected, TypeError, ValueError):
        names, compliant = [], False
    preserved = None
    if reference:
        preserved = bool(calls)
        for call in calls:
            arguments = call.get("function", {}).get("arguments") if isinstance(call, dict) else None
            if isinstance(arguments, str):
                from app.agent.contracts import decode
                try:
                    arguments = decode(arguments.encode(), 8192)
                except AgentRejected:
                    arguments = None
            preserved &= isinstance(arguments, dict) and arguments.get("product_ref") == reference
    return {"schema_compliant": compliant, "correct_tool_selection": compliant and set(names) == set(expected),
            "reference_preserved": preserved, "model_tool_names": names,
            "free_form_content_attempt": bool(message.get("content")),
            "answer_without_tools": bool(message.get("content")) and not calls}


async def prepare_cases():
    repo, backend = FrozenPharmaReleaseRepository(), ProcessBackend()
    fixtures = {}
    for case in CASES:
        session = ProductSession(OWNER, backend=backend)
        resolution = await session.resolve_for_user(case["query"], owner_id=OWNER)
        if not case["categories"]:
            if len(resolution["candidates"]) < 2:
                raise AgentRejected("ambiguous_fixture_not_available")
            fixtures[case["id"]] = (session, {"candidate_count": len(resolution["candidates"])})
            continue
        if len(resolution["candidates"]) != 1 or resolution["results_may_be_incomplete"]:
            raise AgentRejected("exact_fixture_not_available")
        # Explicit scripted-user corpus selection, outside model authority.
        await session.confirm(resolution["candidates"][0]["product_ref"], owner_id=OWNER)
        identifier = session._candidates[session.selected_ref]["product_id"]
        fixtures[case["id"]] = (session, repo.safety(identifier))
    return fixtures


def fresh_fixture(template):
    # Evaluation-only copy lets BOTH models receive byte-identical references
    # without sharing execution counters or reusing per-tool limits. Not a service API.
    clone = ProductSession(OWNER, backend=ProcessBackend(), limits=template.limits)
    clone._candidates = deepcopy(template._candidates)
    clone._selected = template.selected_ref
    clone.workflow_state = template.workflow_state
    return clone


async def evaluate(*, models=False):
    fixtures = await prepare_cases()
    release = release_metadata()
    verification = []
    for case in CASES:
        template, expected = fixtures[case["id"]]
        if not case["categories"]:
            verification.append({"case": case, "candidate_count": expected["candidate_count"],
                                 "selected": template.selected_ref, "passed": template.selected_ref is None})
            continue
        session = fresh_fixture(template)
        result = await ResearchAgent(None).research(case["question"], session=session, owner_id=OWNER,
            categories=case["categories"], routing="deterministic")
        comparisons = compare_evidence(result, expected, case["categories"])
        verification.append({"case": case, "passed": all(comparisons.values()), "comparisons": comparisons,
                             "briefing": result})
        print(f'deterministic {case["id"]}: {result["status"]} {comparisons}', flush=True)
    trials, warmups, installed = [], [], []
    if models:
        probe = OllamaClient()
        tags = await probe.request("/api/tags")
        installed = [item for item in tags.get("models", []) if item["name"] in MODELS]
        if {item["name"] for item in installed} != set(MODELS):
            raise AgentRejected("required_models_not_installed_no_download_attempted")
        for model in MODELS:
            client = OllamaClient(model)
            template = fixtures[CASES[0]["id"]][0]
            names = [TOOLS["recalls"]]
            started = time.perf_counter()
            warm = await client.chat([{"role": "system", "content": RESEARCH_PROMPT}, {"role": "user", "content": json.dumps({
                "question": CASES[0]["question"], "selected_product_ref": template.selected_ref, "requested_evidence_tools": names})}],
                tool_schema(template.selected_ref, names))
            warmups.append({"model": model, "done": warm.get("done"), "seconds": time.perf_counter()-started,
                            "load_duration_ns": warm.get("load_duration")})
            if warm.get("done") is not True:
                raise AgentRejected("warmup_incomplete")
            for case in CASES:
                template, expected = fixtures[case["id"]]
                session = fresh_fixture(template)
                recorder = RecordingClient(client)
                started = time.perf_counter()
                if case["categories"]:
                    result = await ResearchAgent(recorder).research(case["question"], session=session, owner_id=OWNER,
                        categories=case["categories"], routing="auto")
                    comparisons = compare_evidence(result, expected, case["categories"])
                else:
                    result = await ResearchAgent(recorder).run(case["question"], session=session, owner_id=OWNER)
                    comparisons = {"ambiguity": result["status"] == "confirmation_required" and
                        len(result.get("candidates", [])) == expected["candidate_count"] and session.selected_ref is None}
                duration = time.perf_counter()-started
                metrics = score_response(recorder.response, session.selected_ref, case["categories"], session.limits)
                row = {"model": model, "case": case["id"], **metrics, "status": result["status"], "reason": result.get("reason"),
                    "completed_requested_workflow": all(comparisons.values()), "comparisons": comparisons,
                    "routing": result.get("routing"), "model_seconds": recorder.latency, "end_to_end_seconds": duration,
                    "prompt_sha256": recorder.prompt_digest, "response": recorder.response, "result": result,
                    "timeout": result.get("reason") == "timeout" or any(s.get("reason") in {"tool_timeout", "request_timeout"} for s in result.get("sections", []))}
                trials.append(row)
                print(f'{model} {case["id"]}: {result["status"]}, model plan correct={metrics["correct_tool_selection"]}, workflow verified={all(comparisons.values())}, {duration:.2f}s', flush=True)
    summary = {}
    for model in MODELS if models else ():
        rows = [row for row in trials if row["model"] == model]
        summary[model] = {"trials": len(rows), **{key: {"count": sum(row[key] for row in rows if row[key] is not None),
            "eligible": sum(row[key] is not None for row in rows)} for key in ("correct_tool_selection", "schema_compliant",
                "reference_preserved", "completed_requested_workflow", "free_form_content_attempt", "answer_without_tools", "timeout")},
            "deterministic_completion_count": sum((r.get("routing") or {}).get("mode") == "deterministic_completion" for r in rows),
            "median_end_to_end_seconds": statistics.median(row["end_to_end_seconds"] for row in rows),
            "median_model_seconds": statistics.median(row["model_seconds"] for row in rows if row["model_seconds"] is not None)}
    if models:
        for case in CASES:
            if len({row["prompt_sha256"] for row in trials if row["case"] == case["id"]}) != 1:
                raise AgentRejected("paired_prompts_differ")
    return {"schema_version": "agent-v2-evaluation-1", "release": release, "limits": asdict(Limits()),
            "options": {"temperature": 0, "seed": 7, "think": False}, "corpus": CASES,
            "verification": verification, "installed_models": installed, "warmups": warmups, "summary": summary, "trials": trials,
            "limitations": "Six cases per model, one fixed-order trial each. Not a broad medical hallucination evaluation. Free-form content attempts are discarded, not semantically certified. Completion can be partial/unavailable source disclosure and can use explicitly reported deterministic completion. Native model selection is scored separately."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", action="store_true", help="Also compare the two already-installed Ollama models")
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    result = asyncio.run(evaluate(models=arguments.models))
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["summary"], indent=2))
    if not all(row["passed"] for row in result["verification"]):
        raise SystemExit("Real-data verification did not pass; inspect the recorded report.")


if __name__ == "__main__":
    main()
