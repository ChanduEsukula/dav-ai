from fastapi.testclient import TestClient

from app.main import app
from app.services.search_workflows import drug_signal_search
from app.sources.registry import OPENFDA_DRUG_EVENT


class MockDrugEventClientSuccess:
    async def search_drug_events(
        self,
        query: str,
        limit: int = 10,
        request_id: str | None = None,
    ):
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
    async def search_drug_events(
        self,
        query: str,
        limit: int = 10,
        request_id: str | None = None,
    ):
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
    async def search_drug_events(
        self,
        query: str,
        limit: int = 10,
        request_id: str | None = None,
    ):
        raise RuntimeError("openFDA drug event unavailable")


def test_search_drug_events_returns_top_reactions():
    drug_signal_search.client = MockDrugEventClientSuccess()

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
    assert body["trend_snapshot"]["label"] == "Insufficient history"
    assert body["trend_snapshot"]["current_record_count"] == 2
    assert body["trend_snapshot"]["previous_record_count"] is None
    assert body["trend_snapshot"]["trend_version"] == "drug-signal-trend-v0.1"


def test_search_drug_events_returns_empty_results_for_no_matches():
    drug_signal_search.client = MockDrugEventClientEmpty()

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
    assert body["intelligence_score"]["score"] == 0
    assert body["intelligence_score"]["data_confidence"] == "Limited"
    assert body["intelligence_score"]["top_reaction_concentration"] == 0.0
    assert body["reaction_categories"] == []
    assert body["reaction_classifier_version"] == "reaction-classifier-v0.1"
    assert body["trend_snapshot"]["label"] == "Insufficient history"
    assert body["trend_snapshot"]["current_record_count"] == 0
    assert body["source_name"] == "openFDA Drug Event API"
    assert body["endpoint"] == "https://api.fda.gov/drug/event.json"
    assert body["medical_disclaimer"]
    assert body["faers_disclaimer"]


def test_search_drug_events_returns_502_and_persists_error_audit(monkeypatch):
    drug_signal_search.client = MockDrugEventClientFailure()
    saved_audits = []

    def fake_save_audit_event(audit_event, request_id=None):
        saved_audits.append(
            {
                "audit_event": audit_event,
                "request_id": request_id,
            }
        )
        return {"status": "saved", "reason": "audit_event_persisted"}

    monkeypatch.setattr(
        "app.services.search_workflows.drug_signal_search.save_audit_event",
        fake_save_audit_event,
    )

    test_client = TestClient(app)
    response = test_client.get("/api/v1/drug-events/search", params={"q": "metformin", "limit": 5})

    assert response.status_code == 502

    body = response.json()
    assert body["detail"]["message"] == "Unable to retrieve drug event data from openFDA."
    assert body["detail"]["code"] == "OPENFDA_DRUG_EVENT_UPSTREAM_UNAVAILABLE"
    assert "openFDA drug event unavailable" not in response.text

    assert len(saved_audits) == 1
    audit_event = saved_audits[0]["audit_event"]

    assert audit_event["module"] == "DrugSignal"
    assert audit_event["source_id"] == OPENFDA_DRUG_EVENT["source_id"]
    assert audit_event["source_name"] == OPENFDA_DRUG_EVENT["source_name"]
    assert audit_event["endpoint"] == OPENFDA_DRUG_EVENT["endpoint"]
    assert audit_event["query"] == "metformin"
    assert audit_event["query_params"] == {"q": "metformin", "limit": 5}
    assert audit_event["upstream_status"] == "error"
    assert audit_event["record_count"] == 0
    assert audit_event["transform_version"] == "drug-event-transform-v0.1"
    assert audit_event["score_version"] == "drug-signal-intelligence-v0.1"
    assert "openFDA drug event unavailable" in audit_event["error_message"]
    assert audit_event["audit_id"]
    assert audit_event["retrieval_timestamp"]


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


def test_search_drug_events_returns_trend_snapshot_with_previous_audit(monkeypatch):
    drug_signal_search.client = MockDrugEventClientSuccess()

    def fake_get_latest_audit_event_for_query(
        module: str,
        query: str,
        exclude_audit_id: str | None,
        request_id: str | None,
    ):
        assert module == "DrugSignal"
        assert query == "metformin"
        assert exclude_audit_id is not None
        assert request_id is not None

        return "saved", {
            "audit_id": "99999999-9999-4999-8999-999999999999",
            "module": "DrugSignal",
            "query": "metformin",
            "record_count": 1,
            "upstream_status": "success",
            "created_at": "2026-05-08T18:00:00Z",
        }

    monkeypatch.setattr(
        "app.services.search_workflows.drug_signal_search.get_latest_audit_event_for_query",
        fake_get_latest_audit_event_for_query,
    )

    test_client = TestClient(app)
    response = test_client.get("/api/v1/drug-events/search", params={"q": "metformin", "limit": 5})

    assert response.status_code == 200

    body = response.json()
    assert body["trend_snapshot"]["label"] == "Increased"
    assert body["trend_snapshot"]["current_record_count"] == 2
    assert body["trend_snapshot"]["previous_record_count"] == 1
    assert body["trend_snapshot"]["previous_audit_id"] == "99999999-9999-4999-8999-999999999999"
    assert body["trend_snapshot"]["previous_created_at"] == "2026-05-08T18:00:00Z"
    assert "most recent stored DrugSignal audit event" in body["trend_snapshot"]["explanation"]
    assert "stored public-data searches" in body["trend_snapshot"]["limitation"]
