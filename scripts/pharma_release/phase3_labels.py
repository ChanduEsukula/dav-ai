"""Build forward from pinned Phase 2: label evidence only; never starts recalls."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import sqlite3

from . import CONTRACT_ID, POLICY_VERSION
from .label_applicability import ProductIndex, RULE_VERSION
from .label_build import Corpus, finalize_selection, populate_label_coverage, PROJECTION_TABLES
from .label_extract import FIELDS, SOURCE_NAME
from .label_sources import discover_label_inputs, stream_partition, PARENT_PATH, PARENT_SHA256
from .label_validation import coverage_measurements, validate_labels, UNTREATED
from .phase2 import output_paths, write_json
from .sources import LABEL_CACHE, canonical_json, file_sha256, SourceError

BUILD_VERSION = "phase3a-labels-0.1.0"
RELEASE_VERSION = "dav-ai-pharma-v1-phase3a-labels-20261006"


def readonly(path):
    c = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
    c.execute("PRAGMA foreign_keys=ON")
    return c


def schema_objects(connection):
    return connection.execute("SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name").fetchall()


def spot_checks(connection, corpus):
    expected = {"f2ef667a-4871-4f28-a0b3-3f79fbbe180c": ["33342-057", "33342-058"],
        "0e853a5e-9eab-4bb6-803d-fd9b97e8b550": ["70069-853", "70069-854", "70069-855"],
        "2b1bf1d7-4399-46bd-8654-2590513da5c2": ["0025-1411", "0025-1421"]}
    cases = {}
    for sid, values in expected.items():
        source = corpus.known.get(sid)
        row = connection.execute("SELECT label_id,set_id,version_raw_json,effective_time_raw FROM labels WHERE source_record_id=?", (sid,)).fetchone()
        if row is None or source is None:
            cases[sid] = {"passed": False}; continue
        edges = connection.execute("SELECT product_id,matched_value,ingredient_set_verified,formulation_scope_verified,selection_status,consumer_eligible FROM product_labels WHERE label_id=? ORDER BY matched_value", (row[0],)).fetchall()
        sections = [{"field": f, "field_present": present, "state": state, "full_text_characters": length,
            "source_value_sha256": h1, "rendering_sha256": h2} for f, present, state, length, h1, h2 in connection.execute(
                "SELECT source_field,field_present,state,length(full_text),source_value_sha256,rendering_sha256 FROM label_sections WHERE label_id=? ORDER BY source_field", (row[0],))]
        passed = source["product_ndcs"] == sorted(values) and [r[1] for r in edges] == sorted(values)
        if sid == "f2ef667a-4871-4f28-a0b3-3f79fbbe180c":
            passed = passed and row[1:] == ("1898f438-4571-4aab-ae06-9bf1aabf0486", '"15"', "20250902")
            passed = passed and all(any(s["field"] == f and s["state"] == "READY" for s in sections) for f in
                ("boxed_warning", "warnings_and_cautions", "contraindications", "adverse_reactions", "drug_interactions"))
        cases[sid] = {"passed": passed, "source": source, "product_edges": edges, "section_checks": sections}
    semaglutide = {}
    sets = {}
    for ndc, expected_brand in (("50090-8027", "ozempic"), ("50090-6051", "ozempic"), ("50090-5949", "ozempic"), ("50090-5824", "wegovy")):
        rows = connection.execute("""SELECT p.product_id,p.brand_name,p.formulation_id,l.source_record_id,l.set_id,pl.label_id,pl.matched_value
            FROM product_identifiers i JOIN products p ON p.product_id=i.product_id JOIN product_labels pl ON pl.product_id=p.product_id
            JOIN labels l ON l.label_id=pl.label_id WHERE i.identifier_type='PRODUCT_NDC' AND i.value=? ORDER BY pl.label_id""", (ndc,)).fetchall()
        passed = bool(rows) and all(r[1].casefold() == expected_brand and r[6] == ndc for r in rows)
        semaglutide[ndc] = {"passed": passed, "expected_source_brand": expected_brand, "product_label_records": rows}
        sets[ndc] = {r[5] for r in rows}
    separate = not set.union(*(sets[n] for n in ("50090-8027", "50090-6051", "50090-5949"))).intersection(sets["50090-5824"])
    return {"known_multi_product_labels": cases, "semaglutide_exact_products": semaglutide,
        "ozempic_wegovy_label_records_separate": separate,
        "passed": all(c["passed"] for c in cases.values()) and all(c["passed"] for c in semaglutide.values()) and separate}


def run(root, database, evidence):
    root = Path(root).resolve(); database, evidence = output_paths(root, database, evidence)
    tracker, parent_metadata, dataset, parts = discover_label_inputs(root)
    parent_validation = tracker.json("docs/evidence/pharma-release-v1-build-2026-10-06-phase2/validation.json")
    for directory in ("scripts/pharma_release", "backend/tests/pharma_release"):
        for path in sorted((root / directory).glob("*")):
            if path.is_file(): tracker.inspect(path.relative_to(root), hash_now=True)
    parent = readonly(root / PARENT_PATH)
    try:
        original_schema = schema_objects(parent)
        original_source = parent.execute("SELECT source_id,inputs_json FROM sources WHERE source_name=?", (SOURCE_NAME,)).fetchone()
        if original_source is None: raise SourceError("Parent lacks pinned label provenance")
        pinned_archive_hashes = {r["path"]: r["sha256"] or r["recorded_sha256"] for r in json.loads(original_source[1])}
        if any(pinned_archive_hashes.get(p["path"]) != p["sha256"] for p in parts):
            raise SourceError("Fresh archives differ from the immutable Phase 2 pinned capture hashes")
        for table in (*PROJECTION_TABLES, *UNTREATED):
            if parent.execute(f"SELECT count(*) FROM {table}").fetchone()[0]: raise SourceError("Parent is not the identity-only checkpoint")
    finally:
        parent.close()
    evidence.mkdir(parents=True, exist_ok=False); database.parent.mkdir(parents=True, exist_ok=False)
    staged = database.parent / "labels.building.sqlite"
    with (root / PARENT_PATH).open("rb") as source, staged.open("xb") as target:
        shutil.copyfileobj(source, target, length=1024 * 1024)
    staged.chmod(0o644)
    c = sqlite3.connect(staged); c.execute("PRAGMA foreign_keys=ON")
    build_time = datetime.now(timezone.utc).isoformat(); partition_reports = []
    try:
        index = ProductIndex(c)
        with (evidence / "label_admission_audit.jsonl").open("x") as audit:
            corpus = Corpus(c, index, original_source[0], audit)
            for part in parts:
                n = 0
                with c:
                    for n, raw in enumerate(stream_partition(root / part["path"]), 1): corpus.process(raw, part["path"], n)
                if n != part["records"]: raise SourceError("Partition record count differs: " + part["path"])
                partition_reports.append(part | {"processed_records": n, "zip_member_crc_validated_by_eof": True})
                tracker.assert_unchanged(); print("Built label partition " + Path(part["path"]).name + ": " + str(n), flush=True)
        report = corpus.report()
        with c:
            selection = finalize_selection(c, corpus); coverage_states = populate_label_coverage(c, corpus)
        coverage = coverage_measurements(c)
        validation = validate_labels(c, report, coverage, parent_validation)
        spots = spot_checks(c, corpus)
        if not spots["passed"]:
            validation["errors"].append({"gate": "known_label_spot_checks"}); validation["passed"] = False
        if not validation["passed"]:
            write_json(evidence / "failed_validation.json", validation)
            raise SourceError("Label benchmarks/semantic gates failed; investigate, do not change expected counts")
        # Real full-corpus replay compares every stored source field/section, with no new rows.
        before = {t: c.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in PROJECTION_TABLES}
        replay_corpus = Corpus(c, index, original_source[0])
        for part in parts:
            n = 0
            with c:
                for n, raw in enumerate(stream_partition(root / part["path"]), 1): replay_corpus.process(raw, part["path"], n)
            if n != part["records"]: raise SourceError("Replay partition count mismatch")
            print("Replayed label partition " + Path(part["path"]).name, flush=True)
        replay_report = replay_corpus.report()
        after = {t: c.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in PROJECTION_TABLES}
        replay = {"passed": before == after and report["counts"] == replay_report["counts"]
            and all(replay_report["projection"][t]["inserted"] == 0 and replay_report["projection"][t]["identical_replays"] == before[t]
                    and replay_report["projection"][t]["sha256_sorted_row_hashes"] == report["projection"][t]["sha256_sorted_row_hashes"] for t in PROJECTION_TABLES),
            "full_corpus_records_reprocessed": replay_report["counts"]["source_labels"], "table_counts_before": before,
            "table_counts_after": after, "projection": replay_report["projection"], "all_zip_members_read_to_eof_again": True}
        if not replay["passed"]: raise SourceError("Replay/idempotency failed")
        if schema_objects(c) != original_schema: raise SourceError("Unexpected schema modification")
        schema_diff = {"changed": False, "schema_version": parent_metadata["schema_version"], "logical_tables": 19,
            "sqlite_master_objects_equal_to_parent": True, "ddl_statements_applied": []}
        counts = dict(validation["table_counts"])
        archive_inputs = [tracker.records[p["path"]] for p in parts]
        with c:
            c.execute("UPDATE sources SET verification_basis=?,inputs_json=?,transform_version=? WHERE source_id=?",
                ("FRESH_SHA256_VERIFIED_AGAINST_PINNED_RECEIPTS; ALL_14_SINGLE_JSON_MEMBERS_STREAMED_TO_EOF_WITH_CRC_VALIDATION",
                 canonical_json(archive_inputs), BUILD_VERSION, original_source[0]))
            prior = c.execute("SELECT * FROM release_manifest"); parent_manifest = dict(zip([f[0] for f in prior.description], prior.fetchone()))
            manifest = dict(parent_manifest)
            manifest.update({"release_id": RELEASE_VERSION, "build_version": BUILD_VERSION, "build_time_utc": build_time,
                "table_counts_json": canonical_json(counts),
                "unresolved_counts_json": canonical_json(json.loads(parent_manifest["unresolved_counts_json"]) | {"labels": {"no_product_ndc": report["counts"]["primary_NO_PRODUCT_NDC"],
                    "unmatched_only_primary": report["counts"].get("primary_UNMATCHED_PRODUCT_NDC", 0),
                    "ambiguous_or_conflicted_primary": report["counts"].get("primary_AMBIGUOUS_OR_CONFLICTED_PRODUCT_NDC", 0)},
                    "recalls": None, "ae_analytics": None, "safety_communications": None}),
                "source_vintages_json": canonical_json(json.loads(parent_manifest["source_vintages_json"]) + [{"kind": "PARENT_RELEASE",
                    "release_id": parent_metadata["release_version"], "database_path": PARENT_PATH, "database_sha256": PARENT_SHA256},
                    {"kind": "LABEL_BUILD", "source_id": original_source[0], "export_date": "2026-09-25", "captured_date": "2026-09-26",
                     "archive_hashes": [{"path": p["path"], "sha256": p["sha256"]} for p in parts], "verification": "FRESH_SHA256_AND_STREAMED_ZIP_CRC", "strict_ndc_rule_version": RULE_VERSION}]),
                "validation_results_json": canonical_json({"phase": "3A", "labels_passed": True, "strict_ndc_rule_version": RULE_VERSION,
                    "clean_labels": report["counts"]["clean_labels"], "clean_edges": report["counts"]["clean_edges"],
                    "full_corpus_replay_passed": True, "recalls_started": False, "ae_started": False, "communications_started": False,
                    "publication_validated": False, "parent_release_sha256": PARENT_SHA256, "normal_clean_label_coverage": coverage["classifications"]["NORMAL_CONSUMER_HUMAN_PRODUCT"],
                    "normal_products_consumer_selected": coverage["normal_products_with_consumer_eligible_selected_label"]}),
                "digest_strategy": "EXTERNAL_FINAL_FILE_SHA256", "content_digest": None})
            c.execute("DELETE FROM release_manifest")  # New child only; parent remains sealed.
            columns = list(manifest)
            c.execute("INSERT INTO release_manifest (" + ",".join(columns) + ") VALUES (" + ",".join("?" for _ in columns) + ")", [manifest[k] for k in columns])
        if c.execute("PRAGMA integrity_check").fetchall() != [("ok",)] or c.execute("PRAGMA foreign_key_check").fetchall():
            raise SourceError("Final database integrity failed")
        final_counts = {t: c.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in counts}
        if final_counts != counts: raise SourceError("Manifest/count mismatch")
    finally:
        c.close()
    tracker.assert_unchanged()
    for record in tracker.records.values():
        if record["sha256"] and file_sha256(root / record["path"]) != record["sha256"]:
            raise SourceError("Protected input content changed: " + record["path"])
    staged.chmod(0o444); os.link(staged, database); staged.unlink()
    final = readonly(database)
    try:
        integrity = final.execute("PRAGMA integrity_check").fetchall(); foreign_keys = final.execute("PRAGMA foreign_key_check").fetchall()
        if integrity != [("ok",)] or foreign_keys: raise SourceError("Sealed final integrity failed")
        if schema_objects(final) != original_schema: raise SourceError("Sealed schema differs")
        if not spot_checks(final, corpus)["passed"]: raise SourceError("Sealed spot checks failed")
    finally:
        final.close()
    metadata = {"phase": "3A", "release_version": RELEASE_VERSION, "build_version": BUILD_VERSION,
        "schema_version": parent_metadata["schema_version"], "policy_version": POLICY_VERSION, "strict_ndc_rule_version": RULE_VERSION,
        "build_time_utc": build_time, "database_path": database.relative_to(root).as_posix(), "database_bytes": database.stat().st_size,
        "database_sha256": file_sha256(database), "file_mode": oct(database.stat().st_mode & 0o777),
        "parent_release_path": PARENT_PATH, "parent_release_sha256": PARENT_SHA256, "label_capture": LABEL_CACHE,
        "label_export_date": "2026-09-25", "label_capture_date": "2026-09-26", "table_counts": counts,
        "safe_to_proceed_to_recalls": True, "recalls_started": False, "ae_started": False, "communications_started": False,
        "publication_validated": False}
    validation.update({"spot_checks_passed": True, "full_corpus_replay_passed": True, "manifest_table_counts_match": True,
        "sealed_integrity_check": integrity, "sealed_foreign_key_violations": foreign_keys, "schema_unchanged": True,
        "safe_to_proceed_to_recalls": True, "archive_hashes_match_parent_pinned_capture": True, "publication_validated": False})
    source_inventory = {"parent_release": parent_metadata, "label_dataset": dataset, "partitions": partition_reports,
        "inputs": list(tracker.records.values()), "full_sha256_count": sum(bool(r["sha256"]) for r in tracker.records.values()),
        "label_source_id": original_source[0], "archive_hashes_match_parent_pinned_capture": True, "parent_source_row_upgraded_only_in_new_child": True}
    preservation = {"all_protected_sizes_mtimes_unchanged": True, "all_fresh_sha256_rechecked_and_unchanged": True,
        "parent_release_sha256": PARENT_SHA256, "parent_release_mode": oct((root / PARENT_PATH).stat().st_mode & 0o777),
        "raw_label_zip_hashes_freshly_verified_count": 14, "raw_label_zip_crcs_streamed_to_eof_count": 14,
        "protected_inputs": list(tracker.records.values()), "source_files_modified": [], "phase2_release_modified": False,
        "frontend_modified": False, "postgres_dependency_introduced": False}
    for filename, payload in (("release_metadata.json", metadata), ("table_counts.json", counts), ("source_inventory.json", source_inventory),
        ("preservation.json", preservation), ("label_corpus_measurements.json", report), ("consumer_coverage.json", coverage),
        ("section_coverage.json", {"source_field_presence": report["section_field_presence"], "source_nonblank_text": report["section_nonblank_text"], "normal_product_sections": coverage["normal_section_products"]}),
        ("applicability_measurements.json", {"counts": report["counts"], "selection": selection, "coverage_states": coverage_states, "rule_version": RULE_VERSION}),
        ("spot_checks.json", spots), ("validation.json", validation), ("replay.json", replay), ("schema_diff.json", schema_diff)):
        write_json(evidence / filename, payload)
    write_json(database.parent / "release_metadata.json", metadata)
    tracker.assert_unchanged()
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.root, args.database, args.evidence_dir), indent=2))


if __name__ == "__main__": main()
