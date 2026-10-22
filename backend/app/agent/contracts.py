"""Strict local-agent contracts. No authority, sessions or IDs come from a model."""
from dataclasses import dataclass
import json

from pydantic import BaseModel, ConfigDict, Field


class AgentRejected(ValueError):
    pass


class QueryArguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    query: str = Field(min_length=1, max_length=200)


class RecallArguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    product_ref: str = Field(min_length=1, max_length=96)


@dataclass(frozen=True)
class Limits:
    max_iterations: int = 4
    max_tool_calls: int = 4
    max_response_bytes: int = 65536
    max_prompt_bytes: int = 12288
    max_evidence_bytes: int = 65536
    model_timeout: float = 45
    tool_timeout: float = 20
    run_timeout: float = 70
    session_lifetime: float = 600
    context_tokens: int = 4096
    prediction_tokens: int = 512

    def __post_init__(self):
        for name in ("max_iterations", "max_tool_calls", "max_response_bytes", "max_prompt_bytes",
                     "max_evidence_bytes", "context_tokens", "prediction_tokens"):
            value = getattr(self, name)
            if type(value) is not int or not 0 < value <= 1048576:
                raise ValueError("Invalid agent limit")
        for name in ("model_timeout", "tool_timeout", "run_timeout", "session_lifetime"):
            value = getattr(self, name)
            if type(value) not in (int, float) or not 0 < value <= 3600:
                raise ValueError("Invalid agent timeout")


def encode(value, limit):
    try:
        payload = json.dumps(value, ensure_ascii=True, allow_nan=False, separators=(",", ":")).encode()
    except (TypeError, ValueError, RecursionError) as exc:
        raise AgentRejected("invalid_json") from exc
    if len(payload) > limit:
        raise AgentRejected("response_too_large")
    return payload


def decode(payload: bytes, limit: int):
    from app.security.validation import parse_document
    try:
        return parse_document(payload, limit=limit, label="agent", duplicate="Duplicate agent field")
    except ValueError as exc:
        raise AgentRejected("invalid_json") from exc


def tool_schema(selected_ref: str | None):
    if selected_ref is None:
        name, description, schema = ("resolve_drug_product", "Find candidates; a human must confirm the exact product.",
                                     QueryArguments.model_json_schema())
    else:
        name, description, schema = ("search_historical_recalls", "Retrieve historical records for the human-confirmed product only.",
                                     RecallArguments.model_json_schema())
        schema["properties"]["product_ref"]["enum"] = [selected_ref]
    return [{"type": "function", "function": {"name": name, "description": description, "parameters": schema}}]
