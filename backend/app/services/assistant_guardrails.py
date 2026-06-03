from __future__ import annotations

import re
from dataclasses import dataclass

from app.schemas.assistant import AssistantChatResponse, AssistantModelInfo, AssistantSourceCitation


ASSISTANT_POLICY_VERSION = "ask-dav-ai-safety-v0.1"

UNSAFE_QUESTION_PATTERNS = [
    (re.compile(r"\bshould\s+i\s+(stop|start|take|use|change)\b", re.I), "medication guidance"),
    (re.compile(r"\b(is|are)\b.+\bsafe\s+for\s+me\b", re.I), "personal safety assessment"),
    (re.compile(r"\bdid\b.+\b(cause|caused)\b.+\b(my|me)\b", re.I), "personal causation claim"),
    (re.compile(r"\bdo\s+i\s+have\b", re.I), "diagnosis"),
    (re.compile(r"\bwhat\s+(treatment|dose|dosage)\b", re.I), "treatment guidance"),
    (re.compile(r"\bdiagnos", re.I), "diagnosis"),
    (re.compile(r"\bemergency\b|\ber\b|\b911\b", re.I), "emergency guidance"),
]

UNSAFE_OUTPUT_PATTERNS = [
    re.compile(r"\bstop\s+taking\b", re.I),
    re.compile(r"\bstart\s+taking\b", re.I),
    re.compile(r"\bchange\s+your\s+medication\b", re.I),
    re.compile(r"\bdiagnosed\s+with\b", re.I),
    re.compile(r"\bcaused\s+by\s+this\s+drug\b", re.I),
    re.compile(r"\bcaused\s+your\b", re.I),
    re.compile(r"\bsafe\s+for\s+you\b", re.I),
    re.compile(r"\bpersonal\s+risk\s+is\b", re.I),
]


@dataclass(frozen=True)
class GuardrailDecision:
    refused: bool
    reason: str | None = None


def evaluate_question_safety(question: str) -> GuardrailDecision:
    for pattern, reason in UNSAFE_QUESTION_PATTERNS:
        if pattern.search(question):
            return GuardrailDecision(refused=True, reason=reason)

    return GuardrailDecision(refused=False)


def output_has_unsafe_language(answer: str) -> bool:
    return any(pattern.search(answer) for pattern in UNSAFE_OUTPUT_PATTERNS)


def build_refusal_response(
    *,
    reason: str,
    source_citations: list[AssistantSourceCitation],
    limitations: list[str],
) -> AssistantChatResponse:
    return AssistantChatResponse(
        answer=(
            "I can explain the public DAV AI result, source details, audit context, "
            "and review limitations, but I cannot provide medical advice, diagnosis, "
            "treatment guidance, emergency guidance, medication instructions, personal "
            "risk assessment, or FAERS causation claims."
        ),
        bullets=[
            "Use DAV AI for public-data review support only.",
            "Verify official FDA/openFDA source details before acting on a result.",
            "For personal medical questions, contact a qualified clinician or pharmacist.",
        ],
        refused=True,
        refusal_reason=reason,
        source_citations=source_citations,
        limitations=limitations,
        model_info=AssistantModelInfo(provider="guardrail", model="pre-llm-refusal"),
        safety={
            "policy_version": ASSISTANT_POLICY_VERSION,
            "output_checked": True,
        },
    )


def build_unsafe_output_fallback(
    *,
    source_citations: list[AssistantSourceCitation],
    limitations: list[str],
    provider: str,
    model: str,
) -> AssistantChatResponse:
    return AssistantChatResponse(
        answer=(
            "I can only summarize the public-data review context safely. The generated "
            "answer was replaced because it did not meet DAV AI safety boundaries."
        ),
        bullets=[
            "Review the source result, audit ID, retrieval timestamp, and official source details.",
            "Do not use DAV AI output as diagnosis, treatment guidance, or medication instructions.",
            "FAERS reports are reporting patterns only and do not prove causation.",
        ],
        refused=True,
        refusal_reason="unsafe generated output",
        source_citations=source_citations,
        limitations=limitations,
        model_info=AssistantModelInfo(provider=provider, model=model),
        safety={
            "policy_version": ASSISTANT_POLICY_VERSION,
            "output_checked": True,
        },
    )
