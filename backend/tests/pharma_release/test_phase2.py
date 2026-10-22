"""Focused source-backed Phase 2 fixtures; no research mutations or network."""
from copy import deepcopy
import io
import json
import sqlite3

import pytest

from scripts.pharma_release.eligibility import decide, normalize_name, parse_source_date
from scripts.pharma_release.identity import populate_identity, distinct_identifiers
from scripts.pharma_release.ids import decode_id, qualified_id
from scripts.pharma_release.phase2 import output_paths
from scripts.pharma_release.schema_phase2 import create_phase2_schema, PHASE2_SCHEMA_VERSION
from scripts.pharma_release.search import lookup_name, lookup_identifier, candidate_details
from scripts.pharma_release.sources import SourceError
from scripts.pharma_release.validation_phase2 import validate_identity, ambiguity_report

I1 = "ingredient:" + "a" * 24
I2 = "ingredient:" + "b" * 24
F1 = "formulation:" + "a" * 24
F2 = "formulation:" + "b" * 24


def fixture_rows():
    ingredients = [{"ingredient_id": iid, "canonical_name": name, "source": "openfda_ndc_directory", "identity_rule": "exact source name", "observed_at": "2026-09-26"}
                   for iid, name in ((I1, "alpha salt"), (I2, "beta"))]
    formulations = [{"formulation_id": F1, "ingredient_ids": [I1], "strengths_json": '[["alpha salt", "1 mg"]]', "dosage_form": "tablet", "routes": ["oral"]},
                    {"formulation_id": F2, "ingredient_ids": [I1, I2], "strengths_json": '[["alpha salt", "1 mg"], ["beta", "2 mg"]]', "dosage_form": "tablet", "routes": ["oral"]}]
    products = []; envelopes = []
    for sid, members, form, active, category, kind, dosage in (
        (' 001:é/"a" ', [I1], F1, [{"name": "ALPHA SALT", "strength": "1 mg"}], "ANDA", "HUMAN PRESCRIPTION DRUG", "TABLET"),
        ("combo", [I1, I2], F2, [{"name": "ALPHA SALT", "strength": "1 mg"}, {"name": "BETA", "strength": "2 mg"}], "NDA", "HUMAN OTC DRUG", "TABLET"),
        ("kit", [], None, [], "NDA", "HUMAN PRESCRIPTION DRUG", "KIT"),
        ("homeo", [I1], F1, [{"name": "ALPHA SALT", "strength": "1 mg"}], "UNAPPROVED HOMEOPATHIC", "HUMAN OTC DRUG", "TABLET"),
        ("excluded", [I1], F1, [{"name": "ALPHA SALT", "strength": "1 mg"}], "BULK INGREDIENT", "BULK INGREDIENT", "TABLET")):
        raw = {"product_id": sid, "generic_name": "Alpha, Beta kit" if sid == "kit" else "Alpha Salt", "brand_name": "Generic-looking source name",
            "brand_name_base": "Generic-looking source name", "labeler_name": "Source labeler", "active_ingredients": active,
            "marketing_category": category, "product_type": kind, "dosage_form": dosage, "route": ["ORAL"],
            "finished": sid != "excluded", "application_number": "NDA000001", "marketing_start_date": "20200101", "listing_expiration_date": "20261231",
            "product_ndc": "00001-01", "packaging": [{"package_ndc": "00001-01-01"}, {"package_ndc": "00001-01-02"}], "openfda": {"rxcui": ["0001", "0002"]}}
        products.append({"source_id": sid, "ingredient_ids": members, "formulation_id": form, "generic_name": raw["generic_name"], "brand_name": raw["brand_name"],
            "labeler_name": raw["labeler_name"], "product_ndcs": ["00001-01"], "package_ndcs": ["00001-01-01", "00001-01-02"], "rxcuis": ["0001", "0002"], "source_url": "source-url", "observed_at": "2026-09-26"})
        envelopes.append({"source_id": sid, "source_url": "source-url", "observed_at": "2026-09-26", "export_date": "2026-09-26", "raw_json": json.dumps(raw)})
    return ingredients, formulations, products, envelopes


def connection():
    db = sqlite3.connect(":memory:")
    create_phase2_schema(db)
    for sid in ("raw", "identity"):
        db.execute("INSERT INTO sources(source_id,source_name,capture_id,source_kind,verification_basis,inputs_json) VALUES (?,?,?,'RAW_SNAPSHOT','fixture','[]')", (sid, sid, sid))
    db.commit()
    return db


@pytest.fixture
def built():
    db = connection(); audit = io.StringIO()
    with db:
        measurements = populate_identity(db, *fixture_rows(), "raw", "identity", audit)
    yield db, measurements, [json.loads(line) for line in audit.getvalue().splitlines()]
    db.close()


def product_id(sid):
    return qualified_id("product", "openfda_ndc_directory", sid)


def test_lossless_source_product_ids(built):
    db, _, _ = built
    sid = ' 001:é/"a" '
    row = db.execute("SELECT product_id,source_record_id FROM products WHERE source_record_id=?", (sid,)).fetchone()
    assert row == (product_id(sid), sid)
    assert decode_id(row[0])[2] == sid


def test_source_ingredients_and_formulations_preserved(built):
    db, _, _ = built
    assert db.execute("SELECT ingredient_id,canonical_name FROM ingredients ORDER BY ingredient_id").fetchall() == [(I1, "alpha salt"), (I2, "beta")]
    assert db.execute("SELECT strengths_json FROM formulations WHERE formulation_id=?", (F2,)).fetchone()[0] == fixture_rows()[1][1]["strengths_json"]


def test_combination_is_one_product_with_complete_membership(built):
    db, _, _ = built
    data = candidate_details(db, product_id("combo"))
    assert data["ingredient_ids"] == [I1, I2] and data["is_combination"] == 1 and data["formulation_id"] == F2
    assert json.loads(data["formulation"]["ingredient_ids_json"]) == [I1, I2]


def test_unresolved_kit_source_searchable_without_inference(built):
    db, _, audit = built
    data = candidate_details(db, product_id("kit"))
    assert data["dosage_form"] == "KIT" and data["ingredient_ids"] == [] and data["formulation"] is None
    assert data["identity_coverage"]["state"] == "UNKNOWN" and data["identity_coverage"]["measured_count"] is None
    assert data["consumer_classification"] == "UNRESOLVED_IDENTITY"
    assert lookup_name(db, "Alpha, Beta kit", "GENERIC") == [product_id("kit")]
    assert product_id("kit") in lookup_identifier(db, "PRODUCT_NDC", "00001-01")
    assert next(r for r in audit if r["source_record_id"] == "kit")["ingredient_ids"] == []


@pytest.mark.parametrize("kind,values", [("PACKAGE_NDC", ["00001-01-01", "00001-01-02"]), ("RXCUI", ["0001", "0002"])])
def test_multiple_identifiers_preserved(built, kind, values):
    db, _, _ = built
    assert candidate_details(db, product_id("combo"))["identifiers"][kind] == values


def test_multiple_product_ndcs_are_relational_not_product_keys(built):
    db, _, _ = built
    pid = product_id("combo")
    db.execute("INSERT INTO product_identifiers VALUES (?,'PRODUCT_NDC','00002-02','raw',NULL,1,0)", (pid,))
    assert lookup_identifier(db, "PRODUCT_NDC", "00002-02") == [pid]
    assert candidate_details(db, pid)["identifiers"]["PRODUCT_NDC"] == ["00001-01", "00002-02"]
    assert distinct_identifiers(["00001-01", "00002-02", "00001-01"]) == ["00001-01", "00002-02"]


def test_rxcui_not_required_for_inclusion():
    rows = fixture_rows(); rows[2][0]["rxcuis"] = []
    raw = json.loads(rows[3][0]["raw_json"]); raw["openfda"]["rxcui"] = []; rows[3][0]["raw_json"] = json.dumps(raw)
    db = connection()
    with db:
        populate_identity(db, *rows, "raw", "identity", io.StringIO())
    assert db.execute("SELECT eligibility_mode FROM products WHERE source_record_id=?", (rows[2][0]["source_id"],)).fetchone() == ("NORMAL_CONSUMER",)
    db.close()


@pytest.mark.parametrize("role,value", [("BRAND", "  GENERIC-looking   source NAME "), ("GENERIC", "alpha salt"), ("INGREDIENT", "ALPHA SALT")])
def test_source_name_lookup_returns_all_candidates(built, role, value):
    db, _, _ = built
    ids = lookup_name(db, value, role)
    expected = 4 if role == "BRAND" else 3
    assert len(ids) == expected and ids == sorted(ids) and len(set(ids)) == expected


@pytest.mark.parametrize("kind,value", [("PRODUCT_NDC", "00001-01"), ("PACKAGE_NDC", "00001-01-01"), ("RXCUI", "0001")])
def test_identifier_lookup_does_not_collapse_ambiguity(built, kind, value):
    db, _, _ = built
    ids = lookup_identifier(db, kind, value)
    assert len(ids) == 4 and ids == sorted(ids)
    assert db.execute("SELECT DISTINCT is_unique_product,has_conflict FROM product_identifiers WHERE identifier_type=? AND value=?", (kind, value)).fetchall() == [(0, 1)]


def test_regulatory_category_and_labeler_preserved(built):
    db, _, _ = built
    data = candidate_details(db, product_id("homeo"))
    assert data["marketing_category"] == "UNAPPROVED HOMEOPATHIC" and data["eligibility_mode"] == "REGULATORY_ONLY"
    assert data["consumer_classification"] == "SPECIAL_REGULATORY_CATEGORY_HUMAN_PRODUCT"
    assert data["labeler_name"] == "Source labeler" and "manufacturer" not in data


def test_excluded_universe_audited_offline(built):
    db, measurements, audit = built
    assert measurements["source_product_count"] == 5 and measurements["retained_product_count"] == 4
    assert db.execute("SELECT count(*) FROM products WHERE source_record_id='excluded'").fetchone() == (0,)
    excluded = next(r for r in audit if r["source_record_id"] == "excluded")
    assert excluded["eligibility_mode"] == "EXCLUDED_V1" and excluded["retained_in_sqlite"] is False
    assert excluded["consumer_classification"] == "REGULATORY_RESEARCH_ONLY"


def test_ambiguity_includes_different_complete_sets_and_unknown(built):
    db, _, _ = built
    report = ambiguity_report(db)
    assert report["runtime_identifiers"]["PRODUCT_NDC"]["ambiguous_values"] == 1
    assert report["runtime_names"]["BRAND"]["ambiguous_names"] == 1
    assert report["runtime_search_names_multiple_resolved_ingredient_sets"] >= 1
    assert report["runtime_search_names_with_unresolved_identity"] >= 1


def test_identity_validation_and_no_regulatory_evidence(built):
    db, measured, _ = built
    report = validate_identity(db, measured, check_references=False)
    assert report["passed"] and report["table_count"] == 19
    assert report["integrity_check"] == ["ok"] and report["foreign_key_violations"] == []
    assert db.execute("PRAGMA user_version").fetchone() == (2,)
    assert PHASE2_SCHEMA_VERSION.endswith("phase2-identity1")


def test_coverage_lookup_uses_full_entity_primary_key(built):
    db, _, _ = built
    plan = db.execute("""EXPLAIN QUERY PLAN SELECT state FROM coverage
        WHERE entity_type='PRODUCT' AND entity_id=? AND domain='identity' AND window_key=''""", (product_id("kit"),)).fetchall()
    assert any("PRIMARY KEY" in row[3] for row in plan)
    assert not any("SCAN" in row[3] for row in plan)


def test_source_projection_validation_detects_modified_fields(built):
    db, measured, _ = built
    db.execute("UPDATE products SET marketing_category='ANDA' WHERE source_record_id='homeo'")
    report = validate_identity(db, measured, check_references=False)
    assert not report["passed"]
    assert any(e["gate"] == "all_projected_source_fields_reconciled" for e in report["errors"])


@pytest.mark.parametrize("mutation", ["ingredient", "source_id", "identifier", "generic"])
def test_raw_and_projection_disagreements_fail(mutation):
    rows = fixture_rows()
    if mutation == "ingredient": rows[2][1]["ingredient_ids"] = [I1]
    if mutation == "source_id": rows[3][0]["source_id"] = "different"
    if mutation == "identifier": rows[2][0]["rxcuis"] = ["invented"]
    if mutation == "generic": rows[2][0]["generic_name"] = "invented"
    db = connection()
    with pytest.raises(SourceError), db:
        populate_identity(db, *rows, "raw", "identity", io.StringIO())
    db.close()


@pytest.mark.parametrize("value", ["20260230", "2026092", "2026-09-26", " 20260926", 20260926])
def test_invalid_dates_are_not_repaired(value):
    with pytest.raises(ValueError): parse_source_date(value)


@pytest.mark.parametrize("field,value,reason", [("marketing_start_date", "20260927", "MARKETING_NOT_STARTED"),
    ("marketing_end_date", "20260926", "MARKETING_ENDED"), ("listing_expiration_date", "20260925", "LISTING_EXPIRED")])
def test_listing_dates_use_snapshot_boundaries(field, value, reason):
    rows = fixture_rows(); p = rows[2][0]; raw = json.loads(rows[3][0]["raw_json"]); raw[field] = value
    assert decide(p, raw)["eligibility_reason"] == reason
    raw[field] = "20261231"
    if field != "marketing_start_date": assert decide(p, raw)["eligibility_mode"] == "NORMAL_CONSUMER"


def test_missing_formulation_is_partial_not_excluded():
    rows = fixture_rows(); p = deepcopy(rows[2][0]); p["formulation_id"] = None
    raw = json.loads(rows[3][0]["raw_json"])
    result = decide(p, raw)
    assert result["eligibility_mode"] == "NORMAL_CONSUMER" and result["identity_partial"] == 1


def test_names_do_not_split_or_generate_synonyms(built):
    db, _, _ = built
    assert normalize_name("  Alpha, Beta  ") == "alpha, beta"
    assert lookup_name(db, "alpha", "INGREDIENT") == []
    assert lookup_name(db, "alpha salt", "INGREDIENT")


def test_output_guards_prevent_existing_release_or_source_writes(tmp_path):
    root = tmp_path; existing = root / "data/releases/existing"; existing.mkdir(parents=True)
    with pytest.raises(ValueError): output_paths(root, existing / "release.sqlite", root / "docs/evidence/pharma-release-v1-build-test")
    with pytest.raises(ValueError): output_paths(root, root / "data/research/new.sqlite", root / "docs/evidence/pharma-release-v1-build-test")
    db, evidence = output_paths(root, root / "data/releases/new/release.sqlite", root / "docs/evidence/pharma-release-v1-build-test")
    evidence.mkdir(parents=True)
    with pytest.raises(FileExistsError): output_paths(root, db, evidence)
