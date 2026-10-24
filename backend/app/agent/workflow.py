"""Finite Agent v2 workflow: scope -> plan -> bounded source reads -> briefing."""
import asyncio
import json
import re

from app.agent.briefing import build_briefing, validate_card
from app.agent.contracts import AgentRejected, encode, tool_schema
from app.agent.orchestrator import SYSTEM_PROMPT, parse_proposal
from app.agent.research_contracts import TOOLS

RESEARCH_PROMPT = SYSTEM_PROMPT.replace("Return exactly one tool call.",
    "Return one tool call for EACH requested evidence category, at most three calls total.").replace(
    "call search_historical_recalls with that exact reference.",
    "call the requested evidence tools with that exact reference. Labels are product-linked; FAERS is ingredient-level.")


def requested_categories(question, explicit=None):
    if explicit is not None:
        if (not isinstance(explicit, (list, tuple)) or not explicit
                or any(type(value) is not str or value not in TOOLS for value in explicit)
                or len(set(explicit)) != len(explicit)):
            raise AgentRejected("invalid_research_categories")
        return [category for category in TOOLS if category in explicit]
    # Transparent literal-category recognition, not a claim of semantic medical planning.
    patterns = {"labels": r"\b(label(?:ing|s)?|warnings?|boxed|contraindications?|interactions?)\b",
                "recalls": r"\brecalls?\b",
                "faers": r"\b(faers|adverse events?|reported reactions?|spontaneous reports?)\b"}
    return [key for key, pattern in patterns.items() if re.search(pattern, question, re.I)]


def parse_plan(response, reference, names, limits):
    encode(response, limits.max_response_bytes)
    if not isinstance(response, dict) or response.get("done") is not True:
        raise AgentRejected("incomplete_model_response")
    message = response.get("message")
    if not isinstance(message, dict) or message.get("role") != "assistant":
        raise AgentRejected("invalid_model_response")
    calls = message.get("tool_calls")
    if not calls:
        raise AgentRejected("missing_tool_call")
    if not isinstance(calls, list) or len(calls) > limits.max_tools_per_request:
        raise AgentRejected("excessive_tool_calls")
    plan = []
    for call in calls:
        # Reuse v1's strict JSON/extra-argument/reference checks. Validate the entire
        # batch before any dispatch, including calls following a valid first call.
        name, _ = parse_proposal({"done": True, "message": {"role": "assistant", "tool_calls": [call]}},
            selected_ref=reference, limit=limits.max_response_bytes, allowed_tools=names)
        if name in plan:
            raise AgentRejected("repeated_tool_call")
        plan.append(name)
    return plan, bool(message.get("content") or message.get("thinking"))


class ResearchWorkflow:
    def __init__(self, client, *, enable_rag=True, rag_corpus_path=None, rag_index_path=None,
                 rag_embedder=None, rag_retriever=None, **kwargs):
        self.client = client
        self.enable_rag = enable_rag
        self.rag_corpus_path = rag_corpus_path
        self.rag_index_path = rag_index_path
        self.rag_embedder = rag_embedder
        self.rag_retriever = rag_retriever

    async def run(self, question, *, session, owner_id, categories=None, routing="auto", synthesize=False):
        outcomes, requested = {}, []
        route = {"mode": "deterministic" if routing == "deterministic" else "model",
                 "model_planned_tools": [], "backend_completed_tools": [], "discarded_model_content": False}
        locked = False
        finished = None
        try:
            session.authorize(owner_id)
            if type(question) is not str or not question.strip() or len(question) > 2000:
                raise AgentRejected("invalid_question")
            if routing not in {"auto", "model", "deterministic"}:
                raise AgentRejected("invalid_routing_mode")
            requested = requested_categories(question, categories)
            if not requested:
                return {"status": "scope_clarification_required", "categories_available": list(TOOLS), "evidence_cards": []}
            if not session.selected_ref:
                return {"status": "confirmation_required", "reason": "confirmed_product_required", "evidence_cards": []}
            limits = session.limits
            async with asyncio.timeout(limits.run_timeout):
                await session.lock.acquire()
                locked = True
                session.authorize(owner_id)
                if (session.iterations >= limits.max_iterations
                        or len(requested) > limits.max_tools_per_request
                        or session.tool_calls + len(requested) > limits.max_tool_calls):
                    raise AgentRejected("budget_exhausted")
                session.iterations += 1
                session.workflow_state = "PLANNING"
                names = [TOOLS[category] for category in requested]
                if routing == "deterministic":
                    # Explicitly requested categories authorize this read-only plan.
                    route["backend_completed_tools"] = names
                else:
                    messages = [{"role": "system", "content": RESEARCH_PROMPT}, {"role": "user", "content": json.dumps({
                        "question": question, "selected_product_ref": session.selected_ref,
                        "requested_evidence_tools": names})}]
                    schemas = tool_schema(session.selected_ref, names)
                    encode({"messages": messages, "tools": schemas}, limits.max_prompt_bytes)
                    response = await asyncio.wait_for(self.client.chat(messages, schemas), limits.model_timeout)
                    try:
                        planned, discarded = parse_plan(response, session.selected_ref, names, limits)
                    except AgentRejected:
                        session.tool_calls += 1  # Failed proposals consume budget too.
                        raise
                    route["model_planned_tools"], route["discarded_model_content"] = planned, discarded
                    missing = [name for name in names if name not in planned]
                    if missing and routing == "model":
                        session.tool_calls += len(planned)
                        raise AgentRejected("incomplete_model_plan")
                    if missing:
                        route["mode"] = "deterministic_completion"
                        route["backend_completed_tools"] = missing
                session.tool_calls += len(requested)  # Reserve all source attempts up front.
                session.workflow_state = "EXECUTING"
                for category in requested:
                    session.authorize(owner_id)
                    if session.research_attempts.get(category, 0) >= limits.max_calls_per_tool:
                        outcomes[category] = "tool_limit_exhausted"
                        continue
                    session.research_attempts[category] = session.research_attempts.get(category, 0) + 1
                    try:
                        product = await session._verified_product(session.selected_ref)
                        result = await session._execute(category + "_v2", {"product_id": product["product_id"]})
                        session.authorize(owner_id)
                        outcomes[category] = validate_card(category, session.selected_ref,
                            session._public(session.selected_ref), product, result)
                    except TimeoutError:
                        outcomes[category] = "tool_timeout"
                    except AgentRejected as exc:
                        if str(exc) in {"hosted_serving_denied", "wrong_session_owner", "session_closed", "product_binding_changed"}:
                            raise
                        outcomes[category] = str(exc)
                    except Exception:
                        outcomes[category] = "evidence_unavailable"

                rag_evidence = None
                if self.enable_rag:
                    try:
                        product = session._candidates.get(session.selected_ref, {})
                        from app.agent.rag_adapter import execute_hybrid_rag
                        rag_evidence = execute_hybrid_rag(
                            question,
                            product,
                            session.selected_ref,
                            corpus_path=self.rag_corpus_path,
                            index_path=self.rag_index_path,
                            embedder=self.rag_embedder,
                            retriever=self.rag_retriever,
                        )
                    except Exception:
                        rag_evidence = None

                finished = self._finish(session, owner_id, requested, outcomes, route, rag=rag_evidence)
                if synthesize:
                    from app.agent.synthesis import synthesize_answer
                    product = await session._verified_product(session.selected_ref)
                    finished["answer"] = await synthesize_answer(question, finished, self.client, limits,
                        expected_product_id=product["product_id"])
                    session.authorize(owner_id)
                    await session._verified_product(session.selected_ref)
                    # Optional text must never make the existing briefing fail its bound.
                    try:
                        encode(finished, limits.max_briefing_bytes)
                    except AgentRejected:
                        finished["answer"] = None
                return finished
        except TimeoutError:
            if finished is not None:
                try:
                    session.authorize(owner_id)
                    from app.agent.synthesis import fallback
                    finished["answer"] = fallback(session.selected_ref, "unavailable", "model_timeout")
                    encode(finished, session.limits.max_briefing_bytes)
                    return finished
                except AgentRejected:
                    pass
            if locked and outcomes:
                for category in requested:
                    outcomes.setdefault(category, "request_timeout")
                try:
                    return self._finish(session, owner_id, requested, outcomes, route)
                except AgentRejected:
                    pass
            if locked:
                session.workflow_state = "STOPPED"
            return self._stop("timeout")
        except AgentRejected as exc:
            if locked:
                session.workflow_state = "STOPPED"
            return self._stop(str(exc))
        except Exception:
            if locked:
                session.workflow_state = "STOPPED"
            return self._stop("dependency_unavailable")
        finally:
            if locked:
                session.lock.release()

    @staticmethod
    def _stop(reason):
        return {"status": "stopped", "workflow_state": "STOPPED", "reason": reason, "evidence_cards": []}

    @staticmethod
    def _finish(session, owner_id, requested, outcomes, route, rag=None):
        session.authorize(owner_id)
        result = build_briefing(session._public(session.selected_ref), requested, outcomes, route, rag=rag)
        encode(result, session.limits.max_briefing_bytes)
        session.workflow_state = result["workflow_state"]
        return result
