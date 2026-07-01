from fastapi import APIRouter, HTTPException, Query, Request

from app.db.audit_repository import AuditPersistenceError
from app.db.source_pull_repository import SourcePullPersistenceError
from app.schemas.cosmetic_events import CosmeticEventSearchResponse
from app.services.search_workflows.cosmetic_signal_search import execute_cosmetic_signal_search

router = APIRouter()


@router.get("/search", response_model=CosmeticEventSearchResponse)
async def search_cosmetic_events(
    request: Request,
    q: str = Query(..., min_length=2, description="Cosmetic brand, product, reaction, or outcome keyword"),
    limit: int = Query(10, ge=1, le=25),
):
    request_id = getattr(request.state, "request_id", None)

    try:
        return await execute_cosmetic_signal_search(
            query=q,
            limit=limit,
            request_id=request_id,
        )

    except (AuditPersistenceError, SourcePullPersistenceError) as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "message": "CosmeticSignal search completed source work but could not persist required audit/provenance metadata.",
                "code": "COSMETIC_SIGNAL_PROVENANCE_PERSISTENCE_UNAVAILABLE",
            },
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Unable to retrieve cosmetic event data from openFDA.",
                "code": "OPENFDA_COSMETIC_EVENT_UPSTREAM_UNAVAILABLE",
            },
        ) from exc
