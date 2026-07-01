from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Request

from app.db.audit_repository import AuditPersistenceError
from app.db.source_pull_repository import SourcePullPersistenceError
from app.schemas.recalls import RecallSearchResponse
from app.services.search_workflows.recall_search import execute_recall_search

router = APIRouter()


@router.get("/search", response_model=RecallSearchResponse)
async def search_recalls(
    request: Request,
    q: str = Query(..., min_length=2, description="Drug, product, brand, or recall keyword"),
    limit: int = Query(10, ge=1, le=25),
    sort: Literal["score", "latest"] = Query(
        "score",
        description="Sort recall results by review score or latest recall initiation date.",
    ),
):
    request_id = getattr(request.state, "request_id", None)

    try:
        return await execute_recall_search(
            query=q,
            limit=limit,
            request_id=request_id,
            sort=sort,
        )

    except (AuditPersistenceError, SourcePullPersistenceError) as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "message": "Recall search completed source work but could not persist required audit/provenance metadata.",
                "code": "RECALL_PROVENANCE_PERSISTENCE_UNAVAILABLE",
            },
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Unable to retrieve recall data from openFDA.",
                "code": "OPENFDA_RECALL_UPSTREAM_UNAVAILABLE",
            },
        ) from exc
