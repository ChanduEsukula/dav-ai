from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def sample_audit_event() -> dict:
    return {
        "audit_id": "123e4567-e89b-12d3-a456-426614174000",
        "module": "RecallRadar",
        "source_id": "openfda_drug_enforcement",
        "source_name": "openFDA Drug Enforcement",
        "endpoint": "https://api.fda.gov/drug/enforcement.json",
        "query": "eye drops",
        "query_params": {"search": "product_description:eye drops", "limit": 5},
        "retrieval_timestamp": "2026-05-05T12:00:00Z",
        "upstream_status": "success",
        "record_count": 2,
        "transform_version": "recall-transform-v1",
        "score_version": "recall-score-v1",
        "disclaimer_version": "healthcare-safety-v1",
        "error_message": None,
        "created_at": "2026-05-05T12:00:01Z",
    }


def test_list_audit_events_returns_skipped_when_persistence_unavailable(monkeypatch):
    def fake_list_audit_events(limit: int = 50):
        return "skipped", []

    monkeypatch.setattr(
        "app.routes.audit_events.list_audit_events",
        fake_list_audit_events,
    )

    response = client.get("/api/v1/audit-events")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "skipped"
    assert data["persistence_available"] is False
    assert data["count"] == 0
    assert data["items"] == []


def test_list_audit_events_returns_empty_ok_list(monkeypatch):
    def fake_list_audit_events(limit: int = 50):
        return "saved", []

    monkeypatch.setattr(
        "app.routes.audit_events.list_audit_events",
        fake_list_audit_events,
    )

    response = client.get("/api/v1/audit-events")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ok"
    assert data["persistence_available"] is True
    assert data["count"] == 0
    assert data["items"] == []


def test_list_audit_events_returns_recent_audit_events(monkeypatch):
    def fake_list_audit_events(limit: int = 50):
        return "saved", [sample_audit_event()]

    monkeypatch.setattr(
        "app.routes.audit_events.list_audit_events",
        fake_list_audit_events,
    )

    response = client.get("/api/v1/audit-events?limit=10")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ok"
    assert data["persistence_available"] is True
    assert data["count"] == 1
    assert data["items"][0]["audit_id"] == "123e4567-e89b-12d3-a456-426614174000"
    assert data["items"][0]["module"] == "RecallRadar"
    assert data["items"][0]["query"] == "eye drops"
    assert data["items"][0]["record_count"] == 2
    assert data["items"][0]["query_params"]["limit"] == 5


def test_list_audit_events_returns_error_when_repository_read_fails(monkeypatch):
    def fake_list_audit_events(limit: int = 50):
        return "error", []

    monkeypatch.setattr(
        "app.routes.audit_events.list_audit_events",
        fake_list_audit_events,
    )

    response = client.get("/api/v1/audit-events")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "error"
    assert data["persistence_available"] is False
    assert data["count"] == 0
    assert data["items"] == []


def test_get_audit_event_returns_detail_when_event_exists(monkeypatch):
    def fake_get_audit_event_by_id(audit_id: str):
        assert audit_id == "123e4567-e89b-12d3-a456-426614174000"
        return "saved", sample_audit_event()

    monkeypatch.setattr(
        "app.routes.audit_events.get_audit_event_by_id",
        fake_get_audit_event_by_id,
    )

    response = client.get("/api/v1/audit-events/123e4567-e89b-12d3-a456-426614174000")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ok"
    assert data["persistence_available"] is True
    assert data["message"] is None
    assert data["item"]["audit_id"] == "123e4567-e89b-12d3-a456-426614174000"
    assert data["item"]["source_name"] == "openFDA Drug Enforcement"


def test_get_audit_event_returns_not_found_when_event_missing(monkeypatch):
    def fake_get_audit_event_by_id(audit_id: str):
        return "saved", None

    monkeypatch.setattr(
        "app.routes.audit_events.get_audit_event_by_id",
        fake_get_audit_event_by_id,
    )

    response = client.get("/api/v1/audit-events/missing-audit-id")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "not_found"
    assert data["persistence_available"] is True
    assert data["item"] is None
    assert data["message"] == "No audit event found for this audit_id."


def test_get_audit_event_returns_skipped_when_persistence_unavailable(monkeypatch):
    def fake_get_audit_event_by_id(audit_id: str):
        return "skipped", None

    monkeypatch.setattr(
        "app.routes.audit_events.get_audit_event_by_id",
        fake_get_audit_event_by_id,
    )

    response = client.get("/api/v1/audit-events/123e4567-e89b-12d3-a456-426614174000")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "skipped"
    assert data["persistence_available"] is False
    assert data["item"] is None
    assert data["message"] == "Audit persistence is not configured."


def test_get_audit_event_returns_error_when_repository_read_fails(monkeypatch):
    def fake_get_audit_event_by_id(audit_id: str):
        return "error", None

    monkeypatch.setattr(
        "app.routes.audit_events.get_audit_event_by_id",
        fake_get_audit_event_by_id,
    )

    response = client.get("/api/v1/audit-events/123e4567-e89b-12d3-a456-426614174000")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "error"
    assert data["persistence_available"] is False
    assert data["item"] is None
    assert data["message"] == "Audit persistence could not be read."


def test_list_audit_events_rejects_invalid_limit():
    response = client.get("/api/v1/audit-events?limit=0")

    assert response.status_code == 422


def test_list_audit_events_passes_filter_params_to_repository(monkeypatch):
    captured_filters = {}

    def fake_list_audit_events(
        limit: int = 50,
        request_id: str | None = None,
        module: str | None = None,
        upstream_status: str | None = None,
        search_text: str | None = None,
    ):
        captured_filters["limit"] = limit
        captured_filters["request_id"] = request_id
        captured_filters["module"] = module
        captured_filters["upstream_status"] = upstream_status
        captured_filters["search_text"] = search_text
        return "saved", [sample_audit_event()]

    monkeypatch.setattr(
        "app.routes.audit_events.list_audit_events",
        fake_list_audit_events,
    )

    response = client.get(
        "/api/v1/audit-events?limit=10&module=RecallRadar&upstream_status=success&q=eye"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["count"] == 1
    assert captured_filters["limit"] == 10
    assert captured_filters["module"] == "RecallRadar"
    assert captured_filters["upstream_status"] == "success"
    assert captured_filters["search_text"] == "eye"
    assert captured_filters["request_id"] is not None


def sample_source_pull() -> dict:
    return {
        "pull_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "audit_id": "123e4567-e89b-12d3-a456-426614174000",
        "source_id": "openfda_drug_enforcement",
        "source_name": "openFDA Drug Enforcement",
        "endpoint": "https://api.fda.gov/drug/enforcement.json",
        "query": "eye drops",
        "query_params": {"search": "product_description:eye drops", "limit": 5},
        "retrieval_timestamp": "2026-05-05T12:00:00Z",
        "upstream_status": "success",
        "record_count": 2,
        "payload_hash": "a" * 64,
        "transform_version": "recall-transform-v1",
        "created_at": "2026-05-05T12:00:01Z",
        "snapshot_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
    }


def test_get_audit_event_source_pull_returns_metadata_without_raw_payload(monkeypatch):
    def fake_get_source_pull_by_audit_id(audit_id: str, request_id: str | None = None):
        assert audit_id == "123e4567-e89b-12d3-a456-426614174000"
        assert request_id is not None
        row = sample_source_pull()
        row["raw_payload"] = {"results": [{"secret": "should-not-leak"}]}
        return "saved", row

    monkeypatch.setattr(
        "app.routes.audit_events.get_source_pull_by_audit_id",
        fake_get_source_pull_by_audit_id,
    )

    response = client.get(
        "/api/v1/audit-events/123e4567-e89b-12d3-a456-426614174000/source-pull"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ok"
    assert data["persistence_available"] is True
    assert data["message"] is None
    assert data["item"]["audit_id"] == "123e4567-e89b-12d3-a456-426614174000"
    assert data["item"]["pull_id"] == "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    assert data["item"]["snapshot_id"] == "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    assert data["item"]["payload_hash"] == "a" * 64
    assert "raw_payload" not in data["item"]


def test_get_audit_event_source_pull_returns_not_found(monkeypatch):
    def fake_get_source_pull_by_audit_id(audit_id: str, request_id: str | None = None):
        return "saved", None

    monkeypatch.setattr(
        "app.routes.audit_events.get_source_pull_by_audit_id",
        fake_get_source_pull_by_audit_id,
    )

    response = client.get("/api/v1/audit-events/missing-audit-id/source-pull")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "not_found"
    assert data["persistence_available"] is True
    assert data["item"] is None
    assert data["message"] == "No source pull found for this audit_id."


def test_get_audit_event_source_pull_returns_skipped_when_persistence_unavailable(monkeypatch):
    def fake_get_source_pull_by_audit_id(audit_id: str, request_id: str | None = None):
        return "skipped", None

    monkeypatch.setattr(
        "app.routes.audit_events.get_source_pull_by_audit_id",
        fake_get_source_pull_by_audit_id,
    )

    response = client.get(
        "/api/v1/audit-events/123e4567-e89b-12d3-a456-426614174000/source-pull"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "skipped"
    assert data["persistence_available"] is False
    assert data["item"] is None
    assert data["message"] == "Source-pull persistence is not configured."


def test_get_audit_event_source_pull_returns_error_when_read_fails(monkeypatch):
    def fake_get_source_pull_by_audit_id(audit_id: str, request_id: str | None = None):
        return "error", None

    monkeypatch.setattr(
        "app.routes.audit_events.get_source_pull_by_audit_id",
        fake_get_source_pull_by_audit_id,
    )

    response = client.get(
        "/api/v1/audit-events/123e4567-e89b-12d3-a456-426614174000/source-pull"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "error"
    assert data["persistence_available"] is False
    assert data["item"] is None
    assert data["message"] == "Source-pull provenance could not be read."
