import json
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.search_workflows import real_world_safety_search


client = TestClient(app)
FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "real_world_safety"
NO_MATCH_EXPLANATION = (
    "No matching public record was found in the checked U.S. sources. "
    "This does not certify that the product is safe."
)


def _load_json(name: str):
    return json.loads((FIXTURE_ROOT / name).read_text())


def _load_text(name: str) -> str:
    return (FIXTURE_ROOT / name).read_text()


def _response(url: str, *, status_code: int = 200, json_body=None, text: str | None = None):
    request = httpx.Request("GET", url)
    if json_body is not None:
        return httpx.Response(status_code, json=json_body, request=request)
    return httpx.Response(status_code, text=text or "", request=request)


def _patch_persistence(monkeypatch):
    def fake_save_audit_event(audit_event, request_id=None):
        return audit_event

    def fake_source_pull(*, audit_event, raw_payload, request_id=None):
        return {
            "status": "stored",
            "pull_id": f"test-pull-{audit_event['source_id']}",
            "payload_hash": f"test-hash-{audit_event['source_id']}",
        }

    monkeypatch.setattr(real_world_safety_search, "save_audit_event", fake_save_audit_event)
    monkeypatch.setattr(real_world_safety_search, "save_source_pull_with_snapshot", fake_source_pull)


def _patch_public_source_http(monkeypatch):
    cpsc_payload = _load_json("cpsc_recalls.json")
    fda_html = _load_text("fda_public_recalls.html")
    nhtsa_payload = _load_json("nhtsa_recalls.json")
    vpic_payload = _load_json("vpic_decode_toyota_camry.json")

    async def fake_get(self, url, params=None):
        url_text = str(url)
        if "saferproducts.gov" in url_text:
            return _response(url_text, json_body=cpsc_payload)
        if "fda.gov/safety/recalls-market-withdrawals-safety-alerts" in url_text:
            return _response(url_text, text=fda_html)
        if "vpic.nhtsa.dot.gov" in url_text:
            return _response(url_text, json_body=vpic_payload)
        if "api.nhtsa.gov/recalls/recallsByVehicle" in url_text:
            return _response(url_text, json_body=nhtsa_payload)
        raise AssertionError(f"Unexpected URL in real-world safety test: {url_text}")

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)


@pytest.mark.parametrize(
    ("query", "expected_source", "expected_text"),
    [
        ("Samsung washing machine", "CPSC Recalls API", "Samsung Recalls Top-Load Washing Machines"),
        ("air fryer", "CPSC Recalls API", "Insignia® Air Fryers"),
        ("Segway scooter", "CPSC Recalls API", "Segway"),
        ("Fry Pie Factory", "FDA Recalls, Market Withdrawals & Safety Alerts", "Fry Pie Factory"),
        ("Pepperoni Rolls", "FDA Recalls, Market Withdrawals & Safety Alerts", "Pepperoni Rolls"),
    ],
)
def test_real_world_safety_product_and_fda_public_notice_searches(
    monkeypatch,
    query,
    expected_source,
    expected_text,
):
    _patch_persistence(monkeypatch)
    _patch_public_source_http(monkeypatch)

    response = client.get("/api/v1/real-world-safety/search", params={"q": query, "limit": 5})

    assert response.status_code == 200
    body = response.json()

    assert body["query"] == query
    assert body["total_matches"] >= 1
    assert body["count"] == body["total_matches"]
    assert body["no_match_explanation"] is None
    assert body["sources_failed"] == []
    assert body["source_audits"]
    assert "CPSC Recalls API" in {source["source_name"] for source in body["sources_checked"]}
    assert "FDA Recalls, Market Withdrawals & Safety Alerts" in {
        source["source_name"] for source in body["sources_checked"]
    }

    result = next(record for record in body["results"] if record["source_name"] == expected_source)
    searchable = " ".join(
        str(value)
        for value in (
            result["product_name"],
            result["brand_name"],
            result["company_name"],
            result["title"],
        )
        if value
    )
    assert expected_text in searchable

    if expected_source == "FDA Recalls, Market Withdrawals & Safety Alerts":
        assert body["public_notice_matches"] >= 1
        assert result["source_kind"] == "public_notice"
    else:
        assert body["structured_api_matches"] >= 1
        assert result["source_kind"] == "structured_api"



@pytest.mark.parametrize(
    ("query", "expected_source", "expected_text"),
    [
        ("undeclared milk", "openFDA Food Enforcement API", "undeclared milk"),
        ("eye drops", "openFDA Drug Enforcement API", "Eye Drops"),
        ("metformin", "openFDA Drug Enforcement API", "Metformin"),
    ],
)
def test_real_world_safety_curated_official_openfda_sources(
    monkeypatch,
    query,
    expected_source,
    expected_text,
):
    _patch_persistence(monkeypatch)
    _patch_public_source_http(monkeypatch)

    response = client.get("/api/v1/real-world-safety/search", params={"q": query, "limit": 5})

    assert response.status_code == 200
    body = response.json()

    checked_sources = {source["source_name"] for source in body["sources_checked"]}
    assert expected_source in checked_sources
    assert body["sources_failed"] == []
    assert body["structured_api_matches"] >= 1
    assert body["total_matches"] >= 1

    source_entry = next(source for source in body["sources_checked"] if source["source_name"] == expected_source)
    assert source_entry["source_kind"] == "structured_api"
    assert source_entry["source_type"] == "local curated official snapshot"
    assert source_entry["record_count"] >= 1

    result = next(record for record in body["results"] if record["source_name"] == expected_source)
    searchable = " ".join(
        str(value)
        for value in (
            result["product_name"],
            result["company_name"],
            result["title"],
            result["reason"],
            result["recall_number"],
        )
        if value
    )

    assert expected_text.lower() in searchable.lower()
    assert result["source_kind"] == "structured_api"
    assert result["source_type"] == "local curated official snapshot"
    assert result["record_url"] in {
        "https://api.fda.gov/food/enforcement.json",
        "https://api.fda.gov/drug/enforcement.json",
    }



@pytest.mark.parametrize(
    ("query", "expected_source", "expected_text"),
    [
        ("Tylenol", "RxNorm/RxNav API", "RXCUI"),
        ("acetaminophen", "DailyMed SPL API", "DailyMed official label"),
        ("glucose meter", "openFDA Device Enforcement API", "Blood Glucose"),
        ("insulin pump", "openFDA Device Enforcement API", "Insulin pump"),
        ("CPAP", "openFDA Device Enforcement API", "CPAP"),
    ],
)
def test_real_world_safety_drug_reference_and_device_sources(
    monkeypatch,
    query,
    expected_source,
    expected_text,
):
    _patch_persistence(monkeypatch)
    _patch_public_source_http(monkeypatch)

    response = client.get("/api/v1/real-world-safety/search", params={"q": query, "limit": 25})

    assert response.status_code == 200
    body = response.json()

    checked_sources = {source["source_name"] for source in body["sources_checked"]}
    assert expected_source in checked_sources
    assert body["sources_failed"] == []
    assert body["structured_api_matches"] >= 1
    assert body["total_matches"] >= 1

    source_entry = next(source for source in body["sources_checked"] if source["source_name"] == expected_source)
    assert source_entry["source_kind"] == "structured_api"
    assert source_entry["source_type"] == "local curated official snapshot"
    assert source_entry["record_count"] >= 1

    matching_results = [
        record
        for record in body["results"]
        if record["source_name"] == expected_source
    ]
    assert matching_results

    searchable = " ".join(
        str(value)
        for record in matching_results
        for value in (
            record["product_name"],
            record["company_name"],
            record["title"],
            record["reason"],
            record["recall_number"],
            record["hazard_type"],
        )
        if value
    )

    assert expected_text.lower() in searchable.lower()
    assert all(record["source_kind"] == "structured_api" for record in matching_results)
    assert all(record["source_type"] == "local curated official snapshot" for record in matching_results)




@pytest.mark.parametrize(
    ("query", "expected_text"),
    [
        ("heater", "Fire Hazard"),
        ("baby stroller", "Stroller"),
        ("bicycle helmet", "Bicycle Helmets"),
    ],
)
def test_real_world_safety_cpsc_daily_product_snapshot(
    monkeypatch,
    query,
    expected_text,
):
    _patch_persistence(monkeypatch)
    _patch_public_source_http(monkeypatch)

    response = client.get("/api/v1/real-world-safety/search", params={"q": query, "limit": 10})

    assert response.status_code == 200
    body = response.json()

    checked_sources = {source["source_name"] for source in body["sources_checked"]}
    assert "CPSC Recalls API" in checked_sources
    assert body["sources_failed"] == []

    source_entry = next(
        source
        for source in body["sources_checked"]
        if source["source_name"] == "CPSC Recalls API"
    )
    assert source_entry["source_kind"] == "structured_api"
    assert source_entry["source_url"] == "local:data/safety_sources/cpsc/cpsc_daily_products_curated_records.json"
    assert source_entry["record_count"] >= 1

    matching_results = [
        record
        for record in body["results"]
        if record["source_name"] == "CPSC Recalls API"
    ]
    assert matching_results

    searchable = " ".join(
        str(value)
        for record in matching_results
        for value in (
            record["title"],
            record["product_name"],
            record["reason"],
            record["hazard_type"],
            record["remedy"],
        )
        if value
    )

    assert expected_text.lower() in searchable.lower()
    assert all(record["source_kind"] == "structured_api" for record in matching_results)


@pytest.mark.parametrize(
    ("query", "expected_text"),
    [
        ("insulin pump", "openFDA device event report"),
        ("glucose meter", "openFDA device event report"),
        ("ventilator", "openFDA device event report"),
    ],
)
def test_real_world_safety_device_event_source(
    monkeypatch,
    query,
    expected_text,
):
    _patch_persistence(monkeypatch)
    _patch_public_source_http(monkeypatch)

    response = client.get("/api/v1/real-world-safety/search", params={"q": query, "limit": 10})

    assert response.status_code == 200
    body = response.json()

    checked_sources = {source["source_name"] for source in body["sources_checked"]}
    assert "openFDA Device Event API" in checked_sources
    assert body["sources_failed"] == []

    source_entry = next(
        source
        for source in body["sources_checked"]
        if source["source_name"] == "openFDA Device Event API"
    )
    assert source_entry["source_kind"] == "structured_api"
    assert source_entry["source_type"] == "local curated official snapshot"
    assert source_entry["record_count"] >= 1

    matching_results = [
        record
        for record in body["results"]
        if record["source_name"] == "openFDA Device Event API"
    ]
    assert matching_results

    searchable = " ".join(
        str(value)
        for record in matching_results
        for value in (
            record["title"],
            record["product_name"],
            record["brand_name"],
            record["company_name"],
            record["reason"],
            record["hazard_type"],
            record["remedy"],
        )
        if value
    )

    assert expected_text.lower() in searchable.lower()
    assert "not recalls or proof of causation" in searchable.lower()
    assert all(record["source_kind"] == "structured_api" for record in matching_results)
    assert all(record["source_type"] == "local curated official snapshot" for record in matching_results)



def test_real_world_safety_vehicle_query_uses_nhtsa_recalls(monkeypatch):
    _patch_persistence(monkeypatch)
    _patch_public_source_http(monkeypatch)

    response = client.get("/api/v1/real-world-safety/search", params={"q": "2018 Toyota Camry", "limit": 5})

    assert response.status_code == 200
    body = response.json()

    assert body["total_matches"] == 1
    assert body["structured_api_matches"] == 1
    assert body["public_notice_matches"] == 0
    assert "NHTSA Recalls API / datasets" in {source["source_name"] for source in body["sources_checked"]}

    result = body["results"][0]
    assert result["source_name"] == "NHTSA Recalls API / datasets"
    assert result["product_name"] == "2018 TOYOTA CAMRY"
    assert result["recall_number"] == "18V200000"
    assert result["brand_name"] == "TOYOTA"


def test_real_world_safety_vin_input_decodes_vehicle_before_recall_search(monkeypatch):
    _patch_persistence(monkeypatch)
    _patch_public_source_http(monkeypatch)

    response = client.get(
        "/api/v1/real-world-safety/search",
        params={"q": "4T1B11HK5JU000001", "limit": 5},
    )

    assert response.status_code == 200
    body = response.json()

    checked_names = {source["source_name"] for source in body["sources_checked"]}
    assert "NHTSA vPIC VIN Decoder API" in checked_names
    assert "NHTSA Recalls API / datasets" in checked_names
    assert body["total_matches"] == 1
    assert body["results"][0]["product_name"] == "2018 TOYOTA CAMRY"
    assert body["results"][0]["recall_number"] == "18V200000"


def test_real_world_safety_no_match_response_does_not_certify_safety(monkeypatch):
    _patch_persistence(monkeypatch)
    _patch_public_source_http(monkeypatch)

    response = client.get(
        "/api/v1/real-world-safety/search",
        params={"q": "unlikely product xyz", "limit": 5},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["total_matches"] == 0
    assert body["results"] == []
    assert body["no_match_explanation"] == NO_MATCH_EXPLANATION
    assert body["sources_failed"] == []
    assert body["structured_api_matches"] == 0
    assert body["public_notice_matches"] == 0


def old_test_real_world_safety_returns_partial_results_when_one_source_fails(monkeypatch):
    _patch_persistence(monkeypatch)
    fda_html = _load_text("fda_public_recalls.html")

    async def fake_get(self, url, params=None):
        url_text = str(url)
        if "saferproducts.gov" in url_text:
            return _response(url_text, status_code=503, text="CPSC unavailable")
        if "fda.gov/safety/recalls-market-withdrawals-safety-alerts" in url_text:
            return _response(url_text, text=fda_html)
        raise AssertionError(f"Unexpected URL in real-world safety failure test: {url_text}")

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    response = client.get(
        "/api/v1/real-world-safety/search",
        params={"q": "Fry Pie Factory", "limit": 5},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["total_matches"] == 1
    assert body["results"][0]["source_name"] == "FDA Recalls, Market Withdrawals & Safety Alerts"
    assert body["sources_failed"]
    assert body["sources_failed"][0]["source_name"] == "CPSC Recalls API"
    assert body["sources_failed"][0]["reason"]
    assert "FDA Recalls, Market Withdrawals & Safety Alerts" in {
        source["source_name"] for source in body["sources_checked"]
    }
    assert any(audit["source_id"] == "cpsc_recalls_api" for audit in body["source_audits"])


@pytest.mark.parametrize(
    ("query", "expected_text"),
    [
        ("meatloaf", "USDA FSIS"),
        ("chicken", "USDA FSIS"),
        ("beef", "USDA FSIS"),
    ],
)
def test_real_world_safety_usda_fsis_recall_source(
    monkeypatch,
    query,
    expected_text,
):
    _patch_persistence(monkeypatch)
    _patch_public_source_http(monkeypatch)

    response = client.get("/api/v1/real-world-safety/search", params={"q": query, "limit": 20})

    assert response.status_code == 200
    body = response.json()

    checked_sources = {source["source_name"] for source in body["sources_checked"]}
    assert "USDA FSIS Recall API" in checked_sources
    assert body["sources_failed"] == []

    source_entry = next(
        source
        for source in body["sources_checked"]
        if source["source_name"] == "USDA FSIS Recall API"
    )
    assert source_entry["source_kind"] == "structured_api"
    assert source_entry["source_type"] == "local curated official snapshot"
    assert source_entry["record_count"] >= 1

    matching_results = [
        record
        for record in body["results"]
        if record["source_name"] == "USDA FSIS Recall API"
    ]
    assert matching_results

    searchable = " ".join(
        str(value)
        for record in matching_results
        for value in (
            record["title"],
            record["product_name"],
            record["company_name"],
            record["reason"],
            record["hazard_type"],
            record["remedy"],
        )
        if value
    )

    assert expected_text.lower() in searchable.lower()
    assert all(record["source_kind"] == "structured_api" for record in matching_results)
    assert all(record["source_type"] == "local curated official snapshot" for record in matching_results)
