from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_system_status_returns_core_operational_fields(monkeypatch):
    monkeypatch.setattr("app.routes.system.is_database_configured", lambda: False)

    response = client.get("/api/v1/system/status")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["app"] == "MedTrek AI API"
    assert data["version"] == "0.1.0"
    assert data["database"]["configured"] is False
    assert data["database"]["audit_readable"] is False
    assert data["sources"]["registered_count"] == 2
    assert data["sources"]["available"] is True
    assert "RecallRadar" in data["modules"]
    assert "DrugSignal" in data["modules"]
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
