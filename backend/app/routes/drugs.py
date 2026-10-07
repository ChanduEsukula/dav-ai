import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from app.db.pharma.release_connection import PharmaceuticalReleaseUnavailable
from app.db.pharma.release_repository import FrozenPharmaReleaseRepository
from app.schemas.drugs import DrugOverview, DrugSearchResponse

router = APIRouter(prefix="/api/drugs", tags=["Drug Catalog"])
logger = logging.getLogger("dav_ai.pharma")


def get_repository():
    return FrozenPharmaReleaseRepository()


def unavailable():
    logger.warning("pharmaceutical_release_unavailable")
    return HTTPException(
        status_code=503,
        detail="Pharmaceutical release is unavailable",
    )


@router.get("/search", response_model=DrugSearchResponse)
def search_drugs(
    q: str = Query(..., min_length=1, max_length=200),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0, le=100000),
    repository=Depends(get_repository),
):
    if not q.strip():
        raise HTTPException(422, "Query must not be blank")

    try:
        rows = repository.search(
            q,
            limit=limit,
            offset=offset,
        )
    except PharmaceuticalReleaseUnavailable as exc:
        raise unavailable() from exc

    return {
        "query": q,
        "count": len(rows),
        "limit": limit,
        "offset": offset,
        "results": rows,
    }


@router.get("/{product_id}", response_model=DrugOverview)
def drug_detail(
    product_id: str,
    repository=Depends(get_repository),
):
    try:
        row = repository.find_by_id(product_id)
    except PharmaceuticalReleaseUnavailable as exc:
        raise unavailable() from exc

    if row is None:
        raise HTTPException(404, "Drug not found")

    return row
