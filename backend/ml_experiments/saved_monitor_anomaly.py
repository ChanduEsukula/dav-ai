"""Pure-Python saved-monitor anomaly baseline for Dav AI ML experiments.

This is intentionally offline and dependency-free. It is not wired into FastAPI
routes or production behavior.

The prediction target is public-data saved-monitor change state only:
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

from collections import Counter
from dataclasses import dataclass

from ml_experiments.saved_monitor_anomaly_dataset import (
    ALLOWED_MONITOR_ANOMALY_LABELS,
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    MonitorAnomalyLabel,
)


SavedMonitorAnomalySafetyDisclaimer = (
    "This predicts public-data saved-monitor change state only. It is not medical "
    "advice, diagnosis, treatment guidance, patient risk prediction, clinical "
    "decision support, outbreak prediction, or proof of causation."
)


@dataclass(frozen=True)
class MonitorAnomalyPrediction:
    label: MonitorAnomalyLabel
    reasons: list[str]
    safety_disclaimer: str = SavedMonitorAnomalySafetyDisclaimer


def encode_categorical_features(rows: list[dict[str, object]]) -> list[dict[str, int]]:
    """One-hot encode monitor categorical features without ordinal assumptions."""

    categories_by_feature: dict[str, list[str]] = {}

    for feature in CATEGORICAL_FEATURES:
        categories = sorted({str(row.get(feature, "missing")) for row in rows})
        categories_by_feature[feature] = categories

    encoded_rows: list[dict[str, int]] = []

    for row in rows:
        encoded: dict[str, int] = {}

        for feature, categories in categories_by_feature.items():
            value = str(row.get(feature, "missing"))
            for category in categories:
                encoded[f"{feature}__{category}"] = 1 if value == category else 0

        encoded_rows.append(encoded)

    return encoded_rows


def standardize_numeric_features(rows: list[dict[str, object]]) -> list[dict[str, float]]:
    """Standardize continuous numeric monitor features only.

    One-hot dummy variables should not be standardized.
    """

    means: dict[str, float] = {}
    stds: dict[str, float] = {}

    for feature in NUMERIC_FEATURES:
        values = [float(row.get(feature, 0) or 0) for row in rows]
        mean = sum(values) / len(values)
        variance = sum((value - mean) ** 2 for value in values) / len(values)
        std = variance**0.5

        means[feature] = mean
        stds[feature] = std if std > 0 else 1.0

    standardized_rows: list[dict[str, float]] = []

    for row in rows:
        standardized = {}
        for feature in NUMERIC_FEATURES:
            value = float(row.get(feature, 0) or 0)
            standardized[feature] = (value - means[feature]) / stds[feature]
        standardized_rows.append(standardized)

    return standardized_rows


class RuleBasedSavedMonitorAnomalyClassifier:
    """Explainable baseline for saved-monitor public-data change state."""

    def fit(
        self,
        rows: list[dict[str, object]],
        labels: list[MonitorAnomalyLabel],
    ) -> "RuleBasedSavedMonitorAnomalyClassifier":
        if len(rows) != len(labels):
            raise ValueError("rows and labels must have the same length")

        unknown_labels = set(labels) - ALLOWED_MONITOR_ANOMALY_LABELS
        if unknown_labels:
            raise ValueError(f"unknown labels: {sorted(unknown_labels)}")

        return self

    def predict_one(self, row: dict[str, object]) -> MonitorAnomalyPrediction:
        reasons: list[str] = []

        upstream_status = str(row.get("upstream_status", ""))
        freshness_status = str(row.get("freshness_status", ""))
        provenance_state = str(row.get("provenance_state", ""))
        last_scheduled_status = str(row.get("last_scheduled_status", ""))

        run_count = int(row.get("run_count", 0) or 0)
        days_since_last_run = int(row.get("days_since_last_run", 0) or 0)
        record_count_delta = int(row.get("record_count_delta", 0) or 0)
        record_count_pct_change = float(row.get("record_count_pct_change", 0) or 0)
        score_delta = int(row.get("score_delta", 0) or 0)

        source_pull_present = bool(row.get("source_pull_present", False))
        payload_hash_present = bool(row.get("payload_hash_present", False))

        if (
            upstream_status == "error"
            or last_scheduled_status == "error"
            or freshness_status in {"error", "delayed", "unknown"}
            or provenance_state == "missing_source_pull"
            or not source_pull_present
            or not payload_hash_present
        ):
            reasons.append("source, schedule, freshness, or provenance requires review")
            return MonitorAnomalyPrediction(label="source_warning", reasons=reasons)

        if run_count < 2:
            reasons.append("monitor has insufficient run history")
            return MonitorAnomalyPrediction(label="insufficient_history", reasons=reasons)

        if days_since_last_run >= 14:
            reasons.append("monitor has not run recently")
            return MonitorAnomalyPrediction(label="source_warning", reasons=reasons)

        if record_count_pct_change >= 75 or score_delta >= 20 or record_count_delta >= 20:
            reasons.append("notable increase in public-data monitor activity")
            return MonitorAnomalyPrediction(label="notable_increase", reasons=reasons)

        if record_count_pct_change <= -60 or score_delta <= -20 or record_count_delta <= -15:
            reasons.append("notable decrease in public-data monitor activity")
            return MonitorAnomalyPrediction(label="notable_decrease", reasons=reasons)

        if record_count_pct_change >= 25 or score_delta >= 5 or record_count_delta >= 5:
            reasons.append("increase in public-data monitor activity")
            return MonitorAnomalyPrediction(label="increased", reasons=reasons)

        if record_count_pct_change <= -25 or score_delta <= -5 or record_count_delta <= -5:
            reasons.append("decrease in public-data monitor activity")
            return MonitorAnomalyPrediction(label="decreased", reasons=reasons)

        reasons.append("public-data monitor activity appears stable")
        return MonitorAnomalyPrediction(label="stable", reasons=reasons)

    def predict(self, rows: list[dict[str, object]]) -> list[MonitorAnomalyPrediction]:
        return [self.predict_one(row) for row in rows]


def confusion_matrix(
    true_labels: list[MonitorAnomalyLabel],
    predicted_labels: list[MonitorAnomalyLabel],
) -> dict[str, dict[str, int]]:
    labels = sorted(ALLOWED_MONITOR_ANOMALY_LABELS)

    matrix = {
        true_label: {predicted_label: 0 for predicted_label in labels}
        for true_label in labels
    }

    for true_label, predicted_label in zip(true_labels, predicted_labels, strict=True):
        matrix[true_label][predicted_label] += 1

    return matrix


def accuracy_score(
    true_labels: list[MonitorAnomalyLabel],
    predicted_labels: list[MonitorAnomalyLabel],
) -> float:
    if not true_labels:
        return 0.0

    correct = sum(
        1
        for true_label, predicted_label in zip(true_labels, predicted_labels, strict=True)
        if true_label == predicted_label
    )

    return correct / len(true_labels)


def macro_f1_score(
    true_labels: list[MonitorAnomalyLabel],
    predicted_labels: list[MonitorAnomalyLabel],
) -> float:
    labels = sorted(ALLOWED_MONITOR_ANOMALY_LABELS)
    f1_scores: list[float] = []

    for label in labels:
        true_positive = sum(
            1
            for true_label, predicted_label in zip(true_labels, predicted_labels, strict=True)
            if true_label == label and predicted_label == label
        )
        false_positive = sum(
            1
            for true_label, predicted_label in zip(true_labels, predicted_labels, strict=True)
            if true_label != label and predicted_label == label
        )
        false_negative = sum(
            1
            for true_label, predicted_label in zip(true_labels, predicted_labels, strict=True)
            if true_label == label and predicted_label != label
        )

        precision = (
            true_positive / (true_positive + false_positive)
            if true_positive + false_positive > 0
            else 0.0
        )
        recall = (
            true_positive / (true_positive + false_negative)
            if true_positive + false_negative > 0
            else 0.0
        )

        if precision + recall == 0:
            f1_scores.append(0.0)
        else:
            f1_scores.append(2 * precision * recall / (precision + recall))

    return sum(f1_scores) / len(f1_scores)


def evaluate_classifier(
    true_labels: list[MonitorAnomalyLabel],
    predicted_labels: list[MonitorAnomalyLabel],
) -> dict[str, object]:
    label_counts = Counter(predicted_labels)

    return {
        "accuracy": accuracy_score(true_labels, predicted_labels),
        "macro_f1": macro_f1_score(true_labels, predicted_labels),
        "confusion_matrix": confusion_matrix(true_labels, predicted_labels),
        "prediction_counts": dict(label_counts),
        "safety_disclaimer": SavedMonitorAnomalySafetyDisclaimer,
    }