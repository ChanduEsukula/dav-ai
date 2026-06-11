"""Deterministic AI Monitor Insights v1.

This module analyzes saved monitor run history for public FDA/openFDA data.
It does not provide medical advice, diagnosis, treatment guidance, clinical
decision support, patient-specific recommendations, or causality claims.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from app.schemas.saved_monitors import SavedMonitor, SavedMonitorRun


INSIGHT_VERSION = "monitor-insight-v0.2"
SAFETY_LIMITATION = (
    "This insight is based only on stored Dav AI public-data monitor history. "
    "It is not medical advice, diagnosis, treatment guidance, clinical decision "
    "support, or proof of causality."
)


@dataclass(frozen=True)
class MonitorInsight:
    monitor_id: str
    label: str
    headline: str
    explanation: str
    latest_run_id: str | None
    previous_run_id: str | None
    latest_record_count: int | None
    previous_record_count: int | None
    record_count_delta: int | None
    percent_change: float | None
    latest_score: int | None
    previous_score: int | None
    score_delta: int | None
    confidence: str
    insight_version: str
    limitation: str


def _safe_percent_change(latest: int, previous: int) -> float | None:
    if previous == 0:
        return None

    return round(((latest - previous) / previous) * 100, 2)


def _successful_runs(runs: Sequence[SavedMonitorRun]) -> list[SavedMonitorRun]:
    return [run for run in runs if run.status.value == "success"]


def _latest_run(runs: Sequence[SavedMonitorRun]) -> SavedMonitorRun | None:
    return runs[0] if runs else None


def build_monitor_insight(
    *,
    monitor: SavedMonitor,
    runs: Sequence[SavedMonitorRun],
) -> MonitorInsight:
    """Build a deterministic monitor insight from recent saved monitor runs."""

    latest_overall_run = _latest_run(runs)

    if latest_overall_run is not None and latest_overall_run.status.value == "error":
        return MonitorInsight(
            monitor_id=str(monitor.id),
            label="source_warning",
            headline="Source or monitor warning",
            explanation=(
                "The latest saved monitor run ended in an error. Review the run "
                "history, audit event, and source status before interpreting trends."
            ),
            latest_run_id=str(latest_overall_run.run_id),
            previous_run_id=None,
            latest_record_count=latest_overall_run.record_count,
            previous_record_count=None,
            record_count_delta=None,
            percent_change=None,
            latest_score=latest_overall_run.score,
            previous_score=None,
            score_delta=None,
            confidence="low",
            insight_version=INSIGHT_VERSION,
            limitation=SAFETY_LIMITATION,
        )

    if monitor.status.value == "error":
        return MonitorInsight(
            monitor_id=str(monitor.id),
            label="source_warning",
            headline="Source or monitor warning",
            explanation=(
                "The saved monitor state indicates an error. Review the run history, "
                "audit event, and source status before interpreting trends."
            ),
            latest_run_id=str(latest_overall_run.run_id) if latest_overall_run else None,
            previous_run_id=None,
            latest_record_count=latest_overall_run.record_count if latest_overall_run else None,
            previous_record_count=None,
            record_count_delta=None,
            percent_change=None,
            latest_score=latest_overall_run.score if latest_overall_run else None,
            previous_score=None,
            score_delta=None,
            confidence="low",
            insight_version=INSIGHT_VERSION,
            limitation=SAFETY_LIMITATION,
        )

    successful_runs = _successful_runs(runs)

    if len(successful_runs) < 2:
        return MonitorInsight(
            monitor_id=str(monitor.id),
            label="insufficient_history",
            headline="Insufficient history",
            explanation=(
                "Dav AI needs at least two successful saved monitor runs before "
                "it can compare public-data activity over time."
            ),
            latest_run_id=str(successful_runs[0].run_id) if successful_runs else None,
            previous_run_id=None,
            latest_record_count=(
                successful_runs[0].record_count if successful_runs else None
            ),
            previous_record_count=None,
            record_count_delta=None,
            percent_change=None,
            latest_score=successful_runs[0].score if successful_runs else None,
            previous_score=None,
            score_delta=None,
            confidence="low",
            insight_version=INSIGHT_VERSION,
            limitation=SAFETY_LIMITATION,
        )

    latest = successful_runs[0]
    previous = successful_runs[1]

    latest_count = latest.record_count
    previous_count = previous.record_count
    latest_score = latest.score
    previous_score = previous.score

    record_delta = (
        latest_count - previous_count
        if latest_count is not None and previous_count is not None
        else None
    )
    percent_change = (
        _safe_percent_change(latest_count, previous_count)
        if latest_count is not None and previous_count is not None
        else None
    )
    score_delta = (
        latest_score - previous_score
        if latest_score is not None and previous_score is not None
        else None
    )

    label = "stable"
    headline = "Stable public-data activity"
    explanation = (
        "The latest successful saved monitor run is similar to the previous "
        "successful run in stored Dav AI public-data history."
    )
    confidence = "medium"

    if latest_count is not None and previous_count is not None:
        if previous_count == 0 and latest_count > 0:
            label = "notable_increase"
            headline = "Notable increase detected"
            explanation = (
                "The previous successful run returned no records, while the latest "
                "successful run returned public records."
            )
            confidence = "medium"
        elif latest_count == 0 and previous_count > 0:
            label = "notable_decrease"
            headline = "Notable decrease detected"
            explanation = (
                "The latest successful run returned no records, while the previous "
                "successful run returned public records."
            )
            confidence = "medium"
        elif (
            percent_change is not None
            and record_delta is not None
            and percent_change >= 50
            and record_delta >= 3
        ):
            label = "notable_increase"
            headline = "Notable increase detected"
            explanation = (
                "The latest successful run returned substantially more public records "
                "than the previous successful run."
            )
            confidence = "medium"
        elif (
            percent_change is not None
            and record_delta is not None
            and percent_change <= -50
            and abs(record_delta) >= 3
        ):
            label = "notable_decrease"
            headline = "Notable decrease detected"
            explanation = (
                "The latest successful run returned substantially fewer public records "
                "than the previous successful run."
            )
            confidence = "medium"
        elif record_delta > 0:
            label = "increased"
            headline = "Public-data activity increased"
            explanation = (
                "The latest successful run returned more public records than the "
                "previous successful run."
            )
            confidence = "medium"
        elif record_delta < 0:
            label = "decreased"
            headline = "Public-data activity decreased"
            explanation = (
                "The latest successful run returned fewer public records than the "
                "previous successful run."
            )
            confidence = "medium"

    return MonitorInsight(
        monitor_id=str(monitor.id),
        label=label,
        headline=headline,
        explanation=explanation,
        latest_run_id=str(latest.run_id),
        previous_run_id=str(previous.run_id),
        latest_record_count=latest_count,
        previous_record_count=previous_count,
        record_count_delta=record_delta,
        percent_change=percent_change,
        latest_score=latest_score,
        previous_score=previous_score,
        score_delta=score_delta,
        confidence=confidence,
        insight_version=INSIGHT_VERSION,
        limitation=SAFETY_LIMITATION,
    )