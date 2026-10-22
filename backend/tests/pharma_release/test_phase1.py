"""Focused schema/identity/source protections, with synthetic in-memory fixtures."""
import json
from pathlib import Path
import sqlite3

import pytest

from scripts.pharma_release.build import phase1
from scripts.pharma_release.ids import decode_id, existing_id, qualified_id
from scripts.pharma_release.schema import create_schema, schema_sql, TABLES
from scripts.pharma_release.sources import InputTracker, SourceError, file_sha256, repo_file, readonly_analytics
from scripts.pharma_release.validation import validate_structure


@pytest.fixture
def db():
    c = sqlite3.connect(":memory:")
    create_schema(c)
    c.execute("INSERT INTO sources(source_id,source_name,capture_id,source_kind,verification_basis,inputs_json) VALUES ('s','example','capture','RAW_SNAPSHOT','fixture','[]')")
    c.execute("INSERT INTO ingredients VALUES ('i','source ingredient','exact source name','2026-09-26','s')")
    c.execute("INSERT INTO products(product_id,source_id,source_record_id,observed_at,ingredient_set_complete,is_combination,eligibility_mode,eligibility_reason,additional_deficiencies_json,identity_partial,policy_version) VALUES ('p','s','original-p','2026-09-26',1,0,'NORMAL_CONSUMER','ELIGIBLE','[]',0,'1.0.0')")
    yield c
    c.close()


def insert(c, table, values):
    columns = list(values)
    c.execute(f"INSERT INTO {table} ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})", [values[k] for k in columns])


def label(c, *, date_status="VALID", effective_date="2026-09-25"):
    insert(c, "labels", {"label_id": "l", "source_id": "s", "source_record_id": "original-label", "set_id": "set",
        "version_raw_json": '"1"', "version_number": 1, "effective_time_raw": "20260925", "effective_date": effective_date,
        "date_status": date_status, "source_identity_json": "{}", "has_requested_safety_section": 1,
        "extraction_valid": 1, "source_content_sha256": "a" * 64})


def label_edge(**changes):
    row = {"product_id": "p", "label_id": "l", "applicability_class": "EXACT_PRODUCT", "match_method": "EXACT_NDC",
        "matched_value": "12345-1234", "is_combination": 0, "ingredient_set_verified": 1,
        "formulation_scope_verified": 1, "evidence_scope": "PRODUCT", "verification_basis_json": '{"fixture":true}',
        "conflicts_json": "[]", "unresolved_identifiers_json": "[]", "selection_status": "SELECTED_STORED",
        "consumer_eligible": 1, "policy_version": "1.0.0"}
    return {**row, **changes}


def test_exact_tables_keys_and_foreign_keys(db):
    r = validate_structure(db)
    assert r["passed"] and r["table_count"] == 19 and set(r["table_counts"]) == set(TABLES)
    assert all(any(f["primary_key_position"] for f in columns) for columns in r["columns"].values())
    assert db.execute("PRAGMA foreign_keys").fetchone() == (1,)
    assert schema_sql() == schema_sql()


def test_schema_refuses_existing_database(db):
    before = db.execute("SELECT sql FROM sqlite_master ORDER BY name").fetchall()
    with pytest.raises(ValueError, match="existing database"):
        create_schema(db)
    assert db.execute("SELECT sql FROM sqlite_master ORDER BY name").fetchall() == before


def test_primary_and_foreign_key_failures(db):
    db.execute("INSERT INTO product_ingredients VALUES ('p','i')")
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO product_ingredients VALUES ('p','i')")
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO product_ingredients VALUES ('p','missing')")
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO product_ingredients VALUES ('missing','i')")


@pytest.mark.parametrize("value", [123, 1.5, b"binary", None, "", "   "])
def test_ids_reject_coercion(value):
    with pytest.raises(ValueError):
        qualified_id("product", "source", value)


def test_lossless_id_codec_collision_and_namespace_rules():
    x = qualified_id("product", "src:a", '  a:b/"é"  ')
    assert decode_id(x) == ("product", "src:a", '  a:b/"é"  ')
    assert x != qualified_id("product", "src", 'a:a:b/"é"')
    assert qualified_id("label", "source", "same") != qualified_id("product", "source", "same")
    assert existing_id("ingredient:" + "a" * 24, "ingredient") == "ingredient:" + "a" * 24
    with pytest.raises(ValueError):
        existing_id("ingredient:" + "a" * 24, "formulation")
    with pytest.raises(ValueError):
        decode_id('product:["source", "noncanonical"]')


def test_sqlite_numeric_identity_is_not_coerced(db):
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO ingredients VALUES (123,'name','rule','2026-09-26','s')")
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO product_identifiers VALUES ('p','PRODUCT_NDC',123,'s',NULL,1,0)")


def test_formulation_full_set_unique_and_referenced(db):
    db.execute("INSERT INTO ingredients VALUES ('j','second component','exact','2026-09-26','s')")
    row = {"formulation_id": "f", "ingredient_ids_json": '["i","j"]', "strengths_json": '[["source ingredient","1 mg"],["second component","2 mg"]]',
        "dosage_form": "tablet", "routes_json": '["oral"]', "source_id": "s"}
    insert(db, "formulations", row)
    assert json.loads(db.execute("SELECT ingredient_ids_json FROM formulations").fetchone()[0]) == ["i", "j"]
    for members in ('["i","missing"]', '["i","i"]', '[1]'):
        with pytest.raises(sqlite3.IntegrityError):
            insert(db, "formulations", {**row, "formulation_id": "bad", "ingredient_ids_json": members})
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("DELETE FROM ingredients WHERE ingredient_id='j'")


def test_polymorphic_search_foreign_keys(db):
    row = {"entity_type": "PRODUCT", "entity_id": "p", "product_id": "p", "name_role": "BRAND",
        "normalized_name": "source brand", "original_names_json": '["Source Brand","SOURCE BRAND"]', "source_id": "s"}
    insert(db, "search_names", row)
    with pytest.raises(sqlite3.IntegrityError):
        insert(db, "search_names", {**row, "entity_id": "missing", "product_id": "missing"})
    with pytest.raises(sqlite3.IntegrityError):
        insert(db, "search_names", {**row, "entity_id": "other"})


@pytest.mark.parametrize("state", ["FULL", "COMPLETE", "SAFE", "NO_RISK", "NO_WARNINGS", "NO_RECALLS"])
def test_coverage_rejects_unsupported_states(db, state):
    with pytest.raises(sqlite3.IntegrityError):
        insert(db, "coverage", {"entity_type": "PRODUCT", "entity_id": "p", "product_id": "p", "domain": "recalls",
            "state": state, "reason_code": "TEST", "scope": "PRODUCT", "rule_version": "1.0.0", "limitations_json": "[]"})


def test_coverage_unknown_cannot_be_zero_and_target_has_fk(db):
    row = {"entity_type": "PRODUCT", "entity_id": "p", "product_id": "p", "domain": "recalls",
        "state": "UNKNOWN", "reason_code": "NO_VERIFIED_LINK", "scope": "PRODUCT", "rule_version": "1.0.0", "limitations_json": "[]"}
    with pytest.raises(sqlite3.IntegrityError):
        insert(db, "coverage", {**row, "measured_count": 0})
    with pytest.raises(sqlite3.IntegrityError):
        insert(db, "coverage", {**row, "entity_id": "missing", "product_id": "missing"})
    insert(db, "coverage", row)
    assert db.execute("SELECT measured_count FROM coverage").fetchone() == (None,)


def test_label_fields_are_distinct_and_missing_sections_nullable(db):
    label(db)
    for name, text in [("warnings", "\n original warning \n"), ("warnings_and_cautions", " distinct cautions ")]:
        insert(db, "label_sections", {"label_id": "l", "source_field": name, "normalized_section": name,
            "field_present": 1, "original_value_json": json.dumps([text]), "full_text": text, "source_shape": "ARRAY_OF_STRINGS",
            "state": "READY", "reason_code": "SOURCE_TEXT", "source_value_sha256": "a" * 64, "rendering_sha256": "b" * 64})
    insert(db, "label_sections", {"label_id": "l", "source_field": "boxed_warning", "normalized_section": "boxed_warning",
        "field_present": 0, "source_shape": "ABSENT", "state": "UNAVAILABLE", "reason_code": "SOURCE_FIELD_NOT_PRESENT"})
    assert db.execute("SELECT count(*) FROM label_sections").fetchone() == (3,)
    assert db.execute("SELECT full_text FROM label_sections WHERE source_field='warnings'").fetchone()[0].startswith("\n ")


@pytest.mark.parametrize("changes", [{"applicability_class": "INGREDIENT_CONTEXT_ONLY"}, {"ingredient_set_verified": 0},
    {"formulation_scope_verified": 0}, {"conflicts_json": '["contradiction"]'}, {"selection_status": "AMBIGUOUS"}])
def test_candidate_or_conflicting_labels_cannot_be_consumer_edges(db, changes):
    label(db)
    with pytest.raises(sqlite3.IntegrityError):
        insert(db, "product_labels", label_edge(**changes))


@pytest.mark.parametrize("status,effective", [("INVALID", None), ("FUTURE_AT_SOURCE_EXPORT", "2026-09-26")])
def test_invalid_future_documents_cannot_be_consumer_edges(db, status, effective):
    label(db, date_status=status, effective_date=effective)
    with pytest.raises(sqlite3.IntegrityError):
        insert(db, "product_labels", label_edge())


def test_selected_label_cannot_be_invalidated_after_edge_validation(db):
    label(db)
    insert(db, "product_labels", label_edge())
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("UPDATE labels SET date_status='FUTURE_AT_SOURCE_EXPORT',effective_date='2026-09-26' WHERE label_id='l'")
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("UPDATE labels SET extraction_valid=0 WHERE label_id='l'")


@pytest.mark.parametrize("effective", ["2026-00-01", "2026-02-30", "2026-9-1", "not-a-date"])
def test_label_date_shape_and_calendar(db, effective):
    with pytest.raises(sqlite3.IntegrityError):
        label(db, effective_date=effective)


def test_recall_metadata_and_unknown_lots_remain_separate(db):
    insert(db, "recalls", {"recall_id": "r", "source_id": "s", "source_record_id": "D-example", "recall_number": "D-example",
        "product_description": "source description", "reason_for_recall": "source reason", "source_identity_json": "{}", "source_content_sha256": "a" * 64})
    row = {"product_id": "p", "recall_id": "r", "applicability_class": "METADATA_CANDIDATE_ONLY", "match_method": "EXACT_NDC",
        "matched_value": "12345-1234", "explicit_scope_verified": 0, "ingredient_set_verified": 1, "formulation_scope_verified": 1,
        "lot_scope": "UNKNOWN", "verification_basis_json": '{}', "conflicts_json": '[]', "consumer_eligible": 0, "policy_version": "1.0.0"}
    with pytest.raises(sqlite3.IntegrityError):
        insert(db, "product_recalls", {**row, "consumer_eligible": 1})
    with pytest.raises(sqlite3.IntegrityError):
        insert(db, "product_recalls", {**row, "lot_scope": "EXPLICIT_ALL_LOTS"})
    insert(db, "product_recalls", row)
    assert db.execute("SELECT lot_scope,lot_code_text FROM product_recalls").fetchone() == ("UNKNOWN", None)


@pytest.mark.parametrize("period", ["2019-12-01", "2026-07-01", "2025-01-02", "2025-13-01"])
def test_ae_window_and_month_key_constraints(db, period):
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO ae_monthly VALUES ('i',?,1,1,'s')", (period,))


def test_ae_observed_zero_not_created(db):
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO ae_monthly VALUES ('i','2026-06-01',0,0,'s')")
    db.execute("INSERT INTO ae_monthly VALUES ('i','2026-06-01',2,1,'s')")
    assert db.execute("SELECT pair_activity FROM ae_monthly").fetchone() == (2,)


def test_input_hash_and_change_protection(tmp_path):
    path = tmp_path / "source.json"
    path.write_text('{"source":"original"}')
    tracker = InputTracker(tmp_path)
    tracker.inspect("source.json", hash_now=True, recorded_sha256=file_sha256(path))
    path.write_text('{"source":"changed"}')
    with pytest.raises(SourceError, match="changed"):
        tracker.assert_unchanged()
    with pytest.raises(SourceError, match="SHA256 mismatch"):
        InputTracker(tmp_path).inspect("source.json", hash_now=True, recorded_sha256="0" * 64)


def test_input_missing_and_escape_refused(tmp_path):
    with pytest.raises(SourceError):
        repo_file(tmp_path, "missing")
    with pytest.raises(SourceError):
        repo_file(tmp_path, "../outside")


def test_source_stat_hash_basis_not_overstated(tmp_path):
    path = tmp_path / "large-input"
    path.write_bytes(b"source bytes")
    tracker = InputTracker(tmp_path)
    tracker.inspect("large-input", recorded_sha256="a" * 64)
    row = tracker.records["large-input"]
    assert row["sha256"] is None and row["recorded_sha256"] == "a" * 64
    assert "NOT_REVERIFIED" in row["verification_basis"]


def test_tracker_hash_upgrade_and_conflicting_receipt(tmp_path):
    path = tmp_path / "input"
    path.write_bytes(b"immutable source")
    tracker = InputTracker(tmp_path)
    tracker.inspect("input", recorded_sha256=file_sha256(path))
    tracker.inspect("input", hash_now=True)
    assert tracker.records["input"]["sha256"] == file_sha256(path)
    assert tracker.records["input"]["verification_basis"] == "FRESH_SHA256"
    with pytest.raises(SourceError, match="Conflicting recorded"):
        tracker.inspect("input", recorded_sha256="0" * 64)


def test_analytics_readonly_does_not_create_or_mutate(tmp_path):
    import duckdb
    p = tmp_path / "source.duckdb"
    c = duckdb.connect(str(p))
    c.execute("CREATE TABLE monthly(i INTEGER)")
    c.close()
    before = p.read_bytes()
    with readonly_analytics(p) as c:
        assert c.execute("SELECT count(*) FROM monthly").fetchone() == (0,)
        with pytest.raises(duckdb.InvalidInputException):
            c.execute("CREATE TABLE forbidden(i INTEGER)")
    assert p.read_bytes() == before
    missing = tmp_path / "missing.duckdb"
    with pytest.raises(SourceError):
        with readonly_analytics(missing):
            pass
    assert not missing.exists()


def test_phase1_cannot_overwrite_existing_evidence_or_write_to_data(tmp_path):
    existing = tmp_path / "docs/evidence/pharma-release-v1-build-existing"
    existing.mkdir(parents=True)
    sentinel = existing / "sentinel"
    sentinel.write_text("original")
    with pytest.raises(FileExistsError):
        phase1(tmp_path, existing)
    assert sentinel.read_text() == "original"
    with pytest.raises(ValueError):
        phase1(tmp_path, tmp_path / "data/releases/not-authorized")
