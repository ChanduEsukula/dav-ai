"""Tests for scheduled saved monitor refresh foundation."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.db.saved_monitor_repository import saved_monitor_repository
from app.schemas.saved_monitors import (
    SavedMonitor,
    SavedMonitorCreate,
    SavedMonitorModule,
    SavedMonitorRunStatus,
    SavedMonitorScheduledStatus,
    SavedMonitorStatus,
)
from app.services import scheduled_monitor_refresh
from app.services.scheduled_monitor_refresh import run_due_saved_monitors


@pytest.fixture(autouse=True)
def clear_saved_monitors(monkeypatch):
    """Use in-memory repository storage for scheduled refresh tests."""

    monkeypatch.setenv("DATABASE_URL", "")
    saved_monitor_repository.clear()
    yield
    saved_monitor_repository.clear()


def _create_monitor(
    *,
    query: str = "eye drops",
    module: SavedMonitorModule = SavedMonitorModule.RECALLRADAR,
) -> SavedMonitor:
    return saved_monitor_repository.create(
        SavedMonitorCreate(
            name=f"Monitor {uuid4()}",
            query=query,
            module=module,
        )
    )


def _set_schedule(
    monitor: SavedMonitor,
    *,
    enabled: bool,
    interval_minutes: int | None,
    next_run_at: datetime | None,
) -> SavedMonitor:
    updated = monitor.model_copy(
        update={
            "refresh_enabled": enabled,
            "refresh_interval_minutes": interval_minutes,
            "next_run_at": next_run_at,
            "last_scheduled_run_at": None,
            "last_scheduled_status": None,
        }
    )
    saved_monitor_repository._items[monitor.id] = updated
    return updated


def test_list_due_for_refresh_ignores_disabled_monitor():
    now = datetime.now(timezone.utc)
    monitor = _create_monitor()
    _set_schedule(
        monitor,
        enabled=False,
        interval_minutes=60,
        next_run_at=now - timedelta(minutes=5),
    )

    due = saved_monitor_repository.list_due_for_refresh(now=now)

    assert due == []


def test_list_due_for_refresh_selects_due_enabled_monitor():
    now = datetime.now(timezone.utc)
    monitor = _create_monitor()
    scheduled = _set_schedule(
        monitor,
        enabled=True,
        interval_minutes=60,
        next_run_at=now - timedelta(minutes=5),
    )

    due = saved_monitor_repository.list_due_for_refresh(now=now)

    assert due == [scheduled]


def test_list_due_for_refresh_skips_future_monitor():
    now = datetime.now(timezone.utc)
    monitor = _create_monitor()
    _set_schedule(
        monitor,
        enabled=True,
        interval_minutes=60,
        next_run_at=now + timedelta(minutes=5),
    )

    due = saved_monitor_repository.list_due_for_refresh(now=now)

    assert due == []


def test_list_due_for_refresh_respects_limit():
    now = datetime.now(timezone.utc)
    first = _set_schedule(
        _create_monitor(query="eye drops one"),
        enabled=True,
        interval_minutes=60,
        next_run_at=now - timedelta(minutes=10),
    )
    _set_schedule(
        _create_monitor(query="eye drops two"),
        enabled=True,
        interval_minutes=60,
        next_run_at=now - timedelta(minutes=5),
    )

    due = saved_monitor_repository.list_due_for_refresh(now=now, limit=1)

    assert due == [first]


@pytest.mark.anyio
async def test_run_due_saved_monitors_creates_success_run_and_advances_schedule(
    monkeypatch,
):
    now = datetime.now(timezone.utc)
    monitor = _create_monitor(query="eye drops")
    _set_schedule(
        monitor,
        enabled=True,
        interval_minutes=60,
        next_run_at=now - timedelta(minutes=1),
    )

    async def fake_run_monitor(_monitor):
        return {
            "record_count": 3,
            "score": 72,
            "score_label": "High",
            "audit_id": str(uuid4()),
        }

    monkeypatch.setattr(scheduled_monitor_refresh, "_run_monitor", fake_run_monitor)

    summary = await run_due_saved_monitors(now=now, limit=10)

    updated = saved_monitor_repository.get(monitor.id)
    runs = saved_monitor_repository.list_runs(monitor.id)

    assert summary["status"] == "ok"
    assert summary["job_run_id"].startswith("scheduled-refresh-")
    assert summary["status"] == "ok"
    assert summary["job_run_id"].startswith("scheduled-refresh-")
    assert summary["due_count"] == 1
    assert summary["attempted_count"] == 1
    assert summary["success_count"] == 1
    assert summary["error_count"] == 0
    assert len(summary["run_ids"]) == 1

    assert updated is not None
    assert updated.status == SavedMonitorStatus.CHECKED
    assert updated.latest_record_count == 3
    assert updated.latest_score == 72
    assert updated.next_run_at is not None
    assert updated.next_run_at > now
    assert updated.last_scheduled_run_at is not None
    assert updated.last_scheduled_status == SavedMonitorScheduledStatus.SUCCESS

    assert len(runs) == 1
    assert runs[0].status == SavedMonitorRunStatus.SUCCESS
    assert runs[0].record_count == 3
    assert runs[0].score == 72
    assert runs[0].score_label == "High"
    assert runs[0].audit_id is not None
    assert runs[0].error_message is None


@pytest.mark.anyio
async def test_run_due_saved_monitors_records_error_run(monkeypatch):
    now = datetime.now(timezone.utc)
    monitor = _create_monitor(query="eye drops")
    _set_schedule(
        monitor,
        enabled=True,
        interval_minutes=60,
        next_run_at=now - timedelta(minutes=1),
    )

    async def fake_run_monitor(_monitor):
        raise RuntimeError("upstream failed")

    monkeypatch.setattr(scheduled_monitor_refresh, "_run_monitor", fake_run_monitor)

    summary = await run_due_saved_monitors(now=now, limit=10)

    updated = saved_monitor_repository.get(monitor.id)
    runs = saved_monitor_repository.list_runs(monitor.id)

    assert summary["due_count"] == 1
    assert summary["attempted_count"] == 1
    assert summary["success_count"] == 0
    assert summary["error_count"] == 1
    assert len(summary["run_ids"]) == 1

    assert updated is not None
    assert updated.status == SavedMonitorStatus.ERROR
    assert updated.next_run_at is not None
    assert updated.next_run_at > now
    assert updated.last_scheduled_run_at is not None
    assert updated.last_scheduled_status == SavedMonitorScheduledStatus.ERROR

    assert len(runs) == 1
    assert runs[0].status == SavedMonitorRunStatus.ERROR
    assert runs[0].record_count == 0
    assert runs[0].error_message == "upstream failed"
