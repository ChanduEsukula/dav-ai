from datetime import datetime, timezone
from typing import Any

import httpx

OPENFDA_DRUG_ENFORCEMENT_URL = "https://api.fda.gov/drug/enforcement.json"


class OpenFDAClient:
    def __init__(self, timeout_seconds: float = 15.0):
        self.timeout_seconds = timeout_seconds

    async def search_drug_recalls(self, query: str, limit: int = 10) -> dict[str, Any]:
        params = {
            "search": f'product_description:"{query}"',
            "limit": min(limit, 25),
        }

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(OPENFDA_DRUG_ENFORCEMENT_URL, params=params)

        retrieval_timestamp = datetime.now(timezone.utc).isoformat()

        if response.status_code == 404:
            return {
                "source_name": "openFDA Drug Enforcement API",
                "endpoint": OPENFDA_DRUG_ENFORCEMENT_URL,
                "query": query,
                "retrieval_timestamp": retrieval_timestamp,
                "raw": {
                    "meta": {},
                    "results": [],
                },
            }

        response.raise_for_status()

        return {
            "source_name": "openFDA Drug Enforcement API",
            "endpoint": OPENFDA_DRUG_ENFORCEMENT_URL,
            "query": query,
            "retrieval_timestamp": retrieval_timestamp,
            "raw": response.json(),
        }