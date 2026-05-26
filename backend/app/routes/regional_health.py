from fastapi import APIRouter, Query, Request

from app.schemas.regional_health import RegionalHealthSearchResponse
from app.services.search_workflows.regional_health_search import (
    execute_regional_health_search,
)

router = APIRouter()


@router.get("/search", response_model=RegionalHealthSearchResponse)
async def search_regional_health(
    request: Request,
    region: str = Query(..., min_length=2, max_length=80),
    category: str = Query(..., min_length=3, max_length=80),
):
    request_id = getattr(request.state, "request_id", None)

    return execute_regional_health_search(
        region=region,
        category=category,
        request_id=request_id,
    )
