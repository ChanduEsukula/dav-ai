from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.services.search_workflows import everyday_safety_search


client = TestClient(app)


def _fake_source_pull(*, audit_event, raw_payload, request_id=None):
    return {
        "status": "stored",
        "pull_id": "test-source-pull-id",
        "payload_hash": "test-payload-hash",
    }


def _fake_save_audit_event(audit_event, request_id=None):
    return audit_event


def test_everyday_safety_food_search_returns_normalized_records(monkeypatch):
    async def fake_search_food_recalls(query, limit, request_id=None):
        return {
            "source_id": "openfda_food_enforcement",
            "source_name": "openFDA Food Enforcement API",
            "endpoint": "https://api.fda.gov/food/enforcement.json",
            "query": query,
            "retrieval_timestamp": datetime.now(timezone.utc).isoformat(),
            "raw": {
                "results": [
                    {
                        "recall_number": "F-1234-2026",
                        "product_description": "Example protein powder",
                        "reason_for_recall": "Potential undeclared allergen",
                        "classification": "Class II",
                        "status": "Ongoing",
                        "recall_initiation_date": "20260601",
                        "report_date": "20260603",
                        "distribution_pattern": "Nationwide",
                        "recalling_firm": "Example Nutrition Inc.",
                        "product_quantity": "1 lb containers",
                        "code_info": "Lot ABC123",
                    }
                ]
            },
        }

    monkeypatch.setattr(
        everyday_safety_search.food_client,
        "search_food_recalls",
        fake_search_food_recalls,
    )
    monkeypatch.setattr(everyday_safety_search, "save_audit_event", _fake_save_audit_event)
    monkeypatch.setattr(
        everyday_safety_search,
        "save_source_pull_with_snapshot",
        _fake_source_pull,
    )

    response = client.get(
        "/api/v1/everyday-safety/search",
        params={"category": "food_supplement", "q": "protein powder", "limit": 5},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["query"] == "protein powder"
    assert body["category"] == "food_supplement"
    assert body["category_label"] == "Food & Supplements"
    assert body["count"] == 1
    assert body["source_name"] == "openFDA Food Enforcement API"
    assert body["audit"]["module"] == "FoodRadar"
    assert body["audit"]["record_count"] == 1
    assert "not medical advice" in body["public_data_disclaimer"].lower()
    assert body["limitations"]

    result = body["results"][0]
    assert result["recall_number"] == "F-1234-2026"
    assert result["product_description"] == "Example protein powder"
    assert result["code_info"] == "Lot ABC123"
    assert result["risk_score"]["score_version"] == "recall-risk-v0.1"


def test_everyday_safety_food_search_handles_empty_results(monkeypatch):
    async def fake_search_food_recalls(query, limit, request_id=None):
        return {
            "source_id": "openfda_food_enforcement",
            "source_name": "openFDA Food Enforcement API",
            "endpoint": "https://api.fda.gov/food/enforcement.json",
            "query": query,
            "retrieval_timestamp": datetime.now(timezone.utc).isoformat(),
            "raw": {"results": []},
        }

    monkeypatch.setattr(
        everyday_safety_search.food_client,
        "search_food_recalls",
        fake_search_food_recalls,
    )
    monkeypatch.setattr(everyday_safety_search, "save_audit_event", _fake_save_audit_event)
    monkeypatch.setattr(
        everyday_safety_search,
        "save_source_pull_with_snapshot",
        _fake_source_pull,
    )

    response = client.get(
        "/api/v1/everyday-safety/search",
        params={"category": "food_supplement", "q": "unlikely product", "limit": 5},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["count"] == 0
    assert body["audit"]["upstream_status"] == "empty"
    assert body["results"] == []


def test_everyday_safety_requires_minimum_query_length():
    response = client.get(
        "/api/v1/everyday-safety/search",
        params={"category": "food_supplement", "q": "a", "limit": 5},
    )

    assert response.status_code == 422


def test_everyday_safety_rejects_invalid_limit():
    response = client.get(
        "/api/v1/everyday-safety/search",
        params={"category": "food_supplement", "q": "protein powder", "limit": 50},
    )

    assert response.status_code == 422
