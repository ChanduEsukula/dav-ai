import httpx
import pytest

from app.services.openfda_client import OpenFDAClient
from app.sources.registry import OPENFDA_DRUG_ENFORCEMENT


@pytest.mark.anyio
async def test_openfda_client_returns_results_for_success_response(monkeypatch):
    async def mock_get(self, url, params=None):
        assert url == OPENFDA_DRUG_ENFORCEMENT["endpoint"]
        assert params["search"] == 'product_description:"eye drops"'
        assert params["limit"] == 5

        return httpx.Response(
            status_code=200,
            json={
                "results": [
                    {
                        "recall_number": "D-1234-2026",
                        "product_description": "Example eye drops",
                    }
                ]
            },
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    client = OpenFDAClient()
    payload = await client.search_drug_recalls(query="eye drops", limit=5)

    assert payload["source_id"] == OPENFDA_DRUG_ENFORCEMENT["source_id"]
    assert payload["source_name"] == OPENFDA_DRUG_ENFORCEMENT["source_name"]
    assert payload["endpoint"] == OPENFDA_DRUG_ENFORCEMENT["endpoint"]
    assert payload["query"] == "eye drops"
    assert payload["raw"]["results"][0]["recall_number"] == "D-1234-2026"
    assert payload["retrieval_timestamp"]


@pytest.mark.anyio
async def test_openfda_client_returns_empty_results_for_404(monkeypatch):
    async def mock_get(self, url, params=None):
        return httpx.Response(
            status_code=404,
            json={"error": {"code": "NOT_FOUND", "message": "No matches found"}},
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    client = OpenFDAClient()
    payload = await client.search_drug_recalls(query="randomfakeproduct123", limit=5)

    assert payload["source_id"] == OPENFDA_DRUG_ENFORCEMENT["source_id"]
    assert payload["source_name"] == OPENFDA_DRUG_ENFORCEMENT["source_name"]
    assert payload["endpoint"] == OPENFDA_DRUG_ENFORCEMENT["endpoint"]
    assert payload["query"] == "randomfakeproduct123"
    assert payload["raw"]["results"] == []


@pytest.mark.anyio
async def test_openfda_client_raises_for_upstream_server_error(monkeypatch):
    async def mock_get(self, url, params=None):
        return httpx.Response(
            status_code=500,
            json={"error": "server error"},
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    client = OpenFDAClient()

    with pytest.raises(httpx.HTTPStatusError):
        await client.search_drug_recalls(query="eye drops", limit=5)