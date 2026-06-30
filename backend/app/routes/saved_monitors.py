"""Routes for Saved Monitors v2 backend foundation."""

from dataclasses import asdict
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.analytics.monitor_insights import build_monitor_insight
from app.db.saved_monitor_repository import saved_monitor_repository
from app.db.source_pull_repository import get_source_pull_by_audit_id
from app.schemas.monitor_insights import MonitorInsightResponse
from app.schemas.saved_monitors import (
    PayloadChangeStatus,
    SavedMonitor,
    SavedMonitorCreate,
    SavedMonitorModule,
    SavedMonitorRun,
    SavedMonitorRunStatus,
)
from app.scoring.source_freshness import (
    classify_payload_change,
    payload_change_result_to_dict,
)
from app.services.auth_context import AuthenticatedUser, get_current_user
from app.services.search_workflows.drug_signal_search import execute_drug_signal_search
from app.services.search_workflows.everyday_safety_search import execute_everyday_safety_search
from app.services.search_workflows.recall_search import execute_recall_search
from app.services.search_workflows.regional_health_search import execute_regional_health_search

router = APIRouter(prefix="/api/v1/saved-monitors", tags=["saved-monitors"])


def _extract_recall_score(response: dict[str, Any]) -> tuple[int | None, str | None]:
    """Return the highest RecallRadar review-priority score and label from a search response."""
    best_score: int | None = None
    best_label: str | None = None

    for result in response.get("results", []):
        review_priority = result.get("risk_score")
        if isinstance(review_priority, int):
            score = review_priority
            label = None
        elif isinstance(review_priority, dict):
            raw_score = review_priority.get("score")
            score = raw_score if isinstance(raw_score, int) else None
            raw_label = review_priority.get("label")
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


def _extract_foodradar_score(response: dict[str, Any]) -> tuple[int | None, str | None]:
    """Return the highest FoodRadar review-priority score and label from a search response."""
    best_score: int | None = None
    best_label: str | None = None

    for result in response.get("results", []):
        review_priority = result.get("risk_score")
        if not isinstance(review_priority, dict):
            continue

        raw_score = review_priority.get("score")
        label = review_priority.get("label")
        score = raw_score if isinstance(raw_score, int) else None

        if score is not None and (best_score is None or score > best_score):
            best_score = score
            best_label = label if isinstance(label, str) else None

    return best_score, best_label


def _parse_regional_health_monitor_query(query: str) -> tuple[str, str]:
    """Parse saved Health Pulse monitor query into region and category.

    The current no-migration format is: "<region> <category>", for example:
    "MN respiratory" or "MN hospital pressure".
    """
    parts = query.strip().split(maxsplit=1)
    if len(parts) != 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail='Regional Health Pulse saved monitor query must use "<region> <category>" format.',
        )

    region, category = parts
    return region, category


def _extract_regional_health_score(response: dict[str, Any]) -> tuple[int | None, str | None]:
    """Return Health Pulse latest value and trend label from a search response."""
    latest_value = response.get("latest_value")
    signal = response.get("signal") or {}
    trend_label = signal.get("trend_label")

    return (
        latest_value if isinstance(latest_value, int) else None,
        trend_label if isinstance(trend_label, str) else None,
    )


def _get_payload_hash_for_audit_id(
    audit_id: str | None,
    request_id: str | None = None,
) -> str | None:
    """Return source-pull payload hash for an audit ID when available."""
    if not audit_id:
        return None

    persistence_status, source_pull = get_source_pull_by_audit_id(
        audit_id=audit_id,
        request_id=request_id,
    )

    if persistence_status != "saved" or not source_pull:
        return None

    payload_hash = source_pull.get("payload_hash")
    return payload_hash if isinstance(payload_hash, str) else None


def _runs_with_payload_change(
    runs: list[SavedMonitorRun],
    *,
    request_id: str | None = None,
) -> list[SavedMonitorRun]:
    """Attach payload-change status to saved monitor runs.

    Runs are expected newest-first. Each successful run is compared with the
    next older run when possible. This is an operational public-data review
    signal only, not medical risk, clinical urgency, or source correctness.
    """
    enriched_runs: list[SavedMonitorRun] = []

    for index, run in enumerate(runs):
        previous_run = runs[index + 1] if index + 1 < len(runs) else None

        latest_hash = _get_payload_hash_for_audit_id(
            run.audit_id,
            request_id=request_id,
        )
        previous_hash = _get_payload_hash_for_audit_id(
            previous_run.audit_id if previous_run else None,
            request_id=request_id,
        )
        latest_available = run.audit_id is not None

        payload_change = classify_payload_change(
            latest_payload_hash=latest_hash,
            previous_payload_hash=previous_hash,
            latest_available=latest_available,
        )

        enriched_runs.append(
            run.model_copy(
                update={
                    "payload_change": PayloadChangeStatus(
                        **payload_change_result_to_dict(payload_change)
                    ),
                }
            )
        )

    return enriched_runs


@router.get("", response_model=list[SavedMonitor])
def list_saved_monitors(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[SavedMonitor]:
    """List saved monitors."""
    return saved_monitor_repository.list_saved_monitors(current_user.id)


@router.get("/{monitor_id}/runs", response_model=list[SavedMonitorRun])
def list_saved_monitor_runs(
    monitor_id: UUID,
    request: Request,
    limit: int = Query(default=10, ge=1, le=50),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[SavedMonitorRun]:
    """List recent manual run-history rows for one saved monitor."""
    monitor = saved_monitor_repository.get_saved_monitor(current_user.id, monitor_id)
    if monitor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved monitor not found",
        )

    request_id = getattr(request.state, "request_id", None)
    runs = saved_monitor_repository.list_runs(
        monitor_id,
        limit=limit,
        user_id=current_user.id,
    )
    return _runs_with_payload_change(runs, request_id=request_id)


@router.get("/{monitor_id}/insights", response_model=MonitorInsightResponse)
def get_saved_monitor_insight(
    monitor_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> MonitorInsightResponse:
    """Return deterministic AI Monitor Insight for one saved monitor.

    This insight is based only on stored Dav AI public-data monitor history.
    It is not medical advice, diagnosis, treatment guidance, clinical decision
    support, or proof of causality.
    """
    monitor = saved_monitor_repository.get_saved_monitor(current_user.id, monitor_id)
    if monitor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved monitor not found",
        )

    runs = saved_monitor_repository.list_runs(
        monitor_id,
        limit=10,
        user_id=current_user.id,
    )
    insight = build_monitor_insight(monitor=monitor, runs=runs)
    return MonitorInsightResponse(**asdict(insight))


@router.post(
    "",
    response_model=SavedMonitor,
    status_code=status.HTTP_201_CREATED,
)
def create_saved_monitor(
    payload: SavedMonitorCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> SavedMonitor:
    """Create a saved monitor.

    Saved monitors are unique by module and normalized query so users do not
    accidentally create duplicate monitors for the same public-data workflow.
    """
    duplicate_exists = saved_monitor_repository.exists_by_module_and_query(
        module=payload.module,
        query=payload.query,
        user_id=current_user.id,
    )

    if duplicate_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A saved monitor already exists for this module and query.",
        )

    return saved_monitor_repository.create_saved_monitor(current_user.id, payload)


@router.post("/{monitor_id}/run", response_model=SavedMonitor)
async def run_saved_monitor(
    monitor_id: UUID,
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> SavedMonitor:
    """Run one saved monitor manually and update its latest result fields."""
    monitor = saved_monitor_repository.get_saved_monitor(current_user.id, monitor_id)
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

        elif monitor.module == SavedMonitorModule.FOODRADAR:
            response = await execute_everyday_safety_search(
                category="food_supplement",
                query=monitor.query,
                limit=5,
                request_id=request_id,
            )
            latest_score, score_label = _extract_foodradar_score(response)

        elif monitor.module == SavedMonitorModule.REGIONAL_HEALTH_PULSE:
            region, category = _parse_regional_health_monitor_query(monitor.query)
            response_model = execute_regional_health_search(
                region=region,
                category=category,
                request_id=request_id,
            )
            response = response_model.model_dump()
            latest_score, score_label = _extract_regional_health_score(response)

        elif monitor.module == SavedMonitorModule.COSMETICSIGNAL:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="CosmeticSignal saved monitor runs are not supported yet.",
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Unsupported saved monitor module",
            )

        latest_audit_id = response.get("audit", {}).get("audit_id")
        latest_record_count = response.get("count", response.get("record_count"))

        updated = saved_monitor_repository.update_after_run(
            monitor_id,
            user_id=current_user.id,
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
        saved_monitor_repository.mark_error(monitor_id, user_id=current_user.id)
        saved_monitor_repository.create_run(
            monitor,
            status=SavedMonitorRunStatus.ERROR,
            record_count=0,
            error_message=str(exc.detail),
        )
        raise

    except Exception as exc:
        saved_monitor_repository.mark_error(monitor_id, user_id=current_user.id)
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
                "code": "SAVED_MONITOR_RUN_UNAVAILABLE",
            },
        ) from exc


@router.delete("/{monitor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_monitor(
    monitor_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> None:
    """Delete a saved monitor by ID."""
    deleted = saved_monitor_repository.delete_saved_monitor(current_user.id, monitor_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved monitor not found",
        )