from datetime import datetime, timezone
from typing import Any

import httpx

from app.sources.registry import OPENFDA_DRUG_ENFORCEMENT


class OpenFDAClient:
    def __init__(self, timeout_seconds: float = 15.0):
        self.timeout_seconds = timeout_seconds
        self.source = OPENFDA_DRUG_ENFORCEMENT

    async def search_drug_recalls(self, query: str, limit: int = 10) -> dict[str, Any]:
        endpoint = self.source["endpoint"]

        params = {
            "search": f'product_description:"{query}"',
            "limit": min(limit, 25),
        }

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(endpoint, params=params)

        retrieval_timestamp = datetime.now(timezone.utc).isoformat()

        if response.status_code == 404:
            return {
                "source_id": self.source["source_id"],
                "source_name": self.source["source_name"],
                "endpoint": endpoint,
                "query": query,
                "retrieval_timestamp": retrieval_timestamp,
                "raw": {
                    "meta": {},
                    "results": [],
                },
            }

        response.raise_for_status()

        return {
            "source_id": self.source["source_id"],
            "source_name": self.source["source_name"],
            "endpoint": endpoint,
            "query": query,
            "retrieval_timestamp": retrieval_timestamp,
            "raw": response.json(),
        }