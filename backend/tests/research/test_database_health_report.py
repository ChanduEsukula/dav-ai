import importlib.util
from pathlib import Path
import duckdb
import pytest

spec=importlib.util.spec_from_file_location('health',Path(__file__).resolve().parents[3]/'scripts/database_health_report.py')
health=importlib.util.module_from_spec(spec);spec.loader.exec_module(health)


def test_database_connection_rejects_mutation(tmp_path):
    p=tmp_path/'database.duckdb'
    c=duckdb.connect(str(p));c.execute('CREATE TABLE existing(i INTEGER)');c.close()
    before=p.read_bytes()
    with health.readonly_database(p) as c:
        assert c.execute('SELECT count(*) FROM existing').fetchone()[0]==0
        with pytest.raises(duckdb.InvalidInputException):c.execute('CREATE TABLE forbidden(i INTEGER)')
    assert p.read_bytes()==before


def test_pair_history_counts_distinct_months_and_excludes_future_without_repair():
    c=duckdb.connect(':memory:')
    c.execute('CREATE TABLE monthly(ingredient_id VARCHAR,reaction VARCHAR,period DATE,report_count BIGINT)')
    c.execute("INSERT INTO monthly VALUES ('a','x','2025-01-01',2),('a','x','2025-01-01',3),('a','x','2025-02-01',5),('a','y','2030-01-01',1)")
    r=health.pair_coverage(c,'2026-06-30')
    assert r['total_pairs']==1 and r['active_2']==1 and r['volume_10_19']==1
    assert c.execute("SELECT count(*) FROM monthly WHERE period='2030-01-01'").fetchone()[0]==1
    c.close()


def test_missing_outcomes_are_unknown_not_false():
    c=duckdb.connect(':memory:')
    c.execute('CREATE TABLE latest_reports(serious BOOLEAN,death BOOLEAN,hospitalization BOOLEAN,disability BOOLEAN,life_threatening BOOLEAN)')
    c.execute('INSERT INTO latest_reports VALUES (NULL,NULL,NULL,NULL,NULL),(TRUE,FALSE,TRUE,FALSE,FALSE)')
    r=health.outcome_availability(c)
    assert r['selected_reports']==2 and r['serious_known']==1 and r['serious_unknown']==1
    assert r['death_true']==0 and r['death_unknown']==1
    c.close()


def test_identity_hash_normalizes_only_case_and_whitespace():
    assert health.canonical_id('  ACETAMINOPHEN  ')==health.canonical_id('acetaminophen')
    assert health.canonical_id('metformin')!=health.canonical_id('metformin hydrochloride')


def test_complete_offline_report_preserves_database_and_separates_pair_counts(tmp_path):
    import gzip,hashlib,json
    import pyarrow as pa
    import pyarrow.parquet as pq
    folder=tmp_path/'identity';folder.mkdir()
    ingredient=health.canonical_id('example ingredient')
    pq.write_table(pa.Table.from_pylist([{'ingredient_id':ingredient,'canonical_name':'example ingredient'}]),folder/'ingredients.parquet')
    pq.write_table(pa.Table.from_pylist([{'source_id':'p1','ingredient_ids':[ingredient],'rxcuis':['123'],
        'product_ndcs':['11111-1111'],'package_ndcs':['11111-1111-11'],'generic_name':'example ingredient','brand_name':'example'}]),folder/'products.parquet')
    mapping={'observed_at':'2026-09-26','aliases':{'name':{},'ndc':{},'rxcui':{}}}
    with gzip.open(folder/'mapping.json.gz','wt') as f:json.dump(mapping,f)
    (folder/'summary.json').write_text(json.dumps({'mapping_hash':hashlib.sha256(json.dumps(mapping,sort_keys=True,default=str).encode()).hexdigest()}))
    p=tmp_path/'analysis.duckdb';c=duckdb.connect(str(p))
    c.execute('CREATE TABLE latest_reports(first_received VARCHAR,last_received VARCHAR,receivedate_raw VARCHAR,receiptdate_raw VARCHAR,serious BOOLEAN,death BOOLEAN,hospitalization BOOLEAN,disability BOOLEAN,life_threatening BOOLEAN)')
    c.execute("INSERT INTO latest_reports VALUES ('2025-01-01','2025-01-02','20250101','20250102',NULL,FALSE,FALSE,FALSE,FALSE)")
    columns=['report_count','unique_case_count','serious_count','serious_known_count','death_report_count','hospitalization_count','disability_count','life_threatening_count','suspect_count','concomitant_count','interacting_count']
    c.execute('CREATE TABLE monthly(ingredient_id VARCHAR,reaction VARCHAR,period DATE,'+','.join(x+' BIGINT' for x in columns)+')')
    for reaction in ['reaction one','reaction two']:
        c.execute('INSERT INTO monthly VALUES (?,?,?,1,1,0,0,0,0,0,0,1,0,0)',[ingredient,reaction,'2025-01-01'])
    c.close();before=p.read_bytes();result=health.health_report(p)
    assert result['identity']['mapped_names']==1
    assert result['monthly_totals_through_cutoff']['report_count']==2
    assert result['outcomes_report_level']['selected_reports']==1
    assert result['outcomes_report_level']['serious_unknown']==1
    assert result['database_size_mtime_unchanged']
    assert p.read_bytes()==before
