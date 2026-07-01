from typing import Literal
import logging

from fastapi import APIRouter, HTTPException, Query, Request

from app.db.audit_repository import AuditPersistenceError
from app.db.source_pull_repository import SourcePullPersistenceError
from app.schemas.real_world_safety import RealWorldSafetySearchResponse
from app.services.search_workflows.real_world_safety_search import execute_real_world_safety_search

router = APIRouter()
logger = logging.getLogger("dav_ai.real_world_safety.route")


@router.get("/search", response_model=RealWorldSafetySearchResponse)
async def search_real_world_safety(
    request: Request,
    q: str = Query(
        ...,
        min_length=2,
        description="Consumer product, vehicle make/model/year, VIN, brand, company, or public recall keyword.",
    ),
    limit: int = Query(10, ge=1, le=25),
    sort: Literal["score", "latest"] = Query(
        "score",
        description="Result ordering. score ranks by query relevance; latest ranks by newest source date.",
    ),
):
    request_id = getattr(request.state, "request_id", None)
    logger.info(
        "real_world_safety_route_entered",
        extra={
            "event": "real_world_safety_route_entered",
            "request_id": request_id,
            "query": q,
            "limit": limit,
            "sort": sort,
        },
    )

    if not q.strip():
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Real-world safety search query must contain at least two non-whitespace characters.",
                "code": "REAL_WORLD_SAFETY_QUERY_EMPTY",
            },
        )

    try:
        response = await execute_real_world_safety_search(
            query=q,
            limit=limit,
            sort=sort,
            request_id=request_id,
        )
        logger.info(
            "real_world_safety_route_completed",
            extra={
                "event": "real_world_safety_route_completed",
                "request_id": request_id,
                "query": q,
                "total_matches": response.get("total_matches"),
                "sources_failed": len(response.get("sources_failed", [])),
            },
        )
        return response
    except ValueError as exc:
        logger.info(
            "real_world_safety_route_rejected",
            extra={
                "event": "real_world_safety_route_rejected",
                "request_id": request_id,
                "query": q,
                "reason": str(exc),
            },
        )
        raise HTTPException(
            status_code=400,
            detail={
                "message": str(exc),
                "code": "REAL_WORLD_SAFETY_QUERY_INVALID",
            },
        ) from exc
    except (AuditPersistenceError, SourcePullPersistenceError) as exc:
        logger.exception(
            "real_world_safety_route_persistence_failed",
            extra={
                "event": "real_world_safety_route_persistence_failed",
                "request_id": request_id,
                "query": q,
            },
        )
        raise HTTPException(
            status_code=503,
            detail={
                "message": "Real-world safety search completed source work but could not persist required audit/provenance metadata.",
                "code": "REAL_WORLD_SAFETY_PROVENANCE_PERSISTENCE_UNAVAILABLE",
            },
        ) from exc
    except Exception as exc:
        logger.exception(
            "real_world_safety_route_failed",
            extra={
                "event": "real_world_safety_route_failed",
                "request_id": request_id,
                "query": q,
            },
        )
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Unable to retrieve real-world safety data from public U.S. sources.",
                "code": "REAL_WORLD_SAFETY_UPSTREAM_UNAVAILABLE",
            },
        ) from exc
