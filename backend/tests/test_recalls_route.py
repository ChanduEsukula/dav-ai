from fastapi.testclient import TestClient
import pytest

from app.db.audit_repository import AuditPersistenceError
from app.main import app
from app.routes import recalls as recalls_route
from app.services.search_workflows import recall_search
from app.services.safety_source_adapters.base import (
    NormalizedSafetyRecord,
    SourceAdapterResult,
)
from app.sources.registry import OPENFDA_DRUG_ENFORCEMENT


class MockOpenFDAClientSuccess:
    async def search_drug_recalls(
        self,
        query: str,
        limit: int = 10,
        request_id: str | None = None,
    ):
        return {
            "source_id": "openfda_drug_enforcement",
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
    async def search_drug_recalls(
        self,
        query: str,
        limit: int = 10,
        request_id: str | None = None,
    ):
        return {
            "source_id": "openfda_drug_enforcement",
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
    async def search_drug_recalls(
        self,
        query: str,
        limit: int = 10,
        request_id: str | None = None,
    ):
        raise RuntimeError("openFDA unavailable")


@pytest.fixture(autouse=True)
def _patch_empty_public_notices(monkeypatch):
    async def fake_notice_search(**kwargs):
        return SourceAdapterResult(
            source_id="fda_recalls_market_withdrawals_safety_alerts",
            source_name="FDA Recalls, Market Withdrawals & Safety Alerts",
            source_type="public notice page",
            source_url="https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts",
            source_kind="public_notice",
            retrieved_at="2026-06-24T12:00:00Z",
            records=[],
            raw_payload={"rows": []},
            upstream_status="empty",
        )

    monkeypatch.setattr(
        recall_search,
        "search_official_public_notices",
        fake_notice_search,
    )


def test_search_recalls_returns_normalized_results():
    recall_search.client = MockOpenFDAClientSuccess()

    test_client = TestClient(app)
    response = test_client.get("/api/v1/recalls/search", params={"q": "eye drops", "limit": 5})

    assert response.status_code == 200

    body = response.json()
    assert body["query"] == "eye drops"
    assert body["count"] == 1
    assert body["source_name"] == "openFDA Drug Enforcement API"
    assert body["endpoint"] == "https://api.fda.gov/drug/enforcement.json"
    assert body["score_version"] == "recall-review-priority-v0.2"
    assert body["medical_disclaimer"]

    assert body["audit"]["source_id"] == "openfda_drug_enforcement"
    assert body["audit"]["module"] == "RecallRadar"
    assert body["audit"]["upstream_status"] == "success"
    assert body["audit"]["record_count"] == 1
    assert body["audit"]["transform_version"] == "recall-transform-v0.1"
    assert body["audit"]["audit_id"]

    result = body["results"][0]
    assert result["recall_number"] == "D-1234-2026"
    assert result["product_description"] == "Example eye drops"
    assert result["classification"] == "Class II"
    assert result["status"] == "Ongoing"
    assert "risk_score" in result
    assert result["source"]["name"] == "openFDA Drug Enforcement API"


def test_search_recalls_returns_empty_results_for_no_matches():
    recall_search.client = MockOpenFDAClientEmpty()

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
    assert body["score_version"] == "recall-review-priority-v0.2"
    assert body["medical_disclaimer"]

    assert body["audit"]["source_id"] == "openfda_drug_enforcement"
    assert body["audit"]["module"] == "RecallRadar"
    assert body["audit"]["upstream_status"] == "empty"
    assert body["audit"]["record_count"] == 0
    assert body["audit"]["transform_version"] == "recall-transform-v0.1"
    assert body["audit"]["audit_id"]


def test_search_recalls_includes_normalized_fda_public_notice(monkeypatch):
    recall_search.client = MockOpenFDAClientEmpty()
    notice = NormalizedSafetyRecord(
        source_name="FDA Recalls, Market Withdrawals & Safety Alerts",
        source_type="normalized official public notice",
        source_url="https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts",
        source_kind="normalized_public_notice",
        category="Drugs",
        product_name="Tylenol Extra Strength Tablets",
        brand_name="Tylenol",
        company_name="Example Pharma",
        title="Tylenol Extra Strength Tablets recall",
        reason="The product was recalled because of a labeling issue.",
        hazard_type="Labeling issue",
        remedy="Consumers should stop using the affected lot and contact the company.",
        published_date="06/20/2026",
        recall_number=None,
        raw_payload_hash="tylenol-notice",
        retrieved_at="2026-06-24T12:00:00Z",
        record_url="https://www.fda.gov/safety/notices/tylenol-example",
        extraction_confidence="high",
        source_text_excerpt="Internal matching excerpt.",
    )

    async def fake_notice_search(**kwargs):
        return SourceAdapterResult(
            source_id="fda_recalls_market_withdrawals_safety_alerts",
            source_name=notice.source_name,
            source_type="public notice page",
            source_url=notice.source_url,
            source_kind="public_notice",
            retrieved_at=notice.retrieved_at,
            records=[notice],
            raw_payload={"rows": []},
            upstream_status="success",
        )

    monkeypatch.setattr(
        recall_search,
        "search_official_public_notices",
        fake_notice_search,
    )

    response = TestClient(app).get(
        "/api/v1/recalls/search",
        params={"q": "Tylenol", "limit": 5},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    result = body["results"][0]
    assert result["source_kind"] == "normalized_public_notice"
    assert result["record_url"] == notice.record_url
    assert result["remedy"] == notice.remedy
    assert result["extraction_confidence"] == "high"


def test_search_recalls_normalizes_xanex_before_upstream_search():
    seen_queries = []

    class CapturingRecallClient(MockOpenFDAClientEmpty):
        async def search_drug_recalls(
            self,
            query: str,
            limit: int = 10,
            request_id: str | None = None,
        ):
            seen_queries.append(query)
            return await super().search_drug_recalls(query, limit, request_id)

    recall_search.client = CapturingRecallClient()

    test_client = TestClient(app)
    response = test_client.get(
        "/api/v1/recalls/search",
        params={"q": "xanex", "limit": 5},
    )

    assert response.status_code == 200
    body = response.json()
    assert seen_queries == ["xanax"]
    assert body["query"] == "xanax"
    assert body["raw_query"] == "xanex"
    assert body["normalized_query"] == "xanax"
    assert body["correction_applied"] is True
    assert body["suggestion_message"] == (
        "Showing results for 'xanax' based on your search 'xanex'."
    )


def test_search_recalls_returns_502_and_persists_error_audit(monkeypatch):
    recall_search.client = MockOpenFDAClientFailure()
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
        "app.services.search_workflows.recall_search.save_audit_event",
        fake_save_audit_event,
    )

    test_client = TestClient(app)
    response = test_client.get("/api/v1/recalls/search", params={"q": "eye drops", "limit": 5})

    assert response.status_code == 502

    body = response.json()
    assert body["detail"]["message"] == "Unable to retrieve recall data from openFDA."
    assert body["detail"]["code"] == "OPENFDA_RECALL_UPSTREAM_UNAVAILABLE"
    assert "openFDA unavailable" not in response.text

    assert len(saved_audits) == 1
    audit_event = saved_audits[0]["audit_event"]

    assert audit_event["module"] == "RecallRadar"
    assert audit_event["source_id"] == OPENFDA_DRUG_ENFORCEMENT["source_id"]
    assert audit_event["source_name"] == OPENFDA_DRUG_ENFORCEMENT["source_name"]
    assert audit_event["endpoint"] == OPENFDA_DRUG_ENFORCEMENT["endpoint"]
    assert audit_event["query"] == "eye drops"
    assert audit_event["query_params"] == {"q": "eye drops", "limit": 5}
    assert audit_event["upstream_status"] == "error"
    assert audit_event["record_count"] == 0
    assert audit_event["transform_version"] == "recall-transform-v0.1"
    assert audit_event["score_version"] == "recall-review-priority-v0.2"
    assert "openFDA unavailable" in audit_event["error_message"]
    assert audit_event["audit_id"]
    assert audit_event["retrieval_timestamp"]


def test_search_recalls_maps_persistence_failure_without_upstream_label(monkeypatch):
    async def fake_execute_recall_search(**kwargs):
        raise AuditPersistenceError("audit database unavailable")

    monkeypatch.setattr(
        recalls_route,
        "execute_recall_search",
        fake_execute_recall_search,
    )

    response = TestClient(app).get(
        "/api/v1/recalls/search",
        params={"q": "eye drops", "limit": 5},
    )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == (
        "RECALL_PROVENANCE_PERSISTENCE_UNAVAILABLE"
    )


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
