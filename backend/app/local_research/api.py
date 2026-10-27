"""Socket-bound local research API. No global/public ASGI application exists."""
import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
import hashlib
import secrets
import socket
import time
from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import Field

from app.agent.backend import ProcessBackend
from app.agent.contracts import AgentRejected, Limits
from app.agent.model import MODELS, OllamaClient
from app.agent.orchestrator import ResearchAgent
from app.agent.research_contracts import (Category, Contract, ResearchBriefing, MedicationIdentity,
    Coverage, IngredientReporting, LabelRecord, RecallRecord, LabelCard, RecallCard, FaersCard, BriefingSection,
    RagEvidence, RagPassage)
from app.agent.state import ProductSession
from app.db.database import is_deployed_environment

ORIGINS = ("http://127.0.0.1:5173", "http://localhost:5173", "http://127.0.0.1:15173")


class Empty(Contract):
    pass


class Search(Contract):
    query: str = Field(min_length=1, max_length=200)


class Confirm(Contract):
    product_ref: str = Field(min_length=1, max_length=96)


class Research(Contract):
    question: str = Field(min_length=1, max_length=2000)
    categories: list[Category] = Field(min_length=1, max_length=3)
    model: Literal["llama3.2:3b", "qwen3.5:4b-q4_K_M"] | None = None
    synthesize: bool = False


class Candidate(Contract):
    product_ref: str
    brand_names: list[str]
    generic_name: str | None
    strength: str | None
    dosage_form: str | None
    routes: list[str]
    active_ingredients: list[str]
    product_ndcs: list[str]
    package_ndcs: list[str]


def candidate(value):
    return Candidate.model_validate({k: value[k] for k in Candidate.model_fields})


class Created(Contract):
    session_id: str
    capability: str
    expires_in: float
    models: list[str]
    model_runtime: Literal["available", "unavailable"]


class Candidates(Contract):
    state: Literal["confirmation_required", "empty"]
    candidates: list[Candidate]
    results_may_be_incomplete: bool


class Confirmed(Contract):
    state: Literal["confirmed"] = "confirmed"
    medication: Candidate


# Wire projections retain provenance, but remove repository identity keys. They
# remain derived from the validated Agent v2 contract, never browser-authored.
class PublicMedication(MedicationIdentity):
    formulation_id: str = Field(exclude=True)
    ingredient_ids: list[str] = Field(exclude=True)


class PublicCoverage(Coverage):
    ingredient_id: str | None = Field(default=None, exclude=True)


class PublicIngredient(IngredientReporting):
    ingredient_id: str = Field(exclude=True)
    coverage: PublicCoverage


class PublicLabelRecord(LabelRecord):
    id: str = Field(exclude=True)


class PublicRecallRecord(RecallRecord):
    id: str = Field(exclude=True)


class PublicLabel(LabelCard):
    records: list[PublicLabelRecord]
    coverage: PublicCoverage


class PublicRecall(RecallCard):
    records: list[PublicRecallRecord]
    product: PublicMedication
    coverage: PublicCoverage


class PublicFaers(FaersCard):
    records: list[PublicIngredient]
    coverage: PublicCoverage


class PublicRagPassage(RagPassage):
    pass


class PublicRagEvidence(RagEvidence):
    product_id: str = Field(exclude=True)


class PublicSection(BriefingSection):
    evidence: Annotated[PublicLabel | PublicRecall | PublicFaers, Field(discriminator="type")] | None = None


class PublicBriefing(ResearchBriefing):
    medication: PublicMedication
    sections: list[PublicSection]
    rag: PublicRagEvidence | None = None


class Outcome(Contract):
    state: Literal["running", "completed", "partial", "stopped", "confirmed", "closed"]
    code: str | None = None
    briefing: PublicBriefing | None = None


def fail(code, status=409):
    raise HTTPException(status, detail={"code": code})


def digest(token):
    return hashlib.sha256(token.encode()).digest()


@dataclass
class Entry:
    session: ProductSession
    credential: bytes
    owner: str
    created: float
    task: asyncio.Task | None = None
    outcome: Outcome | None = None
    started: bool = False
    busy: bool = False


class Registry:
    def __init__(self, pairing, *, backend_factory, model_factory, limits, max_sessions=8):
        self.pairing = digest(pairing)
        self.entries = {}
        self.backend_factory, self.model_factory, self.limits = backend_factory, model_factory, limits
        self.max_sessions, self.active = max_sessions, 0

    async def dispose(self, sid):
        entry = self.entries.pop(sid, None)
        if entry:
            entry.session.closed = True
            if entry.task and not entry.task.done():
                entry.task.cancel()
                await asyncio.gather(entry.task, return_exceptions=True)

    async def reap(self):
        for sid, entry in list(self.entries.items()):
            if entry.session.closed or time.monotonic() - entry.created >= self.limits.session_lifetime:
                await self.dispose(sid)

    def auth(self, request, sid):
        entry = self.entries.get(sid)
        if not entry:
            fail("session_expired", 410)
        if not secrets.compare_digest(digest(bearer(request)), entry.credential):
            fail("session_forbidden", 403)
        try:
            entry.session.authorize(entry.owner)
        except AgentRejected:
            fail("session_expired", 410)
        return entry

    def admit(self, entry=None):
        if self.active >= 1 or (entry and entry.busy):
            fail("research_busy", 429)
        self.active += 1
        if entry:
            entry.busy = True

    def release(self, entry=None):
        self.active -= 1
        if entry:
            entry.busy = False


def bearer(request):
    raw = request.headers.get("authorization", "")
    if not raw.startswith("Bearer ") or not 20 <= len(raw) <= 256:
        fail("authorization_required", 401)
    return raw[7:]


async def available_models(factory):
    try:
        result = await asyncio.wait_for(factory(MODELS[0]).request("/api/tags"), 2)
        names = {m.get("name") for m in result["models"]}
        return [m for m in MODELS if m in names]
    except Exception:
        return []


def create_app(listener: socket.socket, pairing: str, *, backend_factory=ProcessBackend,
               model_factory=OllamaClient, limits=Limits(), max_sessions=8):
    """Requires the actual prebound loopback listener used by the launcher."""
    if is_deployed_environment():
        raise RuntimeError("Hosted research serving denied")
    if (not isinstance(listener, socket.socket) or listener.family != socket.AF_INET
            or listener.getsockname()[0] != "127.0.0.1" or len(pairing) < 40):
        raise ValueError("A loopback-bound socket and strong pairing capability are required")
    host = f"127.0.0.1:{listener.getsockname()[1]}"
    registry = Registry(pairing, backend_factory=backend_factory, model_factory=model_factory,
                        limits=limits, max_sessions=max_sessions)

    @asynccontextmanager
    async def lifespan(app):
        if is_deployed_environment():
            raise RuntimeError("Hosted research serving denied")
        async def sweep():
            while True:
                await asyncio.sleep(1)
                await registry.reap()
        sweeper = asyncio.create_task(sweep())
        try:
            yield
        finally:
            sweeper.cancel()
            await asyncio.gather(sweeper, return_exceptions=True)
            for sid in list(registry.entries):
                await registry.dispose(sid)

    app = FastAPI(title="Ask Dav AI · local only", lifespan=lifespan,
                  docs_url=None, redoc_url=None, openapi_url=None)
    app.state.registry = registry
    app.add_middleware(CORSMiddleware, allow_origins=list(ORIGINS), allow_credentials=False,
                       allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type"])

    @app.middleware("http")
    async def boundary(request, call_next):
        code = None
        if is_deployed_environment():
            code = "hosted_serving_denied"
        elif (request.headers.get("host") != host or not request.client
              or request.client.host != "127.0.0.1" or request.headers.get("origin") not in ORIGINS
              or any(h in request.headers for h in ("forwarded", "x-forwarded-for", "x-forwarded-host"))):
            code = "local_boundary_required"
        if code:
            return JSONResponse({"detail": {"code": code}}, status_code=403,
                                headers={"Cache-Control": "no-store"})
        # Buffer at most 8 KiB before Pydantic parses anything, including chunked bodies.
        if request.method == "POST":
            body = bytearray()
            try:
                async with asyncio.timeout(5):
                    async for chunk in request.stream():
                        if len(body) + len(chunk) > 8192:
                            return JSONResponse({"detail": {"code": "request_too_large"}}, status_code=413)
                        body.extend(chunk)
            except TimeoutError:
                return JSONResponse({"detail": {"code": "request_timeout"}}, status_code=408)
            request._body = bytes(body)
        await registry.reap()
        response = await call_next(request)
        response.headers.update({"Cache-Control": "no-store", "Referrer-Policy": "no-referrer",
                                 "X-Content-Type-Options": "nosniff"})
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid(request, exc):
        return JSONResponse({"detail": {"code": "invalid_request"}}, status_code=422)

    @app.exception_handler(AgentRejected)
    async def rejected(request, exc):
        # Agent codes contain no exception details or user input.
        safe = {"selected_product_locked", "unknown_product_reference", "product_binding_changed", "session_closed"}
        return JSONResponse({"detail": {"code": str(exc) if str(exc) in safe else "evidence_unavailable"}}, status_code=409)

    @app.exception_handler(Exception)
    async def unavailable(request, exc):
        return JSONResponse({"detail": {"code": "dependency_unavailable"}}, status_code=503)

    @app.post("/api/local/research/sessions", response_model=Created)
    async def create(request: Request, body: Empty):
        if not secrets.compare_digest(digest(bearer(request)), registry.pairing):
            fail("pairing_forbidden", 403)
        if len(registry.entries) >= registry.max_sessions:
            fail("session_capacity", 429)
        registry.admit()
        try:
            models = await available_models(model_factory)
            sid, token, owner = (secrets.token_urlsafe(32) for _ in range(3))
            registry.entries[sid] = Entry(ProductSession(owner, backend=backend_factory(), limits=limits),
                                          digest(token), owner, time.monotonic())
            return Created(session_id=sid, capability=token, expires_in=float(limits.session_lifetime),
                           models=models, model_runtime="available" if models else "unavailable")
        finally:
            registry.release()

    async def operation(request, sid, function):
        entry = registry.auth(request, sid)
        registry.admit(entry)
        entry.task = asyncio.create_task(function(entry))
        try:
            async with asyncio.timeout(limits.tool_timeout + 1):
                return await entry.task
        except TimeoutError:
            entry.session.closed = True
            fail("timeout", 504)
        except asyncio.CancelledError:
            fail("cancelled")
        finally:
            registry.release(entry)

    @app.post("/api/local/research/sessions/{sid}/resolve", response_model=Candidates)
    async def resolve(sid: str, body: Search, request: Request):
        async def run(entry):
            result = await entry.session.resolve_for_user(body.query, owner_id=entry.owner)
            return Candidates(state="confirmation_required" if result["candidates"] else "empty",
                candidates=[candidate(p) for p in result["candidates"]],
                results_may_be_incomplete=result["results_may_be_incomplete"])
        return await operation(request, sid, run)

    @app.post("/api/local/research/sessions/{sid}/confirm", response_model=Confirmed)
    async def confirm(sid: str, body: Confirm, request: Request):
        async def run(entry):
            value = await entry.session.confirm(body.product_ref, owner_id=entry.owner)
            return Confirmed(medication=candidate(value))
        return await operation(request, sid, run)

    @app.post("/api/local/research/sessions/{sid}/research", response_model=Outcome)
    async def research(sid: str, body: Research, request: Request):
        entry = registry.auth(request, sid)
        if not entry.session.selected_ref:
            fail("confirmation_required")
        if entry.busy or (entry.task and not entry.task.done()):
            fail("research_already_started")
        if len(set(body.categories)) != len(body.categories) or not body.question.strip():
            fail("invalid_request", 422)
        registry.admit(entry)
        # Mark before the first await: repeated requests cannot enter concurrently.
        entry.started = True
        entry.outcome = Outcome(state="running")
        entry.session.research_attempts.clear()
        entry.session.tool_calls = 0
        entry.session.iterations = 0
        async def run():
            try:
                if body.model and body.model not in await available_models(model_factory):
                    entry.outcome = Outcome(state="stopped", code="model_unavailable")
                    return
                client = model_factory(body.model or MODELS[0])
                result = await ResearchAgent(client).research(body.question, session=entry.session,
                    owner_id=entry.owner, categories=body.categories,
                    routing="auto" if body.model else "deterministic", synthesize=body.synthesize)
                entry.session.authorize(entry.owner)
                if result.get("schema_version") == "agent-research-v2":
                    briefing = ResearchBriefing.model_validate(result)
                    entry.outcome = Outcome(state=briefing.status, briefing=PublicBriefing.model_validate(briefing.model_dump()))
                else:
                    reason = result.get("reason")
                    entry.outcome = Outcome(state="stopped", code=reason if reason in {
                        "timeout", "budget_exhausted", "product_binding_changed", "missing_tool_call",
                        "dependency_unavailable", "model_unavailable"} else "research_stopped")
            except asyncio.CancelledError:
                entry.outcome = Outcome(state="stopped", code="cancelled")
                raise
            except Exception:
                entry.outcome = Outcome(state="stopped", code="dependency_unavailable")
            finally:
                entry.started = False
        entry.task = asyncio.create_task(run())
        # A done callback also releases admission when cancelled before run starts.
        entry.task.add_done_callback(lambda task: registry.release(entry))
        return Outcome(state="running")

    @app.get("/api/local/research/sessions/{sid}/result", response_model=Outcome)
    async def result(sid: str, request: Request):
        entry = registry.auth(request, sid)
        return entry.outcome or Outcome(state="confirmed" if entry.session.selected_ref else "stopped")

    @app.post("/api/local/research/sessions/{sid}/cancel", response_model=Outcome)
    async def cancel(sid: str, body: Empty, request: Request):
        entry = registry.auth(request, sid)
        entry.session.closed = True
        await registry.dispose(sid)
        return Outcome(state="stopped", code="cancelled")

    @app.post("/api/local/research/sessions/{sid}/close", response_model=Outcome)
    async def close(sid: str, body: Empty, request: Request):
        registry.auth(request, sid)
        await registry.dispose(sid)
        return Outcome(state="closed")

    return app
