from __future__ import annotations

import asyncio
import logging
import re
from html.parser import HTMLParser
from typing import Any

import httpx

from app.services.safety_source_adapters.base import (
    NormalizedSafetyRecord,
    SafetySourceAdapterError,
    SourceAdapterResult,
    compact_text,
    dedupe_records,
    first_text,
    record_matches_query,
    stable_payload_hash,
    text_matches_query,
    utc_now_iso,
)
from app.sources.registry import FDA_RECALLS_MARKET_WITHDRAWALS_SAFETY_ALERTS

logger = logging.getLogger("medtrek.real_world_safety.fda_public")


class FDAPublicRecallsAdapter:
    def __init__(self, timeout_seconds: float = 5.0):
        self.timeout_seconds = timeout_seconds
        self.source = FDA_RECALLS_MARKET_WITHDRAWALS_SAFETY_ALERTS

    async def search(
        self,
        *,
        query: str,
        limit: int,
        request_id: str | None = None,
    ) -> SourceAdapterResult:
        endpoint = self.source["endpoint"]
        retrieved_at = utc_now_iso()

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(endpoint)

            response.raise_for_status()
            html = response.text
            rows = parse_fda_recalls_table(html)
            records: list[NormalizedSafetyRecord] = []
            normalized_rows = [
                _normalize_fda_public_row(
                    row=row,
                    index=index,
                    retrieved_at=retrieved_at,
                    source_name=self.source["source_name"],
                    source_url=endpoint,
                )
                for index, row in enumerate(rows)
            ]

            detail_semaphore = asyncio.Semaphore(8)

            async def fetch_notice_text(record: NormalizedSafetyRecord) -> str | None:
                if not record.record_url:
                    return None
                try:
                    async with detail_semaphore:
                        async with httpx.AsyncClient(timeout=self.timeout_seconds) as detail_client:
                            detail_response = await detail_client.get(record.record_url)
                    detail_response.raise_for_status()
                    return parse_visible_text(detail_response.text)
                except Exception:
                    logger.info(
                        "fda_public_notice_detail_normalization_skipped",
                        extra={
                            "event": "fda_public_notice_detail_normalization_skipped",
                            "request_id": request_id,
                            "source_id": self.source["source_id"],
                            "record_url": record.record_url,
                        },
                    )
                    return None

            detail_texts = await asyncio.gather(
                *(fetch_notice_text(record) for record in normalized_rows)
            )

            for row, normalized, notice_text in zip(
                rows,
                normalized_rows,
                detail_texts,
                strict=True,
            ):
                row_matches = record_matches_query(normalized, query)
                detail_matches = bool(
                    notice_text and text_matches_query(notice_text, query)
                )
                if not row_matches and not detail_matches:
                    continue

                normalized = _normalize_fda_public_row(
                    row=row,
                    index=len(records),
                    retrieved_at=retrieved_at,
                    source_name=self.source["source_name"],
                    source_url=endpoint,
                )

                enriched_record = None
                if notice_text:
                    enriched_record = _normalize_notice_from_text(
                        base_record=normalized,
                        notice_text=notice_text,
                        query=query,
                        retrieved_at=retrieved_at,
                        source_name=self.source["source_name"],
                        source_url=endpoint,
                        raw_payload={
                            "row": row,
                            "notice_text": notice_text[:5000],
                            "record_url": normalized.record_url,
                        },
                    )

                records.append(enriched_record or normalized)

            records = dedupe_records(records)[:limit]
            return SourceAdapterResult(
                source_id=self.source["source_id"],
                source_name=self.source["source_name"],
                source_type="public notice page",
                source_url=endpoint,
                source_kind="public_notice",
                retrieved_at=retrieved_at,
                records=records,
                raw_payload={"rows": rows},
                upstream_status="success" if records else "empty",
            )

        except httpx.TimeoutException as exc:
            error_message = f"Timed out after {self.timeout_seconds} seconds contacting FDA public recalls page."
            logger.warning(
                "fda_public_recalls_request_timed_out",
                extra={
                    "event": "fda_public_recalls_request_timed_out",
                    "request_id": request_id,
                    "source_id": self.source["source_id"],
                    "query": query,
                    "timeout_seconds": self.timeout_seconds,
                },
            )
            raise SafetySourceAdapterError(error_message, error_type="timeout") from exc
        except httpx.HTTPStatusError as exc:
            error_message = f"FDA public recalls page returned HTTP {exc.response.status_code}."
            logger.warning(
                "fda_public_recalls_request_http_error",
                extra={
                    "event": "fda_public_recalls_request_http_error",
                    "request_id": request_id,
                    "source_id": self.source["source_id"],
                    "query": query,
                    "status_code": exc.response.status_code,
                },
            )
            raise SafetySourceAdapterError(error_message, error_type="http_status") from exc
        except httpx.RequestError as exc:
            error_message = f"FDA public recalls page request failed: {exc}"
            logger.warning(
                "fda_public_recalls_request_network_error",
                extra={
                    "event": "fda_public_recalls_request_network_error",
                    "request_id": request_id,
                    "source_id": self.source["source_id"],
                    "query": query,
                },
            )
            raise SafetySourceAdapterError(error_message, error_type="network_error") from exc
        except Exception as exc:
            logger.exception(
                "fda_public_recalls_request_failed",
                extra={
                    "event": "fda_public_recalls_request_failed",
                    "request_id": request_id,
                    "source_id": self.source["source_id"],
                    "query": query,
                },
            )
            raise SafetySourceAdapterError(str(exc), error_type="adapter_error") from exc


class _FDARecallTableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_row = False
        self.in_cell = False
        self.current_cell: list[str] = []
        self.current_row: list[str] = []
        self.current_link: str | None = None
        self.row_link: str | None = None
        self.rows: list[dict[str, Any]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self.in_row = True
            self.current_row = []
            self.row_link = None
        elif self.in_row and tag in {"td", "th"}:
            self.in_cell = True
            self.current_cell = []
            self.current_link = None
        elif self.in_cell and tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.current_link = href
                if not self.row_link:
                    self.row_link = href

    def handle_data(self, data: str) -> None:
        if self.in_cell:
            self.current_cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self.in_cell:
            text = compact_text(" ".join(self.current_cell))
            if text:
                self.current_row.append(text)
            self.in_cell = False
            self.current_cell = []
            self.current_link = None
        elif tag == "tr" and self.in_row:
            if len(self.current_row) >= 5 and self.current_row[0].lower() != "date":
                self.rows.append(
                    {
                        "cells": self.current_row,
                        "url": self.row_link,
                    }
                )
            self.in_row = False
            self.current_row = []
            self.row_link = None


class _VisibleTextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self.skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self.skip_depth > 0:
            self.skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.skip_depth == 0:
            text = compact_text(data)
            if text:
                self.parts.append(text)


def parse_visible_text(html: str) -> str:
    parser = _VisibleTextParser()
    parser.feed(html)
    text = compact_text(" ".join(parser.parts))
    junk_patterns = [
        r"Skip to main content.*?",
        r"Share.*?",
        r"Subscribe.*?",
    ]
    for pattern in junk_patterns:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)
    return compact_text(text)


def _sentences(text: str) -> list[str]:
    return [
        compact_text(sentence)
        for sentence in re.split(r"(?<=[.!?])\s+", text)
        if compact_text(sentence)
    ]


def _first_sentence_matching(text: str, keywords: tuple[str, ...]) -> str | None:
    for sentence in _sentences(text):
        lower = sentence.lower()
        if any(keyword in lower for keyword in keywords):
            return sentence
    return None


def _source_excerpt(text: str, query: str, fallback: str | None = None) -> str | None:
    sentences = _sentences(text)
    query_tokens = [token for token in re.findall(r"[a-z0-9]+", query.lower()) if len(token) >= 3]

    for sentence in sentences:
        lower = sentence.lower()
        if any(token in lower for token in query_tokens):
            return sentence[:360]

    if fallback:
        return fallback[:360]
    if sentences:
        return sentences[0][:360]
    return None



def _clean_notice_candidate(value: str | None) -> str | None:
    text = compact_text(value)
    if not text:
        return None

    noisy_terms = (
        "search menu search fda",
        "skip to fda search",
        "skip to main content",
        "featured report a product problem",
        "contact fda",
        "documents recalls, market withdrawals",
        "in this section",
        "an official website",
        "here's how you know",
    )
    lower = text.lower()
    if any(term in lower for term in noisy_terms):
        return None

    if len(text) > 420:
        text = text[:420].rsplit(" ", 1)[0] + "..."

    return text

def _normalize_notice_from_text(
    *,
    base_record: NormalizedSafetyRecord,
    notice_text: str,
    query: str,
    retrieved_at: str,
    source_name: str,
    source_url: str,
    raw_payload: dict[str, Any],
) -> NormalizedSafetyRecord | None:
    if len(notice_text) < 80:
        return None

    detail_reason = _first_sentence_matching(
        notice_text,
        (
            "recall",
            "recalled",
            "because",
            "due to",
            "undeclared",
            "contaminated",
            "contamination",
            "allergen",
            "risk",
            "injury",
            "hazard",
        ),
    )
    reason = _clean_notice_candidate(
        first_text(detail_reason, base_record.reason)
    )

    remedy = _clean_notice_candidate(
        first_text(
            base_record.remedy,
            _first_sentence_matching(
                notice_text,
                (
                    "consumers should",
                    "customers should",
                    "patients should",
                    "stop using",
                    "return",
                    "discard",
                    "refund",
                ),
            ),
        )
    )

    excerpt = _clean_notice_candidate(_source_excerpt(notice_text, query, reason))
    confidence_score = sum(
        1
        for value in (
            base_record.product_name,
            base_record.company_name,
            reason,
            excerpt,
            base_record.published_date,
        )
        if value
    )
    confidence = "high" if confidence_score >= 4 else "medium" if confidence_score >= 3 else "low"

    return NormalizedSafetyRecord(
        source_name=source_name,
        source_type="normalized official public notice",
        source_url=source_url,
        source_kind="normalized_public_notice",
        category=base_record.category,
        product_name=base_record.product_name,
        brand_name=base_record.brand_name,
        company_name=base_record.company_name,
        title=base_record.title,
        reason=reason,
        hazard_type=first_text(base_record.hazard_type, reason),
        remedy=remedy,
        published_date=base_record.published_date,
        recall_number=base_record.recall_number,
        affected_models=base_record.affected_models,
        affected_lots=base_record.affected_lots,
        raw_payload_hash=stable_payload_hash(raw_payload),
        retrieved_at=retrieved_at,
        record_url=base_record.record_url,
        extraction_confidence=confidence,
        source_text_excerpt=excerpt,
    )


def parse_fda_recalls_table(html: str) -> list[dict[str, Any]]:
    parser = _FDARecallTableParser()
    parser.feed(html)
    return parser.rows


def _absolute_fda_url(url: str | None) -> str | None:
    if not url:
        return None
    if url.startswith("http://") or url.startswith("https://"):
        return url
    if url.startswith("/"):
        return f"https://www.fda.gov{url}"
    return f"https://www.fda.gov/{url}"


def _normalize_fda_public_row(
    *,
    row: dict[str, Any],
    index: int,
    retrieved_at: str,
    source_name: str,
    source_url: str,
) -> NormalizedSafetyRecord:
    cells = row.get("cells") or []
    padded = [*cells, *([None] * max(0, 7 - len(cells)))]
    published_date, brand, product, product_type, reason, company, terminated = padded[:7]
    title_parts = [brand, product]
    title = " - ".join(compact_text(part) for part in title_parts if compact_text(part))

    return NormalizedSafetyRecord(
        source_name=source_name,
        source_type="public notice page",
        source_url=source_url,
        source_kind="public_notice",
        category=first_text(product_type),
        product_name=first_text(product),
        brand_name=first_text(brand),
        company_name=first_text(company),
        title=first_text(title, product, brand, f"FDA public recall notice {index + 1}"),
        reason=first_text(reason),
        hazard_type=first_text(product_type, reason),
        remedy=None,
        published_date=first_text(published_date),
        recall_number=None,
        affected_models=[],
        affected_lots=[],
        raw_payload_hash=stable_payload_hash(row),
        retrieved_at=retrieved_at,
        record_url=_absolute_fda_url(row.get("url")),
    )
