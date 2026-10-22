from fastapi.testclient import TestClient

from app.main import app


def test_health_response_includes_generated_request_id():
    test_client = TestClient(app)

    response = test_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
    assert response.headers["X-Request-ID"]


def test_health_response_reuses_provided_request_id():
    test_client = TestClient(app)

    response = test_client.get(
        "/health",
        headers={"X-Request-ID": "test-request-id-123"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "test-request-id-123"


def test_root_response_includes_request_id_header():
    test_client = TestClient(app)

    response = test_client.get("/")

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]
    assert response.json()["status"] == "ok"


def test_coverage_response_includes_request_id_header(monkeypatch):
    # Header contract does not depend on an external 4.83 GB local artifact.
    monkeypatch.setattr("app.routes.evidence.release_metadata", lambda: {"release_id": "synthetic"})
    test_client = TestClient(app)

    response = test_client.get("/api/coverage")

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]
