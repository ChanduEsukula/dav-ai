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


def test_sources_response_includes_request_id_header():
    test_client = TestClient(app)

    response = test_client.get("/api/v1/sources")

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]
