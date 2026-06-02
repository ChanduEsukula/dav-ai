from __future__ import annotations

from typing import Any

from app.services.semantic_similarity_service import SemanticSimilarityServiceRecord


def build_drug_signal_semantic_candidates(
    *,
    query: str,
    top_reactions: list[dict[str, Any]],
    reaction_categories: list[dict[str, Any]],
    source_name: str | None = None,
) -> list[SemanticSimilarityServiceRecord]:
    """
    Convert normalized DrugSignal outputs into safe public-data text candidates.

    This adapter is backend-only. It supports future similar-reaction review
    workflows without making clinical claims, causality claims, patient-risk
    predictions, diagnosis, care guidance, alerts, or production ML output.
    """

    candidates: list[SemanticSimilarityServiceRecord] = []

    for index, reaction in enumerate(top_reactions):
        reaction_name = str(reaction.get("reaction") or "").strip()
        count = reaction.get("count")

        if not reaction_name:
            continue

        text_parts = [
            f"DrugSignal query: {query}",
            f"Reported reaction term: {reaction_name}",
            f"Public report count: {count}",
            "FAERS reports are public adverse-event reports and do not prove causality.",
        ]

        candidates.append(
            SemanticSimilarityServiceRecord(
                record_id=f"reaction-{index + 1}-{reaction_name.lower().replace(' ', '-')}",
                text=" | ".join(text_parts),
                source_name=source_name,
            )
        )

    for index, category in enumerate(reaction_categories):
        category_name = str(category.get("category") or "").strip()
        count = category.get("count")
        reactions = category.get("reactions") or []

        if not category_name:
            continue

        reaction_text = ", ".join(str(reaction).strip() for reaction in reactions if str(reaction).strip())

        text_parts = [
            f"DrugSignal query: {query}",
            f"Reaction category: {category_name}",
            f"Category public report count: {count}",
        ]

        if reaction_text:
            text_parts.append(f"Included reaction terms: {reaction_text}")

        text_parts.append("Category grouping is deterministic public-data organization only.")

        candidates.append(
            SemanticSimilarityServiceRecord(
                record_id=f"category-{index + 1}-{category_name.lower().replace(' ', '-')}",
                text=" | ".join(text_parts),
                source_name=source_name,
            )
        )

    return candidates
