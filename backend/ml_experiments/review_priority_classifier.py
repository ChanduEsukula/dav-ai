"""Pure-Python baseline classifier for Dav AI review-priority ML experiments.

This is intentionally offline and dependency-free. It is not wired into FastAPI
routes or production behavior.

The prediction target is operational public-data review priority only:
- routine
- watch
- elevated

It is not medical advice, diagnosis, treatment guidance, patient-risk prediction,
clinical decision support, or proof of FAERS causation.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Literal

from ml_experiments.review_priority_dataset import (
    ALLOWED_REVIEW_PRIORITY_LABELS,
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    ReviewPriorityLabel,
)


PredictionSafetyDisclaimer = (
    "This predicts public-data review priority only. It is not medical advice, "
    "diagnosis, treatment guidance, patient risk prediction, clinical decision "
    "support, or proof of causation."
)


@dataclass(frozen=True)
class PredictionResult:
    label: ReviewPriorityLabel
    reasons: list[str]
    safety_disclaimer: str = PredictionSafetyDisclaimer


def encode_categorical_features(rows: list[dict[str, object]]) -> list[dict[str, int]]:
    """One-hot encode categorical features without treating them as ordinal."""

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
    """Standardize numeric features for linear-model style experiments.

    This function only standardizes continuous numeric features. It does not
    standardize one-hot dummy variables.
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


def train_test_split(
    rows: list[dict[str, object]],
    labels: list[ReviewPriorityLabel],
    test_every_nth: int = 3,
) -> tuple[
    list[dict[str, object]],
    list[ReviewPriorityLabel],
    list[dict[str, object]],
    list[ReviewPriorityLabel],
]:
    """Deterministic split for small offline tests."""

    train_rows: list[dict[str, object]] = []
    train_labels: list[ReviewPriorityLabel] = []
    test_rows: list[dict[str, object]] = []
    test_labels: list[ReviewPriorityLabel] = []

    for index, (row, label) in enumerate(zip(rows, labels, strict=True), start=1):
        if index % test_every_nth == 0:
            test_rows.append(row)
            test_labels.append(label)
        else:
            train_rows.append(row)
            train_labels.append(label)

    return train_rows, train_labels, test_rows, test_labels


class RuleBasedReviewPriorityClassifier:
    """Explainable baseline for public-data review priority.

    This is a baseline model, not clinical decision support.
    """

    def fit(
        self,
        rows: list[dict[str, object]],
        labels: list[ReviewPriorityLabel],
    ) -> "RuleBasedReviewPriorityClassifier":
        if len(rows) != len(labels):
            raise ValueError("rows and labels must have the same length")

        unknown_labels = set(labels) - ALLOWED_REVIEW_PRIORITY_LABELS
        if unknown_labels:
            raise ValueError(f"unknown labels: {sorted(unknown_labels)}")

        return self

    def predict_one(self, row: dict[str, object]) -> PredictionResult:
        reasons: list[str] = []

        upstream_status = str(row.get("upstream_status", ""))
        provenance_state = str(row.get("provenance_state", ""))
        freshness_status = str(row.get("freshness_status", ""))

        record_count = int(row.get("record_count", 0) or 0)
        score = int(row.get("score", 0) or 0)
        record_count_pct_change = float(row.get("record_count_pct_change", 0) or 0)
        score_delta = int(row.get("score_delta", 0) or 0)
        source_pull_present = bool(row.get("source_pull_present", False))
        payload_hash_present = bool(row.get("payload_hash_present", False))

        if upstream_status == "error":
            reasons.append("upstream status is error")
            return PredictionResult(label="watch", reasons=reasons)

        if provenance_state == "missing_source_pull" or not source_pull_present:
            reasons.append("source pull provenance is incomplete")
            return PredictionResult(label="watch", reasons=reasons)

        if not payload_hash_present:
            reasons.append("payload hash is missing")
            return PredictionResult(label="watch", reasons=reasons)

        if score >= 75 or record_count >= 40:
            reasons.append("high score or high public record count")
            return PredictionResult(label="elevated", reasons=reasons)

        if record_count_pct_change >= 75 or score_delta >= 15:
            reasons.append("notable increase from previous public-data run")
            return PredictionResult(label="elevated", reasons=reasons)

        if score >= 40 or record_count >= 10:
            reasons.append("moderate score or moderate public record count")
            return PredictionResult(label="watch", reasons=reasons)

        if record_count_pct_change >= 25 or score_delta >= 5:
            reasons.append("meaningful increase from previous public-data run")
            return PredictionResult(label="watch", reasons=reasons)

        if freshness_status in {"delayed", "unknown", "scaffold"}:
            reasons.append("source freshness requires reviewer awareness")
            return PredictionResult(label="watch", reasons=reasons)

        reasons.append("low public-data activity with complete provenance")
        return PredictionResult(label="routine", reasons=reasons)

    def predict(self, rows: list[dict[str, object]]) -> list[PredictionResult]:
        return [self.predict_one(row) for row in rows]


def confusion_matrix(
    true_labels: list[ReviewPriorityLabel],
    predicted_labels: list[ReviewPriorityLabel],
) -> dict[str, dict[str, int]]:
    labels = sorted(ALLOWED_REVIEW_PRIORITY_LABELS)

    matrix = {
        true_label: {predicted_label: 0 for predicted_label in labels}
        for true_label in labels
    }

    for true_label, predicted_label in zip(true_labels, predicted_labels, strict=True):
        matrix[true_label][predicted_label] += 1

    return matrix


def accuracy_score(
    true_labels: list[ReviewPriorityLabel],
    predicted_labels: list[ReviewPriorityLabel],
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
    true_labels: list[ReviewPriorityLabel],
    predicted_labels: list[ReviewPriorityLabel],
) -> float:
    labels = sorted(ALLOWED_REVIEW_PRIORITY_LABELS)
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
    true_labels: list[ReviewPriorityLabel],
    predicted_labels: list[ReviewPriorityLabel],
) -> dict[str, object]:
    label_counts = Counter(predicted_labels)

    return {
        "accuracy": accuracy_score(true_labels, predicted_labels),
        "macro_f1": macro_f1_score(true_labels, predicted_labels),
        "confusion_matrix": confusion_matrix(true_labels, predicted_labels),
        "prediction_counts": dict(label_counts),
        "safety_disclaimer": PredictionSafetyDisclaimer,
    }