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


def _patch_persistence(monkeypatch):
    monkeypatch.setattr(everyday_safety_search, "save_audit_event", _fake_save_audit_event)
    monkeypatch.setattr(
        everyday_safety_search,
        "save_source_pull_with_snapshot",
        _fake_source_pull,
    )


def test_everyday_safety_food_search_returns_multi_source_normalized_records(monkeypatch):
    now = datetime.now(timezone.utc).isoformat()

    async def fake_search_food_recalls(query, limit, request_id=None):
        return {
            "source_id": "openfda_food_enforcement",
            "source_name": "openFDA Food Enforcement API",
            "endpoint": "https://api.fda.gov/food/enforcement.json",
            "query": query,
            "retrieval_timestamp": now,
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

    async def fake_search_fsis_recalls(query, limit, request_id=None):
        return {
            "source_id": "usda_fsis_recall",
            "source_name": "USDA FSIS Recall API",
            "endpoint": "https://www.fsis.usda.gov/fsis/api/recall/v/1",
            "query": query,
            "retrieval_timestamp": now,
            "raw": {"results": []},
            "records": [
                {
                    "id": "fsis-1",
                    "field_recall_number": "024-2026",
                    "field_product_items": "Ready-to-eat chicken meal",
                    "field_recall_reason": "Possible foreign material contamination",
                    "field_recall_classification": "Class I",
                    "field_active_notice": "Active",
                    "field_recall_date": "20260602",
                    "field_publication_date": "20260603",
                    "field_states": "MN, WI",
                    "field_establishment": "Example Poultry LLC",
                    "field_pounds_recalled": "12,000 pounds",
                    "field_labels": "EST. 12345",
                }
            ],
        }

    monkeypatch.setattr(
        everyday_safety_search.food_client,
        "search_food_recalls",
        fake_search_food_recalls,
    )
    monkeypatch.setattr(
        everyday_safety_search.fsis_client,
        "search_recalls",
        fake_search_fsis_recalls,
    )
    _patch_persistence(monkeypatch)

    response = client.get(
        "/api/v1/everyday-safety/search",
        params={"category": "food_supplement", "q": "protein powder", "limit": 5},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["query"] == "protein powder"
    assert body["category"] == "food_supplement"
    assert body["category_label"] == "Food & Supplements"
    assert body["source_name"] == "FoodRadar multi-source search"
    assert body["search_strategy_used"] == "intent_supplement_v1"
    assert body["count"] == 2
    assert body["audit"]["module"] == "FoodRadar"
    assert body["audit"]["source_id"] == "foodradar_multi_source"
    assert body["audit"]["record_count"] == 2
    assert "not medical advice" in body["public_data_disclaimer"].lower()
    assert "USDA FSIS" in body["public_data_disclaimer"]
    assert body["limitations"]

    sources_checked = body["sources_checked"]
    assert len(sources_checked) == 2
    assert {source["source_type"] for source in sources_checked} == {
        "FDA_FOOD_ENFORCEMENT",
        "USDA_FSIS_RECALL",
    }

    fda_result = body["results"][0]
    assert fda_result["source_type"] == "FDA_FOOD_ENFORCEMENT"
    assert fda_result["recall_number"] == "F-1234-2026"
    assert fda_result["product_description"] == "Example protein powder"
    assert fda_result["search_strategy_used"] == "intent_supplement_v1"

    fsis_result = body["results"][1]
    assert fsis_result["source_type"] == "USDA_FSIS_RECALL"
    assert fsis_result["recall_number"] == "024-2026"
    assert fsis_result["product_description"] == "Ready-to-eat chicken meal"
    assert fsis_result["code_info"] == "EST. 12345"
    assert fsis_result["source"]["name"] == "USDA FSIS Recall API"
    assert fsis_result["risk_score"]["score_version"] == "recall-review-priority-v0.2"


def test_everyday_safety_food_search_handles_empty_multi_source_results(monkeypatch):
    now = datetime.now(timezone.utc).isoformat()

    async def fake_search_food_recalls(query, limit, request_id=None):
        return {
            "source_id": "openfda_food_enforcement",
            "source_name": "openFDA Food Enforcement API",
            "endpoint": "https://api.fda.gov/food/enforcement.json",
            "query": query,
            "retrieval_timestamp": now,
            "raw": {"results": []},
        }

    async def fake_search_fsis_recalls(query, limit, request_id=None):
        return {
            "source_id": "usda_fsis_recall",
            "source_name": "USDA FSIS Recall API",
            "endpoint": "https://www.fsis.usda.gov/fsis/api/recall/v/1",
            "query": query,
            "retrieval_timestamp": now,
            "raw": {"results": []},
            "records": [],
        }

    monkeypatch.setattr(
        everyday_safety_search.food_client,
        "search_food_recalls",
        fake_search_food_recalls,
    )
    monkeypatch.setattr(
        everyday_safety_search.fsis_client,
        "search_recalls",
        fake_search_fsis_recalls,
    )
    _patch_persistence(monkeypatch)

    response = client.get(
        "/api/v1/everyday-safety/search",
        params={"category": "food_supplement", "q": "unlikely product", "limit": 5},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["count"] == 0
    assert body["audit"]["upstream_status"] == "empty"
    assert body["results"] == []
    assert len(body["sources_checked"]) == 2
    assert all(source["upstream_status"] == "empty" for source in body["sources_checked"])


def test_everyday_safety_returns_partial_results_when_fsis_fails(monkeypatch):
    now = datetime.now(timezone.utc).isoformat()

    async def fake_search_food_recalls(query, limit, request_id=None):
        return {
            "source_id": "openfda_food_enforcement",
            "source_name": "openFDA Food Enforcement API",
            "endpoint": "https://api.fda.gov/food/enforcement.json",
            "query": query,
            "retrieval_timestamp": now,
            "raw": {
                "results": [
                    {
                        "recall_number": "F-9999-2026",
                        "product_description": "Example chocolate powder",
                        "reason_for_recall": "Potential Salmonella contamination",
                        "classification": "Class I",
                        "status": "Ongoing",
                        "recall_initiation_date": "20260601",
                        "report_date": "20260603",
                        "distribution_pattern": "Nationwide",
                        "recalling_firm": "Example Foods Inc.",
                        "product_quantity": "100 cases",
                        "code_info": "Lot XYZ789",
                    }
                ]
            },
        }

    async def fake_search_fsis_recalls(query, limit, request_id=None):
        raise RuntimeError("FSIS upstream unavailable during test")

    monkeypatch.setattr(
        everyday_safety_search.food_client,
        "search_food_recalls",
        fake_search_food_recalls,
    )
    monkeypatch.setattr(
        everyday_safety_search.fsis_client,
        "search_recalls",
        fake_search_fsis_recalls,
    )
    _patch_persistence(monkeypatch)

    response = client.get(
        "/api/v1/everyday-safety/search",
        params={"category": "food_supplement", "q": "chocolate", "limit": 5},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["count"] == 1
    assert body["audit"]["upstream_status"] == "success"
    assert body["results"][0]["source_type"] == "FDA_FOOD_ENFORCEMENT"

    fsis_source = next(
        source
        for source in body["sources_checked"]
        if source["source_type"] == "USDA_FSIS_RECALL"
    )
    assert fsis_source["upstream_status"] == "error"
    assert fsis_source["record_count"] == 0

    assert any("temporarily unavailable" in limitation for limitation in body["limitations"])


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


def test_everyday_safety_chicken_intent_excludes_chicken_of_the_sea_brand_noise(monkeypatch):
    now = datetime.now(timezone.utc).isoformat()

    async def fake_search_food_recalls(query, limit, request_id=None):
        return {
            "source_id": "openfda_food_enforcement",
            "source_name": "openFDA Food Enforcement API",
            "endpoint": "https://api.fda.gov/food/enforcement.json",
            "query": query,
            "retrieval_timestamp": now,
            "raw": {
                "results": [
                    {
                        "recall_number": "F-BRAND-2026",
                        "product_description": "Chicken of the Sea canned tuna",
                        "reason_for_recall": "Can lid issue",
                        "classification": "Class II",
                        "status": "Ongoing",
                        "recall_initiation_date": "20260601",
                        "report_date": "20260603",
                        "distribution_pattern": "Nationwide",
                        "recalling_firm": "Chicken of the Sea",
                        "product_quantity": "100 cases",
                        "code_info": "Lot BRAND",
                    }
                ]
            },
        }

    async def fake_search_fsis_recalls(query, limit, request_id=None):
        return {
            "source_id": "usda_fsis_recall",
            "source_name": "USDA FSIS Recall API",
            "endpoint": "https://www.fsis.usda.gov/fsis/api/recall/v/1",
            "query": query,
            "retrieval_timestamp": now,
            "raw": {"results": []},
            "records": [
                {
                    "id": "fsis-chicken-1",
                    "field_recall_number": "025-2026",
                    "field_product_items": "Ready-to-eat chicken breast meal",
                    "field_recall_reason": "Possible Listeria contamination",
                    "field_recall_classification": "Class I",
                    "field_active_notice": "Active",
                    "field_recall_date": "20260602",
                    "field_publication_date": "20260603",
                    "field_states": "MN, WI",
                    "field_establishment": "Example Poultry LLC",
                    "field_pounds_recalled": "8,000 pounds",
                    "field_labels": "EST. 67890",
                }
            ],
        }

    monkeypatch.setattr(
        everyday_safety_search.food_client,
        "search_food_recalls",
        fake_search_food_recalls,
    )
    monkeypatch.setattr(
        everyday_safety_search.fsis_client,
        "search_recalls",
        fake_search_fsis_recalls,
    )
    _patch_persistence(monkeypatch)

    response = client.get(
        "/api/v1/everyday-safety/search",
        params={"category": "food_supplement", "q": "chicken", "limit": 5},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["search_strategy_used"] == "intent_poultry_meat_v1"
    assert body["count"] == 1
    assert body["results"][0]["source_type"] == "USDA_FSIS_RECALL"
    assert body["results"][0]["product_description"] == "Ready-to-eat chicken breast meal"
    assert "Chicken of the Sea" not in str(body["results"])


def test_everyday_safety_food_search_uses_normalized_query_upstream(monkeypatch):
    now = datetime.now(timezone.utc).isoformat()
    seen_queries = []

    async def fake_search_food_recalls(query, limit, request_id=None):
        seen_queries.append(("fda", query))
        return {
            "source_id": "openfda_food_enforcement",
            "source_name": "openFDA Food Enforcement API",
            "endpoint": "https://api.fda.gov/food/enforcement.json",
            "query": query,
            "retrieval_timestamp": now,
            "raw": {"results": []},
        }

    async def fake_search_fsis_recalls(query, limit, request_id=None):
        seen_queries.append(("fsis", query))
        return {
            "source_id": "usda_fsis_recall",
            "source_name": "USDA FSIS Recall API",
            "endpoint": "https://www.fsis.usda.gov/fsis/api/recall/v/1",
            "query": query,
            "retrieval_timestamp": now,
            "raw": {"results": []},
            "records": [],
        }

    monkeypatch.setattr(
        everyday_safety_search.food_client,
        "search_food_recalls",
        fake_search_food_recalls,
    )
    monkeypatch.setattr(
        everyday_safety_search.fsis_client,
        "search_recalls",
        fake_search_fsis_recalls,
    )
    _patch_persistence(monkeypatch)

    response = client.get(
        "/api/v1/everyday-safety/search",
        params={"category": "food_supplement", "q": "  protien    powder  ", "limit": 5},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["query"] == "protein powder"
    assert body["raw_query"] == "  protien    powder  "
    assert body["normalized_query"] == "protein powder"
    assert body["correction_applied"] is True
    assert body["suggestion_message"] == (
        "Showing results for 'protein powder' based on your search "
        "'protien powder'."
    )
    assert body["search_strategy_used"] == "intent_supplement_v1"
    assert seen_queries == [("fda", "protein powder"), ("fsis", "protein powder")]


def test_everyday_safety_rejects_whitespace_only_query():
    response = client.get(
        "/api/v1/everyday-safety/search",
        params={"category": "food_supplement", "q": "   ", "limit": 5},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "EVERYDAY_SAFETY_QUERY_EMPTY"
