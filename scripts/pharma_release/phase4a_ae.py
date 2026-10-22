"""Build and seal compact ingredient AE analytics in a new Phase 3B child."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import tempfile

from .ae_build import populate_ae, PROJECTION_TABLES
from .ae_derive import derive, RULE_VERSION, WINDOW_START, WINDOW_END, WINDOW_KEY, LIMITATIONS, ACTIVE_SQL, WINDOW_REPORTS_SQL, ELIGIBLE_SQL, SUMMARY_SQL, MONTHLY_SQL, PAIR_STATS_SQL, TOP_SQL
from .ae_sources import discover_ae_inputs, open_research, PARENT_PATH, PARENT_SHA256, RESEARCH_PATH, RESEARCH_SHA256, SUMMARY_PATH
from .ae_validation import parent_fingerprints, validate_ae, UNSTARTED
from .phase2 import output_paths, write_json
from .phase3_labels import readonly, schema_objects
from .schema_ae import extend_ae_schema, AE_TABLES, SCHEMA_VERSION, ae_schema_statements
from .sources import canonical_json, file_sha256, SourceError

BUILD_VERSION = "phase4a-ae-0.1.0"
RELEASE_VERSION = "dav-ai-pharma-v1-phase4a-ae-20261006"
TEST_FILES = [f"backend/tests/pharma_release/test_{phase}.py" for phase in ("phase1", "phase2", "phase3_labels", "phase3b_recalls", "phase4a_ae")]


def run(root, database, evidence):
    root = Path(root).resolve(); database, evidence = output_paths(root, database, evidence)
    parent = readonly(root / PARENT_PATH)
    try:
        tracker, parent_metadata, source, research_summary = discover_ae_inputs(root, parent)
        tracker.inspect("docs/pharma_release_phase4a_ae.md", hash_now=True)
        for directory in ("scripts/pharma_release", "backend/tests/pharma_release"):
            for file in sorted((root / directory).glob("*")):
                if file.is_file(): tracker.inspect(file.relative_to(root), hash_now=True)
        command = [str(root / ".venv/bin/python"), "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", *TEST_FILES]
        tests = subprocess.run(command, cwd=root, env=os.environ | {"PYTHONDONTWRITEBYTECODE": "1"}, capture_output=True, text=True)
        if tests.returncode:
            print(tests.stdout + tests.stderr, flush=True); raise SourceError("Focused Phase 1/2/3A/3B/4A tests failed")
        print(tests.stdout.strip(), flush=True)
        for table in (*AE_TABLES, *UNSTARTED):
            if parent.execute(f"SELECT count(*) FROM {table}").fetchone()[0]: raise SourceError("Parent is not the Phase 3B checkpoint")
        original_schema = schema_objects(parent); frozen = parent_fingerprints(parent)
        ingredient_ids = {row[0] for row in parent.execute("SELECT ingredient_id FROM ingredients")}
        cursor = parent.execute("SELECT * FROM release_manifest")
        parent_manifest = dict(zip([field[0] for field in cursor.description], cursor.fetchone()))
    finally:
        parent.close()
    evidence.mkdir(parents=True, exist_ok=False); database.parent.mkdir(parents=True, exist_ok=False)
    staged = database.parent / "ae.building.sqlite"
    with (root / PARENT_PATH).open("rb") as source_file, staged.open("xb") as target:
        shutil.copyfileobj(source_file, target, length=1024 * 1024)
    staged.chmod(0o644)
    connection = sqlite3.connect(staged); connection.execute("PRAGMA foreign_keys=ON")
    build_time = datetime.now(timezone.utc).isoformat()
    try:
        schema_diff = extend_ae_schema(connection)
        with tempfile.TemporaryDirectory(prefix="dav-phase4a-", dir="/private/tmp") as temporary_directory:
            research = open_research(root / RESEARCH_PATH, temporary_directory)
            try:
                derivation = derive(research, ingredient_ids)
                with connection: report = populate_ae(connection, research, source["source_id"])
                print("Populated compact AE serving projections", flush=True)
                validation = validate_ae(connection, report, derivation, frozen)
                if not validation["passed"]:
                    write_json(evidence / "failed_validation.json", validation); write_json(evidence / "failed_derivation.json", derivation)
                    raise SourceError("AE benchmarks/semantic gates failed; investigate without changing expected values")
                before = {table: connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in PROJECTION_TABLES}
                changes_before = connection.total_changes
                replay_derivation = derive(research, ingredient_ids)
                with connection: replay_report = populate_ae(connection, research, source["source_id"])
                after = {table: connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in PROJECTION_TABLES}
                replay = {"passed": before == after and derivation == replay_derivation and connection.total_changes == changes_before
                    and all(replay_report["projection"][table]["inserted"] == 0
                        and replay_report["projection"][table]["identical_replays"] == report["projection"][table]["projected_rows"]
                        and replay_report["projection"][table]["sha256_sorted_row_hashes"] == report["projection"][table]["sha256_sorted_row_hashes"] for table in PROJECTION_TABLES),
                    "research_derivation_executed_twice": True, "eligible_ingredient_report_associations_rederived": replay_derivation["eligible_ingredient_report_associations"],
                    "sqlite_row_changes": connection.total_changes - changes_before, "table_counts_before": before, "table_counts_after": after, "projection": replay_report["projection"]}
                if not replay["passed"]: raise SourceError("AE full derivation replay/idempotency failed")
                print("Replayed full AE derivation/population with zero SQLite row changes", flush=True)
            finally:
                research.close()
        new_sql = dict(zip(AE_TABLES, [sql.rstrip(";") for sql in ae_schema_statements()]))
        expected_schema = [(kind, name, table, new_sql[name] if kind == "table" and name in new_sql else sql) for kind, name, table, sql in original_schema]
        if schema_objects(connection) != expected_schema: raise SourceError("Unexpected non-AE schema object change")
        schema_diff.update({"other_schema_objects_identical": True, "logical_tables": 19, "parent_user_version": 3})
        counts = validation["table_counts"]
        lineage = {"kind": "INGREDIENT_AE_ANALYTICS_BUILD", "source_id": source["source_id"], "research_path": RESEARCH_PATH,
            "research_sha256": RESEARCH_SHA256, "research_summary_sha256": tracker.records[SUMMARY_PATH]["sha256"],
            "original_source_capture_id": source["capture_id"], "original_source_transform_version": source["transform_version"],
            "research_created_at": research_summary.get("created_at"), "research_analysis_code_sha256": research_summary.get("analysis_code_sha256"),
            "research_input_file_ids": research_summary.get("input_file_ids"), "research_availability_basis": research_summary.get("availability_basis"),
            "window_start": WINDOW_START, "window_end": WINDOW_END, "rule_version": RULE_VERSION,
            "generated_at": build_time, "limitation": LIMITATIONS[3]}
        manifest = parent_manifest | {"release_id": RELEASE_VERSION, "schema_version": SCHEMA_VERSION, "build_version": BUILD_VERSION, "build_time_utc": build_time,
            "table_counts_json": canonical_json(counts), "unresolved_counts_json": canonical_json(json.loads(parent_manifest["unresolved_counts_json"]) | {
                "ae_analytics": {"release_ingredients_without_analytics": len(ingredient_ids) - derivation["identity"]["ae_active_ingredients"], "normal_products_without_active_component": validation["product_coverage"]["uncovered"]}}),
            "source_vintages_json": canonical_json(json.loads(parent_manifest["source_vintages_json"]) + [
                {"kind": "PARENT_RELEASE", "release_id": parent_metadata["release_version"], "database_path": PARENT_PATH, "database_sha256": PARENT_SHA256}, lineage]),
            "validation_results_json": canonical_json(json.loads(parent_manifest["validation_results_json"]) | {
                "phase": "4A", "ae_started": True, "communications_started": False, "ae_validation_passed": True,
                "full_ae_derivation_replay_passed": True, "focused_phase1_2_3a_3b_4a_tests_passed": True, "safe_to_proceed_to_safety_communications": True, "publication_validated": False})}
        with connection:
            connection.execute("UPDATE sources SET verification_basis=?,inputs_json=?,transform_version=? WHERE source_id=?",
                ("FRESH_RESEARCH_AND_SUMMARY_SHA256; READ_ONLY_CURRENT_NORMALIZED_SNAPSHOT; FULL_DEDUP_DERIVATION_REPLAY_VERIFIED",
                 canonical_json([tracker.records[RESEARCH_PATH], tracker.records[SUMMARY_PATH]]), BUILD_VERSION, source["source_id"]))
            connection.execute("DELETE FROM release_manifest")
            connection.execute("INSERT INTO release_manifest (" + ",".join(manifest) + ") VALUES (" + ",".join("?" for _ in manifest) + ")", list(manifest.values()))
        actual_counts = {table: connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0] for table in counts}
        if actual_counts != json.loads(manifest["table_counts_json"]): raise SourceError("Manifest count mismatch")
        if connection.execute("PRAGMA foreign_key_check").fetchall() or connection.execute("PRAGMA integrity_check").fetchall() != [("ok",)]: raise SourceError("Final SQLite structural validation failed")
    finally:
        connection.close()
    tracker.assert_unchanged()
    for relative, pinned in ((PARENT_PATH, PARENT_SHA256), (RESEARCH_PATH, RESEARCH_SHA256)):
        if file_sha256(root / relative) != pinned: raise SourceError("Protected parent/research input changed")
    staged.chmod(0o444); os.link(staged, database); staged.unlink()
    metadata = {"phase": "4A", "release_version": RELEASE_VERSION, "build_version": BUILD_VERSION, "schema_version": SCHEMA_VERSION,
        "policy_version": "1.0.0", "ae_rule_version": RULE_VERSION, "build_time_utc": build_time, "database_path": str(database.relative_to(root)),
        "database_bytes": database.stat().st_size, "database_sha256": file_sha256(database), "file_mode": oct(database.stat().st_mode & 0o777),
        "parent_release_path": PARENT_PATH, "parent_release_sha256": PARENT_SHA256, "research_path": RESEARCH_PATH, "research_sha256": RESEARCH_SHA256,
        "window_start": WINDOW_START, "window_end": WINDOW_END, "table_counts": counts, "safe_to_proceed_to_safety_communications": True,
        "ae_started": True, "communications_started": False, "publication_validated": False}
    rules = {"rule_version": RULE_VERSION, "window": {"start_inclusive": WINDOW_START, "end_inclusive": WINDOW_END, "end_exclusive": "2026-07-01"},
        "temporal_rule": "TRY_CAST(first_received AS DATE) and TRY_CAST(last_received AS DATE) nonnull; first<=last; last>=2020-01-01 and last<2026-07-01",
        "aggregation_type": "Exact ingredient-report deduplication; summary/month outcomes separate from reaction-granular ranking", "role_dedup": "Boolean OR over duplicate ingredient/report memberships", "top_reaction_cap": 50,
        "execution_bounds": {"duckdb_memory_limit": "2GB", "threads": 2, "preserve_insertion_order": False},
        "sql": {"active": ACTIVE_SQL, "window_reports": WINDOW_REPORTS_SQL, "eligible": ELIGIBLE_SQL, "summary": SUMMARY_SQL, "monthly": MONTHLY_SQL, "pair_stats": PAIR_STATS_SQL, "top_reactions": TOP_SQL}, "limitations": LIMITATIONS}
    outputs = {"build_summary.json": metadata | {"identity": derivation["identity"], "product_coverage": validation["product_coverage"], "phase_boundary": "STOP_AFTER_4A"},
        "release_metadata.json": metadata, "source_inventory.json": {"inputs": list(tracker.records.values()), "lineage": lineage, "read_only_research": True, "temporary_spill_location": "task-owned /private/tmp directory removed at completion"},
        "derivation_rules.json": rules, "derivation_measurements.json": derivation, "serving_projection.json": report,
        "identity_overlap.json": derivation["identity"], "product_coverage.json": validation["product_coverage"], "monthly_reconciliation.json": derivation["monthly_reconciliation"],
        "spot_checks.json": validation["spot_checks"], "validation.json": validation, "replay.json": replay, "schema_diff.json": schema_diff, "table_counts.json": counts,
        "tests.json": {"passed": True, "command": command, "exit_code": tests.returncode, "stdout": tests.stdout, "stderr": tests.stderr}}
    for name, value in outputs.items(): write_json(evidence / name, value)
    write_json(database.parent / "release_metadata.json", metadata)
    print(canonical_json(metadata), flush=True)
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--database", type=Path, required=True); parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args(); run(args.root, args.database, args.evidence)


if __name__ == "__main__": main()
