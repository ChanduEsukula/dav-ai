import sys
from pathlib import Path
import duckdb
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'scripts'))
import drug_safety_snapshot as snap


@pytest.fixture
def c():
    c=duckdb.connect(':memory:')
    c.execute('CREATE TABLE report_ingredients(report_uid VARCHAR,ingredient_id VARCHAR,suspect BOOLEAN,concomitant BOOLEAN,interacting BOOLEAN)')
    c.execute('CREATE TABLE latest_reports(report_uid VARCHAR,first_received VARCHAR,last_received VARCHAR,serious BOOLEAN,death BOOLEAN,hospitalization BOOLEAN,disability BOOLEAN,life_threatening BOOLEAN)')
    c.execute('CREATE TABLE report_reactions(report_uid VARCHAR,reaction VARCHAR)')
    c.execute('CREATE TABLE mention_counts(report_uid VARCHAR,co_drugs BIGINT)')
    c.execute('CREATE TABLE monthly(ingredient_id VARCHAR,reaction VARCHAR,period DATE,'+','.join(f+' BIGINT' for f in snap.PAIR_FIELDS)+',mean_co_reported_drugs DOUBLE)')
    c.execute("INSERT INTO report_ingredients VALUES ('r1','a',TRUE,FALSE,FALSE),('r1','a',TRUE,FALSE,FALSE),('r2','a',FALSE,TRUE,FALSE),('bad','a',FALSE,FALSE,FALSE),('reverse','a',FALSE,FALSE,FALSE)")
    c.execute("INSERT INTO latest_reports VALUES ('r1','2025-01-01','2025-02-01',TRUE,FALSE,TRUE,NULL,FALSE),('r2','2025-01-01','9000-01-01',NULL,TRUE,FALSE,FALSE,FALSE),('bad','2025-01-01','not-a-date',NULL,NULL,NULL,NULL,NULL),('reverse','2025-03-01','2025-02-01',TRUE,TRUE,FALSE,FALSE,FALSE)")
    c.execute("INSERT INTO report_reactions VALUES ('r1','death'),('r1','nausea'),('r1','nausea'),('r2','nausea'),('bad','nausea'),('reverse','nausea')")
    c.execute("INSERT INTO mention_counts VALUES ('r1',2),('r2',1),('bad',1),('reverse',1)")
    for term in ['death','nausea']:
        c.execute("INSERT INTO monthly VALUES ('a',?,'2025-02-01',1,1,1,0,1,0,0,1,0,0,2)",[term])
    c.execute("INSERT INTO monthly VALUES ('a','nausea','9000-01-01',1,0,0,1,0,0,0,0,1,0,1)")
    yield c
    c.close()


def test_report_uid_deduplication_and_multiple_reactions(c):
    result=snap.report_snapshots(c,['a'],'2026-06-30')
    eligible=next(r for r in result if r['scope']=='date_eligible_contributing')
    assert eligible['reports']==eligible['distinct_report_uids']==1
    assert eligible['max_input_ingredient_link_rows']==2
    assert eligible['reports_with_multiple_reactions']==1
    assert eligible['report_count']==2
    assert eligible['serious_true']==1 and eligible['serious_count']==2
    assert eligible['disability_unknown']==1


def test_exact_ingredient_lookup_and_no_salt_guess():
    item={'ingredient_id':snap.canonical_id('semaglutide'),'canonical_name':'semaglutide'}
    assert snap.lookup([item],'  SEMAGLUTIDE ')==item
    assert snap.lookup([item],ingredient_id=item['ingredient_id'])==item
    with pytest.raises(snap.LookupFailure):snap.lookup([item],'semaglutide sodium')


def test_ambiguous_exact_name_lists_candidates_and_stops():
    candidates=[{'ingredient_id':'second','canonical_name':'same'},{'ingredient_id':'first','canonical_name':'same'}]
    with pytest.raises(snap.LookupFailure,match='ambiguous.*first.*second'):snap.lookup(candidates,'same')


def test_pair_level_vs_report_level_and_death_concepts(c):
    p=snap.pair_snapshot(c,'a','2026-06-30')
    assert p['totals']['report_count']==2
    assert p['totals']['death_report_count']==0
    assert p['reaction_death']['reaction_death_pair_mentions']==1
    assert p['reaction_death']['death_outcome_mentions_with_reaction_death']==0
    assert p['totals']['pair_weighted_mean_co_reported_drugs']==2
    assert p['windows']['trailing_12m']['pair_mentions'] is None
    assert p['windows']['change_12m_percent'] is None


def test_malformed_future_and_reverse_dates_excluded_not_repaired(c):
    r=snap.report_snapshots(c,['a'],'2026-06-30')
    all_rows=next(x for x in r if x['scope']=='all_selected')
    eligible=next(x for x in r if x['scope']=='date_eligible_contributing')
    assert all_rows['reports']==4 and all_rows['excluded_date_reports']==3
    assert eligible['reports']==1
    assert c.execute("SELECT last_received FROM latest_reports WHERE report_uid='bad'").fetchone()[0]=='not-a-date'
    assert c.execute("SELECT count(*) FROM monthly WHERE period>'2030-01-01'").fetchone()[0]==1


def test_future_cutoff_and_partial_month_stop_before_database_access(tmp_path):
    for cutoff in ['2026-07-31','2026-06-15']:
        with pytest.raises(ValueError):snap.snapshots(tmp_path/'not-opened.duckdb',[],cutoff)


def test_duplicate_context_records_do_not_inflate_link_count(tmp_path):
    import pyarrow as pa
    import pyarrow.parquet as pq
    folder=tmp_path/'context';folder.mkdir()
    rows=[{'ingredient_id':'a','kind':'labels','source_id':'label1','available_at':'2026-09-26'}]*2
    pq.write_table(pa.Table.from_pylist(rows),folder/'regulatory.parquet')
    c=duckdb.connect(':memory:')
    r=snap.regulatory_snapshot(c,tmp_path,'a');c.close()
    assert r['labels']['status']=='VERIFIED' and r['labels']['source_records']==1
    assert r['recalls']['status']=='UNKNOWN' and r['safety_communications']['status']=='UNKNOWN'
