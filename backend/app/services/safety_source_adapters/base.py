from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal


SourceKind = Literal["structured_api", "public_notice", "normalized_public_notice"]


class SafetySourceAdapterError(RuntimeError):
    """Raised when an upstream public safety source cannot be retrieved."""

    def __init__(self, message: str, *, error_type: str = "source_error"):
        super().__init__(message)
        self.error_type = error_type


@dataclass(slots=True)
class NormalizedSafetyRecord:
    source_name: str
    source_type: str
    source_url: str
    source_kind: SourceKind
    category: str | None
    product_name: str | None
    brand_name: str | None
    company_name: str | None
    title: str | None
    reason: str | None
    hazard_type: str | None
    remedy: str | None
    published_date: str | None
    recall_number: str | None
    affected_models: list[str] = field(default_factory=list)
    affected_lots: list[str] = field(default_factory=list)
    raw_payload_hash: str = ""
    retrieved_at: str = ""
    record_url: str | None = None
    extraction_confidence: str | None = None
    source_text_excerpt: str | None = None

    def as_response_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SourceAdapterResult:
    source_id: str
    source_name: str
    source_type: str
    source_url: str
    source_kind: SourceKind
    retrieved_at: str
    records: list[NormalizedSafetyRecord]
    raw_payload: dict[str, Any]
    upstream_status: Literal["success", "empty", "error"] = "empty"
    error_message: str | None = None
    context: dict[str, Any] = field(default_factory=dict)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_payload_hash(payload: Any) -> str:
    serialized_payload = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(serialized_payload.encode("utf-8")).hexdigest()


def compact_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def first_text(*values: Any) -> str | None:
    for value in values:
        text = compact_text(value)
        if text:
            return text
    return None


def list_text(values: Any, *keys: str) -> list[str]:
    if not isinstance(values, list):
        return []

    results: list[str] = []
    for item in values:
        if isinstance(item, str):
            text = compact_text(item)
        elif isinstance(item, dict):
            text = first_text(*(item.get(key) for key in keys))
        else:
            text = compact_text(item)

        if text and text not in results:
            results.append(text)

    return results


def query_tokens(query: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-z0-9]+", query.lower())
        if len(token) >= 2
    ]


def text_matches_query(text: str, query: str) -> bool:
    tokens = query_tokens(query)
    if not tokens:
        return False

    normalized_text = text.lower()

    def token_matches(token: str) -> bool:
        if token in normalized_text:
            return True
        if token.endswith("s") and token[:-1] in normalized_text:
            return True
        return f"{token}s" in normalized_text

    return all(token_matches(token) for token in tokens)


def record_matches_query(record: NormalizedSafetyRecord, query: str) -> bool:
    searchable = " ".join(
        compact_text(value)
        for value in (
            record.product_name,
            record.brand_name,
            record.company_name,
            record.title,
            record.reason,
            record.hazard_type,
            record.remedy,
            record.recall_number,
            " ".join(record.affected_models),
            " ".join(record.affected_lots),
        )
        if value
    )
    return text_matches_query(searchable, query)


def match_score(record: NormalizedSafetyRecord, query: str) -> int:
    normalized_query = " ".join(query_tokens(query))
    fields = {
        "product_name": record.product_name,
        "brand_name": record.brand_name,
        "company_name": record.company_name,
        "title": record.title,
        "reason": record.reason,
        "hazard_type": record.hazard_type,
        "affected_models": " ".join(record.affected_models),
        "affected_lots": " ".join(record.affected_lots),
    }

    score = 0
    for field_name, value in fields.items():
        text = " ".join(query_tokens(compact_text(value)))
        if not text:
            continue
        if normalized_query and normalized_query in text:
            score += 60
        elif text_matches_query(text, query):
            score += 30
        if field_name in {"product_name", "brand_name", "title", "affected_models"}:
            score += 5

    return score


def date_sort_value(value: str | None) -> int:
    if not value:
        return 0
    digits = "".join(character for character in str(value) if character.isdigit())
    if len(digits) >= 8:
        return int(digits[:8])
    return 0


def dedupe_records(records: list[NormalizedSafetyRecord]) -> list[NormalizedSafetyRecord]:
    seen: set[tuple[str, str | None, str | None, str | None]] = set()
    deduped: list[NormalizedSafetyRecord] = []

    for record in records:
        key = (
            record.source_name,
            record.recall_number,
            record.title,
            record.product_name,
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(record)

    return deduped
