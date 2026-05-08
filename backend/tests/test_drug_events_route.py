from fastapi.testclient import TestClient

from app.main import app
from app.routes import drug_events


class MockDrugEventClientSuccess:
    async def search_drug_events(self, query: str, limit: int = 10):
        return {
            "source_id": "openfda_drug_event",
            "source_name": "openFDA Drug Event API",
            "endpoint": "https://api.fda.gov/drug/event.json",
            "query": query,
            "retrieval_timestamp": "2026-05-01T20:30:00+00:00",
            "raw": {
                "results": [
                    {
                        "patient": {
                            "reaction": [
                                {"reactionmeddrapt": "Nausea"},
                                {"reactionmeddrapt": "Headache"},
                            ]
                        }
                    },
                    {
                        "patient": {
                            "reaction": [
                                {"reactionmeddrapt": "Nausea"},
                            ]
                        }
                    },
                ]
            },
        }


class MockDrugEventClientEmpty:
    async def search_drug_events(self, query: str, limit: int = 10):
        return {
            "source_id": "openfda_drug_event",
            "source_name": "openFDA Drug Event API",
            "endpoint": "https://api.fda.gov/drug/event.json",
            "query": query,
            "retrieval_timestamp": "2026-05-01T20:30:00+00:00",
            "raw": {
                "meta": {},
                "results": [],
            },
        }


class MockDrugEventClientFailure:
    async def search_drug_events(self, query: str, limit: int = 10):
        raise RuntimeError("openFDA drug event unavailable")


def test_search_drug_events_returns_top_reactions():
    drug_events.client = MockDrugEventClientSuccess()

    test_client = TestClient(app)
    response = test_client.get("/api/v1/drug-events/search", params={"q": "metformin", "limit": 5})

    assert response.status_code == 200

    body = response.json()
    assert body["query"] == "metformin"
    assert body["count"] == 2
    assert body["source_name"] == "openFDA Drug Event API"
    assert body["endpoint"] == "https://api.fda.gov/drug/event.json"
    assert body["medical_disclaimer"]
    assert body["faers_disclaimer"]

    assert body["top_reactions"][0] == {"reaction": "Nausea", "count": 2}
    assert body["top_reactions"][1] == {"reaction": "Headache", "count": 1}

    assert body["intelligence_score"]["score"] == 57
    assert body["intelligence_score"]["label"] == "Moderate"
    assert body["intelligence_score"]["data_confidence"] == "Limited"
    assert body["intelligence_score"]["top_reaction_concentration"] == 66.67
    assert body["intelligence_score"]["review_priority"] == "Watch"
    assert body["intelligence_score"]["score_version"] == "drug-signal-intelligence-v0.1"
    assert "do not prove causation" in body["intelligence_score"]["limitations"][0]
    assert body["reaction_classifier_version"] == "reaction-classifier-v0.1"
    assert body["reaction_categories"] == [
        {
            "category": "Gastrointestinal",
            "count": 2,
            "reactions": ["Nausea"],
        },
        {
            "category": "Neurological",
            "count": 1,
            "reactions": ["Headache"],
        },
    ]


def test_search_drug_events_returns_empty_results_for_no_matches():
    drug_events.client = MockDrugEventClientEmpty()

    test_client = TestClient(app)
    response = test_client.get(
        "/api/v1/drug-events/search",
        params={"q": "randomfakeproduct123", "limit": 5},
    )

    assert response.status_code == 200

    body = response.json()
    assert body["query"] == "randomfakeproduct123"
    assert body["count"] == 0
    assert body["top_reactions"] == []
    assert body["intelligence_score"]["label"] == "Low"
    assert body["intelligence_score"]["data_confidence"] == "Limited"
    assert body["intelligence_score"]["top_reaction_concentration"] == 0.0
    assert body["reaction_categories"] == []
    assert body["reaction_classifier_version"] == "reaction-classifier-v0.1"
    assert body["source_name"] == "openFDA Drug Event API"
    assert body["endpoint"] == "https://api.fda.gov/drug/event.json"
    assert body["medical_disclaimer"]
    assert body["faers_disclaimer"]


def test_search_drug_events_returns_502_for_upstream_failure():
    drug_events.client = MockDrugEventClientFailure()

    test_client = TestClient(app)
    response = test_client.get("/api/v1/drug-events/search", params={"q": "metformin", "limit": 5})

    assert response.status_code == 502

    body = response.json()
    assert body["detail"]["message"] == "Unable to retrieve drug event data from openFDA."
    assert "openFDA drug event unavailable" in body["detail"]["error"]


def test_search_drug_events_rejects_short_query():
    test_client = TestClient(app)

    response = test_client.get("/api/v1/drug-events/search", params={"q": "a", "limit": 5})

    assert response.status_code == 422


def test_search_drug_events_rejects_limit_below_minimum():
    test_client = TestClient(app)

    response = test_client.get("/api/v1/drug-events/search", params={"q": "metformin", "limit": 0})

    assert response.status_code == 422


def test_search_drug_events_rejects_limit_above_maximum():
    test_client = TestClient(app)

    response = test_client.get("/api/v1/drug-events/search", params={"q": "metformin", "limit": 26})

    assert response.status_code == 422