"""Build a new immutable identity-only SQLite artifact; never starts Phase 3."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3

from . import CONTRACT_ID, POLICY_VERSION
from .eligibility import LISTING_SEMANTICS
from .identity import parquet_rows, populate_identity
from .schema_phase2 import create_phase2_schema, phase2_schema_sql, PHASE2_SCHEMA_VERSION
from .search import lookup_name, lookup_identifier, candidate_details
from .sources import discover_sources, register_sources, file_sha256, canonical_json, SourceError
from .validation_phase2 import validate_identity, ambiguity_report

PHASE2_BUILD_VERSION = "phase2-0.1.0"
RELEASE_VERSION = "dav-ai-pharma-v1-phase2-20261006"


def output_paths(root, database, evidence):
    root = Path(root).resolve(); database = Path(database).resolve(); evidence = Path(evidence).resolve()
    if not database.is_relative_to(root / "data/releases") or database.suffix != ".sqlite" or database.parent.exists():
        raise ValueError("Database must be in a new versioned data/releases directory")
    if not evidence.is_relative_to(root / "docs/evidence") or not evidence.name.startswith("pharma-release-v1-build-"):
        raise ValueError("Evidence must be a new pharma-release-v1-build-* directory")
    if evidence.exists() or database.exists():
        raise FileExistsError("Refusing to overwrite existing outputs")
    return database, evidence


def write_json(path, value):
    with Path(path).open("x") as f:
        json.dump(value, f, indent=2, ensure_ascii=False)
        f.write("\n")


def search_demonstrations(connection):
    cases = {}
    requested = [("Semaglutide", "INGREDIENT", "Semaglutide"), ("Ozempic", "BRAND", "Ozempic"),
        ("Wegovy", "BRAND", "Wegovy"), ("Metformin", "GENERIC", "Metformin hydrochloride"),
        ("Lipitor", "BRAND", "Lipitor"), ("Eliquis", "BRAND", "Eliquis"), ("Jardiance", "BRAND", "Jardiance"),
        ("Mounjaro", "BRAND", "Mounjaro"), ("Amoxicillin", "INGREDIENT", "Amoxicillin")]
    for label, role, value in requested:
        ids = lookup_name(connection, value, role)
        cases[label] = {"lookup_role": role, "exact_source_name_query": value, "candidate_count": len(ids),
            "samples": [candidate_details(connection, pid) for pid in ids[:3]], "passed": bool(ids)}
        if label == "Metformin":
            cases[label]["query_note"] = "Uses the actual source generic name 'Metformin hydrochloride'; no synonym or chemical-equivalence mapping was introduced."
    extra_sql = {
        "combination": "SELECT product_id FROM products WHERE is_combination=1 AND eligibility_mode='NORMAL_CONSUMER' ORDER BY product_id LIMIT 1",
        "otc": "SELECT product_id FROM products WHERE product_type='HUMAN OTC DRUG' AND eligibility_mode='NORMAL_CONSUMER' ORDER BY product_id LIMIT 1",
        "homeopathic_unapproved": "SELECT product_id FROM products WHERE marketing_category='UNAPPROVED HOMEOPATHIC' ORDER BY product_id LIMIT 1",
        "unresolved_kit": "SELECT product_id FROM products WHERE ingredient_set_complete=0 AND finished=1 AND dosage_form='KIT' ORDER BY product_id LIMIT 1",
    }
    for label, sql in extra_sql.items():
        row = connection.execute(sql).fetchone()
        cases[label] = {"selection_sql": sql, "passed": row is not None, "sample": candidate_details(connection, row[0]) if row else None}
    demos = []
    for role, value in (("BRAND", "Ozempic"), ("GENERIC", "Metformin hydrochloride"), ("INGREDIENT", "Semaglutide")):
        ids = lookup_name(connection, value, role)
        demos.append({"lookup": role, "query": value, "candidate_count": len(ids), "sample_product_ids": ids[:5], "returns_all_candidates": True})
    for kind in ("PRODUCT_NDC", "PACKAGE_NDC", "RXCUI"):
        # Prefer a low-cardinality ambiguous value, so every candidate can be shown.
        row = connection.execute("SELECT value,count(*) n FROM product_identifiers WHERE identifier_type=? GROUP BY value HAVING n>1 ORDER BY n,value LIMIT 1", (kind,)).fetchone()
        if not row:
            row = connection.execute("SELECT value,count(*) FROM product_identifiers WHERE identifier_type=? GROUP BY value ORDER BY value LIMIT 1", (kind,)).fetchone()
        ids = lookup_identifier(connection, kind, row[0]) if row else []
        demos.append({"lookup": kind, "query": row[0] if row else None, "candidate_count": len(ids), "all_product_ids": ids,
                      "returns_all_candidates": len(ids) == row[1] if row else False})
    ambiguous = next((d for d in demos if d.get("candidate_count", 0) > 1 and "all_product_ids" in d), None)
    cases["ambiguous_identifier"] = {"passed": ambiguous is not None, "lookup": ambiguous,
        "samples": [candidate_details(connection, pid) for pid in ambiguous["all_product_ids"]] if ambiguous else []}
    plans = {
        "brand": connection.execute("EXPLAIN QUERY PLAN SELECT product_id FROM search_names WHERE normalized_name=? AND entity_type='PRODUCT' AND name_role='BRAND'", ("ozempic",)).fetchall(),
        "product_ndc": connection.execute("EXPLAIN QUERY PLAN SELECT product_id FROM product_identifiers WHERE identifier_type='PRODUCT_NDC' AND value=?", ("example",)).fetchall(),
    }
    return {"representative_cases": cases, "database_lookups": demos, "query_plans": plans,
        "passed": all(c["passed"] for c in cases.values()) and all(d["candidate_count"] and d["returns_all_candidates"] for d in demos),
        "semantics": "Exact source-backed case/whitespace-normalized names and exact identifiers. Every candidate is returned in stable product-ID order; role does not imply exclusive commercial brand. Regulatory-only products remain inspectable; future default consumer search must filter eligibility."}


def run(root, database, evidence):
    root = Path(root).resolve()
    database, evidence = output_paths(root, database, evidence)
    catalog = discover_sources(root)
    for directory in ("scripts/pharma_release", "backend/tests/pharma_release", "docs/evidence/pharma-release-v1-build-2026-10-06-phase1"):
        for path in sorted((root / directory).glob("*")):
            if path.is_file():
                catalog.tracker.inspect(path.relative_to(root), hash_now=True)
    build_time = datetime.now(timezone.utc).isoformat()
    raw_source = next(s for s in catalog.sources if s.source_name == "openfda_ndc_directory" and s.source_kind == "RAW_SNAPSHOT")
    identity_source = next(s for s in catalog.sources if s.source_name == "openfda_ndc_directory" and s.source_kind == "DERIVED")
    evidence.mkdir(parents=True, exist_ok=False)
    database.parent.mkdir(parents=True, exist_ok=False)
    staged = database.parent / "identity.building.sqlite"
    # Exclusive creation plus fresh schema initialization prohibit overwrites.
    with staged.open("xb"):
        pass
    connection = sqlite3.connect(staged)
    try:
        create_phase2_schema(connection)
        register_sources(connection, catalog)
        with connection, (evidence / "source_product_audit.jsonl").open("x") as audit:
            measured = populate_identity(connection,
                parquet_rows(root / "data/research/identity/ingredients.parquet"),
                parquet_rows(root / "data/research/identity/formulations.parquet"),
                parquet_rows(root / "data/research/identity/products.parquet"),
                parquet_rows(root / raw_source.input_paths[0]), raw_source.source_id, identity_source.source_id, audit)
        fixture = catalog.measurements["step1_eligibility_expected"]
        validation = validate_identity(connection, measured, fixture)
        demonstration = search_demonstrations(connection)
        if not demonstration["passed"]:
            validation["errors"].append({"gate": "representative_and_sqlite_search_demonstrations"})
            validation["passed"] = False
        if not validation["passed"]:
            write_json(evidence / "failed_validation.json", validation)
            raise SourceError("Phase 2 identity gates failed; staged artifact is not a release")
        ambiguity = ambiguity_report(connection)
        presentations = dict(connection.execute("SELECT consumer_classification,count(*) FROM products GROUP BY consumer_classification"))
        final_counts = dict(validation["table_counts"]); final_counts["release_manifest"] = 1
        source_vintages = [{"source_id": s.source_id, "export_date": s.export_date, "observed_at": s.observed_at, "captured_at": s.captured_at,
            "phase2_used_for_identity": s.source_id in {raw_source.source_id, identity_source.source_id}} for s in catalog.sources]
        internal_validation = {"phase": 2, "identity_passed": True, "regulatory_evidence_assessed": False, "publication_validated": False,
            "integrity_check": validation["integrity_check"], "foreign_key_violations": validation["foreign_key_violations"],
            "source_product_count": measured["source_product_count"], "consumer_classification_counts": presentations,
            "source_identifier_counts": measured["source_identifier_counts"], "representative_search_passed": True,
            "listing_semantics": LISTING_SEMANTICS, "identity_only_checkpoint": True,
            "schema_extension": "Five additive product fields; original Phase 1 DDL and policy unchanged."}
        manifest = {"release_id": RELEASE_VERSION, "contract_id": CONTRACT_ID, "policy_version": POLICY_VERSION,
            "schema_version": PHASE2_SCHEMA_VERSION, "build_version": PHASE2_BUILD_VERSION, "build_time_utc": build_time,
            "ndc_observation_date": "2026-09-26", "label_export_date": "2026-09-25", "label_capture_date": "2026-09-26",
            "window_start": "2020-01-01", "window_end": "2026-06-30", "source_vintages_json": canonical_json(source_vintages),
            "table_counts_json": canonical_json(final_counts), "eligibility_counts_json": canonical_json(measured["eligibility_counts"]),
            "unresolved_counts_json": canonical_json({"finished_human_identity": measured["finished_human"]["unresolved"], "labels": None, "recalls": None, "ae_analytics": None, "safety_communications": None}),
            "validation_results_json": canonical_json(internal_validation), "digest_strategy": "EXTERNAL_FINAL_FILE_SHA256", "content_digest": None}
        with connection:
            columns = list(manifest)
            connection.execute("INSERT INTO release_manifest (" + ",".join(columns) + ") VALUES (" + ",".join("?" for _ in columns) + ")", [manifest[c] for c in columns])
        # Recheck the actual final file, including the manifest row.
        validation = validate_identity(connection, measured, fixture)
        validation["manifest_table_counts_match"] = validation["table_counts"] == final_counts
        if not validation["passed"] or not validation["manifest_table_counts_match"]:
            raise SourceError("Final Phase 2 validation failed")
    finally:
        connection.close()
    catalog.tracker.assert_unchanged()
    # Rehash only previously freshly verified files; large deferred inputs stay stat-only.
    fresh_verified = []
    for record in catalog.tracker.records.values():
        if record["sha256"]:
            if file_sha256(root / record["path"]) != record["sha256"]:
                raise SourceError("Protected content changed: " + record["path"])
            fresh_verified.append(record["path"])
    # Link is exclusive, unlike replace/rename on POSIX. The release inode is sealed.
    staged.chmod(0o444)
    os.link(staged, database)
    staged.unlink()
    metadata = {"database_path": database.relative_to(root).as_posix(), "database_bytes": database.stat().st_size,
        "database_sha256": file_sha256(database), "release_version": RELEASE_VERSION, "schema_version": PHASE2_SCHEMA_VERSION,
        "build_version": PHASE2_BUILD_VERSION, "build_time_utc": build_time, "source_ids": [s.source_id for s in catalog.sources],
        "table_counts": final_counts, "file_mode": oct(database.stat().st_mode & 0o777), "phase": 2,
        "regulatory_evidence_populated": False, "publication_validated": False}
    # Read-only final-file verification and demonstrations, not a mutable research DB.
    with sqlite3.connect(database.as_uri() + "?mode=ro&immutable=1", uri=True) as readonly:
        readonly.execute("PRAGMA foreign_keys=ON")
        final = validate_identity(readonly, measured, fixture)
        if not final["passed"] or final["table_counts"] != final_counts:
            raise SourceError("Immutable final file failed validation")
        validation = final | {"manifest_table_counts_match": True, "final_file_read_only_validated": True,
            "representative_search_passed": demonstration["passed"], "safe_to_proceed_to_phase3": True, "publication_validated": False}
    preservation = {"protected_input_count": len(catalog.tracker.records), "fresh_sha256_rechecked_count": len(fresh_verified),
        "fresh_sha256_rechecked_paths": fresh_verified, "all_protected_sizes_mtimes_unchanged": True,
        "all_fresh_hashes_unchanged": True, "deferred_full_hash_paths": [r["path"] for r in catalog.tracker.records.values() if not r["sha256"]],
        "no_source_writes": True, "phase1_artifacts_preserved": True,
        "limitations": ["Large label ZIPs, research DuckDB and application dump were not fully freshly hashed. Only their size/mtime and available recorded archive hashes are claimed."]}
    public_measured = {k: v for k, v in measured.items() if k not in {"excluded_source_record_ids", "expected_sqlite_rows"}}
    public_measured["runtime_presentation_counts"] = presentations
    for filename, payload in (("validation.json", validation), ("table_counts.json", final_counts), ("release_metadata.json", metadata),
            ("identity_measurements.json", public_measured), ("ambiguity.json", ambiguity), ("search_demonstrations.json", demonstration),
            ("source_inventory.json", catalog.report()), ("preservation.json", preservation)):
        write_json(evidence / filename, payload)
    with (evidence / "schema.sql").open("x") as f:
        f.write(phase2_schema_sql())
    write_json(database.parent / "release_metadata.json", metadata)
    catalog.tracker.assert_unchanged()
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.root, args.database, args.evidence_dir), indent=2))


if __name__ == "__main__":
    main()
