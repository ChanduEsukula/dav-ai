import httpx
import pytest

from app.services.openfda_drug_event_client import OpenFDADrugEventClient
from app.sources.registry import OPENFDA_DRUG_EVENT


@pytest.mark.anyio
async def test_openfda_drug_event_client_returns_results_for_success_response(monkeypatch):
    async def mock_get(self, url, params=None):
        assert url == OPENFDA_DRUG_EVENT["endpoint"]
        assert params["search"] == 'patient.drug.medicinalproduct:"metformin"'
        assert params["limit"] == 5

        return httpx.Response(
            status_code=200,
            json={
                "results": [
                    {
                        "patient": {
                            "reaction": [
                                {"reactionmeddrapt": "Nausea"},
                                {"reactionmeddrapt": "Headache"},
                            ]
                        }
                    }
                ]
            },
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    client = OpenFDADrugEventClient()
    payload = await client.search_drug_events(query="metformin", limit=5)

    assert payload["source_id"] == OPENFDA_DRUG_EVENT["source_id"]
    assert payload["source_name"] == OPENFDA_DRUG_EVENT["source_name"]
    assert payload["endpoint"] == OPENFDA_DRUG_EVENT["endpoint"]
    assert payload["query"] == "metformin"
    assert len(payload["raw"]["results"]) == 1
    assert payload["retrieval_timestamp"]


@pytest.mark.anyio
async def test_openfda_drug_event_client_returns_empty_results_for_404(monkeypatch):
    async def mock_get(self, url, params=None):
        return httpx.Response(
            status_code=404,
            json={"error": {"code": "NOT_FOUND", "message": "No matches found"}},
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    client = OpenFDADrugEventClient()
    payload = await client.search_drug_events(query="randomfakeproduct123", limit=5)

    assert payload["source_id"] == OPENFDA_DRUG_EVENT["source_id"]
    assert payload["source_name"] == OPENFDA_DRUG_EVENT["source_name"]
    assert payload["endpoint"] == OPENFDA_DRUG_EVENT["endpoint"]
    assert payload["query"] == "randomfakeproduct123"
    assert payload["raw"]["results"] == []


@pytest.mark.anyio
async def test_openfda_drug_event_client_raises_for_upstream_server_error(monkeypatch):
    async def mock_get(self, url, params=None):
        return httpx.Response(
            status_code=500,
            json={"error": "server error"},
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    client = OpenFDADrugEventClient()

    with pytest.raises(httpx.HTTPStatusError):
        await client.search_drug_events(query="metformin", limit=5)