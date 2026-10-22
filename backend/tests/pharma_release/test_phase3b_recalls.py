"""Isolated in-memory recall fixtures; no shared databases or live APIs."""
import hashlib
import io
import json

import pytest

from backend.tests.pharma_release.test_phase3_labels import db as identity_db, insert, raw_label, build as build_labels
from scripts.pharma_release.identity import digest_rows
from scripts.pharma_release.recall_applicability import RecallIndex, extract_text_ndcs
from scripts.pharma_release.recall_build import RecallCorpus, parse_date
from scripts.pharma_release.recall_validation import validate_recalls
from scripts.pharma_release.schema_recalls import extend_recall_method
from scripts.pharma_release.sources import SourceError


@pytest.fixture
def db(identity_db):
    c = identity_db
    extend_recall_method(c)
    insert(c, "sources", {"source_id": "recall-source", "source_name": "openfda_drug_enforcement", "capture_id": "fixture", "source_kind": "RAW_SNAPSHOT", "verification_basis": "fixture", "inputs_json": "[]"})
    for old, new in (("0001-01", "0001-101"), ("0001-02", "0001-102"), ("0002-01", "0002-101"), ("0002-02", "0002-102"), ("0003-01", "0003-101"), ("0004-01", "0004-101"), ("0005-01", "0005-101")):
        c.execute("UPDATE product_identifiers SET value=? WHERE identifier_type='PRODUCT_NDC' AND value=?", (new, old))
    for pid, value, unique, conflict in (("oz", "0001-101-01", 1, 0), ("combo1", "0002-101-01", 1, 0), ("amb1", "0003-101-01", 0, 1), ("amb2", "0003-101-01", 0, 1)):
        insert(c, "product_identifiers", {"product_id": pid, "identifier_type": "PACKAGE_NDC", "value": value, "source_id": "ndc-source", "is_unique_product": unique, "has_conflict": conflict})
    insert(c, "formulations", {"formulation_id": "f-ry", "ingredient_ids_json": '["sem"]', "strengths_json": '[["semaglutide","7 mg"]]', "dosage_form": "TABLET", "routes_json": '["ORAL"]', "source_id": "ndc-source"})
    cursor = c.execute("SELECT * FROM products WHERE product_id='oz'")
    ry = dict(zip([v[0] for v in cursor.description], cursor.fetchone())) | {"product_id": "ry", "source_record_id": "original-ry", "brand_name": "Rybelsus", "formulation_id": "f-ry", "routes_json": '["ORAL"]', "dosage_form": "TABLET"}
    insert(c, "products", ry); c.execute("INSERT INTO product_ingredients VALUES ('ry','sem')")
    insert(c, "product_identifiers", {"product_id": "ry", "identifier_type": "PRODUCT_NDC", "value": "0169-4307", "source_id": "ndc-source", "is_unique_product": 1, "has_conflict": 0})
    c.commit()
    return c


def record(description="NDC 0001-101-01", number=" D-001:é ", **updates):
    raw = {"recall_number": number, "event_id": "event-1", "product_description": description,
        "reason_for_recall": "  Exact source reason.\nSecond line  ", "classification": "Class II", "status": "Terminated",
        "code_info": " Lot 123; expiry 2027-01-01. ", "more_code_info": " Exact supplemental restrictions. ",
        "recalling_firm": "Source firm", "product_type": "Drugs", "distribution_pattern": "US",
        "recall_initiation_date": "20200101", "report_date": "20200115", "termination_date": "20200701",
        "product_quantity": "100 units", "center_classification_date": "20200114", "voluntary_mandated": "Voluntary",
        "state": "NC", "country": "United States", "openfda": {}}
    return raw | updates


def envelope(raw):
    return {"source_id": raw["recall_number"], "source_url": "https://source.example/fixture", "export_date": "2026-09-25",
        "observed_at": "2026-09-26T00:00:00Z", "raw_json": json.dumps(raw, ensure_ascii=False), "quarter": "enforcement"}


def build(c, raws, **kwargs):
    corpus = RecallCorpus(c, RecallIndex(c), "recall-source", io.StringIO(), **kwargs)
    with c:
        for i, raw in enumerate(raws, 1): corpus.process(envelope(raw), i)
        corpus.finalize_coverage()
    return corpus


def edges(c):
    return c.execute("SELECT product_id,match_method,matched_value FROM product_recalls ORDER BY product_id").fetchall()


def test_exact_package(db):
    build(db, [record()]); assert edges(db) == [("oz", "EXACT_PACKAGE_NDC", "0001-101-01")]


@pytest.mark.parametrize("text", ["NDC 0001-101", "NDC 0001-101-99"])
def test_exact_product_and_absent_package_fallback(db, text):
    build(db, [record(text)]); assert edges(db) == [("oz", "EXACT_PRODUCT_NDC", "0001-101")]


@pytest.mark.parametrize("text", ["NDC 0001-101; NDC 0001-101-01", "NDC 0001-101-01; NDC 0001-101"])
def test_package_precedence_independent_of_discovery_order(db, text):
    build(db, [record(text)]); assert edges(db) == [("oz", "EXACT_PACKAGE_NDC", "0001-101-01")]
    basis = json.loads(db.execute("SELECT verification_basis_json FROM product_recalls").fetchone()[0])
    assert len(basis["matching_occurrences"]) == 2


def test_duplicate_ndc_occurrences_one_logical_edge(db):
    build(db, [record("NDC 0001-101-01; NDC 0001-101-01", code_info="NDC 0001-101-01")])
    assert len(edges(db)) == 1
    assert len(json.loads(db.execute("SELECT verification_basis_json FROM product_recalls").fetchone()[0])["matching_occurrences"]) == 3


def test_multiple_products(db):
    build(db, [record("NDC 0001-101-01 and NDC 0002-101-01")]); assert {r[0] for r in edges(db)} == {"oz", "combo1"}


def test_partial_recall_preserves_independent_clean_edge_and_unmatched(db):
    corpus = build(db, [record("NDC 0001-101-01; NDC 9999-999-01")])
    assert len(edges(db)) == 1 and corpus.counts["MIXED_CLEAN_AND_UNMATCHED"] == 1
    basis = json.loads(db.execute("SELECT verification_basis_json FROM product_recalls").fetchone()[0])
    assert basis["recall_applicability_partial"] and basis["recall_unresolved_identifiers"][0]["text_ndc"] == "9999-999-01"


def test_all_unmatched_historical_kept_without_edge(db):
    corpus = build(db, [record("NDC 9999-999-01")]); assert not edges(db)
    assert db.execute("SELECT count(*) FROM recalls").fetchone()[0] == 1 and corpus.counts["ALL_TEXT_NDCS_UNMATCHED"] == 1


@pytest.mark.parametrize("text", ["NDC 0003-101", "NDC 0003-101-01", "NDC 0004-101"])
def test_ambiguous_or_source_flag_conflicted_no_edge(db, text):
    corpus = build(db, [record(text)]); assert not edges(db) and corpus.counts["HAS_AMBIGUOUS_TEXT_NDC"] == 1


def test_ambiguous_identifier_does_not_reject_other_clean_edge(db):
    corpus = build(db, [record("NDC 0003-101; NDC 0001-101-01")])
    assert {r[0] for r in edges(db)} == {"oz"} and corpus.counts["PARTIAL_RECALLS_WITH_CLEAN_EDGES"] == 1


def test_ambiguous_package_does_not_fall_back_to_clean_product(db):
    db.execute("UPDATE product_identifiers SET is_unique_product=0,has_conflict=1 WHERE identifier_type='PACKAGE_NDC' AND product_id='oz'")
    build(db, [record()]); assert not edges(db)


@pytest.mark.parametrize("text", ["0001-101-01", "Ozempic semaglutide Source firm 1 mg injection", "NDC unknown"])
def test_no_explicit_ndc_no_names_metadata_or_rxcui_fallback(db, text):
    corpus = build(db, [record(text, openfda={"product_ndc": ["0001-101"], "package_ndc": ["0001-101-01"], "rxcui": ["11"], "substance_name": ["SEMAGLUTIDE"]})])
    assert not edges(db) and corpus.counts["NO_EXPLICIT_TEXT_NDC"] == 1


@pytest.mark.parametrize("text,metadata", [("NDC 9502-500-01", "49502-500-01"), ("NDC 342023-172-044", "42023-172-04")])
def test_malformed_ndc_not_repaired(db, text, metadata):
    build(db, [record(text, openfda={"package_ndc": [metadata]})]); assert not edges(db)
    saved = json.loads(db.execute("SELECT source_identity_json FROM recalls").fetchone()[0])
    assert saved["applicability"]["occurrences"][0]["text_ndc"] == text.removeprefix("NDC ")


@pytest.mark.parametrize("text", ["NDC 0001-10101", "NDC 0001-101-0100"])
def test_regex_must_not_shorten_overlong_digit_segment_to_valid_identity(db, text):
    corpus = build(db, [record(text)])
    assert not edges(db) and corpus.counts["RECALLS_WITH_OVERLONG_NDC_TOKEN_FRAGMENT"] == 1


def test_broad_openfda_product_family_does_not_expand_scope(db):
    build(db, [record(openfda={"product_ndc": ["0001-101", "0001-102", "0169-4307"], "package_ndc": ["0001-101-01"]})])
    assert {r[0] for r in edges(db)} == {"oz"}


@pytest.mark.parametrize("classification", ["Class I", "Class II", "Class III"])
def test_classification_exact_no_custom_severity(db, classification):
    build(db, [record(classification=classification)])
    assert db.execute("SELECT classification FROM recalls").fetchone()[0] == classification


@pytest.mark.parametrize("status", ["Terminated", "Completed", "Ongoing"])
def test_historical_reported_status_retains_valid_edge(db, status):
    build(db, [record(status=status)]); assert len(edges(db)) == 1
    assert db.execute("SELECT source_reported_status FROM recalls").fetchone()[0] == status


def test_reason_description_lots_raw_fields_and_provenance_lossless(db):
    raw = record(); env = envelope(raw); build(db, [raw])
    row = db.execute("SELECT source_record_id,recall_number,product_description,reason_for_recall,code_info,source_identity_json,source_content_sha256,source_id FROM recalls").fetchone()
    assert row[:5] == (raw["recall_number"], raw["recall_number"], raw["product_description"], raw["reason_for_recall"], raw["code_info"])
    saved = json.loads(row[5]); assert saved["raw_record"] == raw and saved["raw_json"] == env["raw_json"]
    assert saved["envelope"] == {k: v for k, v in env.items() if k != "raw_json"}
    assert row[6] == hashlib.sha256(env["raw_json"].encode()).hexdigest() and row[7] == "recall-source"
    lot = db.execute("SELECT lot_scope,lot_code_text,verification_basis_json FROM product_recalls").fetchone()
    assert lot[:2] == ("UNKNOWN", raw["code_info"]) and json.loads(lot[2])["lots"]["more_code_info"] == raw["more_code_info"]


def test_missing_lots_not_converted_to_all_lots(db):
    build(db, [record(code_info=None, more_code_info=None)])
    assert db.execute("SELECT lot_scope,lot_code_text FROM product_recalls").fetchone() == ("UNKNOWN", None)


def test_real_source_replay_zero_mutations(db):
    records = [record(), record("NDC 9999-999", "historical")]
    first = build(db, records).report(); before = db.total_changes; replay = build(db, records).report()
    assert db.total_changes == before
    for table in first["projection"]:
        assert replay["projection"][table]["inserted"] == 0
        assert replay["projection"][table]["sha256_sorted_row_hashes"] == first["projection"][table]["sha256_sorted_row_hashes"]


def test_nonidentical_replay_fails(db):
    build(db, [record()])
    with pytest.raises(SourceError, match="Nonidentical replay"):
        build(db, [record(reason_for_recall="changed")])


def test_labels_unchanged(db):
    build_labels(db, [raw_label(ndcs=["0001-101"])])
    tables = ("labels", "label_sections", "product_labels")
    before = {t: digest_rows(db.execute(f"SELECT * FROM {t}")) for t in tables}
    build(db, [record()])
    assert before == {t: digest_rows(db.execute(f"SELECT * FROM {t}")) for t in tables}


def test_rybelsus_specific_no_ozempic_wegovy_ingredient_propagation(db):
    build(db, [record("Rybelsus 7 mg oral tablets, NDC 0169-4307-50", openfda={"substance_name": ["SEMAGLUTIDE"], "product_ndc": ["0001-101", "0001-102", "0169-4307"]})])
    assert edges(db) == [("ry", "EXACT_PRODUCT_NDC", "0169-4307")]


def test_combination_not_propagated_to_shared_ingredients_or_formulation(db):
    build(db, [record("NDC 0002-101-01")]); assert {r[0] for r in edges(db)} == {"combo1"}
    assert db.execute("SELECT ingredient_set_verified,formulation_scope_verified FROM product_recalls").fetchone() == (1, 1)


def test_unresolved_frozen_identity_not_consumer_evidence(db):
    build(db, [record("NDC 0005-101")])
    assert db.execute("SELECT consumer_eligible,ingredient_set_verified,formulation_scope_verified FROM product_recalls").fetchone() == (0, 0, 0)


def test_truthful_coverage_states_and_validation(db):
    corpus = build(db, [record()])
    assert db.execute("SELECT state,measured_count FROM coverage WHERE product_id='oz' AND domain='recalls'").fetchone() == ("PARTIAL", 1)
    assert db.execute("SELECT state,measured_count FROM coverage WHERE product_id='weg' AND domain='recalls'").fetchone() == ("UNKNOWN", None)
    assert validate_recalls(db, corpus.report(), check_benchmarks=False)["passed"]


def test_duplicate_identity_in_source_rejected(db):
    with pytest.raises(SourceError, match="Duplicate recall identity"):
        build(db, [record(), record()])


def test_envelope_original_identity_must_match(db):
    corpus = RecallCorpus(db, RecallIndex(db), "recall-source")
    with pytest.raises(SourceError, match="Envelope ID"):
        corpus.process(envelope(record()) | {"source_id": "repaired-id"}, 1)


def test_wrong_envelope_vintage_rejected(db):
    with pytest.raises(SourceError, match="vintage"):
        build(db, [record()], expected_envelope={"export_date": "2020-01-01"})


@pytest.mark.parametrize("text,ndc", [("NDC 0378-1722-93", "0378-1722-93"), ("NDC: 85766-187-01", "85766-187-01"), ("NDC47783-101-01", "47783-101-01"), ("NDC 59898-950", "59898-950"), ("ndc # 0001 - 101 - 01", "0001-101-01")])
def test_accepted_marker_forms_exact_segments(text, ndc):
    assert extract_text_ndcs({"product_description": text})[0]["text_ndc"] == ndc


def test_only_allowed_text_fields_can_create_scope(db):
    build(db, [record("No explicit NDC", reason_for_recall="NDC 0001-101-01", more_code_info="NDC 0002-101-01")])
    assert {r[0] for r in edges(db)} == {"combo1"}


@pytest.mark.parametrize("value,expected", [("20200229", "2020-02-29"), ("20260229", None), ("2026092514", None), (None, None)])
def test_dates_exact_calendar_no_repair(value, expected):
    assert parse_date(value) == expected


def test_enum_extension_retains_other_schema_objects(identity_db):
    # identity_db is also available independently of the recall db fixture.
    c = identity_db
    before = c.execute("SELECT type,name,sql FROM sqlite_master WHERE name!='product_recalls' ORDER BY type,name").fetchall()
    extend_recall_method(c)
    assert before == c.execute("SELECT type,name,sql FROM sqlite_master WHERE name!='product_recalls' ORDER BY type,name").fetchall()
    assert c.execute("PRAGMA user_version").fetchone()[0] == 3
