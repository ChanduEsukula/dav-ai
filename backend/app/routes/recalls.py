from fastapi import APIRouter, HTTPException, Query, Request

from app.schemas.recalls import RecallSearchResponse
from app.services.search_workflows.recall_search import execute_recall_search

router = APIRouter()


@router.get("/search", response_model=RecallSearchResponse)
async def search_recalls(
    request: Request,
    q: str = Query(..., min_length=2, description="Drug, product, brand, or recall keyword"),
    limit: int = Query(10, ge=1, le=25),
):
    request_id = getattr(request.state, "request_id", None)

    try:
        return await execute_recall_search(
            query=q,
            limit=limit,
            request_id=request_id,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Unable to retrieve recall data from openFDA.",
                "code": "OPENFDA_RECALL_UPSTREAM_UNAVAILABLE",
            },
        ) from exc
