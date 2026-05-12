"""Routes for Saved Monitors v2 backend foundation."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status

from app.db.saved_monitor_repository import saved_monitor_repository
from app.schemas.saved_monitors import (
    SavedMonitor,
    SavedMonitorCreate,
    SavedMonitorModule,
)
from app.services.search_workflows.drug_signal_search import execute_drug_signal_search
from app.services.search_workflows.recall_search import execute_recall_search

router = APIRouter(prefix="/api/v1/saved-monitors", tags=["saved-monitors"])


def _extract_recall_score(response: dict[str, Any]) -> int | None:
    """Return the highest RecallRadar risk score from a search response."""

    scores: list[int] = []

    for result in response.get("results", []):
        risk_score = result.get("risk_score")

        if isinstance(risk_score, int):
            scores.append(risk_score)
            continue

        if isinstance(risk_score, dict):
            score = risk_score.get("score")
            if isinstance(score, int):
                scores.append(score)

    if not scores:
        return None

    return max(scores)


def _extract_drug_signal_score(response: dict[str, Any]) -> int | None:
    """Return DrugSignal intelligence score from a search response."""

    intelligence_score = response.get("intelligence_score")

    if isinstance(intelligence_score, int):
        return intelligence_score

    if isinstance(intelligence_score, dict):
        score = intelligence_score.get("score")
        if isinstance(score, int):
            return score

    return None


@router.get("", response_model=list[SavedMonitor])
def list_saved_monitors() -> list[SavedMonitor]:
    """List saved monitors."""

    return saved_monitor_repository.list()


@router.post(
    "",
    response_model=SavedMonitor,
    status_code=status.HTTP_201_CREATED,
)
def create_saved_monitor(payload: SavedMonitorCreate) -> SavedMonitor:
    """Create a saved monitor.

    Saved monitors are unique by module and normalized query so users do not
    accidentally create duplicate monitors for the same public-data workflow.
    """

    duplicate_exists = saved_monitor_repository.exists_by_module_and_query(
        module=payload.module,
        query=payload.query,
    )

    if duplicate_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A saved monitor already exists for this module and query.",
        )

    return saved_monitor_repository.create(payload)


@router.post("/{monitor_id}/run", response_model=SavedMonitor)
async def run_saved_monitor(monitor_id: UUID, request: Request) -> SavedMonitor:
    """Run one saved monitor manually and update its latest result fields."""

    monitor = saved_monitor_repository.get(monitor_id)
    if monitor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved monitor not found",
        )

    request_id = getattr(request.state, "request_id", None)

    try:
        if monitor.module == SavedMonitorModule.RECALLRADAR:
            response = await execute_recall_search(
                query=monitor.query,
                limit=5,
                request_id=request_id,
            )
            latest_score = _extract_recall_score(response)
        elif monitor.module == SavedMonitorModule.DRUGSIGNAL:
            response = await execute_drug_signal_search(
                query=monitor.query,
                limit=10,
                request_id=request_id,
            )
            latest_score = _extract_drug_signal_score(response)
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Unsupported saved monitor module",
            )

        updated = saved_monitor_repository.update_after_run(
            monitor_id,
            latest_audit_id=response.get("audit", {}).get("audit_id"),
            latest_score=latest_score,
            latest_record_count=response.get("count"),
        )

        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Saved monitor not found",
            )

        return updated

    except HTTPException:
        saved_monitor_repository.mark_error(monitor_id)
        raise
    except Exception as exc:
        saved_monitor_repository.mark_error(monitor_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "message": "Unable to run saved monitor.",
                "error": str(exc),
            },
        ) from exc


@router.delete("/{monitor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_monitor(monitor_id: UUID) -> None:
    """Delete a saved monitor by ID."""

    deleted = saved_monitor_repository.delete(monitor_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved monitor not found",
        )