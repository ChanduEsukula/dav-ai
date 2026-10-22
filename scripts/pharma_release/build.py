"""Phase-1-only entry point. No persistent SQLite release is produced."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3

from . import BUILD_VERSION, CONTRACT_ID, POLICY_VERSION, SCHEMA_VERSION
from .schema import create_schema, schema_sql
from .sources import SourceError, discover_sources, register_sources
from .validation import validate_structure


def phase1(root, output):
    root = Path(root).resolve()
    output = Path(output).resolve()
    evidence_root = (root / "docs/evidence").resolve()
    if not output.is_relative_to(evidence_root) or not output.name.startswith("pharma-release-v1-build-"):
        raise ValueError("Phase 1 output must be a new pharma-release-v1-build-* evidence directory")
    if output.exists():
        raise FileExistsError("Refusing to overwrite existing evidence")
    # Discovery and validation complete before any output directory is created.
    catalog = discover_sources(root)
    with sqlite3.connect(":memory:") as connection:
        create_schema(connection)
        register_sources(connection, catalog)
        validation = validate_structure(connection)
    if not validation["passed"]:
        raise SourceError("Phase 1 structural gate failed: " + json.dumps(validation["errors"]))
    source_report = catalog.report()
    summary = {"phase": 1, "status": "VALIDATED_SCHEMA_AND_SOURCE_INFRASTRUCTURE",
        "contract_id": CONTRACT_ID, "policy_version": POLICY_VERSION, "schema_version": SCHEMA_VERSION,
        "build_version": BUILD_VERSION, "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "release_created": False, "phase2_started": False, "source_descriptors": len(catalog.sources),
        "tables": validation["table_count"], "table_counts": validation["table_counts"],
        "unresolved_records": None, "unresolved_reason": "Not evaluated; no applicability/identity ingestion in Phase 1",
        "safe_to_proceed_to_phase2": True, "publication_validated": False}
    output.mkdir(parents=True, exist_ok=False)
    for name, value in (("phase1_summary.json", summary), ("source_inventory.json", source_report),
                        ("validation.json", validation), ("table_counts.json", validation["table_counts"])):
        with (output / name).open("x") as f:
            json.dump(value, f, indent=2, ensure_ascii=False)
            f.write("\n")
    with (output / "schema.sql").open("x") as f:
        f.write(schema_sql())
    catalog.tracker.assert_unchanged()
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", type=int, choices=[1], required=True)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--evidence-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(phase1(args.root, args.evidence_dir), indent=2))


if __name__ == "__main__":
    main()
