from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

OUT = Path("data/source_audits/final_recall_enrichment_audit.json")


def fetch_json(url: str) -> tuple[bool, Any, str | None]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "DavAI/final-recall-enrichment-audit",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return True, json.loads(response.read().decode("utf-8")), None
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
        return sorted(sample.keys())[:40]
    return []


def main() -> None:
    sources = [
        {
            "source_id": "nhtsa_vehicle_control",
            "source_name": "NHTSA vehicle recall control",
            "category": "vehicles",
            "url": "https://api.nhtsa.gov/recalls/recallsByVehicle?make=Honda&model=Civic&modelYear=2020",
        },
        {
            "source_id": "nhtsa_tire_candidate_1",
            "source_name": "NHTSA tire candidate query",
            "category": "tires",
            "url": "https://api.nhtsa.gov/recalls/recallsByVehicle?make=Michelin&model=Pilot&modelYear=2020",
        },
        {
            "source_id": "nhtsa_car_seat_candidate_1",
            "source_name": "NHTSA car seat candidate query",
            "category": "car_seats_child_restraints",
            "url": "https://api.nhtsa.gov/recalls/recallsByVehicle?make=Graco&model=4Ever&modelYear=2020",
        },
        {
            "source_id": "openfda_food_enforcement_fields",
            "source_name": "openFDA Food Enforcement field audit",
            "category": "fda_food_enrichment",
            "url": "https://api.fda.gov/food/enforcement.json?limit=2",
        },
        {
            "source_id": "openfda_drug_enforcement_fields",
            "source_name": "openFDA Drug Enforcement field audit",
            "category": "fda_drug_enrichment",
            "url": "https://api.fda.gov/drug/enforcement.json?limit=2",
        },
        {
            "source_id": "openfda_device_enforcement_fields",
            "source_name": "openFDA Device Enforcement field audit",
            "category": "fda_device_enrichment",
            "url": "https://api.fda.gov/device/enforcement.json?limit=2",
        },
        {
            "source_id": "openfda_ndc_acetaminophen",
            "source_name": "openFDA NDC Directory acetaminophen",
            "category": "drug_reference_ndc",
            "url": "https://api.fda.gov/drug/ndc.json?search=generic_name:%22ACETAMINOPHEN%22&limit=5",
        },
        {
            "source_id": "openfda_ndc_tylenol",
            "source_name": "openFDA NDC Directory Tylenol",
            "category": "drug_reference_ndc",
            "url": "https://api.fda.gov/drug/ndc.json?search=brand_name:%22TYLENOL%22&limit=5",
        },
        {
            "source_id": "cpsc_detail_fields",
            "source_name": "CPSC detail fields",
            "category": "consumer_product_detail_enrichment",
            "url": "https://www.saferproducts.gov/RestWebServices/Recall?format=json",
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
                "purpose": "Audit final recall/enforcement/reference enrichment candidates before implementation. No synthetic data.",
                "results": results,
            },
            indent=2,
            ensure_ascii=False,
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
