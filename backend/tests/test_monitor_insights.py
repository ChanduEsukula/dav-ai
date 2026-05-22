from datetime import datetime, timezone
from uuid import uuid4

from app.analytics.monitor_insights import build_monitor_insight
from app.schemas.saved_monitors import (
    SavedMonitor,
    SavedMonitorModule,
    SavedMonitorRun,
    SavedMonitorRunStatus,
    SavedMonitorStatus,
)


def make_monitor() -> SavedMonitor:
    return SavedMonitor(
        id=uuid4(),
        name="Aspirin monitor",
        query="aspirin",
        module=SavedMonitorModule.RECALLRADAR,
        created_at=datetime.now(timezone.utc),
        status=SavedMonitorStatus.CHECKED,
    )


def make_run(
    *,
    monitor_id,
    record_count: int,
    score: int | None = None,
) -> SavedMonitorRun:
    return SavedMonitorRun(
        run_id=uuid4(),
        monitor_id=monitor_id,
        module=SavedMonitorModule.RECALLRADAR,
        query="aspirin",
        status=SavedMonitorRunStatus.SUCCESS,
        record_count=record_count,
        score=score,
        score_label=None,
        audit_id=str(uuid4()),
        created_at=datetime.now(timezone.utc),
        error_message=None,
    )


def test_monitor_insight_returns_insufficient_history_without_two_successful_runs():
    monitor = make_monitor()
    runs = [make_run(monitor_id=monitor.id, record_count=5, score=40)]

    insight = build_monitor_insight(monitor=monitor, runs=runs)

    assert insight.label == "insufficient_history"
    assert insight.headline == "Insufficient history"
    assert insight.latest_record_count == 5
    assert insight.previous_record_count is None
    assert insight.confidence == "low"
    assert "not medical advice" in insight.limitation


def test_monitor_insight_detects_stable_activity():
    monitor = make_monitor()
    runs = [
        make_run(monitor_id=monitor.id, record_count=5, score=40),
        make_run(monitor_id=monitor.id, record_count=5, score=40),
    ]

    insight = build_monitor_insight(monitor=monitor, runs=runs)

    assert insight.label == "stable"
    assert insight.record_count_delta == 0
    assert insight.percent_change == 0
    assert insight.score_delta == 0


def test_monitor_insight_detects_increased_activity():
    monitor = make_monitor()
    runs = [
        make_run(monitor_id=monitor.id, record_count=6, score=45),
        make_run(monitor_id=monitor.id, record_count=5, score=40),
    ]

    insight = build_monitor_insight(monitor=monitor, runs=runs)

    assert insight.label == "increased"
    assert insight.record_count_delta == 1
    assert insight.percent_change == 20
    assert insight.score_delta == 5


def test_monitor_insight_detects_notable_increase():
    monitor = make_monitor()
    runs = [
        make_run(monitor_id=monitor.id, record_count=10, score=50),
        make_run(monitor_id=monitor.id, record_count=4, score=40),
    ]

    insight = build_monitor_insight(monitor=monitor, runs=runs)

    assert insight.label == "notable_increase"
    assert insight.record_count_delta == 6
    assert insight.percent_change == 150


def test_monitor_insight_detects_notable_decrease():
    monitor = make_monitor()
    runs = [
        make_run(monitor_id=monitor.id, record_count=2, score=35),
        make_run(monitor_id=monitor.id, record_count=8, score=45),
    ]

    insight = build_monitor_insight(monitor=monitor, runs=runs)

    assert insight.label == "notable_decrease"
    assert insight.record_count_delta == -6
    assert insight.percent_change == -75
