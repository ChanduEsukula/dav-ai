from fastapi import APIRouter, Query, Request

from app.db.audit_repository import get_audit_event_by_id, list_audit_events
from app.schemas.audit_history import (
    AuditHistoryDetailResponse,
    AuditHistoryItem,
    AuditHistoryListResponse,
)

router = APIRouter(prefix="/api/v1/audit-events")


def _list_audit_events_with_request_id(limit: int, request_id: str | None):
    try:
        return list_audit_events(limit=limit, request_id=request_id)
    except TypeError as exc:
        if "request_id" not in str(exc):
            raise
        return list_audit_events(limit=limit)


def _get_audit_event_by_id_with_request_id(audit_id: str, request_id: str | None):
    try:
        return get_audit_event_by_id(audit_id=audit_id, request_id=request_id)
    except TypeError as exc:
        if "request_id" not in str(exc):
            raise
        return get_audit_event_by_id(audit_id=audit_id)


@router.get("/", response_model=AuditHistoryListResponse)
@router.get("", response_model=AuditHistoryListResponse, include_in_schema=False)
def get_audit_events(
    request: Request,
    limit: int = Query(default=50, ge=1, le=100),
) -> AuditHistoryListResponse:
    request_id = getattr(request.state, "request_id", None)
    persistence_status, rows = _list_audit_events_with_request_id(limit=limit, request_id=request_id)

    if persistence_status == "skipped":
        return AuditHistoryListResponse(
            status="skipped",
            persistence_available=False,
            count=0,
            items=[],
        )

    if persistence_status == "error":
        return AuditHistoryListResponse(
            status="error",
            persistence_available=False,
            count=0,
            items=[],
        )

    items = [AuditHistoryItem(**row) for row in rows]

    return AuditHistoryListResponse(
        status="ok",
        persistence_available=True,
        count=len(items),
        items=items,
    )


@router.get("/{audit_id}", response_model=AuditHistoryDetailResponse)
def get_audit_event(request: Request, audit_id: str) -> AuditHistoryDetailResponse:
    request_id = getattr(request.state, "request_id", None)
    persistence_status, row = _get_audit_event_by_id_with_request_id(audit_id=audit_id, request_id=request_id)

    if persistence_status == "skipped":
        return AuditHistoryDetailResponse(
            status="skipped",
            persistence_available=False,
            item=None,
            message="Audit persistence is not configured.",
        )

    if persistence_status == "error":
        return AuditHistoryDetailResponse(
            status="error",
            persistence_available=False,
            item=None,
            message="Audit persistence could not be read.",
        )

    if row is None:
        return AuditHistoryDetailResponse(
            status="not_found",
            persistence_available=True,
            item=None,
            message="No audit event found for this audit_id.",
        )

    return AuditHistoryDetailResponse(
        status="ok",
        persistence_available=True,
        item=AuditHistoryItem(**row),
        message=None,
    )
