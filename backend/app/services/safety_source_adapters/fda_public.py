from __future__ import annotations

import logging
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

            for index, row in enumerate(rows):
                normalized = _normalize_fda_public_row(
                    row=row,
                    index=index,
                    retrieved_at=retrieved_at,
                    source_name=self.source["source_name"],
                    source_url=endpoint,
                )
                if record_matches_query(normalized, query):
                    records.append(normalized)

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
