"""Tests for Hybrid RAG integration into the confirmed-product research workflow."""
import asyncio
from copy import deepcopy
import json
import pytest

from app.agent.contracts import Limits
from app.agent.orchestrator import ResearchAgent
from app.agent.rag.corpus import Corpus, Document, Product, document_key, make_chunks
from app.agent.rag.embeddings import MockEmbedder
from app.agent.rag.hybrid import Decision, HybridRetriever
from app.agent.rag.index import RetrievalIndex
from app.agent.rag_adapter import execute_hybrid_rag
from app.agent.research_contracts import LabelRecord, RagEvidence, RagPassage, ReleaseInfo, ResearchBriefing
from app.agent.source_tools import get_drug_label_evidence
from app.agent.state import ProductSession
from app.agent.workflow import ResearchWorkflow
from app.local_research.api import Outcome, PublicBriefing, PublicRagEvidence
from .test_orchestrator import Backend, Model, selected
from .test_research import ResearchBackend, metadata, coverage, label_record, plan
from .test_tools import Repository, product


class StubRetriever:
    """Deterministic stub retriever for testing boundary conditions."""
    def __init__(self, decision, chunks=None, documents=None):
        self.decision = decision
        self.chunks = chunks or {}
        self.documents = documents or {}
        self.corpus = True
        self.index_error = None
        self.last_retrieved_product_id = None
        self.last_query = None

    def retrieve(self, question, confirmed_product_id=""):
        self.last_query = question
        self.last_retrieved_product_id = confirmed_product_id
        return self.decision


def create_synthetic_retriever(product_id="product:[\"test\",\"one\"]", ndc="0009-0029"):
    """Build a functional HybridRetriever with synthetic corpus using numpy-test engine."""
    meta = metadata()
    rel = ReleaseInfo.model_validate({k: meta[k] for k in ReleaseInfo.model_fields})
    label = label_record()
    label["matched_value"] = ndc
    doc = Document(
        product_id=product_id,
        formulation_id="formulation-one",
        product_ndcs=[ndc],
        strength=".25 mg/1",
        dosage_form="TABLET",
        routes=["ORAL"],
        active_ingredients=["alprazolam"],
        package_ndcs=[ndc + "-01"],
        brand_names=["Xanax"],
        source_id="source-label-test",
        source_snapshot_date="2026-09-25",
        release=rel,
        label=LabelRecord.model_validate(label),
    )
    p = Product(
        product_id=product_id,
        formulation_id="formulation-one",
        product_ndcs=[ndc],
        brand_names=["Xanax"],
        label_coverage={"state": "READY"},
    )
    c = Corpus(
        release_artifact_sha256="0" * 64,
        max_chars=128,
        products=[p],
        documents=[doc],
        chunks=make_chunks([doc], 128),
    )
    embedder = MockEmbedder()
    index = RetrievalIndex.build(c, embedder, engine="numpy-test")

    def provider(pid):
        return {
            "product_id": pid,
            "product_ndcs": [ndc],
            "release": rel.model_dump(),
            "evidence": {"records": [label]},
        }

    return HybridRetriever(c, index=index, embedder=embedder, provider=provider, mode="route")


def test_rag_executed_when_confirmed_product_and_retriever_provided():
    """Workflow automatically executes RAG for confirmed products and populates briefing.rag."""
    async def scenario():
        backend = ResearchBackend()
        session = ProductSession("owner", backend=backend)
        candidates = await session.resolve_for_user("0009-0029", owner_id="owner")
        ref = candidates["candidates"][0]["product_ref"]
        await session.confirm(ref, owner_id="owner")

        retriever = create_synthetic_retriever()
        model = Model(plan(ref, ("labels",)))
        agent = ResearchAgent(
            model,
            enable_rag=True,
            rag_retriever=retriever,
        )

        result = await agent.research(
            "What are the contraindications for this product?",
            session=session,
            owner_id="owner",
            categories=["labels"],
            routing="model",
        )

        briefing = ResearchBriefing.model_validate(result)
        assert briefing.status == "completed"
        assert briefing.rag is not None
        assert briefing.rag.product_ref == ref
        assert briefing.rag.status in ("supported", "candidate_only")
        assert len(briefing.rag.passages) > 0
        passage = briefing.rag.passages[0]
        assert passage.section in ("contraindications", "warnings")
        assert "FDA Label" in passage.citation_tag
        assert "Retrieved label passages are bounded strictly" in briefing.rag.limitations[0]

    asyncio.run(scenario())


def test_cross_product_isolation_and_scoping():
    """RAG retrieval is passed the confirmed product_id and cannot query other products."""
    async def scenario():
        backend = ResearchBackend()
        session = ProductSession("owner", backend=backend)
        candidates = await session.resolve_for_user("0009-0029", owner_id="owner")
        ref = candidates["candidates"][0]["product_ref"]
        await session.confirm(ref, owner_id="owner")

        stub_decision = Decision(
            status="supported",
            reason="verified_relevant_sections",
            product_id='product:["test","one"]',
            requested_sections=("contraindications",),
            chunk_ids=(),
            route="sql_section_check",
            verified_answer=True,
            confidence="calibrated",
        )
        stub = StubRetriever(stub_decision)

        model = Model(plan(ref, ("labels",)))
        agent = ResearchAgent(model, enable_rag=True, rag_retriever=stub)
        result = await agent.research(
            "Contraindications?",
            session=session,
            owner_id="owner",
            categories=["labels"],
        )

        assert stub.last_retrieved_product_id == 'product:["test","one"]'
        assert result["rag"]["product_id"] == 'product:["test","one"]'
        assert result["rag"]["product_ref"] == ref

    asyncio.run(scenario())


def test_session_switching_updates_rag_scoping():
    """Switching confirmed products correctly scopes RAG to the new product."""
    async def scenario():
        backend = ResearchBackend()
        session_a = ProductSession("owner", backend=backend)

        # Confirm Product A
        cand_a = await session_a.resolve_for_user("0009-0029", owner_id="owner")
        ref_a = cand_a["candidates"][0]["product_ref"]
        await session_a.confirm(ref_a, owner_id="owner")

        stub = StubRetriever(Decision(
            status="supported",
            reason="verified",
            product_id='product:["test","one"]',
            chunk_ids=(),
        ))
        agent_a = ResearchAgent(Model(plan(ref_a, ("labels",))), enable_rag=True, rag_retriever=stub)
        await agent_a.research("Query A", session=session_a, owner_id="owner", categories=["labels"])
        assert stub.last_retrieved_product_id == 'product:["test","one"]'

        # Now configure and confirm Product B on a new session
        p2 = product("two", ndc="0071-0155-23", name="Lipitor")
        p2["ingredient_ids"] = ["ingredient-test"]
        backend_b = ResearchBackend()
        backend_b.repo.products = [p2]
        session_b = ProductSession("owner", backend=backend_b)
        cand_b = await session_b.resolve_for_user("0071-0155-23", owner_id="owner")
        ref_b = cand_b["candidates"][0]["product_ref"]
        await session_b.confirm(ref_b, owner_id="owner")

        agent_b = ResearchAgent(Model(plan(ref_b, ("labels",))), enable_rag=True, rag_retriever=stub)
        await agent_b.research("Query B", session=session_b, owner_id="owner", categories=["labels"])
        assert stub.last_retrieved_product_id == 'product:["test","two"]'

    asyncio.run(scenario())


def test_missing_index_graceful_degradation():
    """Missing RAG index degrades cleanly to status='not_configured' without error."""
    async def scenario():
        backend = ResearchBackend()
        session = ProductSession("owner", backend=backend)
        candidates = await session.resolve_for_user("0009-0029", owner_id="owner")
        ref = candidates["candidates"][0]["product_ref"]
        await session.confirm(ref, owner_id="owner")

        # Point to definitely nonexistent artifacts
        agent = ResearchAgent(
            Model(plan(ref, ("labels",))),
            enable_rag=True,
            rag_corpus_path="/nonexistent/path/corpus.json",
            rag_index_path="/nonexistent/path/index",
        )

        result = await agent.research(
            "What are the warnings?",
            session=session,
            owner_id="owner",
            categories=["labels"],
        )

        briefing = ResearchBriefing.model_validate(result)
        assert briefing.status == "completed"
        # Core research tools completed normally
        assert briefing.sections[0].status == "available"
        # RAG degraded safely
        assert briefing.rag is not None
        assert briefing.rag.status == "not_configured"
        assert briefing.rag.reason == "rag_artifacts_unavailable"
        assert "not configured on this host" in briefing.rag.limitations[0]

    asyncio.run(scenario())


def test_candidate_only_semantic_matches_remain_unverified():
    """Candidate-only matches never claim verified_answer=True or calibrated confidence."""
    async def scenario():
        backend = ResearchBackend()
        session = ProductSession("owner", backend=backend)
        candidates = await session.resolve_for_user("0009-0029", owner_id="owner")
        ref = candidates["candidates"][0]["product_ref"]
        await session.confirm(ref, owner_id="owner")

        stub = StubRetriever(Decision(
            status="candidate_only",
            reason="candidate_semantic_matches",
            product_id='product:["test","one"]',
            route="bge_semantic",
            chunk_ids=(),
            verified_answer=False,
            confidence="uncalibrated",
        ))

        agent = ResearchAgent(Model(plan(ref, ("labels",))), enable_rag=True, rag_retriever=stub)
        result = await agent.research("Headache?", session=session, owner_id="owner", categories=["labels"])

        rag = result["rag"]
        assert rag["status"] == "candidate_only"
        assert rag["verified_answer"] is False
        assert rag["confidence"] == "uncalibrated"
        assert any("NOT verified clinical answers" in lim for lim in rag["limitations"])

    asyncio.run(scenario())


def test_insufficient_evidence_handling():
    """Unsupported topics or absent sections abstain cleanly with empty passages."""
    async def scenario():
        backend = ResearchBackend()
        session = ProductSession("owner", backend=backend)
        candidates = await session.resolve_for_user("0009-0029", owner_id="owner")
        ref = candidates["candidates"][0]["product_ref"]
        await session.confirm(ref, owner_id="owner")

        stub = StubRetriever(Decision(
            status="insufficient_evidence",
            reason="unsupported_topic",
            product_id='product:["test","one"]',
            chunk_ids=(),
            verified_answer=False,
            confidence="none",
        ))

        agent = ResearchAgent(Model(plan(ref, ("labels",))), enable_rag=True, rag_retriever=stub)
        result = await agent.research("Glaucoma?", session=session, owner_id="owner", categories=["labels"])

        rag = result["rag"]
        assert rag["status"] == "insufficient_evidence"
        assert rag["verified_answer"] is False
        assert rag["confidence"] == "none"
        assert len(rag["passages"]) == 0
        assert any("No admitted label text was found sufficient" in lim for lim in rag["limitations"])

    asyncio.run(scenario())


def test_public_briefing_api_serialization():
    """PublicBriefing wire contract serializes rag safely, excluding private product_id."""
    async def scenario():
        backend = ResearchBackend()
        session = ProductSession("owner", backend=backend)
        candidates = await session.resolve_for_user("0009-0029", owner_id="owner")
        ref = candidates["candidates"][0]["product_ref"]
        await session.confirm(ref, owner_id="owner")

        retriever = create_synthetic_retriever()
        agent = ResearchAgent(Model(plan(ref, ("labels",))), enable_rag=True, rag_retriever=retriever)
        raw_briefing = await agent.research(
            "Contraindications?",
            session=session,
            owner_id="owner",
            categories=["labels"],
        )

        # Validate with PublicBriefing
        public_briefing = PublicBriefing.model_validate(raw_briefing)
        outcome = Outcome(state="completed", briefing=public_briefing)
        serialized = outcome.model_dump(mode="json")

        assert serialized["state"] == "completed"
        assert "briefing" in serialized
        rag_wire = serialized["briefing"]["rag"]
        assert rag_wire is not None
        # Verify private product_id was excluded from wire format
        assert "product_id" not in rag_wire
        # Verify public fields are preserved
        assert rag_wire["product_ref"] == ref
        assert rag_wire["type"] == "hybrid_rag_evidence"
        assert rag_wire["status"] in ("supported", "candidate_only")
        assert isinstance(rag_wire["passages"], list)

    asyncio.run(scenario())
