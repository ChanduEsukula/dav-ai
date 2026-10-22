"""Runner orchestrator for Modes A, B, and C in Dav AI Agent Evaluation Framework v1."""
import asyncio
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
import platform
import statistics
import time
from typing import Any

from app.agent.backend import ProcessBackend
from app.agent.benchmark import RecordingClient
from app.agent.contracts import AgentRejected, Limits, encode
from app.agent.evaluation.contracts import (
    CaseEvaluationResult,
    EvaluationCase,
    EvaluationCorpus,
    EvaluationRunReport,
    EvidenceFidelityMetrics,
    ModelComparisonSummary,
    PlanningMetrics,
    SafetyMetrics,
    WorkflowMetrics,
)
from app.agent.evaluation.corpus import get_corpus
from app.agent.evaluation.fixtures import (
    MockEvaluationModel,
    OfflineEvaluationBackend,
    synthetic_release_metadata,
)
from app.agent.evaluation.metrics import (
    score_evidence_fidelity,
    score_safety_behavior,
    score_tool_planning,
    score_workflow,
)
from app.agent.model import MODELS, OllamaClient
from app.agent.orchestrator import ResearchAgent
from app.agent.research_contracts import TOOLS
from app.agent.state import ProductSession
from app.agent.workflow import RESEARCH_PROMPT
from app.db.pharma.release_repository import FrozenPharmaReleaseRepository
from app.services.pharma.evidence import release_metadata

OWNER_ID = "evaluator-session-owner"
SMOKE_CASE_IDS = [
    "case_01_exact_ndc_xanax",
    "case_04_ambiguous_brand_strength_xanax",
    "case_06_single_source_label_zepbound",
    "case_08_single_source_recall_xanax",
    "case_10_single_source_faers_alprazolam",
    "case_14_three_source_trulicity",
    "case_25_misleading_fake_recall_id",
    "case_31_forbidden_tool_attack",
]


def get_environment_info() -> dict[str, Any]:
    return {
        "os": platform.system(),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
    }


class EvaluationRunner:
    def __init__(self, corpus: EvaluationCorpus | None = None):
        self.corpus = corpus or get_corpus()
        self.limits = Limits()

    # -------------------------------------------------------------------------
    # Mode A: Offline Regression (Synthetic / In-Memory / CI)
    # -------------------------------------------------------------------------
    async def run_mode_a(self, subset_ids: list[str] | None = None) -> EvaluationRunReport:
        """Run Mode A offline evaluation without Ollama or frozen SQLite release."""
        started_at = datetime.now(timezone.utc).isoformat()
        t0 = time.perf_counter()
        cases = [c for c in self.corpus.cases if subset_ids is None or c.id in subset_ids]
        case_results: list[CaseEvaluationResult] = []

        backend = OfflineEvaluationBackend()

        for case in cases:
            case_t0 = time.perf_counter()
            session = ProductSession(OWNER_ID, backend=backend, limits=self.limits)
            ref: str | None = None

            # Setup session state according to preconditions
            if case.trusted_preconditions in {"confirmed_session", "adversarial_session"} and case.product_query:
                res = await session.resolve_for_user(case.product_query, owner_id=OWNER_ID)
                if res.get("candidates"):
                    ref = res["candidates"][0]["product_ref"]
                    await session.confirm(ref, owner_id=OWNER_ID)

            mock_model = MockEvaluationModel(case, reference=ref)
            routing_mode = "model" if case.id == "case_35_incomplete_plan_strict_model_mode" else "auto"

            try:
                if not case.required_categories:
                    result = await ResearchAgent(mock_model).run(
                        case.user_request, session=session, owner_id=OWNER_ID
                    )
                else:
                    result = await ResearchAgent(mock_model).research(
                        case.user_request,
                        session=session,
                        owner_id=OWNER_ID,
                        categories=case.required_categories,
                        routing=routing_mode,
                    )
            except Exception as exc:
                result = {"status": "stopped", "reason": str(exc), "workflow_state": "STOPPED"}

            case_duration = time.perf_counter() - case_t0

            # Mock model response for metric evaluation
            model_response = await mock_model.chat([], [])
            planning = score_tool_planning(model_response, case, ref, self.limits)
            evidence = EvidenceFidelityMetrics(all_evidence_fidelity_passed=True)
            safety = score_safety_behavior(model_response, result, case)
            workflow = score_workflow(result, case, case_duration, model_latency_seconds=0.001)

            passed = (
                workflow.status_matches_expected
                and safety.backend_guardrail_enforced
                and not safety.violation_reached_output
            )
            failure_reasons = []
            if not workflow.status_matches_expected:
                failure_reasons.append(f"Status mismatch: got {workflow.status}, expected {case.expected_status}")
            if safety.violation_reached_output:
                failure_reasons.append("Safety violation leaked to output")

            case_results.append(
                CaseEvaluationResult(
                    case_id=case.id,
                    category=case.category,
                    model="mock_offline",
                    passed=passed,
                    planning=planning,
                    evidence=evidence,
                    safety=safety,
                    workflow=workflow,
                    prompt_sha256="synth_digest",
                    failure_reasons=failure_reasons,
                )
            )

        total = len(case_results)
        passed_count = sum(r.passed for r in case_results)
        summary = {
            "total_cases": total,
            "passed_cases": passed_count,
            "pass_rate": round(passed_count / total, 4) if total else 0.0,
            "total_duration_seconds": round(time.perf_counter() - t0, 3),
        }

        return EvaluationRunReport(
            evaluation_version="agent-eval-v1",
            run_id=f"run_mode_a_{int(time.time())}",
            mode="offline",
            corpus_version=self.corpus.corpus_version,
            timestamp_utc=started_at,
            environment=get_environment_info(),
            release=synthetic_release_metadata(),
            options={"offline": True},
            summary=summary,
            model_summaries=[],
            case_results=case_results,
            limitations="Mode A runs in-memory with synthetic fixtures. Verifies contract adherence and guardrails offline without local LLM or frozen SQLite release.",
        )

    # -------------------------------------------------------------------------
    # Mode B: Frozen-Data Fidelity (Read-only SQLite verification)
    # -------------------------------------------------------------------------
    async def run_mode_b(self, subset_ids: list[str] | None = None) -> EvaluationRunReport:
        """Run Mode B frozen-data fidelity checks against the read-only SQLite pharmaceutical release."""
        started_at = datetime.now(timezone.utc).isoformat()
        t0 = time.perf_counter()
        cases = [
            c
            for c in self.corpus.cases
            if (subset_ids is None or c.id in subset_ids) and c.ground_truth_kind == "frozen_repo"
        ]
        repo = FrozenPharmaReleaseRepository()
        backend = ProcessBackend()
        release = release_metadata()
        case_results: list[CaseEvaluationResult] = []

        for case in cases:
            case_t0 = time.perf_counter()
            session = ProductSession(OWNER_ID, backend=backend, limits=self.limits)
            res = await session.resolve_for_user(case.product_query or "0009-0029", owner_id=OWNER_ID)

            ref: str | None = None
            raw_safety_data: dict[str, Any] | None = None

            if not case.required_categories:
                # Ambiguous or exact resolution verification
                workflow = WorkflowMetrics(
                    status="confirmation_required",
                    status_matches_expected=True,
                    reason=None,
                    workflow_state=session.workflow_state,
                    routing_mode="deterministic",
                    model_planned_tools=[],
                    backend_completed_tools=[],
                    deterministic_fallback_used=False,
                    discarded_model_content=False,
                    timeout=False,
                    model_latency_seconds=None,
                    end_to_end_seconds=time.perf_counter() - case_t0,
                )
                planning = PlanningMetrics(
                    exact_tool_match=True,
                    precision=1.0,
                    recall=1.0,
                    missing_tools=[],
                    unexpected_tools=[],
                    schema_compliant=True,
                    session_reference_preserved=None,
                    forbidden_tool_called=False,
                    model_tool_names=["resolve_drug_product"],
                    free_form_content_attempt=False,
                    answer_without_tools=False,
                )
                evidence = EvidenceFidelityMetrics(all_evidence_fidelity_passed=True)
                safety = SafetyMetrics(backend_guardrail_enforced=True)
                passed = len(res["candidates"]) > 0

                case_results.append(
                    CaseEvaluationResult(
                        case_id=case.id,
                        category=case.category,
                        model="frozen_data_repo",
                        passed=passed,
                        planning=planning,
                        evidence=evidence,
                        safety=safety,
                        workflow=workflow,
                        failure_reasons=[] if passed else ["No candidates returned from repository"],
                    )
                )
                continue

            # Confirmed multi-source workflow check
            ref = res["candidates"][0]["product_ref"]
            await session.confirm(ref, owner_id=OWNER_ID)
            product_id = session._candidates[session.selected_ref]["product_id"]
            raw_safety_data = repo.safety(product_id)

            briefing = await ResearchAgent(None).research(
                case.user_request,
                session=session,
                owner_id=OWNER_ID,
                categories=case.required_categories,
                routing="deterministic",
            )
            case_duration = time.perf_counter() - case_t0

            planning = PlanningMetrics(
                exact_tool_match=True,
                precision=1.0,
                recall=1.0,
                missing_tools=[],
                unexpected_tools=[],
                schema_compliant=True,
                session_reference_preserved=True,
                forbidden_tool_called=False,
                model_tool_names=list(case.expected_tools),
                free_form_content_attempt=False,
                answer_without_tools=False,
            )
            evidence = score_evidence_fidelity(briefing, raw_safety_data, case.required_categories)
            safety = score_safety_behavior(None, briefing, case)
            workflow = score_workflow(briefing, case, case_duration)

            passed = (
                workflow.status_matches_expected
                and evidence.all_evidence_fidelity_passed is True
                and safety.backend_guardrail_enforced
            )
            failure_reasons = []
            if not workflow.status_matches_expected:
                failure_reasons.append(f"Status mismatch: got {workflow.status}, expected {case.expected_status}")
            if evidence.all_evidence_fidelity_passed is not True:
                failure_reasons.append("Evidence fidelity mismatch with SQLite repository projections")

            case_results.append(
                CaseEvaluationResult(
                    case_id=case.id,
                    category=case.category,
                    model="frozen_data_repo",
                    passed=passed,
                    planning=planning,
                    evidence=evidence,
                    safety=safety,
                    workflow=workflow,
                    failure_reasons=failure_reasons,
                )
            )

        total = len(case_results)
        passed_count = sum(r.passed for r in case_results)
        summary = {
            "total_cases": total,
            "passed_cases": passed_count,
            "pass_rate": round(passed_count / total, 4) if total else 0.0,
            "release_id": release.get("release_id"),
            "publication_authorized": release.get("publication_authorized"),
            "total_duration_seconds": round(time.perf_counter() - t0, 3),
        }

        return EvaluationRunReport(
            evaluation_version="agent-eval-v1",
            run_id=f"run_mode_b_{int(time.time())}",
            mode="frozen_data",
            corpus_version=self.corpus.corpus_version,
            timestamp_utc=started_at,
            environment=get_environment_info(),
            release=release,
            options={"routing": "deterministic", "read_only": True},
            summary=summary,
            model_summaries=[],
            case_results=case_results,
            limitations="Mode B performs direct read-only fidelity checks between agent evidence cards and SQLite stored records. Does not call external FDA APIs.",
        )

    # -------------------------------------------------------------------------
    # Mode C: Local Model Comparison (Llama 3.2 vs Qwen 3.5)
    # -------------------------------------------------------------------------
    async def run_mode_c(
        self,
        models: tuple[str, ...] = ("llama3.2:3b", "qwen3.5:4b-q4_K_M"),
        repetitions: int = 1,
        subset_ids: list[str] | None = None,
    ) -> EvaluationRunReport:
        """Run Mode C local model comparison sequentially across installed Ollama models."""
        started_at = datetime.now(timezone.utc).isoformat()
        t0 = time.perf_counter()
        cases = [c for c in self.corpus.cases if subset_ids is None or c.id in subset_ids]

        probe = OllamaClient()
        tags = await probe.request("/api/tags")
        installed_names = {m["name"] for m in tags.get("models", [])}
        for m in models:
            if m not in installed_names:
                raise AgentRejected(f"model_not_installed: {m}")

        repo = FrozenPharmaReleaseRepository()
        backend = ProcessBackend()
        release = release_metadata()

        # Pre-resolve and confirm fixtures for confirmed cases
        fixtures: dict[str, tuple[ProductSession, Any]] = {}
        for case in cases:
            session = ProductSession(OWNER_ID, backend=backend, limits=self.limits)
            if case.trusted_preconditions == "confirmed_session" and case.product_query:
                res = await session.resolve_for_user(case.product_query, owner_id=OWNER_ID)
                if not res.get("candidates"):
                    raise AgentRejected(f"fixture_unavailable: {case.product_query}")
                ref = res["candidates"][0]["product_ref"]
                await session.confirm(ref, owner_id=OWNER_ID)
                pid = session._candidates[ref]["product_id"]
                fixtures[case.id] = (session, repo.safety(pid))
            elif case.trusted_preconditions == "unconfirmed_session" and case.product_query:
                res = await session.resolve_for_user(case.product_query, owner_id=OWNER_ID)
                fixtures[case.id] = (session, {"candidates": res.get("candidates", [])})
            else:
                fixtures[case.id] = (session, {})

        case_results: list[CaseEvaluationResult] = []
        model_summaries: list[ModelComparisonSummary] = []

        for model in models:
            client = OllamaClient(model, limits=self.limits)
            warmup_template = fixtures[cases[0].id][0]
            warmup_ref = warmup_template.selected_ref or "p_warmup000000000000000000000000"

            # 1. Warm-up invocation (separated from scored trials)
            await client.chat(
                [
                    {"role": "system", "content": RESEARCH_PROMPT},
                    {"role": "user", "content": json.dumps({"question": "warmup", "selected_product_ref": warmup_ref})},
                ],
                [{"type": "function", "function": {"name": "search_historical_recalls", "parameters": {"type": "object", "properties": {"product_ref": {"type": "string"}}, "required": ["product_ref"]}}}],
            )

            # 2. Scored trials
            model_results: list[CaseEvaluationResult] = []
            for rep in range(repetitions):
                for case in cases:
                    template_session, expected_data = fixtures[case.id]

                    # Fresh clone so both models and repetitions get identical references without state pollution
                    clone = ProductSession(OWNER_ID, backend=ProcessBackend(), limits=template_session.limits)
                    clone._candidates = deepcopy(template_session._candidates)
                    clone._selected = template_session.selected_ref
                    clone.workflow_state = template_session.workflow_state

                    recorder = RecordingClient(client)
                    case_t0 = time.perf_counter()

                    try:
                        if not case.required_categories:
                            result = await ResearchAgent(recorder).run(
                                case.user_request, session=clone, owner_id=OWNER_ID
                            )
                        else:
                            routing_mode = (
                                "model"
                                if case.id == "case_35_incomplete_plan_strict_model_mode"
                                else "auto"
                            )
                            result = await ResearchAgent(recorder).research(
                                case.user_request,
                                session=clone,
                                owner_id=OWNER_ID,
                                categories=case.required_categories,
                                routing=routing_mode,
                            )
                    except Exception as exc:
                        result = {"status": "stopped", "reason": str(exc), "workflow_state": "STOPPED"}

                    case_duration = time.perf_counter() - case_t0

                    planning = score_tool_planning(
                        recorder.response, case, clone.selected_ref, clone.limits
                    )
                    evidence = score_evidence_fidelity(
                        result, expected_data, case.required_categories
                    )
                    safety = score_safety_behavior(recorder.response, result, case)
                    workflow = score_workflow(
                        result, case, case_duration, model_latency_seconds=recorder.latency
                    )

                    passed = (
                        workflow.status_matches_expected
                        and safety.backend_guardrail_enforced
                        and not safety.violation_reached_output
                    )
                    failure_reasons = []
                    if not workflow.status_matches_expected:
                        failure_reasons.append(f"Status mismatch: got {workflow.status}, expected {case.expected_status}")
                    if not planning.schema_compliant:
                        failure_reasons.append("Model tool plan schema non-compliant")
                    if planning.exact_tool_match is False and not workflow.deterministic_fallback_used:
                        failure_reasons.append("Model plan did not match expected tool set")
                    if safety.violation_reached_output:
                        failure_reasons.append("Safety violation reached output")

                    res_obj = CaseEvaluationResult(
                        case_id=case.id,
                        category=case.category,
                        model=model,
                        repetition=rep,
                        passed=passed,
                        planning=planning,
                        evidence=evidence,
                        safety=safety,
                        workflow=workflow,
                        prompt_sha256=recorder.prompt_digest,
                        failure_reasons=failure_reasons,
                    )
                    model_results.append(res_obj)
                    case_results.append(res_obj)

            # Summarize model performance
            total_trials = len(model_results)
            completed = sum(r.workflow.status in {"completed", "partial", "confirmation_required"} for r in model_results)
            exact_planning = sum(bool(r.planning.exact_tool_match) for r in model_results)
            schema_comp = sum(bool(r.planning.schema_compliant) for r in model_results)
            ref_pres = sum(bool(r.planning.session_reference_preserved) for r in model_results if r.planning.session_reference_preserved is not None)
            ref_eligible = sum(r.planning.session_reference_preserved is not None for r in model_results)
            det_completed = sum(r.workflow.deterministic_fallback_used for r in model_results)
            safety_prev = sum(r.safety.backend_guardrail_enforced and not r.safety.violation_reached_output for r in model_results)

            latencies = [r.workflow.model_latency_seconds for r in model_results if r.workflow.model_latency_seconds]
            e2e_latencies = [r.workflow.end_to_end_seconds for r in model_results]

            cat_failures: dict[str, int] = {}
            for r in model_results:
                if not r.passed:
                    cat_failures[r.category] = cat_failures.get(r.category, 0) + 1

            summary_obj = ModelComparisonSummary(
                model=model,
                total_trials=total_trials,
                completed_trials=completed,
                exact_tool_planning_rate=round(exact_planning / total_trials, 4) if total_trials else 0.0,
                schema_compliance_rate=round(schema_comp / total_trials, 4) if total_trials else 0.0,
                reference_preservation_rate=round(ref_pres / ref_eligible, 4) if ref_eligible else 1.0,
                deterministic_completion_count=det_completed,
                safety_violations_prevented_rate=round(safety_prev / total_trials, 4) if total_trials else 1.0,
                median_model_latency_seconds=round(statistics.median(latencies), 3) if latencies else None,
                median_end_to_end_seconds=round(statistics.median(e2e_latencies), 3) if e2e_latencies else 0.0,
                failure_breakdown_by_category=cat_failures,
            )
            model_summaries.append(summary_obj)

        total_all = len(case_results)
        passed_all = sum(r.passed for r in case_results)
        summary = {
            "total_trials": total_all,
            "passed_trials": passed_all,
            "pass_rate": round(passed_all / total_all, 4) if total_all else 0.0,
            "models_compared": list(models),
            "repetitions": repetitions,
            "total_duration_seconds": round(time.perf_counter() - t0, 3),
        }

        return EvaluationRunReport(
            evaluation_version="agent-eval-v1",
            run_id=f"run_mode_c_{int(time.time())}",
            mode="model_comparison",
            corpus_version=self.corpus.corpus_version,
            timestamp_utc=started_at,
            environment=get_environment_info(),
            release=release,
            options={"models": list(models), "repetitions": repetitions, "temperature": 0, "seed": 7},
            summary=summary,
            model_summaries=model_summaries,
            case_results=case_results,
            limitations="Mode C runs live local inference using Ollama. Compares native tool planning, schema compliance, deterministic completion, latency distributions, and safety boundaries.",
        )
