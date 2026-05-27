"""Offline dataset builder for Dav AI saved-monitor anomaly experiments.

This module uses synthetic weak-label examples inspired by Dav AI Saved Monitors.
It does not use PHI, patient records, private medical history, prescription
history, addresses, or patient-specific data.

The target is public-data monitor change state only:
- insufficient_history
- stable
- increased
- decreased
- notable_increase
- notable_decrease
- source_warning

It is not medical advice, diagnosis, treatment guidance, patient-risk prediction,
clinical decision support, outbreak prediction, or proof of FAERS causation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


MonitorAnomalyLabel = Literal[
    "insufficient_history",
    "stable",
    "increased",
    "decreased",
    "notable_increase",
    "notable_decrease",
    "source_warning",
]


ALLOWED_MONITOR_ANOMALY_LABELS: set[str] = {
    "insufficient_history",
    "stable",
    "increased",
    "decreased",
    "notable_increase",
    "notable_decrease",
    "source_warning",
}

CATEGORICAL_FEATURES = [
    "module",
    "source_id",
    "upstream_status",
    "freshness_status",
    "provenance_state",
    "last_scheduled_status",
]

NUMERIC_FEATURES = [
    "latest_record_count",
    "previous_record_count",
    "record_count_delta",
    "record_count_pct_change",
    "latest_score",
    "previous_score",
    "score_delta",
    "run_count",
    "days_since_last_run",
]

BOOLEAN_FEATURES = [
    "source_pull_present",
    "payload_hash_present",
    "payload_hash_changed",
    "refresh_enabled",
]


@dataclass(frozen=True)
class SavedMonitorAnomalyExample:
    module: str
    source_id: str
    upstream_status: str
    freshness_status: str
    provenance_state: str
    last_scheduled_status: str
    latest_record_count: int
    previous_record_count: int
    latest_score: int
    previous_score: int
    run_count: int
    days_since_last_run: int
    source_pull_present: bool
    payload_hash_present: bool
    payload_hash_changed: bool
    refresh_enabled: bool
    label: MonitorAnomalyLabel

    def record_count_delta(self) -> int:
        return self.latest_record_count - self.previous_record_count

    def record_count_pct_change(self) -> float:
        if self.previous_record_count == 0:
            if self.latest_record_count == 0:
                return 0.0
            return 100.0

        return (
            (self.latest_record_count - self.previous_record_count)
            / self.previous_record_count
            * 100.0
        )

    def score_delta(self) -> int:
        return self.latest_score - self.previous_score

    def to_features(self) -> dict[str, object]:
        return {
            "module": self.module,
            "source_id": self.source_id,
            "upstream_status": self.upstream_status,
            "freshness_status": self.freshness_status,
            "provenance_state": self.provenance_state,
            "last_scheduled_status": self.last_scheduled_status,
            "latest_record_count": self.latest_record_count,
            "previous_record_count": self.previous_record_count,
            "record_count_delta": self.record_count_delta(),
            "record_count_pct_change": self.record_count_pct_change(),
            "latest_score": self.latest_score,
            "previous_score": self.previous_score,
            "score_delta": self.score_delta(),
            "run_count": self.run_count,
            "days_since_last_run": self.days_since_last_run,
            "source_pull_present": self.source_pull_present,
            "payload_hash_present": self.payload_hash_present,
            "payload_hash_changed": self.payload_hash_changed,
            "refresh_enabled": self.refresh_enabled,
        }


def build_saved_monitor_anomaly_examples() -> list[SavedMonitorAnomalyExample]:
    """Return deterministic weak-label examples for offline anomaly testing.

    These are weak labels, not clinical truth. They are designed to test
    monitoring-feature engineering, prediction behavior, metrics, and safety
    boundaries before any production integration.
    """

    return [
        SavedMonitorAnomalyExample(
            module="RecallRadar",
            source_id="openfda_drug_enforcement",
            upstream_status="success",
            freshness_status="fresh",
            provenance_state="complete",
            last_scheduled_status="success",
            latest_record_count=5,
            previous_record_count=0,
            latest_score=34,
            previous_score=0,
            run_count=1,
            days_since_last_run=0,
            source_pull_present=True,
            payload_hash_present=True,
            payload_hash_changed=False,
            refresh_enabled=False,
            label="insufficient_history",
        ),
        SavedMonitorAnomalyExample(
            module="RecallRadar",
            source_id="openfda_drug_enforcement",
            upstream_status="success",
            freshness_status="fresh",
            provenance_state="complete",
            last_scheduled_status="success",
            latest_record_count=10,
            previous_record_count=10,
            latest_score=40,
            previous_score=40,
            run_count=4,
            days_since_last_run=1,
            source_pull_present=True,
            payload_hash_present=True,
            payload_hash_changed=False,
            refresh_enabled=True,
            label="stable",
        ),
        SavedMonitorAnomalyExample(
            module="DrugSignal",
            source_id="openfda_drug_event",
            upstream_status="success",
            freshness_status="fresh",
            provenance_state="complete",
            last_scheduled_status="success",
            latest_record_count=18,
            previous_record_count=12,
            latest_score=52,
            previous_score=46,
            run_count=5,
            days_since_last_run=1,
            source_pull_present=True,
            payload_hash_present=True,
            payload_hash_changed=True,
            refresh_enabled=True,
            label="increased",
        ),
        SavedMonitorAnomalyExample(
            module="DrugSignal",
            source_id="openfda_drug_event",
            upstream_status="success",
            freshness_status="fresh",
            provenance_state="complete",
            last_scheduled_status="success",
            latest_record_count=7,
            previous_record_count=12,
            latest_score=35,
            previous_score=45,
            run_count=5,
            days_since_last_run=1,
            source_pull_present=True,
            payload_hash_present=True,
            payload_hash_changed=True,
            refresh_enabled=True,
            label="decreased",
        ),
        SavedMonitorAnomalyExample(
            module="RecallRadar",
            source_id="openfda_drug_enforcement",
            upstream_status="success",
            freshness_status="fresh",
            provenance_state="complete",
            last_scheduled_status="success",
            latest_record_count=42,
            previous_record_count=18,
            latest_score=84,
            previous_score=58,
            run_count=6,
            days_since_last_run=1,
            source_pull_present=True,
            payload_hash_present=True,
            payload_hash_changed=True,
            refresh_enabled=True,
            label="notable_increase",
        ),
        SavedMonitorAnomalyExample(
            module="RegionalHealthPulse",
            source_id="regional_health_pulse_demo",
            upstream_status="success",
            freshness_status="scaffold",
            provenance_state="complete",
            last_scheduled_status="success",
            latest_record_count=8,
            previous_record_count=30,
            latest_score=28,
            previous_score=70,
            run_count=6,
            days_since_last_run=1,
            source_pull_present=True,
            payload_hash_present=True,
            payload_hash_changed=True,
            refresh_enabled=True,
            label="notable_decrease",
        ),
        SavedMonitorAnomalyExample(
            module="RegionalHealthPulse",
            source_id="regional_health_pulse_demo",
            upstream_status="error",
            freshness_status="error",
            provenance_state="missing_source_pull",
            last_scheduled_status="error",
            latest_record_count=0,
            previous_record_count=12,
            latest_score=0,
            previous_score=48,
            run_count=3,
            days_since_last_run=2,
            source_pull_present=False,
            payload_hash_present=False,
            payload_hash_changed=False,
            refresh_enabled=True,
            label="source_warning",
        ),
        SavedMonitorAnomalyExample(
            module="RecallRadar",
            source_id="openfda_drug_enforcement",
            upstream_status="success",
            freshness_status="delayed",
            provenance_state="complete",
            last_scheduled_status="success",
            latest_record_count=13,
            previous_record_count=12,
            latest_score=47,
            previous_score=46,
            run_count=4,
            days_since_last_run=14,
            source_pull_present=True,
            payload_hash_present=True,
            payload_hash_changed=False,
            refresh_enabled=True,
            label="source_warning",
        ),
        SavedMonitorAnomalyExample(
            module="DrugSignal",
            source_id="openfda_drug_event",
            upstream_status="success",
            freshness_status="fresh",
            provenance_state="complete",
            last_scheduled_status="success",
            latest_record_count=20,
            previous_record_count=19,
            latest_score=51,
            previous_score=50,
            run_count=8,
            days_since_last_run=1,
            source_pull_present=True,
            payload_hash_present=True,
            payload_hash_changed=False,
            refresh_enabled=True,
            label="stable",
        ),
        SavedMonitorAnomalyExample(
            module="RegionalHealthPulse",
            source_id="regional_health_pulse_demo",
            upstream_status="success",
            freshness_status="scaffold",
            provenance_state="complete",
            last_scheduled_status="success",
            latest_record_count=17,
            previous_record_count=10,
            latest_score=55,
            previous_score=42,
            run_count=5,
            days_since_last_run=1,
            source_pull_present=True,
            payload_hash_present=True,
            payload_hash_changed=True,
            refresh_enabled=True,
            label="increased",
        ),
    ]


def build_feature_rows() -> list[dict[str, object]]:
    return [example.to_features() for example in build_saved_monitor_anomaly_examples()]


def build_labels() -> list[MonitorAnomalyLabel]:
    return [example.label for example in build_saved_monitor_anomaly_examples()]