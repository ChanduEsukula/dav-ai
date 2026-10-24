"""Adapter bridging the confirmed-product research workflow to Hybrid RAG."""
import os
from pathlib import Path
import sys

from app.agent.research_contracts import RagEvidence, RagPassage
from app.agent.rag.corpus import document_key

DEFAULT_CORPUS_PATHS = (
    os.environ.get("DAV_AI_RAG_CORPUS_PATH"),
    "/private/tmp/dav-ai-rag-phase1b/corpus.json",
    "/private/tmp/dav-ai-label-rag-demo/corpus.json",
)

DEFAULT_INDEX_PATHS = (
    os.environ.get("DAV_AI_RAG_INDEX_PATH"),
    "/private/tmp/dav-ai-rag-phase1b/bge-index",
    "/private/tmp/dav-ai-label-rag-demo/bge-index",
)

SECTION_TITLES = {
    "boxed_warning": "Boxed Warning",
    "warnings_and_precautions": "Warnings & Precautions",
    "warnings": "General Warnings",
    "contraindications": "Contraindications",
    "drug_interactions": "Drug Interactions",
    "adverse_reactions": "Adverse Reactions",
}


def _find_path(candidates):
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return Path(candidate)
    return None


def get_default_embedder():
    """Try loading the FastEmbed adapter or sentence-transformers model without network calls."""
    try:
        sys.path.insert(0, "/private/tmp/dav-ai-rag-phase1b")
        from fastembed_adapter import FastEmbedBGE
        return FastEmbedBGE()
    except Exception:
        pass
    try:
        model_dir = os.environ.get("DAV_AI_BGE_MODEL_DIR")
        if model_dir and Path(model_dir).is_dir():
            from app.agent.rag.embeddings import LocalBGE
            return LocalBGE(model_dir)
    except Exception:
        pass
    return None


def execute_hybrid_rag(question: str, product: dict, product_ref: str, *,
                       corpus_path=None, index_path=None, embedder=None,
                       retriever=None) -> RagEvidence:
    """Execute hybrid RAG retrieval strictly scoped to the confirmed product.

    Returns typed RagEvidence. Fails gracefully to 'not_configured' or 'insufficient_evidence'
    if artifacts or dependencies are unavailable, never throwing unhandled errors.
    """
    product_id = product.get("product_id", "")
    try:
        from app.agent.rag.hybrid import HybridRetriever
        from app.agent.source_tools import get_drug_label_evidence

        if retriever is None:
            c_path = Path(corpus_path) if corpus_path and Path(corpus_path).exists() else (_find_path(DEFAULT_CORPUS_PATHS) if not corpus_path else None)
            i_path = Path(index_path) if index_path and Path(index_path).exists() else (_find_path(DEFAULT_INDEX_PATHS) if not index_path else None)

            if not c_path or not i_path:
                return RagEvidence(
                    status="not_configured",
                    reason="rag_artifacts_unavailable",
                    product_ref=product_ref,
                    product_id=product_id,
                    degraded_reason="corpus_or_index_not_found",
                    limitations=["Hybrid RAG vector index is not configured on this host."],
                )

            emb = embedder if embedder is not None else get_default_embedder()
            retriever = HybridRetriever.from_paths(
                str(c_path),
                str(i_path),
                embedder=emb,
                provider=get_drug_label_evidence,
                mode="route",
            )

        if not retriever.corpus:
            return RagEvidence(
                status="not_configured",
                reason="corpus_unavailable",
                product_ref=product_ref,
                product_id=product_id,
                degraded_reason=retriever.index_error,
                limitations=["RAG corpus could not be loaded."],
            )

        decision = retriever.retrieve(question, confirmed_product_id=product_id)

        # Build passages and provenance
        passages: list[RagPassage] = []
        if decision.chunk_ids:
            for cid in decision.chunk_ids:
                chunk = retriever.chunks.get(cid)
                if not chunk:
                    continue
                doc = retriever.documents.get(chunk.document_key)
                source_record_id = doc.label.source_record_id if doc else None
                source_url = doc.label.source_url if doc else None
                section_title = SECTION_TITLES.get(chunk.section, chunk.section.replace("_", " ").title())
                citation_tag = f"[FDA Label §{section_title} p.{chunk.ordinal + 1}]"

                passages.append(RagPassage(
                    chunk_id=chunk.chunk_id,
                    section=chunk.section,
                    ordinal=chunk.ordinal,
                    text=chunk.text,
                    source_record_id=source_record_id,
                    source_url=source_url,
                    citation_tag=citation_tag,
                ))

        limitations = [
            "Retrieved label passages are bounded strictly to the confirmed exact product formulation.",
            "Stored label sections represent quoted FDA source text, not an individualized medical opinion.",
        ]
        if decision.status == "candidate_only":
            limitations.append(
                "Candidate-only passages are nearest-neighbor matches in semantic embedding space. "
                "They are NOT verified clinical answers or medical conclusions."
            )
        elif decision.status == "insufficient_evidence":
            limitations.append(
                "No admitted label text was found sufficient to support this specific question."
            )

        return RagEvidence(
            status=decision.status,
            reason=decision.reason,
            product_ref=product_ref,
            product_id=product_id,
            requested_sections=list(decision.requested_sections),
            missing_sections=list(decision.missing_sections),
            route=decision.route,
            verified_answer=decision.verified_answer,
            confidence=decision.confidence,
            passages=passages,
            degraded_reason=decision.degraded_reason,
            limitations=limitations,
        )

    except Exception as exc:
        return RagEvidence(
            status="not_configured",
            reason="rag_execution_degraded",
            product_ref=product_ref,
            product_id=product_id,
            degraded_reason=str(exc),
            limitations=["Hybrid RAG execution encountered an internal degradation."],
        )
