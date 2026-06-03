import logging
import time
from datetime import datetime, timezone
from typing import Any

import httpx

from app.sources.registry import OPENFDA_COSMETIC_EVENT

logger = logging.getLogger("medtrek.openfda.cosmetic")


class OpenFDACosmeticEventClient:
    def __init__(self, timeout_seconds: float = 15.0):
        self.timeout_seconds = timeout_seconds
        self.source = OPENFDA_COSMETIC_EVENT

    async def search_cosmetic_events(
        self,
        query: str,
        limit: int = 10,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        endpoint = self.source["endpoint"]

        params = {
            "search": (
                f'products.brand_name:"{query}" '
                f'OR products.name_brand:"{query}" '
                f'OR products.industry_code:"{query}" '
                f'OR reactions:"{query}" '
                f'OR outcomes:"{query}"'
            ),
            "limit": min(limit, 25),
        }

        start_time = time.perf_counter()

        logger.info(
            "openfda_cosmetic_request_started",
            extra={
                "event": "openfda_cosmetic_request_started",
                "request_id": request_id,
                "product_module": "CosmeticSignal",
                "source_id": self.source["source_id"],
                "endpoint": endpoint,
                "query": query,
                "limit": params["limit"],
            },
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(endpoint, params=params)

            retrieval_timestamp = datetime.now(timezone.utc).isoformat()

            if response.status_code == 404:
                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

                logger.info(
                    "openfda_cosmetic_request_completed",
                    extra={
                        "event": "openfda_cosmetic_request_completed",
                        "request_id": request_id,
                        "product_module": "CosmeticSignal",
                        "source_id": self.source["source_id"],
                        "endpoint": endpoint,
                        "query": query,
                        "upstream_status": "empty",
                        "http_status_code": response.status_code,
                        "record_count": 0,
                        "duration_ms": duration_ms,
                    },
                )

                return {
                    "source_id": self.source["source_id"],
                    "source_name": self.source["source_name"],
                    "endpoint": endpoint,
                    "query": query,
                    "retrieval_timestamp": retrieval_timestamp,
                    "raw": {"meta": {}, "results": []},
                }

            response.raise_for_status()
            raw_payload = response.json()
            record_count = len(raw_payload.get("results", []))
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            logger.info(
                "openfda_cosmetic_request_completed",
                extra={
                    "event": "openfda_cosmetic_request_completed",
                    "request_id": request_id,
                    "product_module": "CosmeticSignal",
                    "source_id": self.source["source_id"],
                    "endpoint": endpoint,
                    "query": query,
                    "upstream_status": "success" if record_count else "empty",
                    "http_status_code": response.status_code,
                    "record_count": record_count,
                    "duration_ms": duration_ms,
                },
            )

            return {
                "source_id": self.source["source_id"],
                "source_name": self.source["source_name"],
                "endpoint": endpoint,
                "query": query,
                "retrieval_timestamp": retrieval_timestamp,
                "raw": raw_payload,
            }

        except Exception:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            logger.exception(
                "openfda_cosmetic_request_failed",
                extra={
                    "event": "openfda_cosmetic_request_failed",
                    "request_id": request_id,
                    "product_module": "CosmeticSignal",
                    "source_id": self.source["source_id"],
                    "endpoint": endpoint,
                    "query": query,
                    "duration_ms": duration_ms,
                    "error_category": "openfda_cosmetic_request_error",
                },
            )
            raise
