from fastapi import APIRouter, Query

from app.schemas.regional_health import RegionalHealthSearchResponse
from app.services.search_workflows.regional_health_search import (
    execute_regional_health_search,
)

router = APIRouter()


@router.get("/search", response_model=RegionalHealthSearchResponse)
async def search_regional_health(
    region: str = Query(..., min_length=2, max_length=80),
    category: str = Query(..., min_length=3, max_length=80),
):
    return execute_regional_health_search(region=region, category=category)
