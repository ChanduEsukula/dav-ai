"""Tests for Saved Monitors v2 backend foundation."""

from fastapi.testclient import TestClient

from app.db.saved_monitor_repository import saved_monitor_repository
from app.main import app

client = TestClient(app)


def setup_function() -> None:
    saved_monitor_repository.clear()


def test_create_saved_monitor() -> None:
    response = client.post(
        "/api/v1/saved-monitors",
        json={
            "name": "Eye drops monitor",
            "query": "eye drops",
            "module": "recallradar",
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert data["id"]
    assert data["name"] == "Eye drops monitor"
    assert data["query"] == "eye drops"
    assert data["module"] == "recallradar"
    assert data["created_at"]
    assert data["last_checked_at"] is None
    assert data["latest_audit_id"] is None
    assert data["latest_score"] is None
    assert data["previous_score"] is None
    assert data["latest_record_count"] is None
    assert data["previous_record_count"] is None
    assert data["status"] == "not_checked"


def test_list_saved_monitors() -> None:
    client.post(
        "/api/v1/saved-monitors",
        json={
            "name": "Metformin monitor",
            "query": "metformin",
            "module": "drugsignal",
        },
    )

    response = client.get("/api/v1/saved-monitors")

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 1
    assert data[0]["name"] == "Metformin monitor"
    assert data[0]["query"] == "metformin"
    assert data[0]["module"] == "drugsignal"


def test_delete_saved_monitor() -> None:
    create_response = client.post(
        "/api/v1/saved-monitors",
        json={
            "name": "Baby formula monitor",
            "query": "baby formula",
            "module": "recallradar",
        },
    )
    monitor_id = create_response.json()["id"]

    delete_response = client.delete(f"/api/v1/saved-monitors/{monitor_id}")

    assert delete_response.status_code == 204

    list_response = client.get("/api/v1/saved-monitors")
    assert list_response.status_code == 200
    assert list_response.json() == []


def test_delete_saved_monitor_not_found() -> None:
    response = client.delete("/api/v1/saved-monitors/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json()["detail"] == "Saved monitor not found"


def test_reject_invalid_module() -> None:
    response = client.post(
        "/api/v1/saved-monitors",
        json={
            "name": "Invalid module monitor",
            "query": "eye drops",
            "module": "invalid",
        },
    )

    assert response.status_code == 422


def test_reject_too_short_query() -> None:
    response = client.post(
        "/api/v1/saved-monitors",
        json={
            "name": "Short query monitor",
            "query": "x",
            "module": "recallradar",
        },
    )

    assert response.status_code == 422


def test_reject_too_short_name() -> None:
    response = client.post(
        "/api/v1/saved-monitors",
        json={
            "name": "x",
            "query": "eye drops",
            "module": "recallradar",
        },
    )

    assert response.status_code == 422
