"""Source-exact label fixtures; in-memory SQLite and temporary ZIPs only."""
from copy import deepcopy
import io
import json
import sqlite3
import zipfile

import pytest

from scripts.pharma_release.label_applicability import ProductIndex, select_group
from scripts.pharma_release.label_build import Corpus, finalize_selection, populate_label_coverage
from scripts.pharma_release.label_extract import FIELDS, parse_effective, parse_version, project_label, section_slot
from scripts.pharma_release.label_sources import stream_partition
from scripts.pharma_release.label_validation import coverage_measurements, validate_labels
from scripts.pharma_release.schema_phase2 import create_phase2_schema
from scripts.pharma_release.sources import SourceError
from scripts.pharma_release.phase3_labels import readonly


def insert(c, table, row):
    columns = list(row)
    c.execute(f"INSERT INTO {table} ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})", [row[k] for k in columns])


@pytest.fixture
def db():
    c = sqlite3.connect(":memory:"); create_phase2_schema(c)
    for sid in ("ndc-source", "label-source"):
        insert(c, "sources", {"source_id": sid, "source_name": sid, "capture_id": sid, "source_kind": "RAW_SNAPSHOT", "verification_basis": "fixture", "inputs_json": "[]"})
    for iid, name in (("sem", "semaglutide"), ("alpha", "alpha salt"), ("beta", "beta")):
        insert(c, "ingredients", {"ingredient_id": iid, "canonical_name": name, "identity_rule": "source exact", "observed_at": "2026-09-26", "source_id": "ndc-source"})
    for fid, names, routes in (("f-sem", ["sem"], ["subcutaneous"]), ("f-combo", ["alpha", "beta"], ["oral"])):
        insert(c, "formulations", {"formulation_id": fid, "ingredient_ids_json": json.dumps(names), "strengths_json": '[["source", "1 mg"]]', "dosage_form": "solution", "routes_json": json.dumps(routes), "source_id": "ndc-source"})
    for pid, ndc, brand, form, names, routes, unique, conflict in (
        ("oz", "0001-01", "Ozempic", "f-sem", ["sem"], ["SUBCUTANEOUS"], 1, 0),
        ("weg", "0001-02", "Wegovy", "f-sem", ["sem"], ["SUBCUTANEOUS"], 1, 0),
        ("combo1", "0002-01", "source combo", "f-combo", ["alpha", "beta"], ["ORAL"], 1, 0),
        ("combo2", "0002-02", "source combo", "f-combo", ["alpha", "beta"], ["ORAL"], 1, 0),
        ("amb1", "0003-01", "source", "f-sem", ["sem"], ["SUBCUTANEOUS"], 0, 1),
        ("amb2", "0003-01", "source", "f-sem", ["sem"], ["SUBCUTANEOUS"], 0, 1),
        ("flagged", "0004-01", "source", "f-sem", ["sem"], ["SUBCUTANEOUS"], 0, 1),
        ("kit", "0005-01", "Source KIT", None, [], ["ORAL"], 1, 0)):
        insert(c, "products", {"product_id": pid, "source_id": "ndc-source", "source_record_id": "original-" + pid, "observed_at": "2026-09-26",
            "brand_name": brand, "generic_name": "source generic", "formulation_id": form, "ingredient_set_complete": int(bool(names)), "is_combination": int(len(names) > 1),
            "eligibility_mode": "NORMAL_CONSUMER" if names else "REGULATORY_ONLY", "eligibility_reason": "ELIGIBLE" if names else "UNRESOLVED_INGREDIENT_SET",
            "additional_deficiencies_json": "[]", "identity_partial": 0, "policy_version": "1.0.0", "routes_json": json.dumps(routes),
            "product_type": "HUMAN PRESCRIPTION DRUG", "consumer_classification": "NORMAL_CONSUMER_HUMAN_PRODUCT" if names else "UNRESOLVED_IDENTITY", "dosage_form": "KIT" if not names else "SOLUTION", "finished": 1})
        for name in names: c.execute("INSERT INTO product_ingredients VALUES (?,?)", (pid, name))
        insert(c, "product_identifiers", {"product_id": pid, "identifier_type": "PRODUCT_NDC", "value": ndc, "source_id": "ndc-source", "is_unique_product": unique, "has_conflict": conflict})
    c.commit(); yield c; c.close()


def raw_label(identifier="  FDA:é/id  ", ndcs=None, **updates):
    raw = {"id": identifier, "set_id": "set-" + identifier, "version": "2", "effective_time": "20200101",
        "openfda": {"product_ndc": ["0001-01"] if ndcs is None else ndcs, "substance_name": ["SEMAGLUTIDE"], "route": ["SUBCUTANEOUS"],
            "brand_name": ["Ozempic"], "generic_name": ["SEMAGLUTIDE"], "manufacturer_name": ["Source labeler"], "spl_id": [identifier]},
        "warnings_and_cautions": ["  exact first line\n", "second paragraph  "], "adverse_reactions": [" exact reactions "]}
    return raw | updates


def build(c, records):
    corpus = Corpus(c, ProductIndex(c), "label-source", io.StringIO())
    with c:
        for i, record in enumerate(records, 1): corpus.process(record, "fixture.zip", i)
        finalize_selection(c, corpus); populate_label_coverage(c, corpus)
    return corpus


def test_clean_single_product_label_preserves_source_identity_and_provenance(db):
    raw = raw_label(); corpus = build(db, [raw])
    label = db.execute("SELECT source_record_id,set_id,version_raw_json,effective_time_raw,source_identity_json,source_id FROM labels").fetchone()
    assert label[:4] == (raw["id"], raw["set_id"], '"2"', "20200101")
    assert json.loads(label[4]) == raw["openfda"] and label[5] == "label-source"
    assert corpus.counts["clean_labels"] == 1
    assert db.execute("SELECT product_id,consumer_eligible FROM product_labels").fetchall() == [("oz", 1)]


def test_clean_multi_product_label_has_one_text_and_multiple_edges(db):
    raw = raw_label(ndcs=["0002-01", "0002-02"])
    raw["openfda"].update({"substance_name": ["ALPHA SALT", "BETA"], "route": ["ORAL"]})
    build(db, [raw])
    assert db.execute("SELECT count(*) FROM labels").fetchone() == (1,)
    assert db.execute("SELECT product_id,is_combination,ingredient_set_verified FROM product_labels ORDER BY product_id").fetchall() == [("combo1", 1, 1), ("combo2", 1, 1)]
    assert db.execute("SELECT count(*) FROM label_sections").fetchone() == (6,)


@pytest.mark.parametrize("bad_ndc,reason", [("0003-01", "AMBIGUOUS_OR_CONFLICTED_PRODUCT_NDC"), ("0004-01", "AMBIGUOUS_OR_CONFLICTED_PRODUCT_NDC"), ("missing", "UNMATCHED_PRODUCT_NDC")])
def test_any_bad_referenced_ndc_rejects_entire_label(db, bad_ndc, reason):
    corpus = build(db, [raw_label(ndcs=["0001-01", bad_ndc])])
    assert corpus.counts["primary_" + reason] == 1
    assert db.execute("SELECT count(*) FROM labels").fetchone() == (0,)
    assert db.execute("SELECT count(*) FROM product_labels").fetchone() == (0,)


@pytest.mark.parametrize("openfda", [{}, {"generic_name": ["SEMAGLUTIDE"], "brand_name": ["Ozempic"], "rxcui": ["11"]}])
def test_no_product_ndc_cannot_use_name_or_rxcui_fallback(db, openfda):
    corpus = build(db, [raw_label(openfda=openfda)])
    assert corpus.counts["primary_NO_PRODUCT_NDC"] == 1
    assert db.execute("SELECT count(*) FROM product_labels").fetchone() == (0,)


@pytest.mark.parametrize("field", ["warnings_and_cautions", "warnings", "adverse_reactions", "boxed_warning", "contraindications", "drug_interactions"])
def test_independent_lossless_section_extraction(db, field):
    original = ["  original text\n", "\tordered second paragraph  "]
    build(db, [raw_label(**{field: original})])
    row = db.execute("SELECT original_value_json,full_text,state FROM label_sections WHERE source_field=?", (field,)).fetchone()
    assert json.loads(row[0]) == original and row[1] == "\n\n".join(original) and row[2] == "READY"


def test_multiple_sections_do_not_merge_warnings_and_cautions(db):
    build(db, [raw_label(warnings=["source warnings"], warnings_and_cautions=["source cautions"])])
    assert dict(db.execute("SELECT source_field,full_text FROM label_sections WHERE source_field IN ('warnings','warnings_and_cautions')")) == {"warnings": "source warnings", "warnings_and_cautions": "source cautions"}


def test_absent_precautions_not_manufactured_and_six_slots_accounted(db):
    build(db, [raw_label()])
    assert db.execute("SELECT count(*) FROM label_sections WHERE source_field='warnings_and_precautions'").fetchone() == (0,)
    assert {r[0] for r in db.execute("SELECT source_field FROM label_sections")} == set(FIELDS)


def test_actual_precautions_preserved_independently(db):
    build(db, [raw_label(warnings_and_precautions=["actual optional source field"])])
    assert db.execute("SELECT full_text FROM label_sections WHERE source_field='warnings_and_precautions'").fetchone() == ("actual optional source field",)


def test_idempotent_replay_preserves_selected_edges_and_text(db):
    raw = raw_label(); first = build(db, [raw])
    second = build(db, [raw])
    assert db.execute("SELECT count(*) FROM labels").fetchone() == (1,)
    for table, value in second.writer.report().items():
        assert value["inserted"] == 0 and value["identical_replays"] == first.writer.counts[table]
    assert db.execute("SELECT selection_status,consumer_eligible FROM product_labels").fetchone() == ("SELECTED_STORED", 1)


def test_changed_source_replay_rejected(db):
    raw = raw_label(); build(db, [raw])
    raw["warnings_and_cautions"] = ["changed text"]
    with pytest.raises(SourceError, match="Nonidentical replay"):
        build(db, [raw])


def test_duplicate_original_id_within_corpus_rejected(db):
    raw = raw_label()
    with pytest.raises(SourceError, match="Duplicate original label ID"):
        build(db, [raw, deepcopy(raw)])


def test_foreign_keys_reject_dangling_sections_and_edges(db):
    with pytest.raises(sqlite3.IntegrityError):
        insert(db, "label_sections", section_slot({"warnings": ["text"]}, "warnings", "missing-label"))
    build(db, [raw_label()])
    cursor = db.execute("SELECT * FROM product_labels")
    edge = dict(zip([c[0] for c in cursor.description], cursor.fetchone()))
    edge.update({"product_id": "missing-product", "consumer_eligible": 0})
    with pytest.raises(sqlite3.IntegrityError): insert(db, "product_labels", edge)


def test_semaglutide_product_labels_remain_separate(db):
    build(db, [raw_label(identifier="oz-source", ndcs=["0001-01"]), raw_label(identifier="weg-source", ndcs=["0001-02"])])
    rows = db.execute("SELECT pl.product_id,l.source_record_id FROM product_labels pl JOIN labels l ON l.label_id=pl.label_id ORDER BY pl.product_id").fetchall()
    assert rows == [("oz", "oz-source"), ("weg", "weg-source")]
    assert db.execute("SELECT count(*) FROM labels").fetchone() == (2,)


def test_missing_section_and_blank_field_have_no_fake_clinical_absence(db):
    build(db, [raw_label(boxed_warning=["  ", "\n"])])
    row = db.execute("SELECT field_present,state,reason_code,full_text FROM label_sections WHERE source_field='boxed_warning'").fetchone()
    assert row == (1, "UNAVAILABLE", "SOURCE_FIELD_EMPTY", "  \n\n\n")
    missing = db.execute("SELECT field_present,state,reason_code,full_text FROM label_sections WHERE source_field='contraindications'").fetchone()
    assert missing == (0, "UNAVAILABLE", "SOURCE_FIELD_NOT_PRESENT", None)
    assert "No structured section" in json.loads(db.execute("SELECT limitations_json FROM coverage WHERE entity_id='oz' AND domain='labels'").fetchone()[0])[1]


def test_invalid_mixed_section_preserved_and_consumer_withheld(db):
    build(db, [raw_label(warnings=["text", 7])])
    row = db.execute("SELECT original_value_json,state,reason_code,full_text FROM label_sections WHERE source_field='warnings'").fetchone()
    assert json.loads(row[0]) == ["text", 7] and row[1:] == ("UNAVAILABLE", "EXTRACTION_FAILED", None)
    assert db.execute("SELECT extraction_valid FROM labels").fetchone() == (0,)
    assert db.execute("SELECT consumer_eligible FROM product_labels").fetchone() == (0,)


def test_unresolved_kit_gets_strict_source_link_without_inferred_membership(db):
    raw = raw_label(ndcs=["0005-01"]); raw["openfda"].update({"substance_name": [], "route": ["ORAL"]})
    build(db, [raw])
    assert db.execute("SELECT ingredient_set_verified,formulation_scope_verified,consumer_eligible FROM product_labels").fetchone() == (0, 0, 0)
    assert db.execute("SELECT count(*) FROM product_ingredients WHERE product_id='kit'").fetchone() == (0,)


def test_ingredient_contradiction_is_not_overridden_by_exact_ndc(db):
    raw = raw_label(); raw["openfda"]["substance_name"] = ["ALPHA SALT"]
    build(db, [raw])
    row = db.execute("SELECT applicability_class,conflicts_json,consumer_eligible FROM product_labels").fetchone()
    assert row[0] == "AMBIGUOUS" and "EXACT_INGREDIENT_SET_CONFLICT" in json.loads(row[1]) and row[2] == 0


@pytest.mark.parametrize("value,status", [("20260926", "FUTURE_AT_SOURCE_EXPORT"), ("20260230", "INVALID"), ("19781018", "VALID")])
def test_source_dates_without_year_cutoff(db, value, status):
    build(db, [raw_label(effective_time=value)])
    assert db.execute("SELECT date_status FROM labels").fetchone() == (status,)
    assert db.execute("SELECT consumer_eligible FROM product_labels").fetchone() == (int(status == "VALID"),)


def test_higher_unusable_version_allows_explicit_earlier_stored_label(db):
    old = raw_label(identifier="old", set_id="same-set", version="1", effective_time="20200101")
    future = raw_label(identifier="future", set_id="same-set", version="2", effective_time="20270101")
    build(db, [old, future])
    row = db.execute("SELECT selection_status,consumer_eligible FROM product_labels pl JOIN labels l ON l.label_id=pl.label_id WHERE l.source_record_id='old'").fetchone()
    assert row == ("EARLIER_STORED", 1)
    assert db.execute("SELECT state FROM coverage WHERE entity_id='oz' AND domain='labels'").fetchone() == ("PARTIAL",)


def test_conflicting_same_version_not_silently_selected(db):
    left = raw_label(identifier="left", set_id="same-set")
    right = raw_label(identifier="right", set_id="same-set", warnings_and_cautions=["different content"])
    build(db, [left, right])
    assert db.execute("SELECT DISTINCT selection_status,consumer_eligible FROM product_labels").fetchall() == [("AMBIGUOUS", 0)]


def test_version_date_ordering_conflict_rejected(db):
    left = raw_label(identifier="left", set_id="same-set", version="1", effective_time="20240101")
    right = raw_label(identifier="right", set_id="same-set", version="2", effective_time="20230101")
    build(db, [left, right])
    assert db.execute("SELECT DISTINCT selection_status,consumer_eligible FROM product_labels").fetchall() == [("AMBIGUOUS", 0)]


def test_higher_strict_rejected_record_blocks_current_claim(db):
    old = raw_label(identifier="old", set_id="same-set", version="1")
    higher = raw_label(identifier="higher", set_id="same-set", version="3", effective_time="20220101", ndcs=["0001-01", "missing"])
    build(db, [old, higher])
    assert db.execute("SELECT selection_status FROM product_labels").fetchone() == ("EARLIER_STORED",)


def test_source_projection_validation_detects_text_tampering(db):
    corpus = build(db, [raw_label()]); coverage = coverage_measurements(db)
    assert validate_labels(db, corpus.report(), coverage, check_benchmarks=False)["passed"]
    db.execute("UPDATE label_sections SET full_text='tampered' WHERE source_field='adverse_reactions'")
    assert not validate_labels(db, corpus.report(), coverage, check_benchmarks=False)["passed"]


def test_streams_one_zip_without_extracting_files(tmp_path):
    path = tmp_path / "source.zip"; raw = raw_label()
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z: z.writestr("source.json", json.dumps({"results": [raw]}))
    assert list(stream_partition(path)) == [raw]
    assert [f.name for f in tmp_path.iterdir()] == ["source.zip"]


def test_readonly_parent_connection_cannot_mutate_or_create(tmp_path):
    path = tmp_path / "parent.sqlite"
    c = sqlite3.connect(path); c.execute("CREATE TABLE identity(x TEXT)"); c.commit(); c.close()
    before = path.read_bytes(); parent = readonly(path)
    try:
        with pytest.raises(sqlite3.OperationalError): parent.execute("INSERT INTO identity VALUES ('changed')")
    finally: parent.close()
    assert path.read_bytes() == before
    with pytest.raises(sqlite3.OperationalError): readonly(tmp_path / "missing.sqlite")
    assert not (tmp_path / "missing.sqlite").exists()


def test_overlapping_rejection_reasons_are_counted_without_double_admission(db):
    corpus = build(db, [raw_label(ndcs=["0003-01", "missing"])])
    assert corpus.counts["primary_AMBIGUOUS_OR_CONFLICTED_PRODUCT_NDC"] == 1
    assert corpus.counts["rejected_with_unmatched_ndc"] == 1 and corpus.counts["rejected_with_conflicted_ndc"] == 1
    assert corpus.counts["rejected_with_both_reasons"] == 1 and corpus.counts["clean_labels"] == 0


@pytest.mark.parametrize("version,expected", [("001", 1), (0, 0), ("bad", None), (True, None), (-1, None), ("9223372036854775808", None)])
def test_version_preservation_and_numeric_gate(version, expected):
    row, _ = project_label(raw_label(version=version), "s")
    assert json.loads(row["version_raw_json"]) == version and parse_version(version) == expected


def test_overflow_version_kept_raw_without_consumer_integer_coercion(db):
    version = "9223372036854775808"
    corpus = build(db, [raw_label(version=version)])
    assert db.execute("SELECT version_raw_json,version_number FROM labels").fetchone() == (json.dumps(version), None)
    assert db.execute("SELECT consumer_eligible FROM product_labels").fetchone() == (0,)
    assert corpus.counts["version_outside_sqlite_integer_range"] == 1
