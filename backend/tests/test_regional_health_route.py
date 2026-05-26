from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_regional_health_search_returns_public_data_signal():
    response = client.get(
        "/api/v1/regional-health/search",
        params={"region": "MN", "category": "respiratory"},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["module"] == "RegionalHealthPulse"
    assert payload["region"] == "MN"
    assert payload["category"] == "respiratory"
    assert payload["source_id"] == "regional_health_pulse_demo"
    assert payload["record_count"] == 2
    assert payload["latest_value"] == 46
    assert payload["previous_value"] == 32
    assert payload["signal"]["trend_label"] == "Increasing"
    assert payload["signal"]["review_priority"] == "Watch"
    assert payload["audit"]["module"] == "RegionalHealthPulse"
    assert payload["audit"]["source_id"] == "regional_health_pulse_demo"
    assert payload["audit"]["upstream_status"] == "success"
    assert payload["audit"]["record_count"] == 2
    assert payload["audit"]["transform_version"] == "regional-health-transform-v0.1"
    assert payload["audit"]["source_snapshot_status"] in {"saved", "skipped", "error"}
    assert "not medical advice" in payload["disclaimer"]


def test_regional_health_search_handles_no_demo_records():
    response = client.get(
        "/api/v1/regional-health/search",
        params={"region": "TX", "category": "respiratory"},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["record_count"] == 0
    assert payload["latest_value"] is None
    assert payload["signal"]["trend_label"] == "Insufficient data"
    assert payload["audit"]["upstream_status"] == "empty"
    assert payload["audit"]["record_count"] == 0


def test_regional_health_search_validates_required_inputs():
    response = client.get("/api/v1/regional-health/search")

    assert response.status_code == 422
