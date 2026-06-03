from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Request

from app.schemas.everyday_safety import EverydaySafetySearchResponse
from app.services.search_workflows.everyday_safety_search import execute_everyday_safety_search

router = APIRouter()


@router.get("/search", response_model=EverydaySafetySearchResponse)
async def search_everyday_safety(
    request: Request,
    category: Literal["food_supplement"] = Query(
        ...,
        description="Everyday safety category. v0.1 supports food_supplement.",
    ),
    q: str = Query(..., min_length=2, description="Food, supplement, product, brand, or recall keyword"),
    limit: int = Query(10, ge=1, le=25),
):
    request_id = getattr(request.state, "request_id", None)

    try:
        return await execute_everyday_safety_search(
            category=category,
            query=q,
            limit=limit,
            request_id=request_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "message": str(exc),
                "code": "EVERYDAY_SAFETY_CATEGORY_NOT_IMPLEMENTED",
            },
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Unable to retrieve everyday safety data from openFDA.",
                "code": "OPENFDA_EVERYDAY_SAFETY_UPSTREAM_UNAVAILABLE",
            },
        ) from exc
