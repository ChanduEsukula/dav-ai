import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

OUT_JSON = Path("data/source_audits/usa_daily_safety_api_audit.json")
OUT_MD = Path("docs/usa_daily_safety_api_audit.md")

SOURCES = [
    {
        "name": "openFDA Food Enforcement",
        "category": "Food / groceries",
        "owner": "FDA / openFDA",
        "url": "https://api.fda.gov/food/enforcement.json",
        "params": {"search": 'reason_for_recall:"undeclared milk"', "limit": "2"},
        "daily_life_value": "High",
        "data_kind": "Recall / enforcement",
        "recommended_use": "Add / keep",
    },
    {
        "name": "openFDA Drug Enforcement",
        "category": "Medicine / OTC / prescriptions",
        "owner": "FDA / openFDA",
        "url": "https://api.fda.gov/drug/enforcement.json",
        "params": {"search": 'product_description:"eye drops"', "limit": "2"},
        "daily_life_value": "High",
        "data_kind": "Recall / enforcement",
        "recommended_use": "Add / keep",
    },
    {
        "name": "openFDA Device Enforcement",
        "category": "Medical devices",
        "owner": "FDA / openFDA",
        "url": "https://api.fda.gov/device/enforcement.json",
        "params": {"search": 'product_description:"glucose meter"', "limit": "2"},
        "daily_life_value": "High",
        "data_kind": "Recall / enforcement",
        "recommended_use": "Add / keep",
    },
    {
        "name": "openFDA Device Event",
        "category": "Medical devices",
        "owner": "FDA / openFDA",
        "url": "https://api.fda.gov/device/event.json",
        "params": {"search": 'device.generic_name:"INSULIN PUMP"', "limit": "2"},
        "daily_life_value": "Medium",
        "data_kind": "Adverse-event signal, not recall",
        "recommended_use": "Keep with strong warning label",
    },
    {
        "name": "openFDA Drug Label",
        "category": "Medicine / labels",
        "owner": "FDA / openFDA",
        "url": "https://api.fda.gov/drug/label.json",
        "params": {"search": 'openfda.generic_name:"ACETAMINOPHEN"', "limit": "2"},
        "daily_life_value": "High",
        "data_kind": "Official label / warnings / dosage",
        "recommended_use": "Add next",
    },
    {
        "name": "openFDA Drug Event",
        "category": "Medicine / adverse events",
        "owner": "FDA / openFDA",
        "url": "https://api.fda.gov/drug/event.json",
        "params": {"search": 'patient.drug.medicinalproduct:"METFORMIN"', "limit": "2"},
        "daily_life_value": "Medium",
        "data_kind": "Adverse-event signal, not recall",
        "recommended_use": "Add later with caution label",
    },
    {
        "name": "openFDA Food Event / CAERS",
        "category": "Food / supplements / cosmetics signals",
        "owner": "FDA / openFDA",
        "url": "https://api.fda.gov/food/event.json",
        "params": {"limit": "2"},
        "daily_life_value": "Medium",
        "data_kind": "Adverse-event signal, not recall",
        "recommended_use": "Investigate",
    },
    {
        "name": "CPSC Recalls",
        "category": "Consumer products",
        "owner": "Consumer Product Safety Commission",
        "url": "https://www.saferproducts.gov/RestWebServices/Recall",
        "params": {"format": "json"},
        "daily_life_value": "Very high",
        "data_kind": "Consumer product recalls",
        "recommended_use": "Add / keep",
    },
    {
        "name": "NHTSA Recalls by Vehicle",
        "category": "Cars / motorcycles / vehicle equipment",
        "owner": "NHTSA",
        "url": "https://api.nhtsa.gov/recalls/recallsByVehicle",
        "params": {"make": "Honda", "model": "Civic", "modelYear": "2020"},
        "daily_life_value": "Very high",
        "data_kind": "Vehicle recalls",
        "recommended_use": "Add / keep",
    },
    {
        "name": "NHTSA Vehicle Products",
        "category": "Cars / bikes / equipment reference",
        "owner": "NHTSA",
        "url": "https://vpic.nhtsa.dot.gov/api/vehicles/GetMakesForVehicleType/car",
        "params": {"format": "json"},
        "daily_life_value": "High",
        "data_kind": "Vehicle reference / metadata",
        "recommended_use": "Keep as reference source",
    },
    {
        "name": "Recalls.gov",
        "category": "Multi-agency recall portal",
        "owner": "U.S. government recall portal",
        "url": "https://www.recalls.gov/rss/recent.xml",
        "params": {},
        "daily_life_value": "Medium",
        "data_kind": "RSS / recall aggregation",
        "recommended_use": "Investigate RSS parser",
    },
    {
        "name": "EPA ECHO",
        "category": "Environment / facility compliance",
        "owner": "EPA",
        "url": "https://echodata.epa.gov/echo/resource/cwa_rest_services.get_facilities",
        "params": {"output": "JSON", "p_st": "MN", "p_act": "Y", "pageno": "1"},
        "daily_life_value": "Low",
        "data_kind": "Facility/environment compliance",
        "recommended_use": "Skip for consumer recall MVP",
    },
    {
        "name": "ClinicalTrials.gov",
        "category": "Drug/device research context",
        "owner": "NIH / NLM",
        "url": "https://clinicaltrials.gov/api/v2/studies",
        "params": {"query.term": "metformin", "pageSize": "2"},
        "daily_life_value": "Low",
        "data_kind": "Clinical research, not recall",
        "recommended_use": "Skip for recall MVP",
    },
]


def fetch(source: dict[str, Any]) -> dict[str, Any]:
    url = source["url"]
    params = source.get("params") or {}
    if params:
        url = url + "?" + urllib.parse.urlencode(params)

    result = {
        **source,
        "request_url": url,
        "reachable": False,
        "http_status": None,
        "content_type": None,
        "json_parseable": False,
        "record_count": 0,
        "top_level_keys": [],
        "sample_record_keys": [],
        "sample_record": None,
        "error": None,
    }

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "DavAI-USA-Daily-Safety-Audit/1.0",
                "Accept": "application/json, application/xml;q=0.9, text/xml;q=0.8, */*;q=0.5",
            },
        )
        with urllib.request.urlopen(req, timeout=25) as response:
            result["http_status"] = response.status
            result["content_type"] = response.headers.get("Content-Type")
            raw = response.read()
            result["reachable"] = 200 <= response.status < 400

        content_type = (result["content_type"] or "").lower()

        if "json" in content_type or raw[:1] in (b"{", b"["):
            payload = json.loads(raw.decode("utf-8", errors="replace"))
            result["json_parseable"] = True

            if isinstance(payload, dict):
                result["top_level_keys"] = sorted(payload.keys())

                records = None
                for key in ("results", "Results", "recalls", "data", "items"):
                    if isinstance(payload.get(key), list):
                        records = payload[key]
                        break

                if records is None and isinstance(payload.get("Result"), list):
                    records = payload["Result"]

                if isinstance(records, list):
                    result["record_count"] = len(records)
                    if records:
                        first = records[0]
                        result["sample_record"] = first
                        if isinstance(first, dict):
                            result["sample_record_keys"] = sorted(first.keys())[:80]
                else:
                    result["sample_record"] = payload

            elif isinstance(payload, list):
                result["record_count"] = len(payload)
                if payload:
                    result["sample_record"] = payload[0]
                    if isinstance(payload[0], dict):
                        result["sample_record_keys"] = sorted(payload[0].keys())[:80]

        else:
            # XML/RSS or HTML fallback
            text = raw.decode("utf-8", errors="replace")
            result["sample_record"] = text[:1000]
            result["record_count"] = text.count("<item>") or text.count("<entry>") or 0

    except Exception as exc:
        result["error"] = str(exc)

    return result


def tier(result: dict[str, Any]) -> str:
    if not result["reachable"]:
        return "D - Not reachable / needs fix"
    if result["daily_life_value"] in {"Very high", "High"} and "recall" in result["data_kind"].lower():
        return "A - Add/keep for USA daily recall MVP"
    if result["daily_life_value"] in {"Very high", "High"}:
        return "B - Useful context/reference"
    if "adverse-event" in result["data_kind"].lower():
        return "B - Signal source, not recall"
    return "C - Not core recall MVP"


def main() -> None:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)

    audited = []
    for source in SOURCES:
        print(f"Checking {source['name']}...")
        result = fetch(source)
        result["tier"] = tier(result)
        audited.append(result)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "purpose": "Audit real-time USA daily-life safety, recall, label, and signal APIs for Dav AI.",
        "sources": audited,
    }

    OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# USA Daily-Life Safety API Audit",
        "",
        f"Generated at: {report['generated_at']}",
        "",
        "Goal: decide which real-time USA APIs are useful for a daily recall/safety app covering cars, bikes, food, medicine, devices, household items, electronics, baby products, and products people buy.",
        "",
        "## Summary Table",
        "",
        "| Tier | Source | Category | Reachable | JSON | Records | Data Kind | Recommended Use |",
        "|---|---|---|---:|---:|---:|---|---|",
    ]

    for r in audited:
        lines.append(
            f"| {r['tier']} | {r['name']} | {r['category']} | {r['reachable']} | {r['json_parseable']} | {r['record_count']} | {r['data_kind']} | {r['recommended_use']} |"
        )

    lines.extend([
        "",
        "## Field Samples",
        "",
    ])

    for r in audited:
        lines.extend([
            f"### {r['name']}",
            "",
            f"- Category: {r['category']}",
            f"- Owner: {r['owner']}",
            f"- Tier: {r['tier']}",
            f"- Reachable: {r['reachable']}",
            f"- HTTP status: {r['http_status']}",
            f"- Content-Type: {r['content_type']}",
            f"- JSON parseable: {r['json_parseable']}",
            f"- Record count in sample: {r['record_count']}",
            f"- Top-level keys: {', '.join(r['top_level_keys']) if r['top_level_keys'] else 'N/A'}",
            f"- Sample record keys: {', '.join(r['sample_record_keys']) if r['sample_record_keys'] else 'N/A'}",
            f"- Error: {r['error'] or 'None'}",
            "",
        ])

    lines.extend([
        "## Initial Product Decision",
        "",
        "For the USA daily recall MVP, prioritize sources that directly answer: has something people buy/use been recalled or flagged by an official source?",
        "",
        "Recommended MVP source groups:",
        "",
        "1. Vehicles: NHTSA recalls + vPIC reference.",
        "2. Consumer products: CPSC recalls.",
        "3. Food/groceries: FDA/openFDA Food Enforcement + FDA public recalls page.",
        "4. Medicine: openFDA Drug Enforcement + DailyMed/RxNorm context.",
        "5. Medical devices: openFDA Device Enforcement + Device Event signal warnings.",
        "6. Later: household chemicals/pesticides if a reliable EPA consumer-product source is confirmed.",
        "",
        "Avoid synthetic data. Skip sources that cannot be fetched reproducibly.",
        "",
    ])

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print()
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    print()
    for r in audited:
        print(f"{r['tier']}: {r['name']} reachable={r['reachable']} json={r['json_parseable']} records={r['record_count']}")


if __name__ == "__main__":
    main()
