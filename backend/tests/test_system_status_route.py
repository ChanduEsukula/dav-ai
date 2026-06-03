from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_system_status_returns_core_operational_fields(monkeypatch):
    monkeypatch.setattr("app.routes.system.is_database_configured", lambda: False)

    response = client.get("/api/v1/system/status")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["app"] == "Dav AI API"
    assert data["version"] == "0.1.0"
    assert data["database"]["configured"] is False
    assert data["database"]["audit_readable"] is False
    assert data["sources"]["registered_count"] == 4
    assert data["sources"]["available"] is True
    assert "RecallRadar" in data["modules"]
    assert "DrugSignal" in data["modules"]
    assert "Regional Health Pulse" in data["modules"]
    assert "Saved Monitors" in data["modules"]
    assert "Sources" in data["modules"]
    assert "Audit History" in data["modules"]


def test_system_status_reports_audit_readable_when_database_read_succeeds(monkeypatch):
    monkeypatch.setattr("app.routes.system.is_database_configured", lambda: True)
    monkeypatch.setattr("app.routes.system.list_audit_events", lambda limit=1: ("saved", []))

    response = client.get("/api/v1/system/status")

    assert response.status_code == 200

    data = response.json()

    assert data["database"]["configured"] is True
    assert data["database"]["audit_readable"] is True


def test_system_status_reports_audit_not_readable_when_database_read_fails(monkeypatch):
    monkeypatch.setattr("app.routes.system.is_database_configured", lambda: True)
    monkeypatch.setattr("app.routes.system.list_audit_events", lambda limit=1: ("error", []))

    response = client.get("/api/v1/system/status")

    assert response.status_code == 200

    data = response.json()

    assert data["database"]["configured"] is True
    assert data["database"]["audit_readable"] is False


def test_data_quality_returns_skipped_when_database_not_configured(monkeypatch):
    monkeypatch.setattr("app.routes.system.is_database_configured", lambda: False)

    response = client.get("/api/v1/system/data-quality")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "skipped"
    assert data["database_configured"] is False
    assert data["audit_readable"] is False
    assert data["source_registry_count"] == 4
    assert data["recent_audit_count"] == 0
    assert data["latest_audit_event"]["exists"] is False


def test_data_quality_returns_recent_audit_summary(monkeypatch):
    monkeypatch.setattr("app.routes.system.is_database_configured", lambda: True)
    monkeypatch.setattr(
        "app.routes.system.list_audit_events",
        lambda limit=25: (
            "saved",
            [
                {
                    "audit_id": "audit-1",
                    "module": "RecallRadar",
                    "query": "eye drops",
                    "upstream_status": "success",
                    "record_count": 5,
                    "created_at": "2026-05-08T14:00:00Z",
                },
                {
                    "audit_id": "audit-2",
                    "module": "DrugSignal",
                    "query": "metformin",
                    "upstream_status": "empty",
                    "record_count": 0,
                    "created_at": "2026-05-08T13:00:00Z",
                },
                {
                    "audit_id": "audit-3",
                    "module": "RecallRadar",
                    "query": "bad upstream",
                    "upstream_status": "error",
                    "record_count": 0,
                    "created_at": "2026-05-08T12:00:00Z",
                },
            ],
        ),
    )

    response = client.get("/api/v1/system/data-quality")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["database_configured"] is True
    assert data["audit_readable"] is True
    assert data["source_registry_count"] == 4
    assert data["recent_audit_count"] == 3
    assert data["upstream_status_counts"]["success"] == 1
    assert data["upstream_status_counts"]["empty"] == 1
    assert data["upstream_status_counts"]["error"] == 1
    assert data["latest_audit_event"]["exists"] is True
    assert data["latest_audit_event"]["audit_id"] == "audit-1"
    assert data["latest_audit_event"]["module"] == "RecallRadar"
    assert data["latest_audit_event"]["query"] == "eye drops"


def test_data_quality_reports_error_when_audit_read_fails(monkeypatch):
    monkeypatch.setattr("app.routes.system.is_database_configured", lambda: True)
    monkeypatch.setattr("app.routes.system.list_audit_events", lambda limit=25: ("error", []))

    response = client.get("/api/v1/system/data-quality")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "error"
    assert data["database_configured"] is True
    assert data["audit_readable"] is False
    assert data["recent_audit_count"] == 0
    assert data["latest_audit_event"]["exists"] is False