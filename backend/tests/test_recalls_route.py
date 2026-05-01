from fastapi.testclient import TestClient

from app.main import app
from app.routes import recalls


class MockOpenFDAClientSuccess:
    async def search_drug_recalls(self, query: str, limit: int = 10):
        return {
            "source_name": "openFDA Drug Enforcement API",
            "endpoint": "https://api.fda.gov/drug/enforcement.json",
            "query": query,
            "retrieval_timestamp": "2026-05-01T10:30:00+00:00",
            "raw": {
                "results": [
                    {
                        "recall_number": "D-1234-2026",
                        "product_description": "Example eye drops",
                        "reason_for_recall": "Example recall reason",
                        "classification": "Class II",
                        "status": "Ongoing",
                        "recall_initiation_date": "20260401",
                        "distribution_pattern": "Nationwide",
                        "recalling_firm": "Example Pharma",
                    }
                ]
            },
        }


class MockOpenFDAClientEmpty:
    async def search_drug_recalls(self, query: str, limit: int = 10):
        return {
            "source_name": "openFDA Drug Enforcement API",
            "endpoint": "https://api.fda.gov/drug/enforcement.json",
            "query": query,
            "retrieval_timestamp": "2026-05-01T10:30:00+00:00",
            "raw": {
                "meta": {},
                "results": [],
            },
        }


class MockOpenFDAClientFailure:
    async def search_drug_recalls(self, query: str, limit: int = 10):
        raise RuntimeError("openFDA unavailable")


def test_search_recalls_returns_normalized_results():
    recalls.client = MockOpenFDAClientSuccess()

    test_client = TestClient(app)
    response = test_client.get("/api/v1/recalls/search", params={"q": "eye drops", "limit": 5})

    assert response.status_code == 200

    body = response.json()
    assert body["query"] == "eye drops"
    assert body["count"] == 1
    assert body["source_name"] == "openFDA Drug Enforcement API"
    assert body["endpoint"] == "https://api.fda.gov/drug/enforcement.json"
    assert body["score_version"] == "recall-risk-v0.1"
    assert body["medical_disclaimer"]

    result = body["results"][0]
    assert result["recall_number"] == "D-1234-2026"
    assert result["product_description"] == "Example eye drops"
    assert result["classification"] == "Class II"
    assert result["status"] == "Ongoing"
    assert "risk_score" in result
    assert result["source"]["name"] == "openFDA Drug Enforcement API"


def test_search_recalls_returns_empty_results_for_no_matches():
    recalls.client = MockOpenFDAClientEmpty()

    test_client = TestClient(app)
    response = test_client.get(
        "/api/v1/recalls/search",
        params={"q": "randomfakeproduct123", "limit": 5},
    )

    assert response.status_code == 200

    body = response.json()
    assert body["query"] == "randomfakeproduct123"
    assert body["count"] == 0
    assert body["results"] == []
    assert body["source_name"] == "openFDA Drug Enforcement API"
    assert body["endpoint"] == "https://api.fda.gov/drug/enforcement.json"
    assert body["score_version"] == "recall-risk-v0.1"
    assert body["medical_disclaimer"]


def test_search_recalls_returns_502_for_upstream_failure():
    recalls.client = MockOpenFDAClientFailure()

    test_client = TestClient(app)
    response = test_client.get("/api/v1/recalls/search", params={"q": "eye drops", "limit": 5})

    assert response.status_code == 502

    body = response.json()
    assert body["detail"]["message"] == "Unable to retrieve recall data from openFDA."
    assert "openFDA unavailable" in body["detail"]["error"]


def test_search_recalls_rejects_short_query():
    test_client = TestClient(app)

    response = test_client.get("/api/v1/recalls/search", params={"q": "a", "limit": 5})

    assert response.status_code == 422


def test_search_recalls_rejects_limit_below_minimum():
    test_client = TestClient(app)

    response = test_client.get("/api/v1/recalls/search", params={"q": "eye drops", "limit": 0})

    assert response.status_code == 422


def test_search_recalls_rejects_limit_above_maximum():
    test_client = TestClient(app)

    response = test_client.get("/api/v1/recalls/search", params={"q": "eye drops", "limit": 26})

    assert response.status_code == 422