import json
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.search_workflows import real_world_safety_search
from app.services.safety_source_adapters import cpsc as cpsc_adapter
from app.sources.registry import (
    CPSC_RECALLS_API,
    CDC_FOODBORNE_OUTBREAKS,
    CDC_VAERS,
    DAILYMED_SPL_API,
    FDA_RECALLS_MARKET_WITHDRAWALS_SAFETY_ALERTS,
    FDA_SAFETY_COMMUNICATIONS,
    OPENFDA_DRUG_ENFORCEMENT,
    OPENFDA_DRUG_LABEL,
    OPENFDA_DEVICE_ENFORCEMENT,
    OPENFDA_FOOD_ENFORCEMENT,
    OPENFDA_NDC_DIRECTORY,
    RXNORM_RXNAV_API,
    USDA_FSIS_RECALL,
)


client = TestClient(app)
FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "real_world_safety"
TEST_FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
CPSC_RECALL_SEARCH_FIXTURE_PATH = TEST_FIXTURES_DIR / "cpsc_recall_search_fixture.json"
NO_MATCH_EXPLANATION = (
    "No matching public record was found in the checked U.S. sources. "
    "This does not certify that the product is safe."
)


SOURCE_KIND_VALUES = {"structured_api", "public_notice", "normalized_public_notice"}


def _assert_checked_source_contract(source):
    assert source["source_id"]
    assert source["source_name"]
    assert source["source_type"]
    assert source["source_url"]
    assert source["source_kind"] in SOURCE_KIND_VALUES
    assert source["upstream_status"]
    assert isinstance(source["record_count"], int)
    assert source["record_count"] >= 0


def _assert_failed_source_contract(source):
    assert source["source_id"]
    assert source["source_name"]
    assert source["source_type"]
    assert source["source_url"]
    assert source["source_kind"] in SOURCE_KIND_VALUES
    assert source["error_type"]
    assert source["reason"]


def _assert_source_audit_contract(audit):
    assert audit["audit_id"]
    assert audit["source_id"]
    assert audit["source_name"]
    assert audit["module"] == "RealWorldSafety"
    assert audit["upstream_status"]
    assert isinstance(audit["record_count"], int)
    assert audit["record_count"] >= 0
    assert audit["transform_version"]


def _assert_source_freshness_contract(freshness, *, expected_checked_at):
    assert freshness["source_id"]
    assert freshness["source_name"]
    assert freshness["source_type"]
    assert freshness["source_kind"] in SOURCE_KIND_VALUES
    assert freshness["upstream_status"]
    assert isinstance(freshness["record_count"], int)
    assert freshness["record_count"] >= 0
    assert freshness["freshness_status"]
    assert freshness["user_label"]
    assert freshness["explanation"]
    assert freshness["checked_at"] == expected_checked_at


def _assert_real_world_source_health_contract(body):
    checked_source_ids = {source["source_id"] for source in body["sources_checked"]}
    failed_source_ids = {source["source_id"] for source in body["sources_failed"]}
    freshness_source_ids = {freshness["source_id"] for freshness in body["source_freshness"]}

    assert checked_source_ids or failed_source_ids
    assert freshness_source_ids == checked_source_ids | failed_source_ids

    for source in body["sources_checked"]:
        _assert_checked_source_contract(source)

    for source in body["sources_failed"]:
        _assert_failed_source_contract(source)

    for audit in body["source_audits"]:
        _assert_source_audit_contract(audit)

    for freshness in body["source_freshness"]:
        _assert_source_freshness_contract(
            freshness,
            expected_checked_at=body["retrieval_timestamp"],
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
    monkeypatch.setattr(cpsc_adapter, "DAILY_RECORDS_PATH", CPSC_RECALL_SEARCH_FIXTURE_PATH)

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
        assert result["source_kind"] in {"public_notice", "normalized_public_notice"}
        if result["source_kind"] == "normalized_public_notice":
            assert result["extraction_confidence"] in {"high", "medium", "low"}
            assert result["source_text_excerpt"]
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
        "local:data/safety_sources/drug/openfda_drug_curated_records.json",
    }


@pytest.mark.parametrize(
    ("query", "expected_source", "expected_text"),
    [
        ("Tylenol", "RxNorm/RxNav API", "RXCUI"),
        ("acetaminophen", "openFDA NDC Directory API", "openFDA NDC listing"),
        ("glucose meter", "openFDA Device Enforcement API", "Blood Glucose"),
        ("insulin pump", "openFDA Device Enforcement API", "Insulin pump"),
        ("insulin pump", "openFDA UDI Directory API", "openFDA UDI listing"),
        ("glucose meter", "openFDA UDI Directory API", "openFDA UDI listing"),
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



def test_real_world_safety_source_health_contract_accepts_failed_sources():
    body = {
        "retrieval_timestamp": "2026-06-30T18:00:00Z",
        "sources_checked": [
            {
                "source_id": "cpsc_recalls_api",
                "source_name": "CPSC Recalls API",
                "source_type": "live official API",
                "source_url": "https://www.saferproducts.gov/RestWebServices/Recall",
                "source_kind": "structured_api",
                "upstream_status": "success",
                "record_count": 1,
            }
        ],
        "sources_failed": [
            {
                "source_id": "fda_recalls_market_withdrawals_safety_alerts",
                "source_name": "FDA Recalls, Market Withdrawals & Safety Alerts",
                "source_type": "live official public page",
                "source_url": "https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts",
                "source_kind": "public_notice",
                "error_type": "upstream_unavailable",
                "reason": "Temporary upstream source issue.",
            }
        ],
        "source_audits": [
            {
                "audit_id": "audit-cpsc",
                "source_id": "cpsc_recalls_api",
                "source_name": "CPSC Recalls API",
                "module": "RealWorldSafety",
                "upstream_status": "success",
                "record_count": 1,
                "transform_version": "real-world-safety-v0.1",
                "source_snapshot_status": "stored",
                "source_pull_id": "pull-cpsc",
                "source_payload_hash": "hash-cpsc",
            }
        ],
        "source_freshness": [
            {
                "source_id": "cpsc_recalls_api",
                "source_name": "CPSC Recalls API",
                "source_type": "live official API",
                "source_kind": "structured_api",
                "upstream_status": "success",
                "record_count": 1,
                "freshness_status": "pulled_and_stored",
                "user_label": "Pulled and stored",
                "explanation": "DavAI checked this public source and stored audit metadata.",
                "source_snapshot_status": "stored",
                "source_pull_id": "pull-cpsc",
                "source_payload_hash": "hash-cpsc",
                "checked_at": "2026-06-30T18:00:00Z",
            },
            {
                "source_id": "fda_recalls_market_withdrawals_safety_alerts",
                "source_name": "FDA Recalls, Market Withdrawals & Safety Alerts",
                "source_type": "live official public page",
                "source_kind": "public_notice",
                "upstream_status": "error",
                "record_count": 0,
                "freshness_status": "source_issue_reported",
                "user_label": "Source issue reported",
                "explanation": "Temporary upstream source issue.",
                "source_snapshot_status": None,
                "source_pull_id": None,
                "source_payload_hash": None,
                "checked_at": "2026-06-30T18:00:00Z",
            },
        ],
    }

    _assert_real_world_source_health_contract(body)


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
    assert result["source_type"] == "API"
    assert result["source_kind"] == "structured_api"
    assert result["category"] == "Vehicle recall"
    assert result["product_name"] == "2018 TOYOTA CAMRY"
    assert result["recall_number"] == "18V200000"
    assert result["brand_name"] == "TOYOTA"
    assert result["hazard_type"] == "ENGINE AND ENGINE COOLING"
    assert "stall" in result["reason"].lower()
    assert "repair" in result["remedy"].lower()

    identifier_check = body["identifier_check"]
    assert identifier_check["detected"] == []
    assert identifier_check["user_message"].startswith("Verify exact identifiers")
    assert {
        "type": "campaign_number",
        "label": "NHTSA campaign number",
        "value": "18V200000",
        "source": "NHTSA Recalls API / datasets",
        "reason": "Match this official record number before acting on the result.",
    } in identifier_check["to_verify"]
    assert any(
        item["type"] == "model" and item["value"] == "2018 TOYOTA CAMRY"
        for item in identifier_check["to_verify"]
    )

    nhtsa_audits = [
        audit
        for audit in body["source_audits"]
        if audit["source_id"] == "nhtsa_recalls_api_datasets"
    ]
    assert nhtsa_audits
    assert nhtsa_audits[0]["source_snapshot_status"] == "stored"
    assert nhtsa_audits[0]["source_payload_hash"] == "test-hash-nhtsa_recalls_api_datasets"


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
    assert body["results"][0]["source_name"] == "NHTSA Recalls API / datasets"
    assert body["results"][0]["source_kind"] == "structured_api"
    assert body["results"][0]["product_name"] == "2018 TOYOTA CAMRY"
    assert body["results"][0]["recall_number"] == "18V200000"

    assert {
        "type": "vin",
        "label": "VIN",
        "value": "4T1B11HK5JU000001",
        "source": "query",
        "reason": "Use this VIN to verify the exact vehicle and recall campaign on the official NHTSA page.",
    } in body["identifier_check"]["detected"]
    assert any(
        item["type"] == "campaign_number" and item["value"] == "18V200000"
        for item in body["identifier_check"]["to_verify"]
    )

    audit_source_ids = {audit["source_id"] for audit in body["source_audits"]}
    assert "nhtsa_vpic_vin_decoder_api" in audit_source_ids
    assert "nhtsa_recalls_api_datasets" in audit_source_ids


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
    assert body["search_plan"]["intent"] == "unknown"
    assert set(body["search_plan"]["sources_to_check"]) == {
        CPSC_RECALLS_API["source_id"],
        FDA_RECALLS_MARKET_WITHDRAWALS_SAFETY_ALERTS["source_id"],
        OPENFDA_FOOD_ENFORCEMENT["source_id"],
        OPENFDA_DRUG_ENFORCEMENT["source_id"],
        OPENFDA_DEVICE_ENFORCEMENT["source_id"],
    }
    assert {source["source_id"] for source in body["sources_checked"]} == set(
        body["search_plan"]["sources_to_check"]
    )
    _assert_real_world_source_health_contract(body)


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
    _assert_real_world_source_health_contract(body)


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


def test_real_world_safety_returns_intelligence_summary_for_reference_only_drug(monkeypatch):
    _patch_persistence(monkeypatch)
    _patch_public_source_http(monkeypatch)

    response = client.get("/api/v1/real-world-safety/search", params={"q": "acetaminophen", "limit": 25})

    assert response.status_code == 200
    body = response.json()
    summary = body["safety_intelligence_summary"]

    assert summary["query_type"] == "drug"
    assert summary["reference_or_label_found"] is True
    assert "openFDA NDC Directory API" in summary["matched_sources_by_role"]["reference_identity"]
    assert "DailyMed SPL API" in summary["matched_sources_by_role"]["label_reference"]
    assert "official identity or label reference records" in summary["plain_language_summary"]
    assert "does not invent missing recalls" in summary["caveat"]


def test_real_world_safety_returns_intelligence_summary_for_recall_match(monkeypatch):
    _patch_persistence(monkeypatch)
    _patch_public_source_http(monkeypatch)

    response = client.get("/api/v1/real-world-safety/search", params={"q": "Segway scooter", "limit": 10})

    assert response.status_code == 200
    body = response.json()
    summary = body["safety_intelligence_summary"]

    assert summary["query_type"] in {"consumer_product", "unknown"}
    assert summary["recall_or_enforcement_found"] is True
    assert "CPSC Recalls API" in summary["matched_sources_by_role"]["recall_enforcement"]
    assert "official recall/enforcement records" in summary["plain_language_summary"]
    assert summary["suggested_next_steps"]


def test_real_world_safety_query_understanding_corrects_typo_in_route(monkeypatch):
    _patch_persistence(monkeypatch)
    _patch_public_source_http(monkeypatch)

    response = client.get("/api/v1/real-world-safety/search", params={"q": "tylonal", "limit": 25})

    assert response.status_code == 200
    body = response.json()

    assert body["raw_query"] == "tylonal"
    assert body["query"] == "tylenol"
    assert body["query_understanding"]["normalized_query"] == "tylenol"
    assert body["query_understanding"]["search_query"] == "tylenol"
    assert "tylonal → tylenol" in body["query_understanding"]["corrections_applied"]
    assert "acetaminophen" in body["query_understanding"]["expanded_terms"]
    assert "drug" in body["query_understanding"]["query_type_hints"]
    assert body["total_matches"] >= 1


def test_real_world_safety_uses_expansion_search_terms_for_brand_generic_fallback(monkeypatch):
    _patch_persistence(monkeypatch)
    _patch_public_source_http(monkeypatch)

    response = client.get("/api/v1/real-world-safety/search", params={"q": "Advil", "limit": 25})

    assert response.status_code == 200
    body = response.json()

    assert body["query"] == "Advil"
    assert body["query_understanding"]["normalized_query"] == "advil"
    assert "ibuprofen" in body["query_understanding"]["expanded_terms"]
    assert "ibuprofen" in body["query_understanding"]["expansion_search_terms_used"]
    assert body["total_matches"] >= 1

    matched_sources = {
        record["source_name"]
        for record in body["results"]
    }
    assert {
        "RxNorm/RxNav API",
        "openFDA NDC Directory API",
        "DailyMed SPL API",
        "openFDA Drug Label API",
    } & matched_sources

    summary = body["safety_intelligence_summary"]
    assert any("ibuprofen" in explanation for explanation in summary["expansion_explanations"])
    assert any("ibuprofen" in step for step in summary["suggested_next_steps"])


def test_real_world_safety_microwave_checks_consumer_sources_without_drug_sources(monkeypatch):
    _patch_persistence(monkeypatch)
    _patch_public_source_http(monkeypatch)

    response = client.get("/api/v1/real-world-safety/search", params={"q": "microwave", "limit": 5})

    assert response.status_code == 200
    body = response.json()
    checked_source_ids = {source["source_id"] for source in body["sources_checked"]}

    assert body["search_plan"]["intent"] == "consumer_product"
    assert checked_source_ids == set(body["search_plan"]["sources_to_check"])
    assert CPSC_RECALLS_API["source_id"] in checked_source_ids
    assert {
        RXNORM_RXNAV_API["source_id"],
        DAILYMED_SPL_API["source_id"],
        OPENFDA_DRUG_LABEL["source_id"],
        OPENFDA_NDC_DIRECTORY["source_id"],
    }.isdisjoint(checked_source_ids)


def test_real_world_safety_advil_checks_drug_sources_without_cpsc(monkeypatch):
    _patch_persistence(monkeypatch)
    _patch_public_source_http(monkeypatch)

    response = client.get("/api/v1/real-world-safety/search", params={"q": "Advil", "limit": 25})

    assert response.status_code == 200
    body = response.json()
    checked_source_ids = {source["source_id"] for source in body["sources_checked"]}

    assert body["search_plan"]["intent"] == "drug"
    assert checked_source_ids == set(body["search_plan"]["sources_to_check"])
    assert {
        OPENFDA_DRUG_ENFORCEMENT["source_id"],
        RXNORM_RXNAV_API["source_id"],
        DAILYMED_SPL_API["source_id"],
        OPENFDA_DRUG_LABEL["source_id"],
        OPENFDA_NDC_DIRECTORY["source_id"],
    }.issubset(checked_source_ids)
    assert CPSC_RECALLS_API["source_id"] not in checked_source_ids


def test_real_world_safety_chicken_checks_food_sources_without_drug_label(monkeypatch):
    _patch_persistence(monkeypatch)
    _patch_public_source_http(monkeypatch)

    response = client.get("/api/v1/real-world-safety/search", params={"q": "chicken", "limit": 20})

    assert response.status_code == 200
    body = response.json()
    checked_source_ids = {source["source_id"] for source in body["sources_checked"]}

    assert body["search_plan"]["intent"] == "food"
    assert checked_source_ids == set(body["search_plan"]["sources_to_check"])
    assert {
        OPENFDA_FOOD_ENFORCEMENT["source_id"],
        USDA_FSIS_RECALL["source_id"],
        FDA_RECALLS_MARKET_WITHDRAWALS_SAFETY_ALERTS["source_id"],
    }.issubset(checked_source_ids)
    assert OPENFDA_DRUG_LABEL["source_id"] not in checked_source_ids


def test_real_world_safety_sunscreen_routes_to_drug_with_cosmetic_context(monkeypatch):
    _patch_persistence(monkeypatch)
    _patch_public_source_http(monkeypatch)

    response = client.get("/api/v1/real-world-safety/search", params={"q": "sunscreen", "limit": 5})

    assert response.status_code == 200
    body = response.json()

    assert body["search_plan"]["intent"] == "drug"
    assert body["search_plan"]["clarification_required"] is False
    assert OPENFDA_DRUG_ENFORCEMENT["source_id"] in body["search_plan"]["sources_to_check"]
    assert FDA_RECALLS_MARKET_WITHDRAWALS_SAFETY_ALERTS["source_id"] in body["search_plan"]["sources_to_check"]
    assert body["query_understanding"]["category_classification"]["primary_category"] == "drug"
    assert "cosmetic" in body["query_understanding"]["category_classification"]["secondary_categories"]
    assert body["query_understanding"]["category_classification"]["flags"]["cosmetic_possible"] is True

    checked_source_ids = {source["source_id"] for source in body["sources_checked"]}
    assert OPENFDA_DRUG_ENFORCEMENT["source_id"] in checked_source_ids
    assert FDA_RECALLS_MARKET_WITHDRAWALS_SAFETY_ALERTS["source_id"] in checked_source_ids
    assert body["sources_failed"] == []
    assert body["public_data_disclaimer"] == real_world_safety_search.PUBLIC_DATA_DISCLAIMER
    assert body["limitations"] == real_world_safety_search.LIMITATIONS


def test_real_world_safety_response_includes_source_freshness(monkeypatch):
    _patch_persistence(monkeypatch)
    _patch_public_source_http(monkeypatch)

    response = client.get(
        "/api/v1/real-world-safety/search",
        params={"q": "2018 Toyota Camry", "limit": 5},
    )

    assert response.status_code == 200
    body = response.json()

    nhtsa_freshness = [
        freshness
        for freshness in body["source_freshness"]
        if freshness["source_id"] == "nhtsa_recalls_api_datasets"
    ]

    assert len(nhtsa_freshness) == 1
    assert nhtsa_freshness[0]["source_name"] == "NHTSA Recalls API / datasets"
    assert nhtsa_freshness[0]["freshness_status"] == "pulled_and_stored"
    assert nhtsa_freshness[0]["user_label"] == "Pulled and stored"
    assert nhtsa_freshness[0]["upstream_status"] == "success"
    assert nhtsa_freshness[0]["record_count"] == 1
    assert nhtsa_freshness[0]["source_snapshot_status"] == "stored"
    assert nhtsa_freshness[0]["source_pull_id"]
    assert nhtsa_freshness[0]["source_payload_hash"] == "test-hash-nhtsa_recalls_api_datasets"
    assert nhtsa_freshness[0]["checked_at"] == body["retrieval_timestamp"]
    assert "stored audit metadata" in nhtsa_freshness[0]["explanation"]
    _assert_real_world_source_health_contract(body)


def test_real_world_safety_udi_identifier_routes_to_device_identity(monkeypatch):
    _patch_persistence(monkeypatch)
    _patch_public_source_http(monkeypatch)

    response = client.get(
        "/api/v1/real-world-safety/search",
        params={"q": "UDI 00312345678901", "limit": 10},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["query_understanding"]["detected_identifiers"]["udi"] == "00312345678901"
    assert "openFDA UDI Directory API" in {source["source_name"] for source in body["sources_checked"]}

    result = next(
        record
        for record in body["results"]
        if record["source_name"] == "openFDA UDI Directory API"
    )

    assert result["category"] == "Medical device reference / UDI directory"
    assert result["hazard_type"] == "Reference record, not a recall"
    assert result["recall_number"] == "00312345678901"
    assert "device identity/reference record" in result["reason"]
    assert "verify the exact device" in result["remedy"]
    assert "00312345678901" in result["affected_lots"]

    assert any(
        item["type"] == "udi" and item["value"] == "00312345678901"
        for item in body["identifier_check"]["detected"]
    )
    assert any(
        freshness["source_id"] == "openfda_udi_directory"
        and freshness["freshness_status"] == "pulled_and_stored"
        for freshness in body["source_freshness"]
    )


def test_real_world_safety_vaccine_query_returns_vaers_signal_report(monkeypatch):
    _patch_persistence(monkeypatch)
    _patch_public_source_http(monkeypatch)

    response = client.get(
        "/api/v1/real-world-safety/search",
        params={"q": "MMR vaccine rash", "limit": 10},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["search_plan"]["intent"] == "vaccine"
    assert "CDC/VAERS Vaccine Adverse Event Reports" in {
        source["source_name"] for source in body["sources_checked"]
    }

    result = next(
        record
        for record in body["results"]
        if record["source_name"] == "CDC/VAERS Vaccine Adverse Event Reports"
    )

    assert result["category"] == "Vaccine adverse-event signal report"
    assert result["hazard_type"] == "Reported adverse-event signal, not proof of causation"
    assert result["recall_number"] == "VAERS-DEMO-0002"
    assert "does not prove causation" in result["reason"]
    assert "public signal reports only" in result["remedy"]

    summary = body["safety_intelligence_summary"]
    assert summary["signal_report_found"] is True
    assert "CDC/VAERS Vaccine Adverse Event Reports" in summary["matched_sources_by_role"]["signal_report"]

    assert any(
        freshness["source_id"] == "cdc_vaers"
        and freshness["freshness_status"] == "pulled_and_stored"
        for freshness in body["source_freshness"]
    )


def test_real_world_safety_foodborne_outbreak_context_source(monkeypatch):
    _patch_persistence(monkeypatch)
    _patch_public_source_http(monkeypatch)

    response = client.get(
        "/api/v1/real-world-safety/search",
        params={"q": "Salmonella outbreak peanut butter", "limit": 10},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["search_plan"]["intent"] == "food"
    assert "CDC/FDA Foodborne Outbreak Investigation Context" in {
        source["source_name"] for source in body["sources_checked"]
    }

    result = next(
        record
        for record in body["results"]
        if record["source_name"] == "CDC/FDA Foodborne Outbreak Investigation Context"
    )

    assert result["category"] == "Foodborne outbreak / investigation context"
    assert result["hazard_type"] == "Salmonella"
    assert result["recall_number"] == "CDC-FOODBORNE-DEMO-0001"
    assert "not automatically a formal recall" in result["reason"]
    assert "public-health investigation context only" in result["remedy"]

    summary = body["safety_intelligence_summary"]
    assert summary["query_type"] == "food"
    assert summary["outbreak_context_found"] is True
    assert "CDC/FDA Foodborne Outbreak Investigation Context" in summary["matched_sources_by_role"]["outbreak_context"]

    assert any(
        freshness["source_id"] == "cdc_foodborne_outbreaks"
        and freshness["freshness_status"] == "pulled_and_stored"
        for freshness in body["source_freshness"]
    )


def test_real_world_safety_fda_safety_communication_source(monkeypatch):
    _patch_persistence(monkeypatch)
    _patch_public_source_http(monkeypatch)

    response = client.get(
        "/api/v1/real-world-safety/search",
        params={"q": "FDA safety communication insulin pump", "limit": 10},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["search_plan"]["intent"] == "medical_device"
    assert "FDA Medical Device Safety Communications" in {
        source["source_name"] for source in body["sources_checked"]
    }

    result = next(
        record
        for record in body["results"]
        if record["source_name"] == "FDA Medical Device Safety Communications"
    )

    assert result["category"] == "FDA safety communication / advisory context"
    assert result["recall_number"] == "FDA-SAFETY-COMM-DEMO-0002"
    assert "not automatically a recall" in result["reason"]
    assert "official FDA safety communication" in result["remedy"]

    assert any(
        freshness["source_id"] == "fda_safety_communications"
        and freshness["freshness_status"] == "pulled_and_stored"
        for freshness in body["source_freshness"]
    )