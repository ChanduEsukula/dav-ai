"""DuckDB/SQLite memory fixtures only; no shared research or serving DB writes."""
import json
import sqlite3

import duckdb
import pytest

from backend.tests.pharma_release.test_phase3b_recalls import db as frozen_db, record, build as build_recalls
from backend.tests.pharma_release.test_phase3_labels import db as identity_db, insert, raw_label, build as build_labels
from scripts.pharma_release.ae_build import populate_ae, product_coverage
from scripts.pharma_release.ae_derive import derive, LIMITATIONS
from scripts.pharma_release.ae_validation import validate_ae, summary_record, SPOT_EXPECTED
from scripts.pharma_release.identity import digest_rows
from scripts.pharma_release.schema_ae import extend_ae_schema
from scripts.pharma_release.sources import SourceError


@pytest.fixture
def db(frozen_db):
    c = frozen_db
    extend_ae_schema(c)
    insert(c, "sources", {"source_id": "ae-source", "source_name": "openfda_drug_event", "capture_id": "fixture", "source_kind": "DERIVED", "verification_basis": "fixture", "inputs_json": "[]"})
    c.commit(); return c


@pytest.fixture
def research():
    c = duckdb.connect(":memory:")
    c.execute("CREATE TABLE latest_reports(report_uid VARCHAR,case_id VARCHAR,first_received VARCHAR,last_received VARCHAR,serious BOOLEAN,death BOOLEAN,hospitalization BOOLEAN,disability BOOLEAN,life_threatening BOOLEAN)")
    c.execute("CREATE TABLE report_ingredients(report_uid VARCHAR,ingredient_id VARCHAR,suspect BOOLEAN,concomitant BOOLEAN,interacting BOOLEAN)")
    c.execute("CREATE TABLE report_reactions(report_uid VARCHAR,reaction VARCHAR)")
    c.execute("CREATE TABLE monthly(ingredient_id VARCHAR,reaction VARCHAR,period DATE,report_count BIGINT)")
    yield c; c.close()


def add_report(c, uid="r1", first="2020-01-01", last="2020-01-15", case=None, serious=True, death=True, hospitalization=True, disability=False, life_threatening=False):
    c.execute("INSERT INTO latest_reports VALUES (?,?,?,?,?,?,?,?,?)", [uid, uid if case is None else case, first, last, serious, death, hospitalization, disability, life_threatening])


def add_membership(c, uid="r1", iid="sem", suspect=True, concomitant=False, interacting=False):
    c.execute("INSERT INTO report_ingredients VALUES (?,?,?,?,?)", [uid, iid, suspect, concomitant, interacting])


def add_month(c, iid="sem", reaction="rash", period="2020-01-01", count=1):
    c.execute("INSERT INTO monthly VALUES (?,?,?::DATE,?)", [iid, reaction, period, count])


def build(c, source):
    report = derive(source, {row[0] for row in c.execute("SELECT ingredient_id FROM ingredients")})
    with c: projection = populate_ae(c, source, "ae-source")
    return projection, report


def seed(c, **kwargs):
    add_report(c, **kwargs); add_membership(c); add_month(c)


def test_report_uid_ingredient_dedup_and_roles_or(db, research):
    seed(research); add_membership(research); add_membership(research, suspect=False, concomitant=True, interacting=True)
    build(db, research); row=summary_record(db, "sem")
    assert row["report_count"] == 1 and row["suspect_report_count"] == row["concomitant_report_count"] == row["interacting_report_count"] == 1


@pytest.mark.parametrize("field", ["serious_report_count", "death_report_count", "hospitalization_report_count", "disability_report_count", "life_threatening_report_count"])
def test_reported_outcome_flags_once_per_ingredient(db, research, field):
    seed(research, disability=True, life_threatening=True); add_membership(research); add_month(research,reaction="headache")
    build(db,research); assert summary_record(db,"sem")[field]==1


def test_many_reactions_do_not_inflate_summary(db,research):
    seed(research)
    for reaction in ("headache","nausea","death"):
        add_month(research,reaction=reaction);research.execute("INSERT INTO report_reactions VALUES ('r1',?)",[reaction])
    build(db,research);row=summary_record(db,"sem")
    assert row["report_count"]==1 and row["co_report_activity"]==4 and row["reaction_term_count"]==4


def test_serious_unknown_not_counted_as_false_known(db,research):
    seed(research,serious=None);build(db,research)
    assert db.execute("SELECT serious_report_count,serious_known_report_count FROM ae_summary").fetchone()==(0,0)


def test_monthly_deduplicates_memberships_and_reactions(db,research):
    seed(research);add_membership(research);add_month(research,reaction="nausea")
    add_report(research,uid="r2",last="2020-01-31");add_membership(research,uid="r2")
    build(db,research)
    assert db.execute("SELECT period,report_count,death_report_count FROM ae_monthly").fetchall()==[("2020-01-01",2,2)]


@pytest.mark.parametrize("first,last", [("2021-01-01","2020-01-01"),("malformed","2020-01-01"),(None,"2020-01-01"),("2020-01-01","malformed"),("2020-01-01",None)])
def test_bad_or_reversed_dates_excluded_without_repair(db,research,first,last):
    seed(research,first=first,last=last);build(db,research)
    assert db.execute("SELECT count(*) FROM ae_summary").fetchone()[0]==0


@pytest.mark.parametrize("last,included", [("2019-12-31",False),("2020-01-01",True),("2026-06-30",True),("2026-07-01",False)])
def test_inclusive_lower_and_june_upper_exclusive_july(db,research,last,included):
    seed(research,first="2019-01-01",last=last);build(db,research)
    assert bool(db.execute("SELECT count(*) FROM ae_summary").fetchone()[0])==included


def test_exact_salt_identity_is_not_merged_to_base(db,research):
    seed(research);add_membership(research,iid="alpha");add_month(research,iid="alpha")
    build(db,research)
    assert {row[0] for row in db.execute("SELECT ingredient_id FROM ae_summary")}=={"sem","alpha"}
    assert not db.execute("SELECT 1 FROM ae_summary WHERE ingredient_id='beta'").fetchone()


def test_missing_frozen_identity_stops(db,research):
    add_month(research,iid="unknown-salt")
    with pytest.raises(SourceError,match="absent from frozen"):build(db,research)


def test_same_report_under_each_ingredient_not_global_unique_total(db,research):
    seed(research);add_membership(research,iid="alpha");add_month(research,iid="alpha")
    build(db,research)
    assert db.execute("SELECT sum(report_count) FROM ae_summary").fetchone()[0]==2
    assert research.execute("SELECT count(*) FROM latest_reports").fetchone()[0]==1


def test_top_reaction_ranking_and_deterministic_ties(db,research):
    seed(research)
    for reaction,activity in (("zeta",3),("alpha",3),("beta",5)):add_month(research,reaction=reaction,count=activity)
    add_month(research,reaction="beta",period="2020-02-01",count=2)
    build(db,research)
    assert db.execute("SELECT reaction,co_report_activity,rank FROM ae_top_reactions ORDER BY rank").fetchall()==[("beta",7,1),("alpha",3,2),("zeta",3,3),("rash",1,4)]


@pytest.mark.parametrize("number", [3,49,50,61])
def test_top50_cap_and_short_rankings(db,research,number):
    add_report(research);add_membership(research)
    for i in range(number):add_month(research,reaction=f"reaction {i:03d}")
    build(db,research)
    assert db.execute("SELECT count(*),max(rank) FROM ae_top_reactions").fetchone()==(min(number,50),min(number,50))


def test_reaction_outcome_sums_not_served_as_report_outcomes(db,research):
    seed(research);add_month(research,reaction="death",count=999)
    build(db,research)
    assert summary_record(db,"sem")["death_report_count"]==1
    assert "death_report_count" not in {row[1] for row in db.execute("PRAGMA table_info(ae_top_reactions)")}


def test_no_raw_faers_tables_copied(db,research):
    seed(research);build(db,research)
    tables={row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert len(tables)==19 and not tables.intersection({"latest_reports","report_ingredients","report_reactions","raw_reports","raw_drugs","raw_reactions"})


def test_partial_combination_availability_no_product_counts(db,research):
    add_report(research);add_membership(research,iid="alpha");add_month(research,iid="alpha");build(db,research)
    coverage=db.execute("SELECT state,measured_count,scope FROM coverage WHERE entity_type='PRODUCT' AND entity_id='combo1' AND domain='ae_analytics'").fetchone()
    assert coverage==("PARTIAL",1,"COMPONENT_ANALYTICS_AVAILABILITY_ONLY; NOT_PRODUCT_REPORT_COUNTS")
    assert product_coverage(db)["combination_partially_covered"]==2


def test_complete_combination_component_coverage(db,research):
    add_report(research)
    for iid in ("alpha","beta"):add_membership(research,iid=iid);add_month(research,iid=iid)
    build(db,research)
    assert db.execute("SELECT state,measured_count FROM coverage WHERE entity_id='combo1' AND domain='ae_analytics'").fetchone()==("READY",2)


def test_uncovered_ingredient_unknown_with_truthful_wording(db,research):
    seed(research);build(db,research)
    state,count,limitations=db.execute("SELECT state,measured_count,limitations_json FROM coverage WHERE entity_type='INGREDIENT' AND entity_id='beta' AND domain='ae_analytics'").fetchone()
    assert (state,count)==("UNKNOWN",None) and "AE analytics are unavailable for this ingredient in this release." in json.loads(limitations)


@pytest.mark.parametrize("iid,expected", list(SPOT_EXPECTED.items()))
def test_deduplicated_spot_benchmark_vectors(db,research,iid,expected):
    # Independently construct report flags to match the requested source vectors.
    insert(db,"ingredients",{"ingredient_id":iid,"canonical_name":iid,"identity_rule":"exact fixture","observed_at":"2026-09-26","source_id":"ndc-source"})
    n=expected["report_count"]
    research.execute(f"""INSERT INTO latest_reports SELECT 'report-'||i,'case-'||i,'2020-01-01','2020-01-15',
        CASE WHEN i<{expected['serious_known_report_count']} THEN i<{expected['serious_report_count']} ELSE NULL END,
        i<{expected['death_report_count']},i<{expected['hospitalization_report_count']},
        i<{expected['disability_report_count']},i<{expected['life_threatening_report_count']} FROM range({n}) r(i)""")
    research.execute("INSERT INTO report_ingredients SELECT report_uid,?,true,false,false FROM latest_reports",[iid])
    terms=expected.get("reaction_term_count",1);activity=expected.get("co_report_activity",n)
    for i in range(terms):add_month(research,iid=iid,reaction=f"term {i:04d}",count=activity-(terms-1) if i==0 else 1)
    build(db,research);actual=summary_record(db,iid)
    assert all(actual[field]==value for field,value in expected.items())


def test_parent_labels_and_recalls_unchanged(db,research):
    build_labels(db,[raw_label(ndcs=["0001-101"])]);build_recalls(db,[record()])
    tables=("labels","label_sections","product_labels","recalls","product_recalls")
    before={table:digest_rows(db.execute("SELECT * FROM "+table)) for table in tables}
    seed(research);build(db,research)
    assert before=={table:digest_rows(db.execute("SELECT * FROM "+table)) for table in tables}


def test_real_derivation_replay_zero_row_changes(db,research):
    seed(research);first,derivation=build(db,research);changes=db.total_changes
    second,rederived=build(db,research)
    assert changes==db.total_changes and derivation==rederived
    for table in first["projection"]:
        assert second["projection"][table]["inserted"]==0
        assert first["projection"][table]["sha256_sorted_row_hashes"]==second["projection"][table]["sha256_sorted_row_hashes"]


def test_nonidentical_ae_replay_rejected(db,research):
    seed(research);build(db,research);research.execute("UPDATE latest_reports SET death=false")
    with pytest.raises(SourceError,match="Nonidentical AE replay"):build(db,research)


def test_duplicate_latest_report_identity_not_guessed(db,research):
    seed(research);add_report(research)
    with pytest.raises(SourceError,match="missing/duplicated"):build(db,research)


def test_foreign_keys_and_compact_semantic_validation(db,research):
    seed(research);report,derivation=build(db,research)
    assert db.execute("PRAGMA foreign_key_check").fetchall()==[]
    assert validate_ae(db,report,derivation,check_benchmarks=False)["passed"]
    with pytest.raises(sqlite3.IntegrityError):db.execute("UPDATE ae_monthly SET ingredient_id='unknown'")


def test_provenance_and_no_unsupported_interpretations(db,research):
    seed(research);build(db,research);row=summary_record(db,"sem")
    assert row["source_id"]=="ae-source" and row["window_start"]=="2020-01-01" and row["window_end"]=="2026-06-30"
    assert row["count_unit"]=="deduplicated ingredient-report associations"
    text=' '.join(LIMITATIONS).casefold()
    assert "current normalized/revised research snapshot" in text
    for forbidden in ("caused","incidence","risk","probability","patient harm rate","most common side effects"):
        assert forbidden not in text


def test_report_without_reaction_still_creates_month(db,research):
    seed(research);add_report(research,uid="r2",last="2023-09-01");add_membership(research,uid="r2")
    _,report=build(db,research)
    assert report["monthly_reconciliation"]["report_only_rows"]==[("sem","2023-09-01")]
    assert db.execute("SELECT report_count FROM ae_monthly WHERE period='2023-09-01'").fetchone()==(1,)


def test_schema_changes_only_three_empty_ae_tables(frozen_db):
    before=frozen_db.execute("SELECT type,name,sql FROM sqlite_master WHERE tbl_name NOT IN ('ae_summary','ae_monthly','ae_top_reactions') ORDER BY type,name").fetchall()
    extend_ae_schema(frozen_db)
    assert before==frozen_db.execute("SELECT type,name,sql FROM sqlite_master WHERE tbl_name NOT IN ('ae_summary','ae_monthly','ae_top_reactions') ORDER BY type,name").fetchall()
    assert frozen_db.execute("PRAGMA user_version").fetchone()[0]==4
