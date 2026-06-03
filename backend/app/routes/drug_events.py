from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Request

from app.schemas.drug_events import DrugEventSearchResponse
from app.services.search_workflows.drug_signal_search import execute_drug_signal_search

router = APIRouter()


@router.get("/search", response_model=DrugEventSearchResponse)
async def search_drug_events(
    request: Request,
    q: str = Query(..., min_length=2, description="Drug name or medicinal product"),
    limit: int = Query(10, ge=1, le=25),
    sort: Literal["reports", "alpha"] = Query(
        "reports",
        description="Sort DrugSignal top reactions by report count or alphabetically.",
    ),
):
    request_id = getattr(request.state, "request_id", None)

    try:
        return await execute_drug_signal_search(
            query=q,
            limit=limit,
            request_id=request_id,
            sort=sort,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Unable to retrieve drug event data from openFDA.",
                "code": "OPENFDA_DRUG_EVENT_UPSTREAM_UNAVAILABLE",
            },
        ) from exc
