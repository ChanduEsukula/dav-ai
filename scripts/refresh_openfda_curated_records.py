from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

OPENFDA_FOOD_ENDPOINT = "https://api.fda.gov/food/enforcement.json"
OPENFDA_DRUG_ENDPOINT = "https://api.fda.gov/drug/enforcement.json"

OPENFDA_FOOD_OUT = ROOT / "data" / "safety_sources" / "food" / "openfda_food_curated_records.json"
OPENFDA_DRUG_OUT = ROOT / "data" / "safety_sources" / "drug" / "openfda_drug_curated_records.json"


def fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "DavAI/real-world-safety-refresh",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def build_openfda_url(endpoint: str, query: str, limit: int = 5) -> str:
    return endpoint + "?" + urllib.parse.urlencode(
        {
            "search": query,
            "limit": str(limit),
        }
    )


def fetch_openfda_records(endpoint: str, queries: list[str], *, max_records: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[str] = set()

    for query in queries:
        url = build_openfda_url(endpoint, query, limit=5)
        payload = fetch_json(url)

        for record in payload.get("results", []):
            key = "|".join(
                str(record.get(field, ""))
                for field in (
                    "recall_number",
                    "product_description",
                    "recalling_firm",
                    "recall_initiation_date",
                )
            )
            if key in seen:
                continue

            seen.add(key)
            records.append(record)

            if len(records) >= max_records:
                return records

    return records


def write_records(path: Path, records: list[dict[str, Any]]) -> None:
    if not records:
        raise RuntimeError(f"No records fetched for {path}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    firms = sorted({str(record.get("recalling_firm", "")).strip() for record in records if record.get("recalling_firm")})
    print(f"Wrote {len(records)} records to {path}")
    print("Sample firms:")
    for firm in firms[:8]:
        print(f"  - {firm}")


def main() -> None:
    food_queries = [
        'reason_for_recall:"undeclared milk"',
        'reason_for_recall:"listeria"',
        'product_description:"pepperoni"',
        'product_description:"ice cream"',
        'product_description:"salad"',
    ]

    drug_queries = [
        'product_description:"eye drops"',
        'product_description:"hand sanitizer"',
        'product_description:"metformin"',
        'product_description:"acetaminophen"',
        'reason_for_recall:"NDMA"',
    ]

    food_records = fetch_openfda_records(
        OPENFDA_FOOD_ENDPOINT,
        food_queries,
        max_records=10,
    )
    drug_records = fetch_openfda_records(
        OPENFDA_DRUG_ENDPOINT,
        drug_queries,
        max_records=12,
    )

    write_records(OPENFDA_FOOD_OUT, food_records)
    write_records(OPENFDA_DRUG_OUT, drug_records)


if __name__ == "__main__":
    main()
