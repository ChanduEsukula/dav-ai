from __future__ import annotations

import json
import os

from app.schemas.assistant import (
    AssistantChatRequest,
    AssistantChatResponse,
    AssistantModelInfo,
    AssistantSourceCitation,
)
from app.services.assistant_guardrails import (
    ASSISTANT_POLICY_VERSION,
    build_refusal_response,
    build_unsafe_output_fallback,
    evaluate_question_safety,
    output_has_unsafe_language,
)
from app.services.llm_provider import AssistantLLMProvider, get_assistant_provider


class AssistantRequestError(ValueError):
    pass


SYSTEM_PROMPT = """You are Ask DAV AI, a public-data review assistant for DAV AI.

You may answer only using the DAV AI context provided in this request:
- current RecallRadar results
- current DrugSignal results
- current FoodRadar results
- current CosmeticSignal results
- current Public Safety Search results
- source metadata
- audit ID
- scores
- disclaimers
- known limitations

Do not use outside knowledge, browse the internet, infer facts not in context, or provide medical advice.

You must not provide diagnosis, treatment guidance, medication start/stop/change advice, emergency guidance, personal risk assessment, FAERS causation claims, or claims that a product or drug is safe/unsafe for a specific person.

For FAERS/DrugSignal, explain that reports are public reporting patterns only. They do not prove causation or incidence and may be incomplete, duplicated, delayed, or influenced by reporting behavior.

For RecallRadar, explain fields to verify against the official source. Do not say a specific product is safe or unsafe for a person.

Answer style: short, plain English, useful to average users, and grounded in the provided context."""


def _int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name, "").strip()
    if not raw_value:
        return default

    try:
        return int(raw_value)
    except ValueError:
        return default


def _validate_request(request: AssistantChatRequest) -> None:
    max_question_chars = _int_env("ASSISTANT_MAX_QUESTION_CHARS", 500)

    if len(request.question.strip()) > max_question_chars:
        raise AssistantRequestError("Assistant question is too long.")

    if request.module == "recall" and request.page_context.recall is None:
        raise AssistantRequestError("Recall assistant context is required.")

    if request.module == "drug_event" and request.page_context.drug_event is None:
        raise AssistantRequestError("DrugSignal assistant context is required.")

    if request.module == "food" and request.page_context.food is None:
        raise AssistantRequestError("FoodRadar assistant context is required.")

    if request.module == "cosmetic" and request.page_context.cosmetic is None:
        raise AssistantRequestError("CosmeticSignal assistant context is required.")

    if request.module == "public_safety" and request.page_context.public_safety is None:
        raise AssistantRequestError("Public Safety Search assistant context is required.")


def _source_citations(request: AssistantChatRequest) -> list[AssistantSourceCitation]:
    context = request.page_context
    return [
        AssistantSourceCitation(label="Source", value=context.source_name),
        AssistantSourceCitation(label="Retrieved", value=context.retrieval_timestamp),
        AssistantSourceCitation(label="Audit ID", value=context.audit_id),
    ]


def _limitations(request: AssistantChatRequest) -> list[str]:
    limitations = [
        limitation.strip()
        for limitation in request.page_context.limitations
        if limitation.strip()
    ]

    if request.module == "recall":
        recall_limit = (
            "RecallRadar uses public FDA/openFDA recall data only. It is not medical advice, "
            "clinical decision support, or a safety guarantee."
        )
        if recall_limit not in limitations:
            limitations.append(recall_limit)

    if request.module == "drug_event":
        faers_limit = request.page_context.drug_event.faers_disclaimer if request.page_context.drug_event else ""
        if faers_limit and faers_limit not in limitations:
            limitations.append(faers_limit)

        standard_limit = (
            "FAERS reports are public reporting patterns only and do not prove causation, "
            "incidence, personal risk, diagnosis, or treatment guidance."
        )
        if standard_limit not in limitations:
            limitations.append(standard_limit)

    if request.module == "food":
        food_limit = (
            "FoodRadar uses public FDA/openFDA and USDA FSIS-style food recall data only. "
            "It is not medical advice, official recall instruction, or a safety guarantee."
        )
        if food_limit not in limitations:
            limitations.append(food_limit)

    if request.module == "cosmetic":
        cosmetic_limit = (
            "CosmeticSignal uses public openFDA cosmetic adverse-event reports only. "
            "Reports do not prove causation, incidence, personal risk, diagnosis, or treatment guidance."
        )
        if cosmetic_limit not in limitations:
            limitations.append(cosmetic_limit)

    if request.module == "public_safety":
        public_safety_limit = (
            "Public Safety Search uses public official-source records and curated public-data context. "
            "Results are for review and verification only; they are not medical advice, legal advice, "
            "a causation finding, or a safety guarantee."
        )
        if public_safety_limit not in limitations:
            limitations.append(public_safety_limit)

    return limitations


def _context_for_prompt(request: AssistantChatRequest) -> dict:
    max_results = _int_env("ASSISTANT_MAX_CONTEXT_RESULTS", 5)
    context = request.page_context.model_dump(exclude_none=True)

    if "recall" in context:
        context["recall"]["top_results"] = context["recall"].get("top_results", [])[:max_results]

    if "drug_event" in context:
        context["drug_event"]["top_reactions"] = context["drug_event"].get("top_reactions", [])[:max_results]
        context["drug_event"]["reaction_categories"] = context["drug_event"].get("reaction_categories", [])[:max_results]

    if "food" in context:
        context["food"]["top_results"] = context["food"].get("top_results", [])[:max_results]

    if "cosmetic" in context:
        context["cosmetic"]["top_reactions"] = context["cosmetic"].get("top_reactions", [])[:max_results]
        context["cosmetic"]["records"] = context["cosmetic"].get("records", [])[:max_results]

    if "public_safety" in context:
        context["public_safety"]["top_records"] = context["public_safety"].get("top_records", [])[:max_results]
        context["public_safety"]["sources_checked"] = context["public_safety"].get("sources_checked", [])[:12]
        context["public_safety"]["sources_failed"] = context["public_safety"].get("sources_failed", [])[:8]

    return {
        "module": request.module,
        "question": request.question.strip(),
        "page_context": context,
        "required_limitations": _limitations(request),
    }


def _user_prompt(request: AssistantChatRequest) -> str:
    return (
        "Answer the user question using only this DAV AI public-data context. "
        "Keep the answer short and include the relevant source/audit limitations in plain language.\n\n"
        f"{json.dumps(_context_for_prompt(request), indent=2, sort_keys=True)}"
    )


def _bullets(request: AssistantChatRequest) -> list[str]:
    context = request.page_context

    if request.module == "recall" and context.recall:
        top_result = context.recall.top_results[0] if context.recall.top_results else None
        bullets = [
            f"{context.count} public FDA recall record(s) matched this search.",
            "Verify exact product, package, lot details, recalling firm, recall number, and official source record.",
        ]

        if top_result:
            bullets.insert(
                1,
                f"Top result: {top_result.product_description or 'Unknown product'}; "
                f"class/status: {top_result.classification or 'Unknown'} / {top_result.status or 'Unknown'}.",
            )
            bullets.insert(
                2,
                f"Reason listed: {top_result.reason_for_recall or 'No reason provided'}.",
            )

        return bullets

    if request.module == "drug_event" and context.drug_event:
        top_reaction = context.drug_event.top_reactions[0] if context.drug_event.top_reactions else None
        bullets = [
            f"{context.count} public FAERS-style report record(s) were reviewed.",
            (
                "DrugSignal score: "
                f"{context.drug_event.intelligence_score.score}/100 "
                f"{context.drug_event.intelligence_score.label}; "
                f"review priority: {context.drug_event.intelligence_score.review_priority}."
            ),
            "FAERS reports do not prove causation, incidence, personal risk, diagnosis, or treatment guidance.",
        ]

        if top_reaction:
            bullets.insert(
                2,
                f"Top reported reaction term: {top_reaction.reaction} ({top_reaction.count} mention(s)).",
            )

        return bullets

    if request.module == "food" and context.food:
        top_result = context.food.top_results[0] if context.food.top_results else None
        bullets = [
            f"{context.count} public food/supplement recall record(s) matched this search.",
            "Verify exact product name, recall number, lot/code details, recalling firm, status, source, and official record.",
            "No match or low score does not prove a product is safe or unsafe.",
        ]

        if top_result:
            bullets.insert(
                1,
                f"Top result: {top_result.product_description or 'Unknown product'}; "
                f"class/status: {top_result.classification or 'Unknown'} / {top_result.status or 'Unknown'}.",
            )
            bullets.insert(
                2,
                f"Reason listed: {top_result.reason_for_recall or 'No reason provided'}.",
            )

        return bullets

    if request.module == "cosmetic" and context.cosmetic:
        top_reaction = context.cosmetic.top_reactions[0] if context.cosmetic.top_reactions else None
        bullets = [
            f"{context.count} public cosmetic adverse-event report record(s) were reviewed.",
            (
                "CosmeticSignal score: "
                f"{context.cosmetic.signal_score.score}/100 "
                f"{context.cosmetic.signal_score.label}; "
                f"review priority: {context.cosmetic.signal_score.review_priority}."
            ),
            "Cosmetic adverse-event reports do not prove causation, incidence, personal risk, diagnosis, or treatment guidance.",
        ]

        if top_reaction:
            bullets.insert(
                2,
                f"Top reported reaction term: {top_reaction.reaction} ({top_reaction.count} mention(s)).",
            )

        return bullets

    if request.module == "public_safety" and context.public_safety:
        summary = context.public_safety.summary
        top_record = context.public_safety.top_records[0] if context.public_safety.top_records else None
        bullets = [
            f"{context.count} public safety record(s) or context item(s) matched this search.",
            summary.plain_language_summary,
            "Verify exact identifiers such as lot, UPC, NDC, UDI, model, recall number, or VIN when available.",
            "Adverse-event reports, complaints, and investigation context are public-data signals, not proof of causation.",
        ]

        if top_record:
            title = top_record.title or top_record.product_name or "Untitled public safety record"
            bullets.insert(
                1,
                f"Top record: {title}; source: {top_record.source_name}; type: {top_record.source_type}.",
            )

        if summary.caveat:
            bullets.append(summary.caveat)

        return bullets

    return ["Review the source details, audit ID, retrieval timestamp, and limitations."]


def _truncate_answer(answer: str) -> str:
    max_output_chars = _int_env("ASSISTANT_MAX_OUTPUT_CHARS", 1200)
    stripped = answer.strip()

    if len(stripped) <= max_output_chars:
        return stripped

    return stripped[: max_output_chars - 3].rstrip() + "..."


async def generate_assistant_response(
    request: AssistantChatRequest,
    *,
    provider: AssistantLLMProvider | None = None,
) -> AssistantChatResponse:
    _validate_request(request)

    source_citations = _source_citations(request)
    limitations = _limitations(request)
    question_safety = evaluate_question_safety(request.question)

    if question_safety.refused:
        return build_refusal_response(
            reason=question_safety.reason or "unsafe medical question",
            source_citations=source_citations,
            limitations=limitations,
        )

    assistant_provider = provider or get_assistant_provider()
    provider_response = await assistant_provider.generate_answer(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=_user_prompt(request),
    )
    answer = _truncate_answer(provider_response.text)

    if output_has_unsafe_language(answer):
        return build_unsafe_output_fallback(
            source_citations=source_citations,
            limitations=limitations,
            provider=provider_response.provider,
            model=provider_response.model,
        )

    return AssistantChatResponse(
        answer=answer,
        bullets=_bullets(request),
        refused=False,
        refusal_reason=None,
        source_citations=source_citations,
        limitations=limitations,
        model_info=AssistantModelInfo(
            provider=provider_response.provider,
            model=provider_response.model,
        ),
        safety={
            "policy_version": ASSISTANT_POLICY_VERSION,
            "output_checked": True,
        },
    )
