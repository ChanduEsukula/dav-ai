from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

OUT = Path("data/source_audits/recall_expansion_source_audit.json")


def fetch_json(url: str) -> tuple[bool, Any, str | None]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "DavAI/recall-source-expansion-audit",
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return True, payload, None
    except Exception as exc:
        return False, None, str(exc)


def record_count(payload: Any) -> int:
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, dict):
        for key in ("results", "Results", "recalls", "data", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return len(value)
    return 0


def sample_keys(payload: Any) -> list[str]:
    sample = None

    if isinstance(payload, list) and payload:
        sample = payload[0]
    elif isinstance(payload, dict):
        for key in ("results", "Results", "recalls", "data", "items"):
            value = payload.get(key)
            if isinstance(value, list) and value:
                sample = value[0]
                break

    if isinstance(sample, dict):
        return sorted(sample.keys())[:30]

    return []


def main() -> None:
    sources = [
        {
            "source_id": "usda_fsis_candidate",
            "source_name": "USDA FSIS Recall Candidate",
            "category": "meat_poultry_egg_products",
            "url": "https://www.fsis.usda.gov/fsis/api/recall/v/1",
            "target_decision": "add_if_real_json_records_work",
        },
        {
            "source_id": "cpsc_recall_detail_candidate",
            "source_name": "CPSC Recall API Detail Candidate",
            "category": "consumer_product_detail_enrichment",
            "url": "https://www.saferproducts.gov/RestWebServices/Recall?format=json",
            "target_decision": "already_supported_enrich_if_detail_fields_are_available",
        },
        {
            "source_id": "nhtsa_equipment_candidate",
            "source_name": "NHTSA Recalls Equipment Candidate",
            "category": "tires_car_seats_vehicle_equipment",
            "url": "https://api.nhtsa.gov/recalls/recallsByVehicle?make=Graco&model=car%20seat&modelYear=2020",
            "target_decision": "investigate_query_shape_before_adding",
        },
        {
            "source_id": "nhtsa_vehicle_known_candidate",
            "source_name": "NHTSA Known Vehicle Recall Candidate",
            "category": "vehicle_recall_control",
            "url": "https://api.nhtsa.gov/recalls/recallsByVehicle?make=Honda&model=Civic&modelYear=2020",
            "target_decision": "already_supported_control_probe",
        },
        {
            "source_id": "openfda_food_enforcement_control",
            "source_name": "openFDA Food Enforcement Control",
            "category": "food_recall_control",
            "url": "https://api.fda.gov/food/enforcement.json?limit=2",
            "target_decision": "already_supported_control_probe",
        },
        {
            "source_id": "openfda_drug_enforcement_control",
            "source_name": "openFDA Drug Enforcement Control",
            "category": "drug_recall_control",
            "url": "https://api.fda.gov/drug/enforcement.json?limit=2",
            "target_decision": "already_supported_control_probe",
        },
        {
            "source_id": "openfda_device_enforcement_control",
            "source_name": "openFDA Device Enforcement Control",
            "category": "device_recall_control",
            "url": "https://api.fda.gov/device/enforcement.json?limit=2",
            "target_decision": "already_supported_control_probe",
        },
    ]

    results = []

    for source in sources:
        ok, payload, error = fetch_json(source["url"])
        results.append(
            {
                **source,
                "reachable": ok,
                "json_records": record_count(payload) if ok else 0,
                "sample_keys": sample_keys(payload) if ok else [],
                "error": error,
            }
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "purpose": "Read-only audit of candidate recall source expansions before implementation.",
                "results": results,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    for result in results:
        status = "OK" if result["reachable"] else "FAIL"
        print(f"{status} {result['source_id']}: records={result['json_records']}")
        if result["error"]:
            print(f"  error: {result['error']}")


if __name__ == "__main__":
    main()
