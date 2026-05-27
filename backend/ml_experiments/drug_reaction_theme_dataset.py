"""Offline dataset builder for Dav AI DrugSignal reaction-theme experiments.

This module uses synthetic weak-label examples inspired by public FAERS/openFDA
reaction term patterns. It does not use PHI, patient records, private medical
history, prescription history, addresses, or patient-specific data.

The target is public reaction-term theme only:
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

from dataclasses import dataclass
from typing import Literal


ReactionThemeLabel = Literal[
    "neurological",
    "gastrointestinal",
    "respiratory",
    "cardiovascular",
    "skin_allergy",
    "infection_immune",
    "metabolic",
    "general_other",
]


ALLOWED_REACTION_THEME_LABELS: set[str] = {
    "neurological",
    "gastrointestinal",
    "respiratory",
    "cardiovascular",
    "skin_allergy",
    "infection_immune",
    "metabolic",
    "general_other",
}

TEXT_FEATURES = [
    "reaction_terms",
    "top_reaction",
]

CATEGORICAL_FEATURES = [
    "source_id",
    "upstream_status",
    "data_confidence",
]

NUMERIC_FEATURES = [
    "record_count",
    "reaction_count",
    "top_reaction_count",
    "top_reaction_concentration",
    "reaction_diversity_count",
    "reaction_terms_length",
    "reaction_terms_word_count",
]


@dataclass(frozen=True)
class DrugReactionThemeExample:
    reaction_terms: list[str]
    top_reaction: str
    source_id: str
    upstream_status: str
    data_confidence: str
    record_count: int
    top_reaction_count: int
    label: ReactionThemeLabel

    def reaction_count(self) -> int:
        return len(self.reaction_terms)

    def top_reaction_concentration(self) -> float:
        if self.record_count <= 0:
            return 0.0

        return self.top_reaction_count / self.record_count

    def reaction_diversity_count(self) -> int:
        return len(set(term.lower() for term in self.reaction_terms))

    def combined_text(self) -> str:
        return " ".join([self.top_reaction, *self.reaction_terms])

    def to_features(self) -> dict[str, object]:
        combined_text = self.combined_text()

        return {
            "reaction_terms": self.reaction_terms,
            "top_reaction": self.top_reaction,
            "source_id": self.source_id,
            "upstream_status": self.upstream_status,
            "data_confidence": self.data_confidence,
            "record_count": self.record_count,
            "reaction_count": self.reaction_count(),
            "top_reaction_count": self.top_reaction_count,
            "top_reaction_concentration": self.top_reaction_concentration(),
            "reaction_diversity_count": self.reaction_diversity_count(),
            "reaction_terms_length": len(combined_text),
            "reaction_terms_word_count": len(combined_text.split()),
            "combined_text": combined_text,
        }


def build_drug_reaction_theme_examples() -> list[DrugReactionThemeExample]:
    """Return deterministic weak-label examples for offline NLP testing.

    These examples are not clinical truth and do not prove drug causation. They
    are weak labels for testing public reaction-term theme classification,
    preprocessing, metrics, and safety boundaries before production integration.
    """

    return [
        DrugReactionThemeExample(
            reaction_terms=["Headache", "Dizziness", "Migraine", "Tremor"],
            top_reaction="Headache",
            source_id="openfda_drug_event",
            upstream_status="success",
            data_confidence="moderate",
            record_count=40,
            top_reaction_count=12,
            label="neurological",
        ),
        DrugReactionThemeExample(
            reaction_terms=["Seizure", "Somnolence", "Confusion", "Paraesthesia"],
            top_reaction="Seizure",
            source_id="openfda_drug_event",
            upstream_status="success",
            data_confidence="limited",
            record_count=22,
            top_reaction_count=6,
            label="neurological",
        ),
        DrugReactionThemeExample(
            reaction_terms=["Nausea", "Vomiting", "Diarrhoea", "Abdominal pain"],
            top_reaction="Nausea",
            source_id="openfda_drug_event",
            upstream_status="success",
            data_confidence="moderate",
            record_count=55,
            top_reaction_count=18,
            label="gastrointestinal",
        ),
        DrugReactionThemeExample(
            reaction_terms=["Constipation", "Dyspepsia", "Gastritis", "Flatulence"],
            top_reaction="Constipation",
            source_id="openfda_drug_event",
            upstream_status="success",
            data_confidence="limited",
            record_count=28,
            top_reaction_count=8,
            label="gastrointestinal",
        ),
        DrugReactionThemeExample(
            reaction_terms=["Dyspnoea", "Cough", "Wheezing", "Bronchospasm"],
            top_reaction="Dyspnoea",
            source_id="openfda_drug_event",
            upstream_status="success",
            data_confidence="moderate",
            record_count=36,
            top_reaction_count=11,
            label="respiratory",
        ),
        DrugReactionThemeExample(
            reaction_terms=["Respiratory distress", "Hypoxia", "Asthma", "Throat tightness"],
            top_reaction="Respiratory distress",
            source_id="openfda_drug_event",
            upstream_status="success",
            data_confidence="limited",
            record_count=25,
            top_reaction_count=7,
            label="respiratory",
        ),
        DrugReactionThemeExample(
            reaction_terms=["Palpitations", "Tachycardia", "Arrhythmia", "Chest pain"],
            top_reaction="Palpitations",
            source_id="openfda_drug_event",
            upstream_status="success",
            data_confidence="moderate",
            record_count=44,
            top_reaction_count=13,
            label="cardiovascular",
        ),
        DrugReactionThemeExample(
            reaction_terms=["Hypertension", "Hypotension", "Syncope", "Cardiac failure"],
            top_reaction="Hypertension",
            source_id="openfda_drug_event",
            upstream_status="success",
            data_confidence="limited",
            record_count=31,
            top_reaction_count=9,
            label="cardiovascular",
        ),
        DrugReactionThemeExample(
            reaction_terms=["Rash", "Urticaria", "Pruritus", "Angioedema"],
            top_reaction="Rash",
            source_id="openfda_drug_event",
            upstream_status="success",
            data_confidence="moderate",
            record_count=48,
            top_reaction_count=15,
            label="skin_allergy",
        ),
        DrugReactionThemeExample(
            reaction_terms=["Anaphylaxis", "Skin swelling", "Erythema", "Dermatitis"],
            top_reaction="Anaphylaxis",
            source_id="openfda_drug_event",
            upstream_status="success",
            data_confidence="limited",
            record_count=29,
            top_reaction_count=8,
            label="skin_allergy",
        ),
        DrugReactionThemeExample(
            reaction_terms=["Infection", "Sepsis", "Pneumonia", "Immune disorder"],
            top_reaction="Infection",
            source_id="openfda_drug_event",
            upstream_status="success",
            data_confidence="moderate",
            record_count=38,
            top_reaction_count=10,
            label="infection_immune",
        ),
        DrugReactionThemeExample(
            reaction_terms=["Neutropenia", "Leukopenia", "Immune suppression", "Viral infection"],
            top_reaction="Neutropenia",
            source_id="openfda_drug_event",
            upstream_status="success",
            data_confidence="limited",
            record_count=24,
            top_reaction_count=6,
            label="infection_immune",
        ),
        DrugReactionThemeExample(
            reaction_terms=["Hyperglycaemia", "Hypoglycaemia", "Weight increased", "Dehydration"],
            top_reaction="Hyperglycaemia",
            source_id="openfda_drug_event",
            upstream_status="success",
            data_confidence="moderate",
            record_count=35,
            top_reaction_count=10,
            label="metabolic",
        ),
        DrugReactionThemeExample(
            reaction_terms=["Electrolyte imbalance", "Hyponatraemia", "Acidosis", "Weight decreased"],
            top_reaction="Electrolyte imbalance",
            source_id="openfda_drug_event",
            upstream_status="success",
            data_confidence="limited",
            record_count=26,
            top_reaction_count=7,
            label="metabolic",
        ),
        DrugReactionThemeExample(
            reaction_terms=["Fatigue", "Malaise", "Drug ineffective", "Product quality issue"],
            top_reaction="Fatigue",
            source_id="openfda_drug_event",
            upstream_status="success",
            data_confidence="limited",
            record_count=33,
            top_reaction_count=8,
            label="general_other",
        ),
        DrugReactionThemeExample(
            reaction_terms=["No adverse event", "Incorrect dose administered", "Medication error"],
            top_reaction="Medication error",
            source_id="openfda_drug_event",
            upstream_status="success",
            data_confidence="limited",
            record_count=19,
            top_reaction_count=5,
            label="general_other",
        ),
    ]


def build_feature_rows() -> list[dict[str, object]]:
    return [example.to_features() for example in build_drug_reaction_theme_examples()]


def build_labels() -> list[ReactionThemeLabel]:
    return [example.label for example in build_drug_reaction_theme_examples()]