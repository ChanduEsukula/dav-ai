import logging
import time
from datetime import datetime, timezone
from typing import Any

import httpx

from app.sources.registry import USDA_FSIS_RECALL

logger = logging.getLogger("medtrek.usda.fsis")


class USDAFSISRecallClient:
    def __init__(self, timeout_seconds: float = 15.0):
        self.timeout_seconds = timeout_seconds
        self.source = USDA_FSIS_RECALL

    async def search_recalls(
        self,
        query: str,
        limit: int = 10,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        endpoint = self.source["endpoint"]

        params = {
            "search": query,
            "limit": min(limit, 25),
        }

        start_time = time.perf_counter()

        logger.info(
            "usda_fsis_request_started",
            extra={
                "event": "usda_fsis_request_started",
                "request_id": request_id,
                "product_module": "FoodRadar",
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
                    "usda_fsis_request_completed",
                    extra={
                        "event": "usda_fsis_request_completed",
                        "request_id": request_id,
                        "product_module": "FoodRadar",
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
                    "raw": {"results": []},
                }

            response.raise_for_status()
            raw_payload = response.json()
            records = _extract_fsis_records(raw_payload)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            logger.info(
                "usda_fsis_request_completed",
                extra={
                    "event": "usda_fsis_request_completed",
                    "request_id": request_id,
                    "product_module": "FoodRadar",
                    "source_id": self.source["source_id"],
                    "endpoint": endpoint,
                    "query": query,
                    "upstream_status": "success" if records else "empty",
                    "http_status_code": response.status_code,
                    "record_count": len(records),
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
                "records": records[: params["limit"]],
            }

        except Exception:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            logger.exception(
                "usda_fsis_request_failed",
                extra={
                    "event": "usda_fsis_request_failed",
                    "request_id": request_id,
                    "product_module": "FoodRadar",
                    "source_id": self.source["source_id"],
                    "endpoint": endpoint,
                    "query": query,
                    "duration_ms": duration_ms,
                    "error_category": "usda_fsis_request_error",
                },
            )
            raise


def _extract_fsis_records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [record for record in payload if isinstance(record, dict)]

    if not isinstance(payload, dict):
        return []

    for key in ("results", "data", "items", "recalls", "rows"):
        value = payload.get(key)
        if isinstance(value, list):
            return [record for record in value if isinstance(record, dict)]

    if isinstance(payload.get("result"), list):
        return [record for record in payload["result"] if isinstance(record, dict)]

    return []
