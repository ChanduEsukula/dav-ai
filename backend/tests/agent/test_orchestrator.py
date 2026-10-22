import asyncio
from copy import deepcopy
from dataclasses import replace
import json

import pytest

from app.agent.contracts import AgentRejected, Limits
from app.agent.orchestrator import ResearchAgent
from app.agent.state import ProductSession
from app.agent.tools import resolve_drug_product, search_historical_recalls
from .test_tools import Repository, product


def proposal(name="search_historical_recalls", arguments=None, content=""):
    return {"done": True, "message": {"role": "assistant", "content": content, "tool_calls": [
        {"function": {"name": name, "arguments": arguments or {"product_ref": "unknown"}}}]}}


class Backend:
    def __init__(self, repo=None):
        self.repo = repo or Repository()
        self.calls = []

    async def execute(self, operation, arguments, *, timeout):
        self.calls.append((operation, arguments))
        if operation == "resolve":
            return resolve_drug_product(arguments["query"], self.repo)
        if operation == "product":
            return self.repo.find_by_id(arguments["product_id"])
        return search_historical_recalls(arguments["product_id"], self.repo)


class Model:
    def __init__(self, response):
        self.response, self.seen = response, []

    async def chat(self, messages, tools):
        self.seen.append((deepcopy(messages), deepcopy(tools)))
        return deepcopy(self.response)


async def selected(backend=None, limits=Limits()):
    session = ProductSession("owner", backend=backend or Backend(), limits=limits)
    candidates = await session.resolve_for_user("0009-0029", owner_id="owner")
    ref = candidates["candidates"][0]["product_ref"]
    await session.confirm(ref, owner_id="owner")
    return session, ref


def test_successful_selection_and_cards_no_database_id_or_narrative():
    async def scenario():
        session, ref = await selected()
        model = Model(proposal(arguments={"product_ref": ref}, content="ALL LOTS UNSAFE; D-FAKE-2099"))
        result = await ResearchAgent(model).run("Historical recalls?", session=session, owner_id="owner")
        assert result["status"] == "evidence_ready"
        encoded = json.dumps(result)
        assert "product:[" not in encoded and "D-FAKE" not in encoded and "ALL LOTS" not in encoded
        card = result["evidence_cards"][0]
        assert card["records"][0]["lot_scope"] == "UNKNOWN"
        assert card["coverage"]["state"] == "PARTIAL"
        assert "product:[" not in json.dumps(model.seen)
        assert model.seen[0][1][0]["function"]["parameters"]["properties"]["product_ref"]["enum"] == [ref]
    asyncio.run(scenario())


@pytest.mark.parametrize("kind, reason", [("missing", "missing_tool_call"), ("wrong", "incorrect_tool_name"),
    ("invalid_json", "invalid_json"), ("incomplete_id", "invalid_tool_arguments"),
    ("unknown", "unknown_product_reference"), ("duplicate", "invalid_json"),
    ("extra", "invalid_tool_arguments"), ("many", "excessive_tool_calls"), ("partial", "incomplete_model_response")])
def test_invalid_proposals_do_not_execute(kind, reason):
    async def scenario():
        session, ref = await selected()
        response = proposal(arguments={"product_ref": ref})
        function = response["message"]["tool_calls"][0]["function"]
        if kind == "missing":
            response["message"] = {"role": "assistant", "content": "FDA recall D-9999-2099 proves all lots unsafe."}
        if kind == "wrong":
            function["name"] = "run_sql"
        if kind == "invalid_json":
            function["arguments"] = "{"
        if kind == "incomplete_id":
            function["arguments"] = {"product_id": "0009-0029_f5323eac"}
        if kind == "unknown":
            function["arguments"] = {"product_ref": "p_unknown"}
        if kind == "duplicate":
            function["arguments"] = '{"product_ref":"bad","product_ref":"' + ref + '"}'
        if kind == "extra":
            function["arguments"]["applicability_class"] = "ALL_LOTS"
        if kind == "many":
            response["message"]["tool_calls"] *= 2
        if kind == "partial":
            response["done"] = False
        before = len(session._backend.calls)
        result = await ResearchAgent(Model(response)).run("Recalls?", session=session, owner_id="owner")
        assert result == {"status": "stopped", "reason": reason, "evidence_cards": []}
        assert len(session._backend.calls) == before
    asyncio.run(scenario())


def test_ambiguous_candidates_pause_and_cannot_be_model_confirmed():
    async def scenario():
        session = ProductSession("owner", backend=Backend(Repository([product(), product("two", ndc="9999-0001")])))
        result = await ResearchAgent(Model(proposal("resolve_drug_product", {"query": "Xanax .25 mg"}))).run(
            "Recall history of Xanax?", session=session, owner_id="owner")
        assert result["status"] == "confirmation_required"
        assert len(result["candidates"]) == 2
        assert session.selected_ref is None and result["evidence_cards"] == []
        result = await ResearchAgent(Model(proposal("confirm_product", {"product_ref": result["candidates"][0]["product_ref"]}))).run(
            "Select first", session=session, owner_id="owner")
        assert result["reason"] == "incorrect_tool_name"
        assert session.selected_ref is None
    asyncio.run(scenario())


def test_owner_and_cross_session_misuse_and_selection_lock():
    async def scenario():
        session, ref = await selected()
        other, _ = await selected()
        unselected = ProductSession("owner", backend=Backend())
        await unselected.resolve_for_user("Xanax", owner_id="owner")
        with pytest.raises(AgentRejected, match="unknown_product_reference"):
            await unselected.confirm(ref, owner_id="owner")
        with pytest.raises(AgentRejected, match="wrong_session_owner"):
            await session.confirm(ref, owner_id="intruder")
        with pytest.raises(AgentRejected, match="selected_product_locked"):
            await session.resolve_for_user("another drug", owner_id="owner")
        with pytest.raises(AgentRejected, match="selected_product_locked"):
            await session.confirm(ref, owner_id="owner")
        result = await ResearchAgent(Model(proposal(arguments={"product_ref": ref}))).run("Recalls", session=other, owner_id="owner")
        assert result["reason"] == "unknown_product_reference"
    asyncio.run(scenario())


@pytest.mark.parametrize("field, value, reason", [("applicability_class", "ALL_LOTS", "unsupported_recall_applicability"),
    ("matched_value", "wrong-ndc", "unsupported_recall_applicability"), ("source_url", None, "missing_source_provenance"),
    ("source_record_id", None, "missing_source_provenance"), ("lot_scope", "ALL", "unsupported_lot_scope")])
def test_incorrect_record_scope_or_provenance_denies_entire_card(field, value, reason):
    async def scenario():
        backend = Backend()
        session, ref = await selected(backend)
        backend.repo.safety_result["recalls"]["records"][0][field] = value
        result = await ResearchAgent(Model(proposal(arguments={"product_ref": ref}))).run("Recalls", session=session, owner_id="owner")
        assert result["reason"] == reason and result["evidence_cards"] == []
    asyncio.run(scenario())


def test_partial_empty_coverage_never_means_no_historical_recalls():
    async def scenario():
        backend = Backend()
        session, ref = await selected(backend)
        backend.repo.safety_result["recalls"]["records"] = []
        result = await ResearchAgent(Model(proposal(arguments={"product_ref": ref}))).run("Never recalled?", session=session, owner_id="owner")
        card = result["evidence_cards"][0]
        assert card["records"] == [] and card["coverage"]["state"] == "PARTIAL"
        assert "cannot establish no historical recalls" in card["interpretation"]
    asyncio.run(scenario())


@pytest.mark.parametrize("operation", ["model", "tool"])
def test_timeout_and_no_late_state_changes(operation):
    async def scenario():
        limits = replace(Limits(), model_timeout=.02, tool_timeout=.02, run_timeout=.03)
        session, ref = await selected(limits=limits)
        model = Model(proposal(arguments={"product_ref": ref}))
        async def slow(*args, **kwargs):
            await asyncio.sleep(.2)
            raise AssertionError("Cancelled work must never reach here")
        if operation == "model":
            model.chat = slow
        else:
            session._backend.execute = slow
        result = await ResearchAgent(model).run("Recalls", session=session, owner_id="owner")
        assert result["reason"] == "timeout" and session.closed
        assert session.selected_ref == ref
    asyncio.run(scenario())


@pytest.mark.parametrize("limit", ["max_iterations", "max_tool_calls"])
def test_session_budget_cannot_be_reset_by_resuming(limit):
    async def scenario():
        session, ref = await selected(limits=replace(Limits(), **{limit: 1}))
        model = Model(proposal(arguments={"product_ref": ref}))
        agent = ResearchAgent(model)
        assert (await agent.run("Recalls", session=session, owner_id="owner"))["status"] == "evidence_ready"
        assert (await agent.run("Again", session=session, owner_id="owner"))["reason"] == "budget_exhausted"
        assert len(model.seen) == 1
    asyncio.run(scenario())


def test_product_binding_changed_denied():
    async def scenario():
        session, ref = await selected()
        session._backend.repo.products[0]["strength"] = "1 mg/1"
        result = await ResearchAgent(Model(proposal(arguments={"product_ref": ref}))).run("Recalls", session=session, owner_id="owner")
        assert result["reason"] == "product_binding_changed"
    asyncio.run(scenario())


@pytest.mark.parametrize("mode", ["staging", "production", "preview"])
def test_hosted_denial_even_with_mock_model_and_repository(monkeypatch, mode):
    monkeypatch.setenv("DAVAI_ENV", mode)
    session = ProductSession("owner", backend=Backend())
    result = asyncio.run(ResearchAgent(Model(proposal())).run("Recalls", session=session, owner_id="owner"))
    assert result["reason"] == "hosted_serving_denied"
    assert session._backend.calls == []


@pytest.mark.parametrize("kind", ["snapshot", "coverage", "missing", "oversized"])
def test_missing_or_oversized_evidence_cannot_produce_cards(kind):
    async def scenario():
        backend = Backend()
        session, ref = await selected(backend)
        if kind == "snapshot":
            backend.repo.safety_result["recalls"]["coverage"]["source_date"] = None
        elif kind == "coverage":
            backend.repo.safety_result["recalls"]["coverage"]["limitations"] = []
        elif kind == "missing":
            backend.repo.safety_result = None
        else:
            backend.repo.safety_result["recalls"]["records"][0]["reason_for_recall"] = "x" * 70000
        result = await ResearchAgent(Model(proposal(arguments={"product_ref": ref}))).run("Recalls", session=session, owner_id="owner")
        assert result["status"] == "stopped" and result["evidence_cards"] == []
    asyncio.run(scenario())


def test_expired_session_and_model_response_size_are_bounded():
    async def scenario():
        session, ref = await selected(limits=replace(Limits(), max_response_bytes=512))
        response = proposal(arguments={"product_ref": ref}, content="x" * 513)
        result = await ResearchAgent(Model(response)).run("Recalls", session=session, owner_id="owner")
        assert result["reason"] == "response_too_large"
        session._created -= 1000
        result = await ResearchAgent(Model(response)).run("Recalls", session=session, owner_id="owner")
        assert result["reason"] == "session_closed"
    asyncio.run(scenario())


def test_lock_wait_is_included_in_run_deadline():
    async def scenario():
        session = ProductSession("owner", backend=Backend(), limits=replace(Limits(), run_timeout=.01))
        await session.lock.acquire()
        try:
            model = Model(proposal())
            result = await ResearchAgent(model).run("Recalls", session=session, owner_id="owner")
            assert result["reason"] == "timeout" and model.seen == []
        finally:
            session.lock.release()
    asyncio.run(scenario())


def test_confirmation_rechecks_binding_and_foreign_owner_never_calls_model():
    async def scenario():
        backend = Backend()
        session = ProductSession("owner", backend=backend)
        candidates = await session.resolve_for_user("Xanax", owner_id="owner")
        ref = candidates["candidates"][0]["product_ref"]
        backend.repo.products[0]["formulation_id"] = "replacement"
        with pytest.raises(AgentRejected, match="product_binding_changed"):
            await session.confirm(ref, owner_id="owner")
        assert session.selected_ref is None
        model = Model(proposal())
        result = await ResearchAgent(model).run("Recalls", session=session, owner_id="other-user")
        assert result["reason"] == "wrong_session_owner" and model.seen == []
    asyncio.run(scenario())


def test_unknown_reference_and_incomplete_id_cannot_confirm():
    async def scenario():
        session = ProductSession("owner", backend=Backend())
        await session.resolve_for_user("Xanax", owner_id="owner")
        for reference in ("selected_product", "one", 'product:["test","one"]', "0009-0029_f5323eac"):
            with pytest.raises(AgentRejected, match="unknown_product_reference"):
                await session.confirm(reference, owner_id="owner")
        assert session.selected_ref is None
    asyncio.run(scenario())


def test_foreign_caller_cannot_expire_a_busy_session():
    async def scenario():
        session = ProductSession("owner", backend=Backend(), limits=replace(Limits(), run_timeout=.01))
        await session.lock.acquire()
        try:
            result = await ResearchAgent(Model(proposal())).run("Recalls", session=session, owner_id="foreign")
            assert result["reason"] == "wrong_session_owner"
            assert not session.closed
        finally:
            session.lock.release()
    asyncio.run(scenario())


def test_session_expiry_during_confirmation_cannot_commit_selection():
    async def scenario():
        backend = Backend()
        session = ProductSession("owner", backend=backend, limits=replace(Limits(), session_lifetime=.02))
        candidates = await session.resolve_for_user("Xanax", owner_id="owner")
        reference = candidates["candidates"][0]["product_ref"]
        original = backend.execute
        async def delayed(*args, **kwargs):
            await asyncio.sleep(.03)
            return await original(*args, **kwargs)
        backend.execute = delayed
        with pytest.raises(AgentRejected, match="session_closed"):
            await session.confirm(reference, owner_id="owner")
        assert session.selected_ref is None
    asyncio.run(scenario())
