"""Scheduled saved monitor refresh foundation.

This module provides backend-only scheduled refresh logic for Saved Monitors.
It does not define a public API endpoint, scheduler, alerts, auth, or frontend UI.
A future Render Cron job can call this through a small CLI wrapper.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from app.db.saved_monitor_repository import saved_monitor_repository
from app.db.scheduler_lock_repository import scheduler_lock_repository
from app.schemas.saved_monitors import (
    SavedMonitor,
    SavedMonitorModule,
    SavedMonitorRunStatus,
    SavedMonitorScheduledStatus,
)
from app.services.search_workflows.drug_signal_search import execute_drug_signal_search
from app.services.search_workflows.everyday_safety_search import execute_everyday_safety_search
from app.services.search_workflows.recall_search import execute_recall_search
from app.services.search_workflows.regional_health_search import execute_regional_health_search

logger = logging.getLogger("medtrek.scheduled_monitor_refresh")

SCHEDULER_LOCK_NAME = "saved-monitor-refresh"
SCHEDULER_LOCK_TTL_MINUTES = 15


def _utc_now() -> datetime:
    """Return current UTC datetime."""

    return datetime.now(timezone.utc)


def _calculate_next_run_at(
    *,
    base_time: datetime,
    refresh_interval_minutes: int | None,
) -> datetime | None:
    """Calculate the next scheduled run time from a base timestamp."""

    if refresh_interval_minutes is None or refresh_interval_minutes <= 0:
        return None

    return base_time + timedelta(minutes=refresh_interval_minutes)


def _extract_recall_score(result: dict[str, Any]) -> tuple[int | None, str | None]:
    """Extract the first RecallRadar score and label from a result payload."""

    results = result.get("results") or []
    if not results:
        return None, None

    risk_score = results[0].get("risk_score") or {}
    return risk_score.get("score"), risk_score.get("label")


def _extract_drug_signal_score(result: dict[str, Any]) -> tuple[int | None, str | None]:
    """Extract DrugSignal intelligence score and label from a result payload."""

    intelligence_score = result.get("intelligence_score") or {}
    return intelligence_score.get("score"), intelligence_score.get("label")


def _extract_foodradar_score(result: dict[str, Any]) -> tuple[int | None, str | None]:
    """Extract the first FoodRadar review score and label from a result payload."""

    results = result.get("results") or []
    if not results:
        return None, None

    risk_score = results[0].get("risk_score") or {}
    return risk_score.get("score"), risk_score.get("label")


def _parse_regional_health_monitor_query(query: str) -> tuple[str, str]:
    """Parse saved Health Pulse monitor query into region and category."""

    parts = query.strip().split(maxsplit=1)
    if len(parts) != 2:
        raise ValueError(
            'Regional Health Pulse saved monitor query must use "<region> <category>" format.'
        )

    region, category = parts
    return region, category


def _extract_regional_health_score(result: dict[str, Any]) -> tuple[int | None, str | None]:
    """Extract Health Pulse latest value and trend label from a result payload."""

    latest_value = result.get("latest_value")
    signal = result.get("signal") or {}

    return (
        latest_value if isinstance(latest_value, int) else None,
        signal.get("trend_label") if isinstance(signal.get("trend_label"), str) else None,
    )


async def _run_monitor(monitor: SavedMonitor) -> dict[str, Any]:
    """Run one saved monitor through the existing search workflow."""

    request_id = f"scheduled-monitor-{monitor.id}"

    if monitor.module == SavedMonitorModule.RECALLRADAR:
        result = await execute_recall_search(
            query=monitor.query,
            limit=5,
            request_id=request_id,
        )
        score, score_label = _extract_recall_score(result)
        return {
            "record_count": result.get("count", 0),
            "score": score,
            "score_label": score_label,
            "audit_id": (result.get("audit") or {}).get("audit_id"),
        }

    if monitor.module == SavedMonitorModule.DRUGSIGNAL:
        result = await execute_drug_signal_search(
            query=monitor.query,
            limit=5,
            request_id=request_id,
        )
        score, score_label = _extract_drug_signal_score(result)
        return {
            "record_count": result.get("count", 0),
            "score": score,
            "score_label": score_label,
            "audit_id": (result.get("audit") or {}).get("audit_id"),
        }

    if monitor.module == SavedMonitorModule.FOODRADAR:
        result = await execute_everyday_safety_search(
            category="food_supplement",
            query=monitor.query,
            limit=5,
            request_id=request_id,
        )
        score, score_label = _extract_foodradar_score(result)
        return {
            "record_count": result.get("count", 0),
            "score": score,
            "score_label": score_label,
            "audit_id": (result.get("audit") or {}).get("audit_id"),
        }

    if monitor.module == SavedMonitorModule.REGIONAL_HEALTH_PULSE:
        region, category = _parse_regional_health_monitor_query(monitor.query)
        result_model = execute_regional_health_search(
            region=region,
            category=category,
            request_id=request_id,
        )
        result = result_model.model_dump()
        score, score_label = _extract_regional_health_score(result)
        return {
            "record_count": result.get("record_count", 0),
            "score": score,
            "score_label": score_label,
            "audit_id": (result.get("audit") or {}).get("audit_id"),
        }

    raise ValueError(f"Unsupported saved monitor module: {monitor.module}")


async def run_due_saved_monitors(
    *,
    now: datetime | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Run due saved monitors and persist run-history rows.

    This is a backend foundation for scheduled refresh. It intentionally does
    not send alerts. It is safe by default because only monitors with
    refresh_enabled=true and next_run_at<=now are selected.
    """

    run_started_at = now or _utc_now()
    job_run_id = (
        f"scheduled-refresh-{run_started_at.strftime('%Y%m%d-%H%M%S')}-"
        f"{uuid4().hex[:8]}"
    )
    locked_until = run_started_at + timedelta(minutes=SCHEDULER_LOCK_TTL_MINUTES)

    lock_acquired = scheduler_lock_repository.acquire_lock(
        lock_name=SCHEDULER_LOCK_NAME,
        locked_by=job_run_id,
        locked_until=locked_until,
        now=run_started_at,
    )

    if not lock_acquired:
        return {
            "status": "skipped",
            "reason": "active_scheduler_lock",
            "lock_name": SCHEDULER_LOCK_NAME,
            "job_run_id": job_run_id,
            "job_started_at": run_started_at.isoformat(),
            "due_count": 0,
            "attempted_count": 0,
            "success_count": 0,
            "error_count": 0,
            "skipped_count": 0,
            "run_ids": [],
        }

    try:
        due_monitors = saved_monitor_repository.list_due_for_refresh(
            now=run_started_at,
            limit=limit,
        )

        summary: dict[str, Any] = {
            "status": "ok",
            "job_run_id": job_run_id,
            "job_started_at": run_started_at.isoformat(),
            "due_count": len(due_monitors),
            "attempted_count": 0,
            "success_count": 0,
            "error_count": 0,
            "skipped_count": 0,
            "run_ids": [],
        }

        for monitor in due_monitors:
            summary["attempted_count"] += 1
            scheduled_run_at = _utc_now()
            next_run_at = _calculate_next_run_at(
                base_time=scheduled_run_at,
                refresh_interval_minutes=monitor.refresh_interval_minutes,
            )

            try:
                run_result = await _run_monitor(monitor)

                updated_monitor = saved_monitor_repository.update_after_run(
                    monitor.id,
                    latest_audit_id=run_result["audit_id"],
                    latest_score=run_result["score"],
                    latest_record_count=run_result["record_count"],
                )

                run = saved_monitor_repository.create_run(
                    updated_monitor or monitor,
                    status=SavedMonitorRunStatus.SUCCESS,
                    record_count=run_result["record_count"],
                    score=run_result["score"],
                    score_label=run_result["score_label"],
                    audit_id=run_result["audit_id"],
                    error_message=None,
                )

                saved_monitor_repository.update_schedule_after_run(
                    monitor.id,
                    next_run_at=next_run_at,
                    last_scheduled_run_at=scheduled_run_at,
                    last_scheduled_status=SavedMonitorScheduledStatus.SUCCESS,
                )

                summary["success_count"] += 1
                summary["run_ids"].append(str(run.run_id))

            except Exception as exc:
                logger.exception(
                    "scheduled_saved_monitor_run_failed",
                    extra={
                        "event": "scheduled_saved_monitor_run_failed",
                        "monitor_id": str(monitor.id),
                        "monitor_module": monitor.module.value,
                    },
                )

                run = saved_monitor_repository.create_run(
                    monitor,
                    status=SavedMonitorRunStatus.ERROR,
                    record_count=0,
                    score=None,
                    score_label=None,
                    audit_id=None,
                    error_message=str(exc),
                )

                saved_monitor_repository.mark_error(monitor.id)
                saved_monitor_repository.update_schedule_after_run(
                    monitor.id,
                    next_run_at=next_run_at,
                    last_scheduled_run_at=scheduled_run_at,
                    last_scheduled_status=SavedMonitorScheduledStatus.ERROR,
                )

                summary["error_count"] += 1
                summary["run_ids"].append(str(run.run_id))

        return summary

    finally:
        scheduler_lock_repository.release_lock(
            lock_name=SCHEDULER_LOCK_NAME,
            locked_by=job_run_id,
        )
