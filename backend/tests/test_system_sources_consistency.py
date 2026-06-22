from fastapi.testclient import TestClient

from app.main import app
from app.sources.registry import REGISTERED_SOURCES


client = TestClient(app)


def test_system_status_registered_count_matches_shared_registry(monkeypatch):
    monkeypatch.setattr("app.routes.system.is_database_configured", lambda: False)

    response = client.get("/api/v1/system/status")

    assert response.status_code == 200
    assert response.json()["sources"]["registered_count"] == len(REGISTERED_SOURCES)


def test_data_quality_source_registry_count_matches_shared_registry(monkeypatch):
    monkeypatch.setattr("app.routes.system.is_database_configured", lambda: False)

    response = client.get("/api/v1/system/data-quality")

    assert response.status_code == 200
    assert response.json()["source_registry_count"] == len(REGISTERED_SOURCES)


def test_sources_route_count_and_ids_match_shared_registry():
    response = client.get("/api/v1/sources")

    assert response.status_code == 200

    body = response.json()
    expected_source_ids = {source["source_id"] for source in REGISTERED_SOURCES}
    actual_source_ids = {source["source_id"] for source in body["sources"]}

    assert body["count"] == len(REGISTERED_SOURCES)
    assert actual_source_ids == expected_source_ids
    assert actual_source_ids == {
        "openfda_drug_enforcement",
        "openfda_drug_event",
            "rxnorm_rxnav_api",
            "dailymed_spl_api",
            "openfda_device_enforcement",
            "openfda_device_event",
        "openfda_cosmetic_event",
        "openfda_food_enforcement",
        "usda_fsis_recall",
        "foodradar_multi_source",
        "fda_recalls_market_withdrawals_safety_alerts",
        "cpsc_recalls_api",
        "nhtsa_vpic_vin_decoder_api",
        "nhtsa_recalls_api_datasets",
        "regional_health_pulse_demo",
    }
