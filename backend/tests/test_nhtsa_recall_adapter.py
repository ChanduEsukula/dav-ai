from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from app.services.safety_source_adapters.nhtsa import (
    NHTSARecallsAdapter,
    NHTSAVPICAdapter,
    VehicleIdentity,
    _extract_nhtsa_recall_records,
    _extract_vehicle_identity,
    _normalize_nhtsa_recall,
)


FIXTURE_PATH = Path("backend/tests/fixtures/real_world_safety/nhtsa_recalls.json")


def load_fixture() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_extract_nhtsa_recall_records_from_results_payload() -> None:
    payload = load_fixture()

    records = _extract_nhtsa_recall_records(payload)

    assert len(records) == 1
    assert records[0]["NHTSACampaignNumber"] == "18V200000"


def test_normalize_nhtsa_recall_preserves_vehicle_recall_fields() -> None:
    payload = load_fixture()
    raw_record = _extract_nhtsa_recall_records(payload)[0]
    vehicle = VehicleIdentity(make="Toyota", model="Camry", model_year="2018")

    normalized = _normalize_nhtsa_recall(
        record=raw_record,
        vehicle=vehicle,
        retrieved_at="2026-06-24T00:00:00+00:00",
        source_name="NHTSA Recalls API / datasets",
        source_url="https://api.nhtsa.gov/recalls/recallsByVehicle",
    )

    assert normalized.source_name == "NHTSA Recalls API / datasets"
    assert normalized.source_type == "API"
    assert normalized.source_kind == "structured_api"
    assert normalized.category == "Vehicle recall"
    assert normalized.product_name == "2018 TOYOTA CAMRY"
    assert normalized.brand_name == "TOYOTA"
    assert normalized.company_name == "Toyota Motor Engineering & Manufacturing"
    assert normalized.recall_number == "18V200000"
    assert normalized.published_date == "20180328"
    assert normalized.hazard_type == "ENGINE AND ENGINE COOLING"
    assert "stall" in (normalized.reason or "").lower()
    assert "repair" in (normalized.remedy or "").lower()
    assert normalized.record_url == "https://www.nhtsa.gov/recalls"
    assert normalized.raw_payload_hash


def test_extract_vehicle_identity_from_vpic_payload() -> None:
    payload = {
        "Results": [
            {
                "Make": "HONDA",
                "Model": "CIVIC",
                "ModelYear": "2020",
            }
        ]
    }

    vehicle = _extract_vehicle_identity(payload, "2HGFC2F59LH000000")

    assert vehicle is not None
    assert vehicle.make == "HONDA"
    assert vehicle.model == "CIVIC"
    assert vehicle.model_year == "2020"
    assert vehicle.vin == "2HGFC2F59LH000000"


def test_nhtsa_recalls_adapter_searches_vehicle_recalls(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = load_fixture()

    class FakeResponse:
        status_code = 200

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return payload

    class FakeAsyncClient:
        def __init__(self, timeout: float):
            self.timeout = timeout

        async def __aenter__(self) -> "FakeAsyncClient":
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

        async def get(self, endpoint: str, params: dict[str, str]) -> FakeResponse:
            assert endpoint == "https://api.nhtsa.gov/recalls/recallsByVehicle"
            assert params == {
                "make": "Toyota",
                "model": "Camry",
                "modelYear": "2018",
            }
            return FakeResponse()

    monkeypatch.setattr(
        "app.services.safety_source_adapters.nhtsa.httpx.AsyncClient",
        FakeAsyncClient,
    )

    adapter = NHTSARecallsAdapter()
    result = asyncio.run(
        adapter.search_vehicle_recalls(
            vehicle=VehicleIdentity(make="Toyota", model="Camry", model_year="2018"),
            limit=5,
            request_id="test-request",
        )
    )

    assert result.source_id == "nhtsa_recalls_api_datasets"
    assert result.source_name == "NHTSA Recalls API / datasets"
    assert result.source_kind == "structured_api"
    assert result.upstream_status == "success"
    assert len(result.records) == 1
    assert result.records[0].recall_number == "18V200000"
    assert result.context == {
        "vehicle_identity": {
            "make": "Toyota",
            "model": "Camry",
            "model_year": "2018",
            "vin": None,
        }
    }


def test_nhtsa_vpic_adapter_decodes_vin(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "Results": [
            {
                "Make": "HONDA",
                "Model": "CIVIC",
                "ModelYear": "2020",
            }
        ]
    }

    class FakeResponse:
        status_code = 200

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return payload

    class FakeAsyncClient:
        def __init__(self, timeout: float):
            self.timeout = timeout

        async def __aenter__(self) -> "FakeAsyncClient":
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

        async def get(self, endpoint: str, params: dict[str, str]) -> FakeResponse:
            assert endpoint == "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/2HGFC2F59LH000000"
            assert params == {"format": "json"}
            return FakeResponse()

    monkeypatch.setattr(
        "app.services.safety_source_adapters.nhtsa.httpx.AsyncClient",
        FakeAsyncClient,
    )

    adapter = NHTSAVPICAdapter()
    result = asyncio.run(
        adapter.decode(vin="2HGFC2F59LH000000", request_id="test-request")
    )

    assert result.source_id == "nhtsa_vpic_vin_decoder_api"
    assert result.upstream_status == "success"
    assert result.records == []
    assert result.context == {
        "vehicle_identity": {
            "make": "HONDA",
            "model": "CIVIC",
            "model_year": "2020",
            "vin": "2HGFC2F59LH000000",
        }
    }
