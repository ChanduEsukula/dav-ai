"""Build and seal only Phase 3B recall evidence in a new Phase 3A child."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys

from .phase2 import output_paths, write_json
from .phase3_labels import readonly, schema_objects
from .recall_applicability import RecallIndex, NDC_PATTERN, RULE_VERSION, TEXT_FIELDS
from .recall_build import RecallCorpus, PROJECTION_TABLES
from .recall_sources import discover_recall_inputs, stream_enforcement, PARENT_PATH, PARENT_SHA256, PARQUET, PARTITION, SOURCE_NAME
from .recall_validation import parent_fingerprints, validate_recalls, spot_checks, UNSTARTED
from .schema_recalls import extend_recall_method, SCHEMA_VERSION
from .sources import canonical_json, file_sha256, SourceError

BUILD_VERSION = "phase3b-recalls-0.1.0"
RELEASE_VERSION = "dav-ai-pharma-v1-phase3b-recalls-20261006"
TEST_FILES = [f"backend/tests/pharma_release/test_{phase}.py" for phase in ("phase1", "phase2", "phase3_labels", "phase3b_recalls")]


def run(root, database, evidence):
    root = Path(root).resolve(); database, evidence = output_paths(root, database, evidence)
    tracker, parent_metadata, snapshot = discover_recall_inputs(root)
    tracker.inspect("docs/pharma_release_phase3b_recalls.md", hash_now=True)
    for directory in ("scripts/pharma_release", "backend/tests/pharma_release"):
        for path in sorted((root / directory).glob("*")):
            if path.is_file(): tracker.inspect(path.relative_to(root), hash_now=True)
    command = [str(root / ".venv/bin/python"), "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", *TEST_FILES]
    test_run = subprocess.run(command, cwd=root, env=os.environ | {"PYTHONDONTWRITEBYTECODE": "1"}, capture_output=True, text=True)
    if test_run.returncode:
        print(test_run.stdout + test_run.stderr, flush=True)
        raise SourceError("Focused Phase 1/2/3A/3B tests failed")
    print(test_run.stdout.strip(), flush=True)
    parent = readonly(root / PARENT_PATH)
    try:
        original_schema = schema_objects(parent)
        for table in ("recalls", "product_recalls", *UNSTARTED):
            if parent.execute(f"SELECT count(*) FROM {table}").fetchone()[0]: raise SourceError("Parent is not the Phase 3A checkpoint")
        source = parent.execute("SELECT source_id,inputs_json FROM sources WHERE source_name=?", (SOURCE_NAME,)).fetchone()
        if source is None: raise SourceError("Parent enforcement source is missing")
        pinned = {v["path"]: v["sha256"] or v["recorded_sha256"] for v in json.loads(source[1])}
        if pinned.get(PARQUET) != tracker.records[PARQUET]["sha256"]:
            raise SourceError("Enforcement partition differs from frozen parent provenance")
        parent_manifest_cursor = parent.execute("SELECT * FROM release_manifest")
        parent_manifest = dict(zip([v[0] for v in parent_manifest_cursor.description], parent_manifest_cursor.fetchone()))
        frozen = parent_fingerprints(parent)
    finally:
        parent.close()
    evidence.mkdir(parents=True, exist_ok=False); database.parent.mkdir(parents=True, exist_ok=False)
    staged = database.parent / "recalls.building.sqlite"
    with (root / PARENT_PATH).open("rb") as source_file, staged.open("xb") as target:
        shutil.copyfileobj(source_file, target, length=1024 * 1024)
    staged.chmod(0o644)
    connection = sqlite3.connect(staged); connection.execute("PRAGMA foreign_keys=ON")
    build_time = datetime.now(timezone.utc).isoformat()
    expected_envelope = {"export_date": "2026-09-25", "observed_at": snapshot["snapshot"]["observed_at"],
        "source_url": snapshot["receipt"]["url"], "quarter": "enforcement"}
    try:
        schema_diff = extend_recall_method(connection)
        index = RecallIndex(connection)
        with (evidence / "recall_admission_audit.jsonl").open("x") as audit:
            corpus = RecallCorpus(connection, index, source[0], audit, expected_envelope)
            with connection:
                for n, envelope in enumerate(stream_enforcement(root / PARQUET), 1): corpus.process(envelope, n)
                corpus.finalize_coverage()
        report = corpus.report(); print("Built enforcement corpus: " + str(n), flush=True)
        validation = validate_recalls(connection, report, frozen)
        spots = spot_checks(connection)
        if not spots["passed"]: validation["errors"].append({"gate": "known_recall_spot_checks"}); validation["passed"] = False
        if not validation["passed"]:
            write_json(evidence / "failed_validation.json", validation)
            write_json(evidence / "failed_spot_checks.json", spots)
            raise SourceError("Recall benchmarks/semantic gates failed; investigate without changing expected benchmarks")
        before = {t: connection.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in PROJECTION_TABLES}
        total_changes_before = connection.total_changes
        replay_corpus = RecallCorpus(connection, index, source[0], expected_envelope=expected_envelope)
        with connection:
            for n, envelope in enumerate(stream_enforcement(root / PARQUET), 1): replay_corpus.process(envelope, n)
            replay_corpus.finalize_coverage()
        replay_report = replay_corpus.report()
        after = {t: connection.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in PROJECTION_TABLES}
        replay = {"passed": report["counts"] == replay_report["counts"] and before == after and connection.total_changes == total_changes_before
            and all(replay_report["projection"][t]["inserted"] == 0
                and replay_report["projection"][t]["identical_replays"] == report["projection"][t]["projected_rows"]
                and replay_report["projection"][t]["sha256_sorted_row_hashes"] == report["projection"][t]["sha256_sorted_row_hashes"] for t in PROJECTION_TABLES),
            "full_corpus_records_reprocessed": n, "table_counts_before": before, "table_counts_after": after,
            "sqlite_row_changes": connection.total_changes - total_changes_before, "projection": replay_report["projection"]}
        if not replay["passed"]: raise SourceError("Full-source recall replay failed")
        print("Replayed all enforcement rows with zero SQLite row changes", flush=True)
        expected_schema = [(kind, name, table, sql.replace("'EXACT_NDC'", "'EXACT_NDC', 'EXACT_PRODUCT_NDC'") if name == "product_recalls" and kind == "table" else sql)
            for kind, name, table, sql in original_schema]
        if schema_objects(connection) != expected_schema: raise SourceError("Unexpected schema object change")
        schema_diff.update({"other_schema_objects_identical": True, "logical_tables": 19, "parent_user_version": 2})
        counts = validation["table_counts"]
        manifest = parent_manifest | {"release_id": RELEASE_VERSION, "schema_version": SCHEMA_VERSION, "build_version": BUILD_VERSION,
            "build_time_utc": build_time, "table_counts_json": canonical_json(counts),
            "unresolved_counts_json": canonical_json(json.loads(parent_manifest["unresolved_counts_json"]) | {"recalls": report["counts"]}),
            "source_vintages_json": canonical_json(json.loads(parent_manifest["source_vintages_json"]) + [
                {"kind": "PARENT_RELEASE", "database_path": PARENT_PATH, "database_sha256": PARENT_SHA256, "release_id": parent_metadata["release_version"]},
                {"kind": "RECALL_BUILD", "source_id": source[0], "export_date": "2026-09-25", "observed_at": expected_envelope["observed_at"],
                 "parquet_path": PARQUET, "parquet_sha256": tracker.records[PARQUET]["sha256"], "quarantined": 1, "rule_version": RULE_VERSION}]),
            "validation_results_json": canonical_json(json.loads(parent_manifest["validation_results_json"]) | {
                "phase": "3B", "recalls_started": True, "ae_started": False, "communications_started": False,
                "recall_validation_passed": True, "full_recall_replay_passed": True, "focused_phase1_2_3a_3b_tests_passed": True,
                "safe_to_proceed_to_ae_communications": True, "publication_validated": False})}
        with connection:
            connection.execute("UPDATE sources SET verification_basis=?,inputs_json=?,transform_version=? WHERE source_id=?",
                ("FRESH_SHA256_VERIFIED_AGAINST_PINNED_RECEIPT_AND_PARENT; COMPLETE_USABLE_ENFORCEMENT_CORPUS_REPLAYED",
                 canonical_json([tracker.records[PARQUET], tracker.records[PARTITION + "/quarantine.jsonl"]]), BUILD_VERSION, source[0]))
            connection.execute("DELETE FROM release_manifest")
            connection.execute("INSERT INTO release_manifest (" + ",".join(manifest) + ") VALUES (" + ",".join("?" for _ in manifest) + ")", list(manifest.values()))
        actual_counts = {t: connection.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in counts}
        if actual_counts != json.loads(manifest["table_counts_json"]): raise SourceError("Manifest count mismatch")
        if connection.execute("PRAGMA foreign_key_check").fetchall() or connection.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
            raise SourceError("Final SQLite structural validation failed")
    finally:
        connection.close()
    tracker.assert_unchanged()
    # Rehash the protected parent and raw partition after all build/replay work.
    if file_sha256(root / PARENT_PATH) != PARENT_SHA256 or file_sha256(root / PARQUET) != tracker.records[PARQUET]["sha256"]:
        raise SourceError("Protected parent/source changed")
    staged.chmod(0o444); os.link(staged, database); staged.unlink()
    metadata = {"phase": "3B", "release_version": RELEASE_VERSION, "build_version": BUILD_VERSION, "schema_version": SCHEMA_VERSION,
        "policy_version": "1.0.0", "recall_rule_version": RULE_VERSION, "build_time_utc": build_time,
        "database_path": str(database.relative_to(root)), "database_bytes": database.stat().st_size,
        "database_sha256": file_sha256(database), "file_mode": oct(database.stat().st_mode & 0o777),
        "parent_release_path": PARENT_PATH, "parent_release_sha256": PARENT_SHA256, "table_counts": counts,
        "safe_to_proceed_to_ae_communications": True, "recalls_started": True, "ae_started": False, "communications_started": False, "publication_validated": False}
    rules = {"rule_version": RULE_VERSION, "pattern": NDC_PATTERN, "text_fields": TEXT_FIELDS,
        "scope_authority": "Explicit NDC-marked recall text only; harmonized metadata never expands scope",
        "resolution": "Exact clean PACKAGE_NDC first; absent package uses exact unique/conflict-free first-two-segment PRODUCT_NDC. Ambiguous/conflicted identifiers are held back. Regex fragments followed by a digit remain audited unmatched rather than silently shortening an overlong NDC.",
        "precedence": "Package wins for each recall-product pair regardless of occurrence order; all occurrences remain in verification basis.",
        "ingredient_formulation_verification": "Exact product identity carries its frozen ingredient set and formulation; full membership is checked against frozen formulation. No free-text ingredient, strength, route or form heuristics.",
        "raw_field_mapping": "Canonical columns preserve common fields; source_identity_json.raw_record preserves every source field, .raw_json preserves the original JSON bytes as UTF-8 text, .envelope preserves provenance and partition-derived quarter, .applicability preserves unresolved accounting.",
        "lots": "All lot_scope UNKNOWN: exact code_info and more_code_info retained separately without guessing lot applicability.",
        "coverage": "Positive product/recall collections PARTIAL; no edges UNKNOWN with null measured_count. Neither state asserts absence of historical recalls."}
    tests = {"passed": True, "command": command, "exit_code": test_run.returncode, "stdout": test_run.stdout, "stderr": test_run.stderr}
    for filename, payload in {"build_summary.json": metadata | {"consumer": validation["consumer"], "corpus_counts": report["counts"], "phase_boundary": "STOP_AFTER_3B"},
        "release_metadata.json": metadata, "source_inventory.json": {"inputs": list(tracker.records.values()), "protected_inputs_size_mtime_unchanged": True},
        "snapshot_accounting.json": snapshot, "recall_rules.json": rules, "corpus_measurements.json": report,
        "consumer_coverage.json": validation["consumer"], "validation.json": validation, "spot_checks.json": spots,
        "replay.json": replay, "schema_diff.json": schema_diff, "table_counts.json": counts, "tests.json": tests}.items():
        write_json(evidence / filename, payload)
    write_json(database.parent / "release_metadata.json", metadata)
    print(canonical_json(metadata), flush=True)
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args(); run(args.root, args.database, args.evidence)


if __name__ == "__main__":
    main()
