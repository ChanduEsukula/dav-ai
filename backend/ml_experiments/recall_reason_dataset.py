"""Offline dataset builder for Dav AI recall-reason NLP experiments.

This module uses synthetic weak-label examples inspired by public FDA/openFDA
recall reason text. It does not use PHI, patient records, private medical
history, prescription history, addresses, or patient-specific data.

The target is public recall reason text category only:
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

from dataclasses import dataclass
from typing import Literal


RecallReasonLabel = Literal[
    "sterility",
    "contamination",
    "labeling",
    "packaging",
    "potency",
    "foreign_material",
    "temperature_control",
    "other",
]


ALLOWED_RECALL_REASON_LABELS: set[str] = {
    "sterility",
    "contamination",
    "labeling",
    "packaging",
    "potency",
    "foreign_material",
    "temperature_control",
    "other",
}

TEXT_FEATURES = [
    "reason_for_recall",
    "product_description",
    "distribution_pattern",
]

CATEGORICAL_FEATURES = [
    "classification",
    "status",
]

NUMERIC_FEATURES = [
    "reason_length",
    "reason_word_count",
    "product_description_length",
    "distribution_pattern_length",
]


@dataclass(frozen=True)
class RecallReasonExample:
    reason_for_recall: str
    product_description: str
    distribution_pattern: str
    classification: str
    status: str
    label: RecallReasonLabel

    def combined_text(self) -> str:
        return " ".join(
            [
                self.reason_for_recall,
                self.product_description,
                self.distribution_pattern,
            ]
        )

    def to_features(self) -> dict[str, object]:
        return {
            "reason_for_recall": self.reason_for_recall,
            "product_description": self.product_description,
            "distribution_pattern": self.distribution_pattern,
            "classification": self.classification,
            "status": self.status,
            "reason_length": len(self.reason_for_recall),
            "reason_word_count": len(self.reason_for_recall.split()),
            "product_description_length": len(self.product_description),
            "distribution_pattern_length": len(self.distribution_pattern),
            "combined_text": self.combined_text(),
        }


def build_recall_reason_examples() -> list[RecallReasonExample]:
    """Return deterministic weak-label examples for offline NLP testing.

    These examples are not official FDA labels. They are weak labels for testing
    text normalization, keyword baselines, category prediction, metrics, and
    safety boundaries before any production ML integration.
    """

    return [
        RecallReasonExample(
            reason_for_recall="Lack of sterility assurance for ophthalmic solution.",
            product_description="Sterile eye drops in multi-dose bottles.",
            distribution_pattern="Distributed nationwide to retail pharmacies.",
            classification="Class II",
            status="Ongoing",
            label="sterility",
        ),
        RecallReasonExample(
            reason_for_recall="Product may be non-sterile due to manufacturing deviation.",
            product_description="Injectable solution vials.",
            distribution_pattern="Distributed to clinics and hospitals.",
            classification="Class II",
            status="Ongoing",
            label="sterility",
        ),
        RecallReasonExample(
            reason_for_recall="Microbial contamination detected in finished product testing.",
            product_description="Liquid oral medication.",
            distribution_pattern="Distributed nationwide.",
            classification="Class II",
            status="Ongoing",
            label="contamination",
        ),
        RecallReasonExample(
            reason_for_recall="Possible contamination with cleaning solution residue.",
            product_description="Topical antiseptic wipes.",
            distribution_pattern="Distributed to wholesalers.",
            classification="Class II",
            status="Completed",
            label="contamination",
        ),
        RecallReasonExample(
            reason_for_recall="Incorrect label strength printed on carton.",
            product_description="Prescription tablets in bottles.",
            distribution_pattern="Distributed to retail pharmacies.",
            classification="Class II",
            status="Ongoing",
            label="labeling",
        ),
        RecallReasonExample(
            reason_for_recall="Mislabeled product contains incorrect expiration date.",
            product_description="Over the counter capsules.",
            distribution_pattern="Distributed in the United States.",
            classification="Class III",
            status="Completed",
            label="labeling",
        ),
        RecallReasonExample(
            reason_for_recall="Bottle cap may not seal properly due to packaging defect.",
            product_description="Oral suspension bottles.",
            distribution_pattern="Distributed to wholesalers and retailers.",
            classification="Class II",
            status="Ongoing",
            label="packaging",
        ),
        RecallReasonExample(
            reason_for_recall="Blister packaging may be missing tablets.",
            product_description="Tablet blister cards.",
            distribution_pattern="Distributed nationwide.",
            classification="Class III",
            status="Completed",
            label="packaging",
        ),
        RecallReasonExample(
            reason_for_recall="Subpotent active ingredient results below specification.",
            product_description="Prescription capsules.",
            distribution_pattern="Distributed to pharmacies.",
            classification="Class II",
            status="Ongoing",
            label="potency",
        ),
        RecallReasonExample(
            reason_for_recall="Superpotent product due to assay results above specification.",
            product_description="Compounded medication.",
            distribution_pattern="Distributed to healthcare facilities.",
            classification="Class II",
            status="Ongoing",
            label="potency",
        ),
        RecallReasonExample(
            reason_for_recall="Foreign material observed in product container.",
            product_description="Liquid medication bottle.",
            distribution_pattern="Distributed to pharmacies and clinics.",
            classification="Class II",
            status="Ongoing",
            label="foreign_material",
        ),
        RecallReasonExample(
            reason_for_recall="Visible particulate matter found in injectable solution.",
            product_description="Sterile injectable vial.",
            distribution_pattern="Distributed to hospitals.",
            classification="Class II",
            status="Ongoing",
            label="foreign_material",
        ),
        RecallReasonExample(
            reason_for_recall="Temperature excursion occurred during cold chain shipment.",
            product_description="Refrigerated biologic product.",
            distribution_pattern="Distributed through specialty pharmacies.",
            classification="Class II",
            status="Ongoing",
            label="temperature_control",
        ),
        RecallReasonExample(
            reason_for_recall="Product stored outside labeled temperature range.",
            product_description="Cold storage medication.",
            distribution_pattern="Distributed regionally.",
            classification="Class II",
            status="Completed",
            label="temperature_control",
        ),
        RecallReasonExample(
            reason_for_recall="Recall initiated due to customer complaint investigation.",
            product_description="General healthcare product.",
            distribution_pattern="Limited distribution.",
            classification="Class III",
            status="Completed",
            label="other",
        ),
        RecallReasonExample(
            reason_for_recall="Market withdrawal due to administrative issue.",
            product_description="Healthcare product.",
            distribution_pattern="Distributed to one account.",
            classification="Class III",
            status="Completed",
            label="other",
        ),
    ]


def build_feature_rows() -> list[dict[str, object]]:
    return [example.to_features() for example in build_recall_reason_examples()]


def build_labels() -> list[RecallReasonLabel]:
    return [example.label for example in build_recall_reason_examples()]