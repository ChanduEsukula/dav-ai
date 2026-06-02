from __future__ import annotations

from typing import Any

from app.services.semantic_similarity_service import SemanticSimilarityServiceRecord


def build_recall_semantic_candidates(
    recall_results: list[dict[str, Any]],
) -> list[SemanticSimilarityServiceRecord]:
    """
    Convert normalized RecallRadar results into safe public-data text candidates.

    This is a backend-only adapter for future similar-recall review workflows.
    It does not make clinical claims, product danger claims, causality claims,
    diagnosis, care guidance, alerts, or production ML output.
    """

    candidates: list[SemanticSimilarityServiceRecord] = []

    for index, recall in enumerate(recall_results):
        recall_number = recall.get("recall_number") or f"recall-{index + 1}"

        text_parts = [
            recall.get("product_description"),
            recall.get("reason_for_recall"),
            recall.get("classification"),
            recall.get("status"),
            recall.get("recall_initiation_date"),
            recall.get("distribution_pattern"),
            recall.get("recalling_firm"),
        ]

        text = " | ".join(
            str(part).strip()
            for part in text_parts
            if part is not None and str(part).strip()
        )

        if not text:
            continue

        source = recall.get("source") or {}
        source_name = source.get("name") if isinstance(source, dict) else None

        candidates.append(
            SemanticSimilarityServiceRecord(
                record_id=str(recall_number),
                text=text,
                source_name=source_name,
            )
        )

    return candidates
