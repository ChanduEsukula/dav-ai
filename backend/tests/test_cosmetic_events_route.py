from fastapi.testclient import TestClient

from app.main import app
from app.services.search_workflows import cosmetic_signal_search
from app.sources.registry import OPENFDA_COSMETIC_EVENT


class MockCosmeticEventClientSuccess:
    async def search_cosmetic_events(
        self,
        query: str,
        limit: int = 10,
        request_id: str | None = None,
    ):
        return {
            "source_id": "openfda_cosmetic_event",
            "source_name": "openFDA Cosmetic Event API",
            "endpoint": "https://api.fda.gov/cosmetic/event.json",
            "query": query,
            "retrieval_timestamp": "2026-06-03T20:30:00+00:00",
            "raw": {
                "results": [
                    {
                        "report_number": "COS-1",
                        "date_started": "20260102",
                        "serious": "Y",
                        "outcomes": ["Visited a health care provider"],
                        "reactions": ["Rash", "Burning sensation"],
                        "products": [
                            {
                                "brand_name": "Example Glow",
                                "name_brand": "Example Glow Face Cream",
                                "industry_code": "53",
                                "industry_name": "Skin Care Products",
                            }
                        ],
                    },
                    {
                        "report_number": "COS-2",
                        "date_started": "20260105",
                        "serious": "N",
                        "outcomes": ["Other serious or important medical events"],
                        "reactions": ["Rash"],
                        "products": [
                            {
                                "brand_name": "Example Glow",
                                "name_brand": "Example Glow Serum",
                                "industry_code": "53",
                                "industry_name": "Skin Care Products",
                            }
                        ],
                    },
                ]
            },
        }


class MockCosmeticEventClientEmpty:
    async def search_cosmetic_events(
        self,
        query: str,
        limit: int = 10,
        request_id: str | None = None,
    ):
        return {
            "source_id": "openfda_cosmetic_event",
            "source_name": "openFDA Cosmetic Event API",
            "endpoint": "https://api.fda.gov/cosmetic/event.json",
            "query": query,
            "retrieval_timestamp": "2026-06-03T20:30:00+00:00",
            "raw": {"meta": {}, "results": []},
        }


class MockCosmeticEventClientFailure:
    async def search_cosmetic_events(
        self,
        query: str,
        limit: int = 10,
        request_id: str | None = None,
    ):
        raise RuntimeError("openFDA cosmetic event unavailable")


def test_search_cosmetic_events_returns_reaction_summary():
    cosmetic_signal_search.client = MockCosmeticEventClientSuccess()

    test_client = TestClient(app)
    response = test_client.get(
        "/api/v1/cosmetic-events/search",
        params={"q": "face cream", "limit": 5},
    )

    assert response.status_code == 200

    body = response.json()
    assert body["query"] == "face cream"
    assert body["count"] == 2
    assert body["source_name"] == "openFDA Cosmetic Event API"
    assert body["endpoint"] == "https://api.fda.gov/cosmetic/event.json"
    assert body["medical_disclaimer"]
    assert body["cosmetic_disclaimer"]
    assert "do not prove" in body["cosmetic_disclaimer"]

    assert body["top_reactions"][0] == {"reaction": "Rash", "count": 2}
    assert body["top_reactions"][1] == {"reaction": "Burning sensation", "count": 1}

    assert body["signal_score"]["label"] in {"Low", "Moderate", "High"}
    assert body["signal_score"]["score_version"] == "cosmetic-signal-score-v0.1"
    assert "do not prove" in body["signal_score"]["limitations"][0]

    assert body["records"][0]["report_number"] == "COS-1"
    assert body["records"][0]["products"][0]["brand_name"] == "Example Glow"
    assert body["audit"]["module"] == "CosmeticSignal"
    assert body["audit"]["source_id"] == "openfda_cosmetic_event"


def test_search_cosmetic_events_returns_empty_results():
    cosmetic_signal_search.client = MockCosmeticEventClientEmpty()

    test_client = TestClient(app)
    response = test_client.get(
        "/api/v1/cosmetic-events/search",
        params={"q": "randomfakecosmetic123", "limit": 5},
    )

    assert response.status_code == 200

    body = response.json()
    assert body["query"] == "randomfakecosmetic123"
    assert body["count"] == 0
    assert body["top_reactions"] == []
    assert body["records"] == []
    assert body["signal_score"]["label"] == "Low"
    assert body["audit"]["upstream_status"] == "empty"


def test_search_cosmetic_events_returns_502_and_persists_error_audit(monkeypatch):
    cosmetic_signal_search.client = MockCosmeticEventClientFailure()
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
        "app.services.search_workflows.cosmetic_signal_search.save_audit_event",
        fake_save_audit_event,
    )

    test_client = TestClient(app)
    response = test_client.get(
        "/api/v1/cosmetic-events/search",
        params={"q": "face cream", "limit": 5},
    )

    assert response.status_code == 502

    body = response.json()
    assert body["detail"]["message"] == "Unable to retrieve cosmetic event data from openFDA."
    assert body["detail"]["code"] == "OPENFDA_COSMETIC_EVENT_UPSTREAM_UNAVAILABLE"
    assert "openFDA cosmetic event unavailable" not in response.text

    assert len(saved_audits) == 1
    audit_event = saved_audits[0]["audit_event"]

    assert audit_event["module"] == "CosmeticSignal"
    assert audit_event["source_id"] == OPENFDA_COSMETIC_EVENT["source_id"]
    assert audit_event["source_name"] == OPENFDA_COSMETIC_EVENT["source_name"]
    assert audit_event["endpoint"] == OPENFDA_COSMETIC_EVENT["endpoint"]
    assert audit_event["query"] == "face cream"
    assert audit_event["query_params"] == {"q": "face cream", "limit": 5}
    assert audit_event["upstream_status"] == "error"
    assert audit_event["record_count"] == 0
    assert audit_event["transform_version"] == "cosmetic-event-transform-v0.1"
    assert audit_event["score_version"] == "cosmetic-signal-score-v0.1"
    assert "openFDA cosmetic event unavailable" in audit_event["error_message"]


def test_search_cosmetic_events_rejects_short_query():
    test_client = TestClient(app)

    response = test_client.get(
        "/api/v1/cosmetic-events/search",
        params={"q": "a", "limit": 5},
    )

    assert response.status_code == 422


def test_search_cosmetic_events_rejects_limit_above_maximum():
    test_client = TestClient(app)

    response = test_client.get(
        "/api/v1/cosmetic-events/search",
        params={"q": "face cream", "limit": 26},
    )

    assert response.status_code == 422


def test_cosmetic_search_expands_common_user_terms():
    from app.services.openfda_cosmetic_event_client import _build_cosmetic_search_query

    hair_query = _build_cosmetic_search_query("hair dye")
    assert 'products.brand_name:"hair color"' in hair_query
    assert 'products.name_brand:"hair coloring"' in hair_query
    assert 'products.industry_name:"hair"' in hair_query

    rash_query = _build_cosmetic_search_query("rash")
    assert 'reactions:"irritation"' in rash_query
    assert 'outcomes:"burning"' in rash_query

    mascara_query = _build_cosmetic_search_query("mascara")
    assert 'products.name_brand:"eye"' in mascara_query
    assert 'products.brand_name:"eyelash"' in mascara_query
