import argparse
import asyncio
from copy import deepcopy
import json
import pytest

from app.agent.cli import (
    format_candidate,
    format_candidates,
    format_strength,
    resolve_selection,
    run,
)
from app.agent.contracts import AgentRejected
from app.agent.orchestrator import ResearchAgent
from app.agent.state import ProductSession
from .test_orchestrator import Backend, Model, proposal
from .test_tools import Repository, product


def sample_candidate(ref="p_test1", *, name="Xanax", strength=".25 mg/1", ndc="0009-0029", pkg="0009-0029-01"):
    return {
        "product_ref": ref,
        "brand_names": [name],
        "generic_name": "alprazolam",
        "strength": strength,
        "dosage_form": "TABLET",
        "product_ndcs": [ndc],
        "package_ndcs": [pkg, pkg[:-2] + "02"],
        "active_ingredients": ["alprazolam"],
    }


def test_format_strength_normalization():
    assert format_strength(".25 mg/1") == "0.25 mg"
    assert format_strength("0.25 mg") == "0.25 mg"
    assert format_strength("2 mg/1") == "2 mg"
    assert format_strength("500 mg") == "500 mg"
    assert format_strength("10 mg/5mL") == "10 mg/5mL"
    assert format_strength("") == "Not supplied"
    assert format_strength(None) == "Not supplied"


def test_format_candidate_layout():
    c = sample_candidate("p_1")
    text = format_candidate(1, c)
    assert text == (
        "1. Xanax \u2014 0.25 mg \u2014 TABLET\n"
        "   Product NDC: 0009-0029\n"
        "   Package NDCs: 0009-0029-01, 0009-0029-02"
    )


def test_format_candidate_fallback_unnamed():
    c = {
        "product_ref": "p_2",
        "brand_names": [],
        "generic_name": "alprazolam",
        "strength": None,
        "dosage_form": None,
        "product_ndcs": [],
        "package_ndcs": [],
    }
    text = format_candidate(2, c)
    assert text == (
        "2. alprazolam \u2014 Not supplied \u2014 Not supplied\n"
        "   Product NDC: Not supplied\n"
        "   Package NDCs: Not supplied"
    )


def test_format_candidates_single():
    c1 = sample_candidate("p_1")
    output = format_candidates([c1])
    assert output.startswith("One product found.\n\n")
    assert "1. Xanax \u2014 0.25 mg \u2014 TABLET" in output


def test_format_candidates_multiple():
    c1 = sample_candidate("p_1", ndc="0009-0029", pkg="0009-0029-01")
    c2 = sample_candidate("p_2", ndc="58151-452", pkg="58151-452-01")
    output = format_candidates([c1, c2])
    assert output.startswith("Multiple products found.\n\n")
    assert "1. Xanax \u2014 0.25 mg \u2014 TABLET" in output
    assert "Product NDC: 0009-0029" in output
    assert "2. Xanax \u2014 0.25 mg \u2014 TABLET" in output
    assert "Product NDC: 58151-452" in output


@pytest.mark.parametrize("empty_input", ["", "   ", "\t\n"])
def test_resolve_selection_empty_cancels(empty_input):
    candidates = [sample_candidate("p_1"), sample_candidate("p_2")]
    assert resolve_selection(empty_input, candidates) is None


def test_resolve_selection_valid_index():
    candidates = [sample_candidate("p_1"), sample_candidate("p_2")]
    assert resolve_selection("1", candidates) == "p_1"
    assert resolve_selection("2", candidates) == "p_2"
    assert resolve_selection(" 1 ", candidates) == "p_1"


@pytest.mark.parametrize("invalid_input", ["0", "-1", "3", "99", "abc", "1.5", "1a", "p_1", None])
def test_resolve_selection_rejects_invalid(invalid_input):
    candidates = [sample_candidate("p_1"), sample_candidate("p_2")]
    with pytest.raises(AgentRejected, match="invalid_product_selection"):
        resolve_selection(invalid_input, candidates)


def test_resolve_selection_rejects_corrupt_candidate_list():
    with pytest.raises(AgentRejected, match="invalid_product_selection"):
        resolve_selection("1", [{"not_product_ref": "bad"}])


def test_cli_run_successful_numbered_selection(capsys, monkeypatch):
    async def scenario():
        p1 = product("one", ndc="0009-0029")
        p2 = product("two", ndc="58151-452")
        repo = Repository([p1, p2])
        backend = Backend(repo)
        owner = "owner-cli-test"
        session = ProductSession(owner, backend=backend)

        # After confirmation, model calls search_historical_recalls with confirmed ref
        async def chat_handler(messages, tools):
            ref = session.selected_ref
            return proposal("search_historical_recalls", {"product_ref": ref})

        agent = ResearchAgent(Model(proposal()))
        agent.client.chat = chat_handler

        # User enters "1"
        monkeypatch.setattr("builtins.input", lambda prompt: "1")

        args = argparse.Namespace(
            model="llama3.2:3b",
            query="0009-0029",
            question="Retrieve historical recall evidence for the exact product I confirm.",
        )

        await run(args, session=session, agent=agent, owner_id=owner)

        captured = capsys.readouterr()
        assert "Multiple products found." in captured.out
        assert "1. Xanax \u2014 0.25 mg \u2014 TABLET" in captured.out
        assert "Product NDC: 0009-0029" in captured.out
        assert "2. Xanax \u2014 0.25 mg \u2014 TABLET" in captured.out
        assert "Product NDC: 58151-452" in captured.out
        assert '"status": "evidence_ready"' in captured.out
        assert '"recall_number": "D-TEST-2016"' in captured.out
        assert session.selected_ref is not None
    asyncio.run(scenario())


def test_cli_run_single_product_numbered_selection(capsys, monkeypatch):
    async def scenario():
        p1 = product("one", ndc="0009-0029")
        repo = Repository([p1])
        backend = Backend(repo)
        owner = "owner-cli-test"
        session = ProductSession(owner, backend=backend)

        async def chat_handler(messages, tools):
            ref = session.selected_ref
            return proposal("search_historical_recalls", {"product_ref": ref})

        agent = ResearchAgent(Model(proposal()))
        agent.client.chat = chat_handler

        # User enters "1"
        monkeypatch.setattr("builtins.input", lambda prompt: "1")

        args = argparse.Namespace(
            model="llama3.2:3b",
            query="0009-0029",
            question="Retrieve historical recall evidence for the exact product I confirm.",
        )

        await run(args, session=session, agent=agent, owner_id=owner)

        captured = capsys.readouterr()
        assert "One product found." in captured.out
        assert "1. Xanax \u2014 0.25 mg \u2014 TABLET" in captured.out
        assert "Product NDC: 0009-0029" in captured.out
        assert '"status": "evidence_ready"' in captured.out
        assert '"recall_number": "D-TEST-2016"' in captured.out
        assert session.selected_ref is not None
    asyncio.run(scenario())


def test_cli_run_user_cancellation(capsys, monkeypatch):
    async def scenario():
        p1 = product("one", ndc="0009-0029")
        repo = Repository([p1])
        backend = Backend(repo)
        owner = "owner-cli-test"
        session = ProductSession(owner, backend=backend)
        agent = ResearchAgent(Model(proposal()))

        # User enters empty string to cancel
        monkeypatch.setattr("builtins.input", lambda prompt: "")

        args = argparse.Namespace(
            model="llama3.2:3b",
            query="0009-0029",
            question="Check recalls",
        )

        await run(args, session=session, agent=agent, owner_id=owner)

        captured = capsys.readouterr()
        assert "One product found." in captured.out
        # Session stopped without selecting product
        assert session.selected_ref is None
        # No evidence was retrieved
        assert "evidence_ready" not in captured.out
    asyncio.run(scenario())


def test_cli_run_invalid_number_stops_cleanly(capsys, monkeypatch):
    async def scenario():
        p1 = product("one", ndc="0009-0029")
        repo = Repository([p1])
        backend = Backend(repo)
        owner = "owner-cli-test"
        session = ProductSession(owner, backend=backend)
        agent = ResearchAgent(Model(proposal()))

        # User enters invalid index "5"
        monkeypatch.setattr("builtins.input", lambda prompt: "5")

        args = argparse.Namespace(
            model="llama3.2:3b",
            query="0009-0029",
            question="Check recalls",
        )

        await run(args, session=session, agent=agent, owner_id=owner)

        captured = capsys.readouterr()
        assert "One product found." in captured.out
        assert '"status": "stopped"' in captured.out
        assert '"reason": "invalid_product_selection"' in captured.out
        assert session.selected_ref is None
    asyncio.run(scenario())


def test_cli_run_eof_stops_cleanly(capsys, monkeypatch):
    async def scenario():
        p1 = product("one", ndc="0009-0029")
        repo = Repository([p1])
        backend = Backend(repo)
        owner = "owner-cli-test"
        session = ProductSession(owner, backend=backend)
        agent = ResearchAgent(Model(proposal()))

        def raise_eof(prompt):
            raise EOFError

        monkeypatch.setattr("builtins.input", raise_eof)

        args = argparse.Namespace(
            model="llama3.2:3b",
            query="0009-0029",
            question="Check recalls",
        )

        await run(args, session=session, agent=agent, owner_id=owner)

        captured = capsys.readouterr()
        assert "One product found." in captured.out
        assert '"status": "stopped"' in captured.out
        assert '"reason": "confirmation_missing"' in captured.out
        assert session.selected_ref is None
    asyncio.run(scenario())
