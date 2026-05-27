"""Pure-Python recall-reason text classifier for Dav AI ML experiments.

This is intentionally offline and dependency-free. It is not wired into FastAPI
routes or production behavior.

The prediction target is public recall reason text category only:
- sterility
- contamination
- labeling
- packaging
- potency
- foreign_material
- temperature_control
- other

It is not medical advice, diagnosis, treatment guidance, patient-risk prediction,
clinical decision support, or official FDA severity classification.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from ml_experiments.recall_reason_dataset import (
    ALLOWED_RECALL_REASON_LABELS,
    RecallReasonLabel,
)


RecallReasonSafetyDisclaimer = (
    "This predicts public recall reason text category only. It is not medical "
    "advice, diagnosis, treatment guidance, patient risk prediction, clinical "
    "decision support, or official FDA severity classification."
)


KEYWORDS_BY_LABEL: dict[RecallReasonLabel, set[str]] = {
    "sterility": {
        "sterile",
        "sterility",
        "nonsterile",
        "non-sterile",
        "aseptic",
    },
    "contamination": {
        "contamination",
        "contaminated",
        "microbial",
        "bacteria",
        "mold",
        "cleaning",
        "residue",
    },
    "labeling": {
        "label",
        "labeled",
        "labeling",
        "mislabeled",
        "mislabel",
        "incorrect",
        "carton",
        "expiration",
    },
    "packaging": {
        "package",
        "packaging",
        "bottle",
        "cap",
        "seal",
        "blister",
        "missing",
    },
    "potency": {
        "potency",
        "subpotent",
        "superpotent",
        "assay",
        "specification",
        "strength",
    },
    "foreign_material": {
        "foreign",
        "particulate",
        "particle",
        "particles",
        "matter",
        "material",
        "visible",
    },
    "temperature_control": {
        "temperature",
        "refrigerated",
        "cold",
        "storage",
        "excursion",
        "shipment",
        "range",
    },
    "other": {
        "complaint",
        "administrative",
        "withdrawal",
        "investigation",
    },
}


@dataclass(frozen=True)
class RecallReasonPrediction:
    label: RecallReasonLabel
    confidence: float
    matched_keywords: list[str]
    safety_disclaimer: str = RecallReasonSafetyDisclaimer


def normalize_text(value: str) -> str:
    normalized = value.lower()
    normalized = normalized.replace("non sterile", "non-sterile")
    normalized = re.sub(r"[^a-z0-9\-\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def tokenize_text(value: str) -> list[str]:
    normalized = normalize_text(value)
    if not normalized:
        return []
    return normalized.split()


def keyword_scores(text: str) -> dict[RecallReasonLabel, int]:
    normalized = normalize_text(text)
    tokens = set(tokenize_text(text))

    scores: dict[RecallReasonLabel, int] = {}

    for label, keywords in KEYWORDS_BY_LABEL.items():
        score = 0

        for keyword in keywords:
            if " " in keyword or "-" in keyword:
                if keyword in normalized:
                    score += 1
            elif keyword in tokens:
                score += 1

        scores[label] = score

    return scores


class RuleBasedRecallReasonClassifier:
    """Explainable baseline for public recall-reason text categorization."""

    def fit(
        self,
        rows: list[dict[str, object]],
        labels: list[RecallReasonLabel],
    ) -> "RuleBasedRecallReasonClassifier":
        if len(rows) != len(labels):
            raise ValueError("rows and labels must have the same length")

        unknown_labels = set(labels) - ALLOWED_RECALL_REASON_LABELS
        if unknown_labels:
            raise ValueError(f"unknown labels: {sorted(unknown_labels)}")

        return self

    def predict_one(self, row: dict[str, object]) -> RecallReasonPrediction:
        combined_text = " ".join(
            [
                str(row.get("reason_for_recall", "")),
                str(row.get("product_description", "")),
                str(row.get("distribution_pattern", "")),
            ]
        )

        scores = keyword_scores(combined_text)
        best_score = max(scores.values()) if scores else 0

        if best_score == 0:
            return RecallReasonPrediction(
                label="other",
                confidence=0.0,
                matched_keywords=[],
            )

        best_labels = [
            label
            for label, score in scores.items()
            if score == best_score
        ]

        label = sorted(best_labels)[0]
        matched_keywords = sorted(
            keyword
            for keyword in KEYWORDS_BY_LABEL[label]
            if keyword in normalize_text(combined_text)
            or keyword in set(tokenize_text(combined_text))
        )

        total_score = sum(scores.values())
        confidence = best_score / total_score if total_score > 0 else 0.0

        return RecallReasonPrediction(
            label=label,
            confidence=confidence,
            matched_keywords=matched_keywords,
        )

    def predict(self, rows: list[dict[str, object]]) -> list[RecallReasonPrediction]:
        return [self.predict_one(row) for row in rows]


def confusion_matrix(
    true_labels: list[RecallReasonLabel],
    predicted_labels: list[RecallReasonLabel],
) -> dict[str, dict[str, int]]:
    labels = sorted(ALLOWED_RECALL_REASON_LABELS)

    matrix = {
        true_label: {predicted_label: 0 for predicted_label in labels}
        for true_label in labels
    }

    for true_label, predicted_label in zip(true_labels, predicted_labels, strict=True):
        matrix[true_label][predicted_label] += 1

    return matrix


def accuracy_score(
    true_labels: list[RecallReasonLabel],
    predicted_labels: list[RecallReasonLabel],
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
    true_labels: list[RecallReasonLabel],
    predicted_labels: list[RecallReasonLabel],
) -> float:
    labels = sorted(ALLOWED_RECALL_REASON_LABELS)
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
    true_labels: list[RecallReasonLabel],
    predicted_labels: list[RecallReasonLabel],
) -> dict[str, object]:
    label_counts = Counter(predicted_labels)

    return {
        "accuracy": accuracy_score(true_labels, predicted_labels),
        "macro_f1": macro_f1_score(true_labels, predicted_labels),
        "confusion_matrix": confusion_matrix(true_labels, predicted_labels),
        "prediction_counts": dict(label_counts),
        "safety_disclaimer": RecallReasonSafetyDisclaimer,
    }