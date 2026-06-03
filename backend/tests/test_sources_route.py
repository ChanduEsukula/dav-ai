from fastapi.testclient import TestClient

from app.main import app


def test_list_sources_returns_registered_sources():
    test_client = TestClient(app)

    response = test_client.get("/api/v1/sources")

    assert response.status_code == 200

    body = response.json()
    assert body["count"] == 6
    assert len(body["sources"]) == 6

    source_ids = {source["source_id"] for source in body["sources"]}

    assert "openfda_drug_enforcement" in source_ids
    assert "openfda_drug_event" in source_ids
    assert "regional_health_pulse_demo" in source_ids


def test_list_sources_includes_required_metadata():
    test_client = TestClient(app)

    response = test_client.get("/api/v1/sources")

    assert response.status_code == 200

    body = response.json()

    for source in body["sources"]:
        assert source["source_id"]
        assert source["source_name"]
        assert source["endpoint"].startswith("https://")
        assert source["module"]
        assert source["description"]
        assert source["update_cadence"]


def test_list_sources_includes_helper_backed_freshness_fields():
    test_client = TestClient(app)

    response = test_client.get("/api/v1/sources")

    assert response.status_code == 200

    body = response.json()

    for source in body["sources"]:
        assert source["freshness_status"] in {
            "fresh",
            "aging",
            "stale",
            "unknown",
            "source_error",
        }
        assert source["freshness_label"] in {
            "Fresh",
            "Aging",
            "Stale",
            "Unknown",
            "Source Error",
        }
        assert "freshness_days_since_last_success" in source
        assert "freshness_reason" in source
        assert "freshness_safety_note" in source
        assert "operational review signal" in source["freshness_safety_note"]
        assert "clinical urgency" in source["freshness_safety_note"]


def test_list_sources_reports_unknown_freshness_when_audit_history_unavailable(monkeypatch):
    monkeypatch.setattr(
        "app.routes.sources.get_latest_audit_event_for_source",
        lambda source_id, request_id=None: ("skipped", None),
    )

    test_client = TestClient(app)

    response = test_client.get("/api/v1/sources")

    assert response.status_code == 200

    body = response.json()

    for source in body["sources"]:
        assert source["freshness_status"] == "unknown"
        assert source["freshness_label"] == "Unknown"
        assert source["freshness_days_since_last_success"] is None
        assert source["last_successful_retrieval_at"] is None
        assert source["last_attempted_retrieval_at"] is None
        assert source["last_record_count"] is None
        assert source["last_error_message"] is None
        assert "Database is not configured" in source["freshness_reason"]


def test_list_sources_reports_source_error_when_audit_lookup_fails(monkeypatch):
    monkeypatch.setattr(
        "app.routes.sources.get_latest_audit_event_for_source",
        lambda source_id, request_id=None: ("error", None),
    )

    test_client = TestClient(app)

    response = test_client.get("/api/v1/sources")

    assert response.status_code == 200

    body = response.json()

    for source in body["sources"]:
        assert source["freshness_status"] == "source_error"
        assert source["freshness_label"] == "Source Error"
        assert source["freshness_days_since_last_success"] is None
        assert source["last_error_message"] == "Could not read latest audit event for this source."
        assert "Audit history lookup failed" in source["freshness_reason"]


def test_list_sources_reports_fresh_status_from_recent_success(monkeypatch):
    monkeypatch.setattr(
        "app.routes.sources.get_latest_audit_event_for_source",
        lambda source_id, request_id=None: (
            "saved",
            {
                "upstream_status": "success",
                "retrieval_timestamp": "2999-01-01T00:00:00Z",
                "created_at": "2999-01-01T00:00:00Z",
                "record_count": 7,
                "error_message": None,
            },
        ),
    )

    test_client = TestClient(app)

    response = test_client.get("/api/v1/sources")

    assert response.status_code == 200

    body = response.json()

    for source in body["sources"]:
        assert source["freshness_status"] == "fresh"
        assert source["freshness_label"] == "Fresh"
        assert source["freshness_days_since_last_success"] == 0
        assert source["last_successful_retrieval_at"] == "2999-01-01T00:00:00+00:00"
        assert source["last_attempted_retrieval_at"] == "2999-01-01T00:00:00+00:00"
        assert source["last_record_count"] == 7
        assert source["last_error_message"] is None


def test_list_sources_reports_source_error_from_latest_upstream_error(monkeypatch):
    monkeypatch.setattr(
        "app.routes.sources.get_latest_audit_event_for_source",
        lambda source_id, request_id=None: (
            "saved",
            {
                "upstream_status": "error",
                "retrieval_timestamp": "2026-05-28T10:00:00Z",
                "created_at": "2026-05-28T10:00:00Z",
                "record_count": 0,
                "error_message": "openFDA timeout",
            },
        ),
    )

    test_client = TestClient(app)

    response = test_client.get("/api/v1/sources")

    assert response.status_code == 200

    body = response.json()

    for source in body["sources"]:
        assert source["freshness_status"] == "source_error"
        assert source["freshness_label"] == "Source Error"
        assert source["freshness_days_since_last_success"] is None
        assert source["last_successful_retrieval_at"] is None
        assert source["last_attempted_retrieval_at"] == "2026-05-28T10:00:00+00:00"
        assert source["last_record_count"] == 0
        assert source["last_error_message"] == "openFDA timeout"