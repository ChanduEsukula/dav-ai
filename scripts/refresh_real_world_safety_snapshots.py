from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]

OPENFDA_FOOD_ENDPOINT = "https://api.fda.gov/food/enforcement.json"
OPENFDA_DRUG_ENDPOINT = "https://api.fda.gov/drug/enforcement.json"
OPENFDA_DRUG_LABEL_ENDPOINT = "https://api.fda.gov/drug/label.json"
OPENFDA_NDC_ENDPOINT = "https://api.fda.gov/drug/ndc.json"
OPENFDA_DEVICE_ENDPOINT = "https://api.fda.gov/device/enforcement.json"
OPENFDA_DEVICE_EVENT_ENDPOINT = "https://api.fda.gov/device/event.json"
CPSC_RECALLS_ENDPOINT = "https://www.saferproducts.gov/RestWebServices/Recall?format=json"
USDA_FSIS_ENDPOINT = "https://www.fsis.usda.gov/fsis/api/recall/v/1"

OPENFDA_FOOD_OUT = ROOT / "data" / "safety_sources" / "food" / "openfda_food_curated_records.json"
OPENFDA_DRUG_OUT = ROOT / "data" / "safety_sources" / "drug" / "openfda_drug_curated_records.json"
OPENFDA_DRUG_LABEL_OUT = ROOT / "data" / "safety_sources" / "drug" / "openfda_drug_label_curated_records.json"
OPENFDA_NDC_OUT = ROOT / "data" / "safety_sources" / "drug" / "openfda_ndc_curated_records.json"
OPENFDA_DEVICE_OUT = ROOT / "data" / "safety_sources" / "device" / "openfda_device_enforcement_curated_records.json"
OPENFDA_DEVICE_EVENT_OUT = ROOT / "data" / "safety_sources" / "device" / "openfda_device_event_curated_records.json"
CPSC_DAILY_PRODUCTS_OUT = ROOT / "data" / "safety_sources" / "cpsc" / "cpsc_daily_products_curated_records.json"
USDA_FSIS_OUT = ROOT / "data" / "safety_sources" / "food" / "usda_fsis_curated_records.json"
SNAPSHOT_REFRESH_MANIFEST_OUT = ROOT / "data" / "source_audits" / "snapshot_refresh_manifest.json"


class SourceFetchError(RuntimeError):
    def __init__(
        self,
        *,
        source_name: str,
        endpoint: str,
        reason: str,
        http_status: int | None = None,
    ) -> None:
        super().__init__(reason)
        self.source_name = source_name
        self.endpoint = endpoint
        self.reason = reason
        self.http_status = http_status


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    normalized_argv = [
        f"--{argument[1:]}" if argument.startswith(("\u2013", "\u2014")) else argument
        for argument in (argv or [])
    ]
    parser = argparse.ArgumentParser(
        description=(
            "Refresh curated RealWorldSafety snapshots from official/public sources."
        ),
    )
    parser.add_argument(
        "--source",
        choices=("all", "fsis", "cpsc", "openfda"),
        default="all",
        help="Source group to refresh (default: all).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and print planned snapshot/manifest results without writing files.",
    )
    return parser.parse_args(normalized_argv)


def fetch_json(url: str) -> Any:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "DavAI/real-world-safety-refresh",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_source_records(
    *,
    source_name: str,
    endpoint: str,
    fetcher: Callable[[], list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    try:
        return fetcher()
    except urllib.error.HTTPError as exc:
        raise SourceFetchError(
            source_name=source_name,
            endpoint=exc.url or endpoint,
            http_status=exc.code,
            reason=str(exc.reason or exc),
        ) from None
    except urllib.error.URLError as exc:
        raise SourceFetchError(
            source_name=source_name,
            endpoint=endpoint,
            reason=str(exc.reason or exc),
        ) from None
    except (TimeoutError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise SourceFetchError(
            source_name=source_name,
            endpoint=endpoint,
            reason=str(exc),
        ) from None


def print_source_fetch_error(error: SourceFetchError) -> None:
    print(
        "Snapshot refresh failed; no snapshot or manifest files were written.",
        file=sys.stderr,
    )
    print(f"Source: {error.source_name}", file=sys.stderr)
    print(f"Endpoint: {error.endpoint}", file=sys.stderr)
    if error.http_status is not None:
        print(f"HTTP status: {error.http_status}", file=sys.stderr)
    print(f"Reason: {error.reason}", file=sys.stderr)


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




def fetch_openfda_drug_label_records(
    queries: list[str],
    *,
    max_records: int,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[str] = set()

    for query in queries:
        url = build_openfda_url(OPENFDA_DRUG_LABEL_ENDPOINT, query, limit=10)
        payload = fetch_json(url)

        for record in payload.get("results", []):
            openfda = record.get("openfda") or {}
            brand_names = openfda.get("brand_name") or []
            generic_names = openfda.get("generic_name") or []
            manufacturers = openfda.get("manufacturer_name") or []

            key = "|".join(
                [
                    ";".join(str(value) for value in brand_names),
                    ";".join(str(value) for value in generic_names),
                    ";".join(str(value) for value in manufacturers),
                    str(record.get("id") or record.get("set_id") or ""),
                ]
            )

            if not key.strip("|") or key in seen:
                continue

            seen.add(key)
            records.append(record)

            if len(records) >= max_records:
                return records

    return records




def fetch_openfda_ndc_records(
    queries: list[str],
    *,
    max_records: int,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[str] = set()

    for query in queries:
        url = build_openfda_url(OPENFDA_NDC_ENDPOINT, query, limit=10)
        payload = fetch_json(url)

        for record in payload.get("results", []):
            key = str(record.get("product_ndc") or record.get("product_id") or "")
            if not key or key in seen:
                continue

            record["_dav_query"] = query
            seen.add(key)
            records.append(record)

            if len(records) >= max_records:
                return records

    return records


def fetch_openfda_device_event_records(
    queries: list[str],
    *,
    max_records: int,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[str] = set()

    for query in queries:
        url = build_openfda_url(OPENFDA_DEVICE_EVENT_ENDPOINT, query, limit=10)
        payload = fetch_json(url)

        for record in payload.get("results", []):
            key = str(record.get("mdr_report_key") or record.get("report_number") or "")
            if not key or key in seen:
                continue

            seen.add(key)
            records.append(record)

            if len(records) >= max_records:
                return records

    return records


def fetch_cpsc_daily_product_records(*, max_records: int) -> list[dict[str, Any]]:
    daily_terms = [
        "air fryer",
        "power bank",
        "charger",
        "battery",
        "scooter",
        "bicycle",
        "bike",
        "helmet",
        "heater",
        "toaster",
        "blender",
        "stroller",
        "crib",
        "baby",
        "toy",
        "furniture",
        "dresser",
        "candle",
        "vaporizer",
        "lithium-ion",
    ]

    payload = fetch_json(CPSC_RECALLS_ENDPOINT)
    if not isinstance(payload, list):
        return []

    selected: list[dict[str, Any]] = []
    seen: set[str] = set()

    for record in payload:
        searchable = " ".join(
            str(record.get(key) or "")
            for key in [
                "Name",
                "Title",
                "Description",
                "Hazards",
                "Remedies",
                "ConsumerContact",
                "Products",
                "Injuries",
                "ManufacturerCountries",
            ]
        ).lower()

        if not any(term in searchable for term in daily_terms):
            continue

        recall_id = str(record.get("RecallID") or record.get("RecallNumber") or "")
        if not recall_id or recall_id in seen:
            continue

        seen.add(recall_id)
        selected.append(record)

        if len(selected) >= max_records:
            break

    return selected




def fetch_usda_fsis_records(*, max_records: int) -> list[dict[str, Any]]:
    terms = [
        "chicken",
        "beef",
        "turkey",
        "pork",
        "sausage",
        "meatloaf",
        "poultry",
        "ham",
        "egg",
        "listeria",
        "salmonella",
        "e. coli",
        "undeclared",
        "allergen",
        "misbranding",
        "ready-to-eat",
        "frozen",
    ]

    payload = fetch_json(USDA_FSIS_ENDPOINT)
    if not isinstance(payload, list):
        return []

    selected: list[dict[str, Any]] = []
    seen: set[str] = set()

    for record in payload:
        searchable = " ".join(
            str(record.get(key) or "")
            for key in [
                "field_title",
                "field_recall_number",
                "field_recall_date",
                "field_recall_reason",
                "field_recall_classification",
                "field_risk_level",
                "field_product_items",
                "field_establishment",
                "field_states",
                "field_summary",
                "field_recall_type",
                "field_processing",
            ]
        ).lower()

        if not any(term in searchable for term in terms):
            continue

        recall_number = str(record.get("field_recall_number") or record.get("field_title") or "")
        if not recall_number or recall_number in seen:
            continue

        seen.add(recall_number)
        selected.append(record)

        if len(selected) >= max_records:
            break

    return selected




def payload_hash(records: list[dict[str, Any]]) -> str:
    canonical = json.dumps(records, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def manifest_entry(
    *,
    source_id: str,
    source_name: str,
    endpoint: str,
    snapshot_path: Path,
    records: list[dict[str, Any]],
    refreshed_at: str,
    mode: str = "local_curated_official_snapshot",
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "source_name": source_name,
        "endpoint": endpoint,
        "snapshot_path": str(snapshot_path.relative_to(ROOT)),
        "record_count": len(records),
        "refreshed_at": refreshed_at,
        "mode": mode,
        "payload_sha256": payload_hash(records),
    }


def write_snapshot_manifest(entries: list[dict[str, Any]]) -> None:
    SNAPSHOT_REFRESH_MANIFEST_OUT.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_REFRESH_MANIFEST_OUT.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "purpose": "Records official/public curated snapshot refresh metadata for RealWorldSafety sources.",
                "entries": entries,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote snapshot refresh manifest to {SNAPSHOT_REFRESH_MANIFEST_OUT}")


def print_dry_run(
    snapshots: list[tuple[Path, list[dict[str, Any]]]],
    manifest_entries: list[dict[str, Any]],
) -> None:
    print("Dry run: fetched snapshot data; no files will be written.")
    print("Planned snapshots:")
    for path, records in snapshots:
        print(
            f"  - {path.relative_to(ROOT)}: "
            f"{len(records)} records, sha256={payload_hash(records)}"
        )

    print(f"Planned manifest: {SNAPSHOT_REFRESH_MANIFEST_OUT.relative_to(ROOT)}")
    print(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "purpose": "Records official/public curated snapshot refresh metadata for RealWorldSafety sources.",
                "entries": manifest_entries,
            },
            indent=2,
            ensure_ascii=False,
        )
    )



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


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

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

    drug_label_queries = [
        'openfda.brand_name:"TYLENOL"',
        'openfda.generic_name:"ACETAMINOPHEN"',
        'openfda.brand_name:"ADVIL"',
        'openfda.generic_name:"IBUPROFEN"',
        'openfda.brand_name:"BENADRYL"',
        'openfda.generic_name:"DIPHENHYDRAMINE"',
        'openfda.brand_name:"CLARITIN"',
        'openfda.generic_name:"LORATADINE"',
        'openfda.generic_name:"METFORMIN"',
        'openfda.generic_name:"ALBUTEROL"',
    ]

    ndc_queries = [
        'brand_name:"TYLENOL"',
        'generic_name:"ACETAMINOPHEN"',
        'brand_name:"ADVIL"',
        'generic_name:"IBUPROFEN"',
        'brand_name:"BENADRYL"',
        'generic_name:"DIPHENHYDRAMINE"',
        'brand_name:"CLARITIN"',
        'generic_name:"LORATADINE"',
        'generic_name:"METFORMIN"',
        'generic_name:"ALBUTEROL"',
    ]

    device_queries = [
        'product_description:"glucose meter"',
        'product_description:"insulin pump"',
        'product_description:"CPAP"',
        'product_description:"syringe"',
        'product_description:"contact lens"',
        'reason_for_recall:"software"',
        'reason_for_recall:"battery"',
    ]

    device_event_queries = [
        'device.generic_name:"INSULIN PUMP"',
        'device.generic_name:"BLOOD GLUCOSE METER"',
        'device.generic_name:"VENTILATOR"',
        'device.brand_name:"TRILOGY"',
        'device.brand_name:"CPAP"',
    ]

    refreshed_at = datetime.now(timezone.utc).isoformat()
    snapshots: list[tuple[Path, list[dict[str, Any]]]] = []
    manifest_entries: list[dict[str, Any]] = []

    def add_snapshot(
        *,
        source_id: str,
        source_name: str,
        endpoint: str,
        snapshot_path: Path,
        records: list[dict[str, Any]],
    ) -> None:
        snapshots.append((snapshot_path, records))
        manifest_entries.append(
            manifest_entry(
                source_id=source_id,
                source_name=source_name,
                endpoint=endpoint,
                snapshot_path=snapshot_path,
                records=records,
                refreshed_at=refreshed_at,
            )
        )

    if args.source in {"all", "openfda"}:
        add_snapshot(
            source_id="openfda_food_enforcement",
            source_name="openFDA Food Enforcement API",
            endpoint=OPENFDA_FOOD_ENDPOINT,
            snapshot_path=OPENFDA_FOOD_OUT,
            records=fetch_source_records(
                source_name="openFDA Food Enforcement API",
                endpoint=OPENFDA_FOOD_ENDPOINT,
                fetcher=lambda: fetch_openfda_records(
                    OPENFDA_FOOD_ENDPOINT,
                    food_queries,
                    max_records=10,
                ),
            ),
        )
        add_snapshot(
            source_id="openfda_drug_enforcement",
            source_name="openFDA Drug Enforcement API",
            endpoint=OPENFDA_DRUG_ENDPOINT,
            snapshot_path=OPENFDA_DRUG_OUT,
            records=fetch_source_records(
                source_name="openFDA Drug Enforcement API",
                endpoint=OPENFDA_DRUG_ENDPOINT,
                fetcher=lambda: fetch_openfda_records(
                    OPENFDA_DRUG_ENDPOINT,
                    drug_queries,
                    max_records=12,
                ),
            ),
        )
        add_snapshot(
            source_id="openfda_drug_label",
            source_name="openFDA Drug Label API",
            endpoint=OPENFDA_DRUG_LABEL_ENDPOINT,
            snapshot_path=OPENFDA_DRUG_LABEL_OUT,
            records=fetch_source_records(
                source_name="openFDA Drug Label API",
                endpoint=OPENFDA_DRUG_LABEL_ENDPOINT,
                fetcher=lambda: fetch_openfda_drug_label_records(
                    drug_label_queries,
                    max_records=30,
                ),
            ),
        )
        add_snapshot(
            source_id="openfda_ndc_directory",
            source_name="openFDA NDC Directory API",
            endpoint=OPENFDA_NDC_ENDPOINT,
            snapshot_path=OPENFDA_NDC_OUT,
            records=fetch_source_records(
                source_name="openFDA NDC Directory API",
                endpoint=OPENFDA_NDC_ENDPOINT,
                fetcher=lambda: fetch_openfda_ndc_records(
                    ndc_queries,
                    max_records=40,
                ),
            ),
        )
        add_snapshot(
            source_id="openfda_device_enforcement",
            source_name="openFDA Device Enforcement API",
            endpoint=OPENFDA_DEVICE_ENDPOINT,
            snapshot_path=OPENFDA_DEVICE_OUT,
            records=fetch_source_records(
                source_name="openFDA Device Enforcement API",
                endpoint=OPENFDA_DEVICE_ENDPOINT,
                fetcher=lambda: fetch_openfda_records(
                    OPENFDA_DEVICE_ENDPOINT,
                    device_queries,
                    max_records=15,
                ),
            ),
        )
        add_snapshot(
            source_id="openfda_device_event",
            source_name="openFDA Device Event API",
            endpoint=OPENFDA_DEVICE_EVENT_ENDPOINT,
            snapshot_path=OPENFDA_DEVICE_EVENT_OUT,
            records=fetch_source_records(
                source_name="openFDA Device Event API",
                endpoint=OPENFDA_DEVICE_EVENT_ENDPOINT,
                fetcher=lambda: fetch_openfda_device_event_records(
                    device_event_queries,
                    max_records=30,
                ),
            ),
        )

    if args.source in {"all", "cpsc"}:
        add_snapshot(
            source_id="cpsc_recalls_api",
            source_name="CPSC Recalls API",
            endpoint=CPSC_RECALLS_ENDPOINT,
            snapshot_path=CPSC_DAILY_PRODUCTS_OUT,
            records=fetch_source_records(
                source_name="CPSC Recalls API",
                endpoint=CPSC_RECALLS_ENDPOINT,
                fetcher=lambda: fetch_cpsc_daily_product_records(max_records=80),
            ),
        )

    if args.source in {"all", "fsis"}:
        add_snapshot(
            source_id="usda_fsis_recall",
            source_name="USDA FSIS Recall API",
            endpoint=USDA_FSIS_ENDPOINT,
            snapshot_path=USDA_FSIS_OUT,
            records=fetch_source_records(
                source_name="USDA FSIS Recall API",
                endpoint=USDA_FSIS_ENDPOINT,
                fetcher=lambda: fetch_usda_fsis_records(max_records=100),
            ),
        )

    if args.dry_run:
        print_dry_run(snapshots, manifest_entries)
        return

    for snapshot_path, records in snapshots:
        write_records(snapshot_path, records)
    write_snapshot_manifest(manifest_entries)


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except SourceFetchError as error:
        print_source_fetch_error(error)
        raise SystemExit(1) from None
