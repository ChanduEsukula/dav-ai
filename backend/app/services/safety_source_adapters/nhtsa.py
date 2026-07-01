from __future__ import annotations

import logging
import re
from dataclasses import asdict, dataclass
from typing import Any

import httpx

from app.services.safety_source_adapters.base import (
    NormalizedSafetyRecord,
    SafetySourceAdapterError,
    SourceAdapterResult,
    compact_text,
    dedupe_records,
    first_text,
    record_matches_query,
    stable_payload_hash,
    utc_now_iso,
)
from app.sources.registry import NHTSA_RECALLS_API_DATASETS, NHTSA_VPIC_VIN_DECODER_API

logger = logging.getLogger("dav_ai.real_world_safety.nhtsa")

VIN_RE = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$", re.IGNORECASE)
YEAR_RE = re.compile(r"\b(19[8-9]\d|20\d{2})\b")


@dataclass(slots=True)
class VehicleIdentity:
    make: str
    model: str
    model_year: str
    vin: str | None = None

    @property
    def query_label(self) -> str:
        return " ".join(part for part in (self.model_year, self.make, self.model) if part)


def is_vin_like(value: str) -> bool:
    return bool(VIN_RE.fullmatch(value.strip()))


def parse_vehicle_query(query: str) -> VehicleIdentity | None:
    cleaned = compact_text(query)
    year_match = YEAR_RE.search(cleaned)
    if not year_match:
        return None

    year = year_match.group(1)
    vehicle_text = compact_text(
        f"{cleaned[:year_match.start()]} {cleaned[year_match.end():]}"
    )
    parts = vehicle_text.split()

    if len(parts) < 2:
        return None

    make = parts[0]
    model = " ".join(parts[1:])

    return VehicleIdentity(make=make, model=model, model_year=year)


class NHTSAVPICAdapter:
    def __init__(self, timeout_seconds: float = 5.0):
        self.timeout_seconds = timeout_seconds
        self.source = NHTSA_VPIC_VIN_DECODER_API
        self.endpoint_root = "https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues"

    async def decode(
        self,
        *,
        vin: str,
        request_id: str | None = None,
    ) -> SourceAdapterResult:
        retrieved_at = utc_now_iso()
        endpoint = f"{self.endpoint_root}/{vin}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(endpoint, params={"format": "json"})

            response.raise_for_status()
            payload = response.json()
            identity = _extract_vehicle_identity(payload, vin)

            return SourceAdapterResult(
                source_id=self.source["source_id"],
                source_name=self.source["source_name"],
                source_type="API",
                source_url=self.source["endpoint"],
                source_kind="structured_api",
                retrieved_at=retrieved_at,
                records=[],
                raw_payload=payload,
                upstream_status="success" if identity else "empty",
                context={"vehicle_identity": asdict(identity) if identity else None},
            )

        except httpx.TimeoutException as exc:
            error_message = f"Timed out after {self.timeout_seconds} seconds contacting NHTSA vPIC VIN Decoder API."
            logger.warning(
                "nhtsa_vpic_request_timed_out",
                extra={
                    "event": "nhtsa_vpic_request_timed_out",
                    "request_id": request_id,
                    "source_id": self.source["source_id"],
                    "vin": vin,
                    "timeout_seconds": self.timeout_seconds,
                },
            )
            raise SafetySourceAdapterError(error_message, error_type="timeout") from exc
        except httpx.HTTPStatusError as exc:
            error_message = f"NHTSA vPIC VIN Decoder API returned HTTP {exc.response.status_code}."
            logger.warning(
                "nhtsa_vpic_request_http_error",
                extra={
                    "event": "nhtsa_vpic_request_http_error",
                    "request_id": request_id,
                    "source_id": self.source["source_id"],
                    "vin": vin,
                    "status_code": exc.response.status_code,
                },
            )
            raise SafetySourceAdapterError(error_message, error_type="http_status") from exc
        except httpx.RequestError as exc:
            error_message = f"NHTSA vPIC VIN Decoder API request failed: {exc}"
            logger.warning(
                "nhtsa_vpic_request_network_error",
                extra={
                    "event": "nhtsa_vpic_request_network_error",
                    "request_id": request_id,
                    "source_id": self.source["source_id"],
                    "vin": vin,
                },
            )
            raise SafetySourceAdapterError(error_message, error_type="network_error") from exc
        except Exception as exc:
            logger.exception(
                "nhtsa_vpic_request_failed",
                extra={
                    "event": "nhtsa_vpic_request_failed",
                    "request_id": request_id,
                    "source_id": self.source["source_id"],
                    "vin": vin,
                },
            )
            raise SafetySourceAdapterError(str(exc), error_type="adapter_error") from exc


class NHTSARecallsAdapter:
    def __init__(self, timeout_seconds: float = 5.0):
        self.timeout_seconds = timeout_seconds
        self.source = NHTSA_RECALLS_API_DATASETS
        self.endpoint = "https://api.nhtsa.gov/recalls/recallsByVehicle"

    async def search_vehicle_recalls(
        self,
        *,
        vehicle: VehicleIdentity,
        limit: int,
        request_id: str | None = None,
    ) -> SourceAdapterResult:
        retrieved_at = utc_now_iso()
        vehicle_query = vehicle.query_label

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(
                    self.endpoint,
                    params={
                        "make": vehicle.make,
                        "model": vehicle.model,
                        "modelYear": vehicle.model_year,
                    },
                )

            if response.status_code == 404:
                payload: dict[str, Any] = {"results": []}
            else:
                response.raise_for_status()
                payload = response.json()

            raw_records = _extract_nhtsa_recall_records(payload)
            records = [
                _normalize_nhtsa_recall(
                    record=record,
                    vehicle=vehicle,
                    retrieved_at=retrieved_at,
                    source_name=self.source["source_name"],
                    source_url=self.endpoint,
                )
                for record in raw_records
            ]
            records = [
                record
                for record in records
                if record_matches_query(record, vehicle_query)
            ]
            records = dedupe_records(records)[:limit]

            return SourceAdapterResult(
                source_id=self.source["source_id"],
                source_name=self.source["source_name"],
                source_type="API",
                source_url=self.endpoint,
                source_kind="structured_api",
                retrieved_at=retrieved_at,
                records=records,
                raw_payload=payload,
                upstream_status="success" if records else "empty",
                context={"vehicle_identity": asdict(vehicle)},
            )

        except httpx.TimeoutException as exc:
            error_message = f"Timed out after {self.timeout_seconds} seconds contacting NHTSA Recalls API."
            logger.warning(
                "nhtsa_recalls_request_timed_out",
                extra={
                    "event": "nhtsa_recalls_request_timed_out",
                    "request_id": request_id,
                    "source_id": self.source["source_id"],
                    "vehicle": asdict(vehicle),
                    "timeout_seconds": self.timeout_seconds,
                },
            )
            raise SafetySourceAdapterError(error_message, error_type="timeout") from exc
        except httpx.HTTPStatusError as exc:
            error_message = f"NHTSA Recalls API returned HTTP {exc.response.status_code}."
            logger.warning(
                "nhtsa_recalls_request_http_error",
                extra={
                    "event": "nhtsa_recalls_request_http_error",
                    "request_id": request_id,
                    "source_id": self.source["source_id"],
                    "vehicle": asdict(vehicle),
                    "status_code": exc.response.status_code,
                },
            )
            raise SafetySourceAdapterError(error_message, error_type="http_status") from exc
        except httpx.RequestError as exc:
            error_message = f"NHTSA Recalls API request failed: {exc}"
            logger.warning(
                "nhtsa_recalls_request_network_error",
                extra={
                    "event": "nhtsa_recalls_request_network_error",
                    "request_id": request_id,
                    "source_id": self.source["source_id"],
                    "vehicle": asdict(vehicle),
                },
            )
            raise SafetySourceAdapterError(error_message, error_type="network_error") from exc
        except Exception as exc:
            logger.exception(
                "nhtsa_recalls_request_failed",
                extra={
                    "event": "nhtsa_recalls_request_failed",
                    "request_id": request_id,
                    "source_id": self.source["source_id"],
                    "vehicle": asdict(vehicle),
                },
            )
            raise SafetySourceAdapterError(str(exc), error_type="adapter_error") from exc


def _extract_vehicle_identity(payload: Any, vin: str) -> VehicleIdentity | None:
    if not isinstance(payload, dict):
        return None

    results = payload.get("Results") or payload.get("results") or []
    if not isinstance(results, list) or not results:
        return None

    first = results[0]
    if not isinstance(first, dict):
        return None

    make = first_text(first.get("Make"), first.get("make"))
    model = first_text(first.get("Model"), first.get("model"))
    model_year = first_text(first.get("ModelYear"), first.get("modelYear"))

    if not make or not model or not model_year:
        return None

    return VehicleIdentity(make=make, model=model, model_year=model_year, vin=vin)


def _extract_nhtsa_recall_records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]

    if not isinstance(payload, dict):
        return []

    for key in ("results", "Results", "recalls", "items"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]

    return []


def _normalize_nhtsa_recall(
    *,
    record: dict[str, Any],
    vehicle: VehicleIdentity,
    retrieved_at: str,
    source_name: str,
    source_url: str,
) -> NormalizedSafetyRecord:
    recall_number = first_text(
        record.get("NHTSACampaignNumber"),
        record.get("CampaignNumber"),
        record.get("nhtsaCampaignNumber"),
    )
    component = first_text(record.get("Component"), record.get("component"))
    summary = first_text(record.get("Summary"), record.get("summary"))
    consequence = first_text(record.get("Consequence"), record.get("consequence"))
    remedy = first_text(record.get("Remedy"), record.get("remedy"))
    make = first_text(record.get("Make"), vehicle.make)
    model = first_text(record.get("Model"), vehicle.model)
    model_year = first_text(record.get("ModelYear"), vehicle.model_year)
    product_name = compact_text(f"{model_year} {make} {model}")

    return NormalizedSafetyRecord(
        source_name=source_name,
        source_type="API",
        source_url=source_url,
        source_kind="structured_api",
        category="Vehicle recall",
        product_name=product_name,
        brand_name=make,
        company_name=first_text(record.get("Manufacturer"), record.get("manufacturer"), make),
        title=first_text(
            record.get("Title"),
            f"{product_name} vehicle recall{f' - {component}' if component else ''}",
        ),
        reason=summary,
        hazard_type=first_text(component, consequence),
        remedy=remedy,
        published_date=first_text(record.get("ReportReceivedDate"), record.get("reportReceivedDate")),
        recall_number=recall_number,
        affected_models=[product_name],
        affected_lots=[],
        raw_payload_hash=stable_payload_hash(record),
        retrieved_at=retrieved_at,
        record_url="https://www.nhtsa.gov/recalls",
    )
