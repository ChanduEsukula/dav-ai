"""Offline dataset builder for Dav AI public-data review-priority experiments.

This module intentionally uses synthetic/weak-label examples derived from Dav AI's
public-data workflows. It does not use PHI, patient records, private medical
history, prescription history, addresses, or any patient-specific data.

The target is operational review priority only:
- routine
- watch
- elevated

It is not medical advice, diagnosis, treatment guidance, patient-risk prediction,
clinical decision support, or proof of FAERS causation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


ReviewPriorityLabel = Literal["routine", "watch", "elevated"]


ALLOWED_REVIEW_PRIORITY_LABELS: set[str] = {"routine", "watch", "elevated"}

CATEGORICAL_FEATURES = [
    "module",
    "source_id",
    "upstream_status",
    "score_label",
    "freshness_status",
    "provenance_state",
]

NUMERIC_FEATURES = [
    "record_count",
    "score",
    "query_length",
    "query_word_count",
    "record_count_delta",
    "record_count_pct_change",
    "score_delta",
]

BOOLEAN_FEATURES = [
    "source_pull_present",
    "payload_hash_present",
]


@dataclass(frozen=True)
class ReviewPriorityExample:
    module: str
    source_id: str
    upstream_status: str
    query: str
    record_count: int
    score: int
    score_label: str
    source_pull_present: bool
    payload_hash_present: bool
    freshness_status: str
    provenance_state: str
    record_count_delta: int
    record_count_pct_change: float
    score_delta: int
    label: ReviewPriorityLabel

    def to_features(self) -> dict[str, object]:
        return {
            "module": self.module,
            "source_id": self.source_id,
            "upstream_status": self.upstream_status,
            "record_count": self.record_count,
            "score": self.score,
            "score_label": self.score_label,
            "query_length": len(self.query),
            "query_word_count": len(self.query.split()),
            "source_pull_present": self.source_pull_present,
            "payload_hash_present": self.payload_hash_present,
            "freshness_status": self.freshness_status,
            "provenance_state": self.provenance_state,
            "record_count_delta": self.record_count_delta,
            "record_count_pct_change": self.record_count_pct_change,
            "score_delta": self.score_delta,
        }


def build_review_priority_examples() -> list[ReviewPriorityExample]:
    """Return deterministic weak-label examples for offline ML testing.

    These examples are not ground truth. They are weak labels designed to test
    feature engineering, preprocessing, classifier behavior, metrics, and safety
    boundaries before any production ML integration.
    """

    return [
        ReviewPriorityExample(
            module="RecallRadar",
            source_id="openfda_drug_enforcement",
            upstream_status="success",
            query="eye drops",
            record_count=2,
            score=22,
            score_label="low",
            source_pull_present=True,
            payload_hash_present=True,
            freshness_status="fresh",
            provenance_state="complete",
            record_count_delta=0,
            record_count_pct_change=0.0,
            score_delta=0,
            label="routine",
        ),
        ReviewPriorityExample(
            module="RecallRadar",
            source_id="openfda_drug_enforcement",
            upstream_status="success",
            query="sterile eye drops",
            record_count=18,
            score=58,
            score_label="moderate",
            source_pull_present=True,
            payload_hash_present=True,
            freshness_status="fresh",
            provenance_state="complete",
            record_count_delta=6,
            record_count_pct_change=50.0,
            score_delta=8,
            label="watch",
        ),
        ReviewPriorityExample(
            module="RecallRadar",
            source_id="openfda_drug_enforcement",
            upstream_status="success",
            query="class i recall",
            record_count=45,
            score=88,
            score_label="high",
            source_pull_present=True,
            payload_hash_present=True,
            freshness_status="fresh",
            provenance_state="complete",
            record_count_delta=20,
            record_count_pct_change=80.0,
            score_delta=18,
            label="elevated",
        ),
        ReviewPriorityExample(
            module="DrugSignal",
            source_id="openfda_drug_event",
            upstream_status="empty",
            query="metformin",
            record_count=0,
            score=0,
            score_label="unavailable",
            source_pull_present=True,
            payload_hash_present=True,
            freshness_status="fresh",
            provenance_state="complete",
            record_count_delta=0,
            record_count_pct_change=0.0,
            score_delta=0,
            label="routine",
        ),
        ReviewPriorityExample(
            module="DrugSignal",
            source_id="openfda_drug_event",
            upstream_status="success",
            query="aspirin",
            record_count=12,
            score=42,
            score_label="moderate",
            source_pull_present=True,
            payload_hash_present=True,
            freshness_status="fresh",
            provenance_state="complete",
            record_count_delta=4,
            record_count_pct_change=33.0,
            score_delta=5,
            label="watch",
        ),
        ReviewPriorityExample(
            module="DrugSignal",
            source_id="openfda_drug_event",
            upstream_status="success",
            query="insulin",
            record_count=80,
            score=83,
            score_label="high",
            source_pull_present=True,
            payload_hash_present=True,
            freshness_status="fresh",
            provenance_state="complete",
            record_count_delta=35,
            record_count_pct_change=77.0,
            score_delta=20,
            label="elevated",
        ),
        ReviewPriorityExample(
            module="RegionalHealthPulse",
            source_id="regional_health_pulse_demo",
            upstream_status="success",
            query="Minnesota respiratory",
            record_count=3,
            score=18,
            score_label="scaffold-low",
            source_pull_present=True,
            payload_hash_present=True,
            freshness_status="scaffold",
            provenance_state="complete",
            record_count_delta=0,
            record_count_pct_change=0.0,
            score_delta=0,
            label="routine",
        ),
        ReviewPriorityExample(
            module="RegionalHealthPulse",
            source_id="regional_health_pulse_demo",
            upstream_status="success",
            query="Minnesota hospital pressure",
            record_count=16,
            score=52,
            score_label="scaffold-moderate",
            source_pull_present=True,
            payload_hash_present=True,
            freshness_status="scaffold",
            provenance_state="complete",
            record_count_delta=5,
            record_count_pct_change=45.0,
            score_delta=7,
            label="watch",
        ),
        ReviewPriorityExample(
            module="RegionalHealthPulse",
            source_id="regional_health_pulse_demo",
            upstream_status="success",
            query="Minnesota respiratory elevated",
            record_count=38,
            score=76,
            score_label="scaffold-high",
            source_pull_present=True,
            payload_hash_present=True,
            freshness_status="scaffold",
            provenance_state="complete",
            record_count_delta=18,
            record_count_pct_change=90.0,
            score_delta=15,
            label="elevated",
        ),
        ReviewPriorityExample(
            module="RecallRadar",
            source_id="openfda_drug_enforcement",
            upstream_status="error",
            query="recall source error",
            record_count=0,
            score=0,
            score_label="unavailable",
            source_pull_present=False,
            payload_hash_present=False,
            freshness_status="error",
            provenance_state="missing_source_pull",
            record_count_delta=0,
            record_count_pct_change=0.0,
            score_delta=0,
            label="watch",
        ),
    ]


def build_feature_rows() -> list[dict[str, object]]:
    return [example.to_features() for example in build_review_priority_examples()]


def build_labels() -> list[ReviewPriorityLabel]:
    return [example.label for example in build_review_priority_examples()]