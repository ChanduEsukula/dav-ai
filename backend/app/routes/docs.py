from fastapi import APIRouter, HTTPException, Query

from app.schemas.docs import (
    StaticDocsChunkPreviewResponse,
    StaticDocsEmbeddingPreviewResponse,
    StaticDocsSemanticPreviewResponse,
    StaticDocsSearchResponse,
)
from app.services.static_docs_chunking import (
    DOCS_CHUNK_LIMITATIONS,
    preview_static_docs_chunks,
)
from app.services.static_docs_embeddings import (
    DOCS_EMBEDDING_PREVIEW_LIMITATIONS,
    preview_static_docs_embeddings,
)
from app.services.static_docs_retrieval import (
    DOCS_SEARCH_LIMITATIONS,
    search_static_docs,
)
from app.services.static_docs_semantic_preview import (
    DOCS_SEMANTIC_PREVIEW_LIMITATIONS,
    semantic_preview_search,
)

router = APIRouter()


@router.get("/search", response_model=StaticDocsSearchResponse)
async def search_docs(
    q: str = Query(
        ...,
        min_length=2,
        max_length=120,
        description="Keyword search over approved Dav AI documentation.",
    ),
    max_results: int = Query(
        8,
        ge=1,
        le=20,
        description="Maximum number of cited documentation snippets to return.",
    ),
):
    clean_query = q.strip()
    if len(clean_query) < 2:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Documentation search query must contain at least two non-whitespace characters.",
                "code": "DOCS_QUERY_TOO_SHORT",
            },
        )

    results = search_static_docs(clean_query, max_results=max_results)

    return {
        "query": clean_query,
        "count": len(results),
        "results": results,
        "limitations": DOCS_SEARCH_LIMITATIONS,
    }


@router.get("/chunks", response_model=StaticDocsChunkPreviewResponse)
async def preview_docs_chunks(
    max_results: int = Query(
        20,
        ge=1,
        le=100,
        description="Maximum number of deterministic documentation chunks to preview.",
    ),
):
    chunks = preview_static_docs_chunks(max_results=max_results)

    return {
        "count": len(chunks),
        "chunks": chunks,
        "limitations": DOCS_CHUNK_LIMITATIONS,
    }


@router.get("/embedding-preview", response_model=StaticDocsEmbeddingPreviewResponse)
async def preview_docs_embeddings(
    max_results: int = Query(
        20,
        ge=1,
        le=100,
        description="Maximum number of deterministic documentation embedding previews to return.",
    ),
):
    embeddings = preview_static_docs_embeddings(max_results=max_results)

    return {
        "count": len(embeddings),
        "embeddings": embeddings,
        "limitations": DOCS_EMBEDDING_PREVIEW_LIMITATIONS,
    }


@router.get("/semantic-preview", response_model=StaticDocsSemanticPreviewResponse)
async def preview_docs_semantic_retrieval(
    q: str = Query(
        ...,
        min_length=2,
        max_length=120,
        description="Deterministic preview query over stored documentation chunk preview embeddings.",
    ),
    max_results: int = Query(
        8,
        ge=1,
        le=20,
        description="Maximum number of deterministic semantic preview matches to return.",
    ),
):
    clean_query = q.strip()
    if len(clean_query) < 2:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Semantic preview query must contain at least two non-whitespace characters.",
                "code": "DOCS_SEMANTIC_PREVIEW_QUERY_TOO_SHORT",
            },
        )

    results = semantic_preview_search(clean_query, max_results=max_results)

    return {
        "query": clean_query,
        "count": len(results),
        "results": results,
        "limitations": DOCS_SEMANTIC_PREVIEW_LIMITATIONS,
    }
