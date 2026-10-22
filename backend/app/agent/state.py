"""Caller-owned sessions. No global registry, model selection, or reusable ID alias."""
import asyncio
from copy import deepcopy
import secrets
import time

from app.agent.contracts import AgentRejected, Limits, encode
from app.agent.tools import _project_product
from app.services.pharma.evidence import official_source


class ProductSession:
    def __init__(self, owner_id: str, *, backend, limits: Limits = Limits()):
        if type(owner_id) is not str or not owner_id or len(owner_id) > 256:
            raise ValueError("A trusted caller identity is required")
        self._owner = owner_id
        self._backend = backend
        self.limits = limits
        self._created = time.monotonic()
        self._candidates = {}
        self._selected = None
        self.iterations = 0
        self.tool_calls = 0
        self.research_attempts = {}
        self.workflow_state = "UNSELECTED"
        self.closed = False
        self.lock = asyncio.Lock()

    def authorize(self, owner_id):
        from app.db.database import is_deployed_environment
        if is_deployed_environment():
            raise AgentRejected("hosted_serving_denied")
        if type(owner_id) is not str or not secrets.compare_digest(owner_id.encode(), self._owner.encode()):
            raise AgentRejected("wrong_session_owner")
        if self.closed or time.monotonic() - self._created >= self.limits.session_lifetime:
            raise AgentRejected("session_closed")

    @property
    def selected_ref(self):
        return self._selected

    async def _execute(self, operation, arguments):
        result = await asyncio.wait_for(self._backend.execute(operation, arguments,
                                      timeout=self.limits.tool_timeout), self.limits.tool_timeout)
        encode(result, self.limits.max_evidence_bytes)
        return result

    def _public(self, reference):
        product = self._candidates[reference]
        return {"product_ref": reference, **{k: deepcopy(v) for k, v in product.items() if k != "product_id"}}

    async def _resolve(self, query):
        if self._selected:
            raise AgentRejected("selected_product_locked")
        result = await self._execute("resolve", {"query": query})
        if result.get("status") not in {"resolved", "needs_clarification", "not_found", "invalid_query"}:
            raise AgentRejected("invalid_resolver_result")
        candidates = result.get("candidates")
        if not isinstance(candidates, list) or len(candidates) > 100:
            raise AgentRejected("invalid_resolver_result")
        replacement = {}
        for product in candidates:
            if (not isinstance(product, dict) or not product.get("product_id")
                    or not product.get("formulation_id") or not product.get("product_ndcs")
                    or not isinstance(product.get("provenance"), dict)
                    or not official_source(product["provenance"].get("source_url"))):
                raise AgentRejected("missing_product_provenance")
            reference = "p_" + secrets.token_urlsafe(12)
            replacement[reference] = deepcopy(product)
        self._candidates = replacement  # Replace only after validating the whole result.
        return {"status": "confirmation_required" if candidates else "insufficient_evidence",
                "candidates": [self._public(ref) for ref in replacement],
                "results_may_be_incomplete": result.get("results_may_be_incomplete", False),
                "selection_rule": "Explicit user confirmation required; no automatic formulation selection."}

    async def resolve_for_user(self, query, *, owner_id):
        """Trusted UI/CLI search; never confirmation by a model tool call."""
        from app.agent.contracts import QueryArguments
        QueryArguments(query=query)
        async with self.lock:
            self.authorize(owner_id)
            result = await self._resolve(query)
            self.authorize(owner_id)
            return result

    async def confirm(self, reference, *, owner_id):
        """Embedding caller must obtain explicit human input, not model output."""
        async with self.lock:
            self.authorize(owner_id)
            if self._selected is not None:
                raise AgentRejected("selected_product_locked")
            if type(reference) is not str or reference not in self._candidates:
                raise AgentRejected("unknown_product_reference")
            await self._verified_product(reference)
            self.authorize(owner_id)
            self._selected = reference
            self.workflow_state = "CONFIRMED"
            return self._public(reference)

    async def _verified_product(self, reference):
        if type(reference) is not str or reference not in self._candidates:
            raise AgentRejected("unknown_product_reference")
        original = self._candidates[reference]
        actual = await self._execute("product", {"product_id": original["product_id"]})
        if actual is None or _project_product(actual) != original:
            raise AgentRejected("product_binding_changed")
        return original

    async def _recalls(self, reference):
        if reference not in self._candidates:
            raise AgentRejected("unknown_product_reference")
        if reference != self._selected:
            raise AgentRejected("product_not_confirmed")
        product = await self._verified_product(reference)
        result = await self._execute("recalls", {"product_id": product["product_id"]})
        from app.agent.evidence import evidence_card
        return evidence_card(reference, self._public(reference), product, result)
