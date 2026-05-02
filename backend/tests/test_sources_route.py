from fastapi.testclient import TestClient

from app.main import app


def test_list_sources_returns_registered_sources():
    test_client = TestClient(app)

    response = test_client.get("/api/v1/sources")

    assert response.status_code == 200

    body = response.json()
    assert body["count"] == 2
    assert len(body["sources"]) == 2

    source_ids = {source["source_id"] for source in body["sources"]}

    assert "openfda_drug_enforcement" in source_ids
    assert "openfda_drug_event" in source_ids


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