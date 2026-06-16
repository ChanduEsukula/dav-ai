from fastapi import APIRouter, HTTPException, Query

from app.schemas.docs import StaticDocsChunkPreviewResponse, StaticDocsSearchResponse
from app.services.static_docs_chunking import (
    DOCS_CHUNK_LIMITATIONS,
    preview_static_docs_chunks,
)
from app.services.static_docs_retrieval import (
    DOCS_SEARCH_LIMITATIONS,
    search_static_docs,
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
