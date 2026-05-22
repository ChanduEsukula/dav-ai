"""Routes for Saved Monitors v2 backend foundation."""

from dataclasses import asdict
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request, status

from app.analytics.monitor_insights import build_monitor_insight
from app.db.saved_monitor_repository import saved_monitor_repository
from app.schemas.monitor_insights import MonitorInsightResponse
from app.schemas.saved_monitors import (
    SavedMonitor,
    SavedMonitorCreate,
    SavedMonitorModule,
    SavedMonitorRun,
    SavedMonitorRunStatus,
)
from app.services.search_workflows.drug_signal_search import execute_drug_signal_search
from app.services.search_workflows.recall_search import execute_recall_search

router = APIRouter(prefix="/api/v1/saved-monitors", tags=["saved-monitors"])


def _extract_recall_score(response: dict[str, Any]) -> tuple[int | None, str | None]:
    """Return the highest RecallRadar risk score and label from a search response."""

    best_score: int | None = None
    best_label: str | None = None

    for result in response.get("results", []):
        risk_score = result.get("risk_score")

        if isinstance(risk_score, int):
            score = risk_score
            label = None
        elif isinstance(risk_score, dict):
            raw_score = risk_score.get("score")
            score = raw_score if isinstance(raw_score, int) else None
            raw_label = risk_score.get("label")
            label = raw_label if isinstance(raw_label, str) else None
        else:
            continue

        if score is not None and (best_score is None or score > best_score):
            best_score = score
            best_label = label

    return best_score, best_label


def _extract_drug_signal_score(response: dict[str, Any]) -> tuple[int | None, str | None]:
    """Return DrugSignal intelligence score and label from a search response."""

    intelligence_score = response.get("intelligence_score")

    if isinstance(intelligence_score, int):
        return intelligence_score, None

    if isinstance(intelligence_score, dict):
        score = intelligence_score.get("score")
        label = intelligence_score.get("label")
        return (
            score if isinstance(score, int) else None,
            label if isinstance(label, str) else None,
        )

    return None, None


@router.get("", response_model=list[SavedMonitor])
def list_saved_monitors() -> list[SavedMonitor]:
    """List saved monitors."""

    return saved_monitor_repository.list()


@router.get("/{monitor_id}/runs", response_model=list[SavedMonitorRun])
def list_saved_monitor_runs(
    monitor_id: UUID,
    limit: int = Query(default=10, ge=1, le=50),
) -> list[SavedMonitorRun]:
    """List recent manual run-history rows for one saved monitor."""

    monitor = saved_monitor_repository.get(monitor_id)
    if monitor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved monitor not found",
        )

    return saved_monitor_repository.list_runs(monitor_id, limit=limit)


@router.get("/{monitor_id}/insights", response_model=MonitorInsightResponse)
def get_saved_monitor_insight(monitor_id: UUID) -> MonitorInsightResponse:
    """Return deterministic AI Monitor Insight for one saved monitor.

    This insight is based only on stored Dav AI public-data monitor history.
    It is not medical advice, diagnosis, treatment guidance, clinical decision
    support, or proof of causality.
    """

    monitor = saved_monitor_repository.get(monitor_id)
    if monitor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved monitor not found",
        )

    runs = saved_monitor_repository.list_runs(monitor_id, limit=10)
    insight = build_monitor_insight(monitor=monitor, runs=runs)

    return MonitorInsightResponse(**asdict(insight))


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
            latest_score, score_label = _extract_recall_score(response)
        elif monitor.module == SavedMonitorModule.DRUGSIGNAL:
            response = await execute_drug_signal_search(
                query=monitor.query,
                limit=10,
                request_id=request_id,
            )
            latest_score, score_label = _extract_drug_signal_score(response)
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Unsupported saved monitor module",
            )

        latest_audit_id = response.get("audit", {}).get("audit_id")
        latest_record_count = response.get("count")

        updated = saved_monitor_repository.update_after_run(
            monitor_id,
            latest_audit_id=latest_audit_id,
            latest_score=latest_score,
            latest_record_count=latest_record_count,
        )

        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Saved monitor not found",
            )

        saved_monitor_repository.create_run(
            monitor,
            status=SavedMonitorRunStatus.SUCCESS,
            record_count=latest_record_count if isinstance(latest_record_count, int) else None,
            score=latest_score,
            score_label=score_label,
            audit_id=latest_audit_id if isinstance(latest_audit_id, str) else None,
        )

        return updated

    except HTTPException as exc:
        saved_monitor_repository.mark_error(monitor_id)
        saved_monitor_repository.create_run(
            monitor,
            status=SavedMonitorRunStatus.ERROR,
            record_count=0,
            error_message=str(exc.detail),
        )
        raise
    except Exception as exc:
        saved_monitor_repository.mark_error(monitor_id)
        saved_monitor_repository.create_run(
            monitor,
            status=SavedMonitorRunStatus.ERROR,
            record_count=0,
            error_message=str(exc),
        )
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
