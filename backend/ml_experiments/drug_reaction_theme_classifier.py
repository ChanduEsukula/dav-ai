"""Pure-Python DrugSignal reaction-theme classifier for Dav AI ML experiments.

This is intentionally offline and dependency-free. It is not wired into FastAPI
routes or production behavior.

The prediction target is public FAERS/openFDA reaction-term theme only:
- neurological
- gastrointestinal
- respiratory
- cardiovascular
- skin_allergy
- infection_immune
- metabolic
- general_other

It is not medical advice, diagnosis, treatment guidance, patient-risk prediction,
clinical decision support, incidence estimation, or proof of FAERS causation.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from ml_experiments.drug_reaction_theme_dataset import (
    ALLOWED_REACTION_THEME_LABELS,
    ReactionThemeLabel,
)


DrugReactionThemeSafetyDisclaimer = (
    "This predicts public FAERS/openFDA reaction-term theme only. It is not "
    "medical advice, diagnosis, treatment guidance, patient risk prediction, "
    "clinical decision support, incidence estimation, or proof of FAERS causation."
)


KEYWORDS_BY_LABEL: dict[ReactionThemeLabel, set[str]] = {
    "neurological": {
        "headache",
        "dizziness",
        "migraine",
        "tremor",
        "seizure",
        "somnolence",
        "confusion",
        "paraesthesia",
    },
    "gastrointestinal": {
        "nausea",
        "vomiting",
        "diarrhoea",
        "diarrhea",
        "abdominal",
        "constipation",
        "dyspepsia",
        "gastritis",
        "flatulence",
    },
    "respiratory": {
        "dyspnoea",
        "dyspnea",
        "cough",
        "wheezing",
        "bronchospasm",
        "respiratory",
        "hypoxia",
        "asthma",
        "throat",
    },
    "cardiovascular": {
        "palpitations",
        "tachycardia",
        "arrhythmia",
        "chest",
        "hypertension",
        "hypotension",
        "syncope",
        "cardiac",
    },
    "skin_allergy": {
        "rash",
        "urticaria",
        "pruritus",
        "angioedema",
        "anaphylaxis",
        "swelling",
        "erythema",
        "dermatitis",
        "skin",
    },
    "infection_immune": {
        "infection",
        "sepsis",
        "pneumonia",
        "immune",
        "neutropenia",
        "leukopenia",
        "suppression",
        "viral",
    },
    "metabolic": {
        "hyperglycaemia",
        "hyperglycemia",
        "hypoglycaemia",
        "hypoglycemia",
        "weight",
        "dehydration",
        "electrolyte",
        "hyponatraemia",
        "hyponatremia",
        "acidosis",
    },
    "general_other": {
        "fatigue",
        "malaise",
        "ineffective",
        "quality",
        "incorrect",
        "dose",
        "medication",
        "error",
    },
}


@dataclass(frozen=True)
class DrugReactionThemePrediction:
    label: ReactionThemeLabel
    confidence: float
    matched_keywords: list[str]
    safety_disclaimer: str = DrugReactionThemeSafetyDisclaimer


def normalize_text(value: str) -> str:
    normalized = value.lower()
    normalized = re.sub(r"[^a-z0-9\-\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def tokenize_text(value: str) -> list[str]:
    normalized = normalize_text(value)
    if not normalized:
        return []
    return normalized.split()


def keyword_scores(text: str) -> dict[ReactionThemeLabel, int]:
    normalized = normalize_text(text)
    tokens = set(tokenize_text(text))

    scores: dict[ReactionThemeLabel, int] = {}

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


class RuleBasedDrugReactionThemeClassifier:
    """Explainable baseline for public reaction-term theme categorization."""

    def fit(
        self,
        rows: list[dict[str, object]],
        labels: list[ReactionThemeLabel],
    ) -> "RuleBasedDrugReactionThemeClassifier":
        if len(rows) != len(labels):
            raise ValueError("rows and labels must have the same length")

        unknown_labels = set(labels) - ALLOWED_REACTION_THEME_LABELS
        if unknown_labels:
            raise ValueError(f"unknown labels: {sorted(unknown_labels)}")

        return self

    def predict_one(self, row: dict[str, object]) -> DrugReactionThemePrediction:
        reaction_terms = row.get("reaction_terms", [])
        if isinstance(reaction_terms, list):
            reaction_text = " ".join(str(term) for term in reaction_terms)
        else:
            reaction_text = str(reaction_terms)

        combined_text = " ".join(
            [
                str(row.get("top_reaction", "")),
                reaction_text,
                str(row.get("combined_text", "")),
            ]
        )

        scores = keyword_scores(combined_text)
        best_score = max(scores.values()) if scores else 0

        if best_score == 0:
            return DrugReactionThemePrediction(
                label="general_other",
                confidence=0.0,
                matched_keywords=[],
            )

        best_labels = [
            label
            for label, score in scores.items()
            if score == best_score
        ]

        label = sorted(best_labels)[0]
        normalized = normalize_text(combined_text)
        tokens = set(tokenize_text(combined_text))
        matched_keywords = sorted(
            keyword
            for keyword in KEYWORDS_BY_LABEL[label]
            if keyword in normalized or keyword in tokens
        )

        total_score = sum(scores.values())
        confidence = best_score / total_score if total_score > 0 else 0.0

        return DrugReactionThemePrediction(
            label=label,
            confidence=confidence,
            matched_keywords=matched_keywords,
        )

    def predict(self, rows: list[dict[str, object]]) -> list[DrugReactionThemePrediction]:
        return [self.predict_one(row) for row in rows]


def confusion_matrix(
    true_labels: list[ReactionThemeLabel],
    predicted_labels: list[ReactionThemeLabel],
) -> dict[str, dict[str, int]]:
    labels = sorted(ALLOWED_REACTION_THEME_LABELS)

    matrix = {
        true_label: {predicted_label: 0 for predicted_label in labels}
        for true_label in labels
    }

    for true_label, predicted_label in zip(true_labels, predicted_labels, strict=True):
        matrix[true_label][predicted_label] += 1

    return matrix


def accuracy_score(
    true_labels: list[ReactionThemeLabel],
    predicted_labels: list[ReactionThemeLabel],
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
    true_labels: list[ReactionThemeLabel],
    predicted_labels: list[ReactionThemeLabel],
) -> float:
    labels = sorted(ALLOWED_REACTION_THEME_LABELS)
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
    true_labels: list[ReactionThemeLabel],
    predicted_labels: list[ReactionThemeLabel],
) -> dict[str, object]:
    label_counts = Counter(predicted_labels)

    return {
        "accuracy": accuracy_score(true_labels, predicted_labels),
        "macro_f1": macro_f1_score(true_labels, predicted_labels),
        "confusion_matrix": confusion_matrix(true_labels, predicted_labels),
        "prediction_counts": dict(label_counts),
        "safety_disclaimer": DrugReactionThemeSafetyDisclaimer,
    }