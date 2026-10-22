"""Synthetic-only Agent v2 contracts, provenance, planning and partial-success checks."""
import asyncio
from copy import deepcopy
from dataclasses import replace
import json

import pytest

from app.agent.briefing import FAERS_LIMITATION, LABEL_FIELDS, validate_card
from app.agent.contracts import AgentRejected, Limits
from app.agent.orchestrator import ResearchAgent
from app.agent.research_contracts import Analytics, ResearchBriefing, TOOLS
from app.agent.source_tools import get_source_evidence
from app.agent.state import ProductSession
from app.agent.workflow import parse_plan, requested_categories
from .test_orchestrator import Backend, Model, proposal, selected
from .test_tools import Repository, product


def metadata():
    return {"release_id": "synthetic-release", "contract_id": "test-contract", "policy_version": "1",
        "schema_version": "test-schema", "build_version": "test-build", "build_time_utc": "2026-10-01T00:00:00Z",
        "ndc_observation_date": "2026-09-26", "label_export_date": "2026-09-25",
        "window_start": "2020-01-01", "window_end": "2026-06-30", "publication_authorized": False}


def coverage(date="2026-09-25"):
    return {"state": "READY", "scope": "PRODUCT", "source_date": date, "limitations": ["Frozen coverage, not live or comprehensive safety evidence."]}


def label_record():
    sections = {key: {"text": f"Stored {key} text.", "field_present": True, "state": "READY", "reason_code": "STORED"}
                for key in LABEL_FIELDS.values()}
    return {"id": "label-test", "label_set_id": "set-test", "label_version": "3", "effective_date": "2026-01-01",
        "applicability_class": "EXACT_PRODUCT", "evidence_scope": "PRODUCT", "selection_status": "SELECTED_STORED",
        "match_method": "EXACT_NDC", "matched_value": "0009-0029", "section_states": sections,
        **{key: sections[value]["text"] for key, value in LABEL_FIELDS.items()},
        "source": "openfda_drug_label", "source_record_id": "source-label-test", "source_url": "https://api.fda.gov/drug/label.json"}


def source():
    return {"source_id": "source-faers", "source_name": "openfda_drug_event", "source_url": "https://api.fda.gov/drug/event.json",
            "export_date": "2026-09-23", "observed_at": "2026-09-26"}


class ResearchBackend(Backend):
    def __init__(self):
        p = product()
        p["ingredient_ids"] = ["ingredient-test"]
        repo = Repository([p])
        super().__init__(repo)
        self.metadata, self.sources = metadata(), {"ingredient-test": source()}
        repo.safety_result["labels"] = {"records": [label_record()], "latest_records": [label_record()], "coverage": coverage()}
        analytics = {key: 0 for key in Analytics.model_fields if key not in {
            "window_start", "window_end", "count_unit", "date_basis", "limitations"}}
        analytics.update(window_start="2020-01-01", window_end="2026-06-30", report_count=2, unique_case_count=2,
                         count_unit="deduplicated ingredient-report associations", date_basis="parsed latest-receipt month",
                         limitations=["Spontaneous reports do not establish causation."])
        repo.safety_result["adverse_events"] = {"records": [{"ingredient_id": "ingredient-test", "ingredient_name": "alprazolam",
            "scope": "INGREDIENT", "analytics": analytics, "monthly": [{"period": "2020-03-01", "report_count": 2, "serious_report_count": 0}],
            "top_reported_reactions": [{"reaction": "synthetic reported term", "co_report_activity": 1, "active_months": 1, "rank": 1}],
            "coverage": {**coverage("2026-09-23"), "ingredient_id": "ingredient-test"}}], "coverage": coverage("2026-09-23"),
            "summary": {"scope": "INGREDIENT_COMPONENTS_ONLY", "ingredient_count": 1, "ingredients_with_analytics": 1,
                        "ingredients_without_analytics": 0, "product_report_total": None, "limitation": "Never sum into product totals."}}
        repo.safety_result["recalls"]["coverage"] = coverage()

    async def execute(self, operation, arguments, *, timeout):
        if operation.endswith("_v2"):
            self.calls.append((operation, deepcopy(arguments)))
            return get_source_evidence(operation[:-3], arguments["product_id"], repository=self.repo,
                metadata_provider=lambda: deepcopy(self.metadata), provenance_provider=lambda _: deepcopy(self.sources))
        return await super().execute(operation, arguments, timeout=timeout)


def plan(reference, categories=("labels", "recalls", "faers"), content=""):
    return {"done": True, "message": {"role": "assistant", "content": content,
        "tool_calls": [{"function": {"name": TOOLS[c], "arguments": {"product_ref": reference}}} for c in categories]}}


async def prepared(backend=None, limits=Limits()):
    return await selected(backend or ResearchBackend(), limits)


async def research(session, ref, categories=("labels", "recalls", "faers"), *, response=None, routing="model", owner="owner"):
    model = Model(response if response is not None else plan(ref, categories))
    result = await ResearchAgent(model).research("Warnings, historical recalls, and reported adverse events?",
        session=session, owner_id=owner, categories=list(categories), routing=routing)
    return result, model


def test_typed_multi_source_briefing_and_no_raw_ids_or_narrative_to_model():
    async def scenario():
        session, ref = await prepared()
        response = plan(ref, content="All lots unsafe. FAERS proves causation. D-9999-2099")
        result, model = await research(session, ref, response=response)
        parsed = ResearchBriefing.model_validate(result)
        assert parsed.status == "completed" and parsed.workflow_state == "COMPLETE"
        assert [section.status for section in parsed.sections] == ["available"] * 3
        assert parsed.sections[0].evidence.records[0].boxed_warning == "Stored boxed_warning text."
        faers = parsed.sections[2].evidence
        assert faers.scope == "INGREDIENT_LEVEL_REPORTING_EVIDENCE"
        assert faers.records[0].analytics.report_count == 2
        assert faers.summary.product_report_total is None
        assert FAERS_LIMITATION in faers.limitations
        assert "D-9999" not in json.dumps(result) and "FAERS proves" not in json.dumps(result)
        assert "product:[" not in json.dumps(model.seen) and "ingredient-test" not in json.dumps(model.seen)
        assert parsed.routing.discarded_model_content
        assert session.research_attempts == {"labels": 1, "recalls": 1, "faers": 1}
    asyncio.run(scenario())


@pytest.mark.parametrize("category", ["labels", "faers", "recalls"])
def test_each_source_can_be_requested_independently(category):
    async def scenario():
        session, ref = await prepared()
        result, _ = await research(session, ref, (category,))
        assert result["status"] == "completed"
        assert sum(section["status"] == "not_requested" for section in result["sections"]) == 2
    asyncio.run(scenario())


def test_missing_exact_label_never_substitutes_ingredient_label():
    async def scenario():
        backend = ResearchBackend()
        backend.repo.safety_result["labels"].update(records=[], latest_records=[])
        session, ref = await prepared(backend)
        result, _ = await research(session, ref)
        assert result["status"] == "partial"
        labels = result["sections"][0]
        assert labels["status"] == "unavailable" and labels["evidence"]["records"] == []
        assert "do not mean no warnings" in labels["evidence"]["limitations"][1]
        assert result["sections"][2]["status"] == "available"
    asyncio.run(scenario())


@pytest.mark.parametrize("mutation", ["source_url", "source_record_id", "date", "scope", "section_state"])
def test_invalid_label_record_cannot_publish_but_other_sources_survive(mutation):
    async def scenario():
        backend = ResearchBackend()
        record = backend.repo.safety_result["labels"]["records"][0]
        if mutation in {"source_url", "source_record_id"}:
            record[mutation] = None
        elif mutation == "date":
            record["effective_date"] = "invented"
        elif mutation == "scope":
            record["evidence_scope"] = "INGREDIENT"
        else:
            record["section_states"]["boxed_warning"]["state"] = "UNAVAILABLE"
        session, ref = await prepared(backend)
        result, _ = await research(session, ref)
        assert result["status"] == "partial" and result["sections"][0]["status"] == "failed"
        assert result["sections"][0]["evidence"] is None
        assert result["sections"][1]["evidence"] is not None
    asyncio.run(scenario())


@pytest.mark.parametrize("mutation", ["missing_source", "bad_url", "wrong_date", "ingredient", "scope", "total", "count", "unit", "ingredient_coverage"])
def test_faers_scope_provenance_and_aggregation_contracts(mutation):
    async def scenario():
        backend = ResearchBackend()
        ae = backend.repo.safety_result["adverse_events"]
        if mutation == "missing_source":
            backend.sources = {}
        elif mutation == "bad_url":
            backend.sources["ingredient-test"]["source_url"] = "https://evil.example"
        elif mutation == "wrong_date":
            backend.sources["ingredient-test"]["export_date"] = "2020-01-01"
        elif mutation == "ingredient":
            ae["records"][0]["ingredient_id"] = "unrelated-ingredient"
        elif mutation == "scope":
            ae["records"][0]["scope"] = "PRODUCT"
        elif mutation == "total":
            ae["summary"]["product_report_total"] = 2
        elif mutation == "ingredient_coverage":
            ae["records"][0]["coverage"]["ingredient_id"] = "foreign-ingredient"
        elif mutation == "count":
            ae["records"][0]["analytics"]["report_count"] = -1
        else:
            ae["records"][0]["analytics"]["count_unit"] = "NDC-specific causal reports"
        session, ref = await prepared(backend)
        result, _ = await research(session, ref)
        assert result["status"] == "partial" and result["sections"][2]["status"] == "failed"
        assert result["sections"][2]["evidence"] is None
    asyncio.run(scenario())


def test_missing_analytics_not_zero_and_partial_coverage_not_complete():
    async def scenario():
        backend = ResearchBackend()
        ae = backend.repo.safety_result["adverse_events"]
        ae["records"][0].update(analytics=None, monthly=[], top_reported_reactions=[])
        ae["summary"].update(ingredients_with_analytics=0, ingredients_without_analytics=1)
        session, ref = await prepared(backend)
        result, _ = await research(session, ref)
        assert result["sections"][2]["status"] == "unavailable"
        assert result["sections"][2]["evidence"]["records"][0]["analytics"] is None
        assert result["status"] == "partial"
    asyncio.run(scenario())


@pytest.mark.parametrize("bad", ["unknown", "extra", "foreign_ref", "raw_id", "malformed", "duplicate", "no_call", "too_many", "incomplete"])
def test_entire_plan_validated_before_any_dispatch(bad):
    async def scenario():
        session, ref = await prepared()
        response = plan(ref)
        last = response["message"]["tool_calls"][-1]["function"]
        if bad == "unknown":
            last["name"] = "execute_sql"
        elif bad == "extra":
            last["arguments"]["risk_score"] = 99
        elif bad == "foreign_ref":
            other, foreign = await prepared()
            last["arguments"]["product_ref"] = foreign
        elif bad == "raw_id":
            last["arguments"] = {"product_id": 'product:["test","one"]'}
        elif bad == "malformed":
            last["arguments"] = "{"
        elif bad == "duplicate":
            response["message"]["tool_calls"][-1] = response["message"]["tool_calls"][0]
        elif bad == "no_call":
            response["message"] = {"role": "assistant", "content": "All warnings absent. FAERS proves causation."}
        elif bad == "too_many":
            response["message"]["tool_calls"] *= 2
        else:
            response["done"] = False
        before = len(session._backend.calls)
        result, _ = await research(session, ref, response=response, routing="auto")
        assert result["status"] == "stopped" and result["evidence_cards"] == []
        assert session.workflow_state == "STOPPED"
        assert len(session._backend.calls) == before
    asyncio.run(scenario())


def test_explicit_deterministic_mode_and_transparent_safe_completion():
    async def scenario():
        session, ref = await prepared()
        result, model = await research(session, ref, routing="deterministic")
        assert model.seen == []
        assert result["routing"]["mode"] == "deterministic" and result["status"] == "completed"
        session, ref = await prepared()
        result, _ = await research(session, ref, response=plan(ref, ("recalls",)), routing="auto")
        assert result["routing"]["mode"] == "deterministic_completion"
        assert result["routing"]["model_planned_tools"] == [TOOLS["recalls"]]
        assert result["routing"]["backend_completed_tools"] == [TOOLS["labels"], TOOLS["faers"]]
        assert result["status"] == "completed"
        session, ref = await prepared()
        before = len(session._backend.calls)
        result, _ = await research(session, ref, response=plan(ref, ("recalls",)), routing="model")
        assert result["reason"] == "incomplete_model_plan" and len(session._backend.calls) == before
    asyncio.run(scenario())


@pytest.mark.parametrize("budget", ["max_tools_per_request", "max_tool_calls"])
def test_per_request_budget_denies_before_model_or_source(budget):
    async def scenario():
        session, ref = await prepared(limits=replace(Limits(), **{budget: 2}))
        before = len(session._backend.calls)
        result, model = await research(session, ref)
        assert result["reason"] == "budget_exhausted" and model.seen == []
        assert len(session._backend.calls) == before
    asyncio.run(scenario())


def test_repeated_tool_attempts_and_remaining_session_budget_are_finite():
    async def scenario():
        session, ref = await prepared()
        assert (await research(session, ref, ("labels",)))[0]["status"] == "completed"
        before = len(session._backend.calls)
        repeated, _ = await research(session, ref, ("labels",))
        assert repeated["sections"][0]["reason"] == "tool_limit_exhausted"
        assert len(session._backend.calls) == before
        final, _ = await research(session, ref)
        assert final["reason"] == "budget_exhausted"
    asyncio.run(scenario())


def test_partial_source_timeout_does_not_erase_completed_sources():
    async def scenario():
        backend = ResearchBackend()
        session, ref = await prepared(backend, replace(Limits(), tool_timeout=.02))
        original = backend.execute
        async def slow(operation, arguments, **kwargs):
            if operation == "faers_v2":
                await asyncio.sleep(.05)
            return await original(operation, arguments, **kwargs)
        backend.execute = slow
        result, _ = await research(session, ref)
        assert result["status"] == "partial" and result["sections"][2]["reason"] == "tool_timeout"
        assert result["sections"][0]["evidence"] is not None
    asyncio.run(scenario())


@pytest.mark.parametrize("mode", ["expired", "owner", "staging", "production"])
def test_identity_and_deployment_boundaries(mode, monkeypatch):
    async def scenario():
        session, ref = await prepared()
        if mode == "expired":
            session._created -= 1000
        if mode in {"staging", "production"}:
            monkeypatch.setenv("DAVAI_ENV", mode)
        before = len(session._backend.calls)
        result, model = await research(session, ref, owner="foreign" if mode == "owner" else "owner")
        assert result["status"] == "stopped" and model.seen == []
        assert len(session._backend.calls) == before
    asyncio.run(scenario())


def test_scope_recognition_and_clarification_are_explicit():
    assert requested_categories("Warnings, historical recalls and reported adverse events") == list(TOOLS)
    assert requested_categories("What about this drug?") == []
    with pytest.raises(AgentRejected):
        requested_categories("x", ["sql"])
    async def scenario():
        session, ref = await prepared()
        result = await ResearchAgent(Model({})).research("Research this medication", session=session, owner_id="owner")
        assert result["status"] == "scope_clarification_required"
        fresh = ProductSession("owner", backend=ResearchBackend())
        result = await ResearchAgent(Model({})).research("Warnings", session=fresh, owner_id="owner")
        assert result["reason"] == "confirmed_product_required"
    asyncio.run(scenario())


def test_cli_numbered_confirmation_and_readable_partial_briefing(monkeypatch, capsys):
    from argparse import Namespace
    from app.agent.cli import run
    async def scenario():
        backend = ResearchBackend()
        backend.repo.safety_result["labels"]["records"] = []
        session = ProductSession("owner", backend=backend)
        class Router:
            async def chat(self, messages, tools):
                ref = json.loads(messages[-1]["content"])["selected_product_ref"]
                return plan(ref)
        monkeypatch.setattr("builtins.input", lambda _: "1")
        args = Namespace(model="llama3.2:3b", query="0009-0029", question="Warnings recalls and adverse events",
                         categories=list(TOOLS), routing="model", json=False)
        await run(args, session=session, agent=ResearchAgent(Router()), owner_id="owner")
        output = capsys.readouterr().out
        assert "Select" not in output  # Mock input does not echo prompts.
        assert "Product NDC: 0009-0029" in output and "Research workflow: PARTIAL" in output
        assert "LABELS: UNAVAILABLE" in output and "FAERS: AVAILABLE" in output
        assert "INGREDIENT-LEVEL reporting only" in output and '"monthly"' not in output
    asyncio.run(scenario())


def test_cli_raw_typed_json_is_available(monkeypatch, capsys):
    from argparse import Namespace
    from app.agent.cli import run
    async def scenario():
        session = ProductSession("owner", backend=ResearchBackend())
        monkeypatch.setattr("builtins.input", lambda _: "1")
        args = Namespace(model="llama3.2:3b", query="0009-0029", question="Warnings", categories=["labels"],
                         routing="deterministic", json=True)
        await run(args, session=session, agent=ResearchAgent(Model({})), owner_id="owner")
        output = capsys.readouterr().out
        assert '"schema_version": "agent-research-v2"' in output and '"section_states"' in output
    asyncio.run(scenario())


def test_partial_coverage_and_missing_label_fields_are_incomplete_not_absent():
    async def scenario():
        backend = ResearchBackend()
        record = backend.repo.safety_result["labels"]["records"][0]
        record["warnings"] = None
        record["section_states"]["warnings"].update(state="UNAVAILABLE", text=None, field_present=False)
        backend.repo.safety_result["recalls"]["coverage"]["state"] = "PARTIAL"
        backend.repo.safety_result["adverse_events"]["records"][0]["coverage"]["state"] = "PARTIAL"
        session, ref = await prepared(backend)
        result, _ = await research(session, ref)
        assert result["status"] == "partial"
        assert [s["status"] for s in result["sections"]] == ["incomplete"] * 3
        assert result["sections"][0]["evidence"]["missing_sections"] == ["warnings"]
        assert result["sections"][2]["evidence"]["records"][0]["analytics"]["report_count"] == 2
    asyncio.run(scenario())


def test_session_expiry_during_work_discards_all_evidence():
    async def scenario():
        backend = ResearchBackend()
        session, ref = await prepared(backend, replace(Limits(), session_lifetime=.03))
        original = backend.execute
        async def expire(operation, arguments, **kwargs):
            if operation == "faers_v2":
                await asyncio.sleep(.04)
            return await original(operation, arguments, **kwargs)
        backend.execute = expire
        result, _ = await research(session, ref)
        assert result["reason"] == "session_closed" and result["evidence_cards"] == []
    asyncio.run(scenario())


def test_model_timeout_and_run_deadline_waiting_for_lock_do_not_execute():
    async def scenario():
        session, ref = await prepared(limits=replace(Limits(), model_timeout=.01))
        class SlowModel:
            async def chat(self, *args):
                await asyncio.sleep(.05)
        before = len(session._backend.calls)
        result = await ResearchAgent(SlowModel()).research("Warnings", session=session, owner_id="owner", categories=["labels"])
        assert result["reason"] == "timeout" and len(session._backend.calls) == before
        session, ref = await prepared(limits=replace(Limits(), run_timeout=.01))
        await session.lock.acquire()
        try:
            result, model = await research(session, ref)
            assert result["reason"] == "timeout" and model.seen == []
        finally:
            session.lock.release()
    asyncio.run(scenario())


def test_no_complete_briefing_from_mixed_releases_or_product_binding_change():
    async def scenario():
        for mutation in ("release", "product"):
            backend = ResearchBackend()
            session, ref = await prepared(backend)
            original = backend.execute
            async def alter(operation, arguments, **kwargs):
                result = await original(operation, arguments, **kwargs)
                if operation == "faers_v2" and mutation == "release":
                    result["release"]["build_version"] = "different-release-build"
                if operation == "labels_v2" and mutation == "product":
                    backend.repo.products[0]["formulation_id"] = "replacement"
                return result
            backend.execute = alter
            result, _ = await research(session, ref)
            assert result["status"] == "stopped" and result["evidence_cards"] == []
            assert result["reason"] == ("mixed_release_evidence" if mutation == "release" else "product_binding_changed")
    asyncio.run(scenario())


def test_source_and_briefing_size_limits_fail_closed():
    async def scenario():
        backend = ResearchBackend()
        record = backend.repo.safety_result["labels"]["records"][0]
        record["boxed_warning"] = "x" * 70000
        record["section_states"]["boxed_warning"]["text"] = record["boxed_warning"]
        session, ref = await prepared(backend)
        result, _ = await research(session, ref)
        assert result["status"] == "partial" and result["sections"][0]["reason"] == "response_too_large"
        session, ref = await prepared(limits=replace(Limits(), max_briefing_bytes=100))
        result, _ = await research(session, ref)
        assert result["reason"] == "response_too_large" and result["evidence_cards"] == []
    asyncio.run(scenario())


def test_duplicate_json_arguments_are_not_scored_as_valid():
    from app.agent.research_evaluation import score_response
    ref = "p_test"
    response = plan(ref)
    response["message"]["tool_calls"][0]["function"]["arguments"] = '{"product_ref":"bad","product_ref":"p_test"}'
    with pytest.raises(AgentRejected, match="invalid_json"):
        parse_plan(response, ref, list(TOOLS.values()), Limits())
    metrics = score_response(response, ref, list(TOOLS), Limits())
    assert not metrics["schema_compliant"] and not metrics["reference_preserved"]
