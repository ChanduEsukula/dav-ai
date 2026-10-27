"""Synthetic fixtures exclusively in temporary test directories, never real research."""
import copy
import io
import json
from pathlib import Path
import zipfile

import httpx
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from app.research.bulk import discover,extract,ingest,source_date,fingerprint,SCHEMAS
from app.research.identity import IdentityIndex,build_identity
from app.research.analysis import available_context,eligible_asof,prepare,build_features,diagnose_sparsity


def report(identifier='test-case',version='1',date='20200110'):
    return {'safetyreportid':identifier,'safetyreportversion':version,'receivedate':'20200101','receiptdate':date,
        'serious':'1','seriousnesshospitalization':'1','patient':{
            'drug':[{'medicinalproduct':'Test Brand','drugcharacterization':'1','openfda':{'product_ndc':['12345-6789']}}],
            'reaction':[{'reactionmeddrapt':'Test Reaction','reactionoutcome':'1','reactionmeddraversionpt':'test-version'}]}}


def archive(records):
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:z.writestr('records.json',json.dumps({'results':records}))
    return buf.getvalue()


def source(kind,record_sets):
    parts=[];files={}
    for n,values in enumerate(record_sets):
        url=f'https://download.open.fda.gov/drug/{kind}/2020q1/test-{n}.json.zip'
        parts.append({'file':url,'records':len(values),'size_mb':'0.01'});files[url]=archive(values)
    manifest={'results':{'drug':{kind:{'export_date':'2026-09-26','total_records':sum(p['records'] for p in parts),'partitions':parts}}}}
    requests=[]
    def handler(request):
        requests.append(str(request.url))
        return httpx.Response(200,content=files[str(request.url)],headers={'content-length':str(len(files[str(request.url)]))})
    return manifest,httpx.Client(transport=httpx.MockTransport(handler)),requests,files


def metadata():return {'source_url':'https://download.open.fda.gov/drug/event/test.json.zip','export_date':'2026-09-26',
                       'observed_at':'2026-09-26T00:00:00+00:00','partition':'2020q1'}


def test_manifest_rejects_duplicates_untrusted_hosts_and_counts():
    m,*_=source('event',[[report()]])
    assert discover(m,'event')['total_records']==1
    for mutation in ('duplicate','host','count'):
        bad=copy.deepcopy(m);d=bad['results']['drug']['event']
        if mutation=='duplicate':d['partitions']*=2
        if mutation=='host':d['partitions'][0]['file']='https://evil.invalid/drug/event/x.json.zip'
        if mutation=='count':d['total_records']=3
        with pytest.raises(ValueError):discover(bad,'event')


def test_resume_refuses_changed_snapshot_before_downloading(tmp_path):
    m,h,requests,_=source('event',[[report()]])
    first=ingest(tmp_path,'event',http=h,manifest=m,min_free_gb=0)
    changed=copy.deepcopy(m)
    changed['results']['drug']['event']['export_date']='2026-09-27'
    with pytest.raises(ValueError,match='manifest changed'):
        ingest(tmp_path,'event',http=h,manifest=changed,min_free_gb=0,
               expected_dataset_key=first['dataset_key'])
    assert len(requests)==1
    assert len(list((tmp_path/'event').iterdir()))==1


def test_missing_versions_do_not_discard_unambiguous_source_cases(tmp_path):
    ndc={'product_id':'fixture','product_ndc':'12345-6789','generic_name':'Test Ingredient',
         'active_ingredients':[{'name':'Test Ingredient','strength':'1 mg'}],
         'dosage_form':'TABLET','route':['ORAL']}
    m,h,_,_=source('ndc',[[ndc]])
    ingest(tmp_path,'ndc',http=h,manifest=m,min_free_gb=0);build_identity(tmp_path)
    unique=report('unique',None)
    conflict=report('conflict',None)
    conflict2=report('conflict',None,'20200210')
    mixed=report('mixed',None)
    mixed2=report('mixed','2','20200210')
    known=report('known','1')
    known2=report('known','2','20200210')
    m,h,_,_=source('event',[[unique,copy.deepcopy(unique),conflict,conflict2,mixed,mixed2,known,known2]])
    ingest(tmp_path,'event',http=h,manifest=m,min_free_gb=0)
    result=prepare(tmp_path)
    assert result['latest_cases']==2
    assert result['version_selection']['superseded_distinct_payloads']==1
    assert result['version_selection']['raw_rows_in_ambiguous_cases']==4
    import duckdb
    with duckdb.connect(str(tmp_path/'analysis.duckdb')) as c:
        assert c.execute('SELECT case_id,version FROM latest_reports ORDER BY case_id').fetchall()==[('known',2),('unique',None)]


def test_checkpoint_resume_replay_and_output_integrity(tmp_path):
    m,http,requests,_=source('event',[[report('a')],[report('b')]])
    a=ingest(tmp_path,'event',http=http,manifest=m,max_files=1,min_free_gb=0,discard_archives=True)
    assert a['raw_records']==1 and not a['complete']
    progress=json.loads((Path(a['snapshot_path'])/'progress.json').read_text())
    assert progress['files_complete']==1 and progress['files_remaining']==1
    assert progress['next_partition']==m['results']['drug']['event']['partitions'][1]['file']
    assert progress['stop_reason']=='max_files'
    b=ingest(tmp_path,'event',http=http,manifest=m,min_free_gb=0,discard_archives=True)
    assert b['raw_records']==2 and b['files_skipped_this_run']==1 and b['complete']
    c=ingest(tmp_path,'event',http=http,manifest=m,min_free_gb=0)
    assert c['files_processed_this_run']==0 and len(requests)==2
    assert json.loads((Path(c['snapshot_path'])/'progress.json').read_text())['next_partition'] is None
    file=next(Path(c['snapshot_path']).glob('files/quarter=*/*/reports.parquet'))
    file.write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='checksum'):ingest(tmp_path,'event',http=http,manifest=m,min_free_gb=0)


def test_final_manifest_network_failure_preserves_committed_summary(tmp_path):
    from app.research.bulk import MANIFEST
    manifest,_,_,files=source('event',[[report()]])
    checks=0
    def handler(request):
        nonlocal checks
        if str(request.url)==MANIFEST:
            checks+=1
            if checks==2:raise httpx.ConnectError('fixture DNS failure',request=request)
            return httpx.Response(200,json=manifest)
        return httpx.Response(200,content=files[str(request.url)])
    client=httpx.Client(transport=httpx.MockTransport(handler))
    result=ingest(tmp_path,'event',http=client,min_free_gb=0)
    assert result['files_complete']==1 and result['raw_records']==1
    assert not result['complete']
    assert result['stop_reason']=='manifest_verification_failed'
    assert result['failures'][0]['error']=='ManifestVerificationFailed'
    path=Path(result['snapshot_path'])
    assert json.loads((path/'summary.json').read_text())['files_complete']==1
    assert json.loads((path/'progress.json').read_text())['error']==result['failures']
    assert len(list(path.glob('files/quarter=*/*/receipt.json')))==1


def test_malformed_record_quarantine_and_malformed_file_atomicity(tmp_path):
    m,http,_,files=source('event',[[report(),{'bad':'fixture'}]])
    r=ingest(tmp_path,'event',http=http,manifest=m,min_free_gb=0)
    assert r['raw_records']==2 and r['quarantined']==1
    assert json.loads(next(Path(r['snapshot_path']).glob('files/quarter=*/*/quarantine.jsonl')).read_text())['raw']=={'bad':'fixture'}
    broken=tmp_path/'broken';m2,http2,_,files2=source('event',[[report()]])
    # A well-formed ZIP containing truncated JSON cannot become a completed shard.
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w') as z:z.writestr('x.json','{"results":[')
    files2[next(iter(files2))]=buf.getvalue()
    failed=ingest(broken,'event',http=http2,manifest=m2,min_free_gb=0)
    assert failed['files_complete']==0 and failed['failures']
    assert not list(Path(failed['snapshot_path']).glob('files/quarter=*/*/receipt.json'))


def test_extraction_roles_versions_dates_and_missing_values():
    r=report();r['patient']['reaction']*=2
    x=extract(r,'event',metadata())
    assert x['reports'][0]['case_id']=='test-case' and x['reports'][0]['version']==1
    assert x['reports'][0]['death'] is None
    assert x['drugs'][0]['role']=='1' # Source supports suspect, not primary/secondary.
    assert x['reactions'][0]['normalized_term']=='test reaction'
    assert len(x['reactions'])==2 # Raw mentions retained; analytical dedupe separately.
    assert source_date('20200230') is None and source_date('202001') is None
    r['receiptdate']='202001';assert extract(r,'event',metadata())['reports'][0]['last_received'] is None


def test_conservative_identity_conflict_and_unknown_handling():
    m={'aliases':{'rxcui':{'1':[['i1']]},'ndc':{'12345-6789':[['i1']]},'name':{'test brand':[['i1']],'ambiguous':[['i1'],['i2']]}},
       'ingredients':{'test ingredient':'i1'}}
    index=IdentityIndex(m)
    assert index.resolve({'product_ndc':['12345-6789']})[0]==['i1']
    assert index.resolve({'rxcui':['unknown'],'medicinalproduct':'Test Brand'})[0]==[]
    assert index.resolve({'medicinalproduct':'ambiguous'})[0]==[]
    assert index.resolve({'medicinalproduct':'Test Brand extended'})[0]==[]
    assert index.resolve({'medicinalproduct':' TEST  BRAND '})[0]==['i1']
    m['aliases']['ndc']['other']=[['i2']]
    assert index.resolve({'rxcui':['1'],'product_ndc':['other']})[0]==[]


def test_cutoffs_never_use_future_context_or_mapping():
    rows=[{'ingredient_id':'i','kind':k,'source_date':'2020-01-01','available_at':'2026-09-26'} for k in ['labels','recalls']]
    for k in ['labels','recalls']:
        assert available_context(rows,'i','2023-06-30',k) is None
        assert available_context(rows,'i','2026-09-26',k)
    r={'observed_at':'2026-09-26T00:00:00Z','last_received':'2020-01-01'}
    assert not eligible_asof(r,'2023-06-30','2020-01-01')
    assert not eligible_asof(r,'2026-09-26','2026-10-01')
    assert eligible_asof(r,'2026-09-26','2026-09-26')


def test_export_blocks_incomplete_corpus_before_filling_zero_periods(tmp_path):
    m,h,_,_=source('event',[[report('a')],[report('b')]])
    ingest(tmp_path,'event',http=h,manifest=m,max_files=1,min_free_gb=0)
    with pytest.raises(ValueError,match='Incomplete event snapshot'):
        build_features(tmp_path,tmp_path/'export')
    assert not (tmp_path/'export').exists()


def test_cli_resume_normalizes_each_new_file_and_reuses_completed_outputs(tmp_path,monkeypatch):
    import sys
    from app.jobs import ingest_research as job
    ndc={'product_id':'fixture','product_ndc':'12345-6789','generic_name':'Test Ingredient',
         'active_ingredients':[{'name':'Test Ingredient','strength':'1 mg'}],
         'dosage_form':'TABLET','route':['ORAL']}
    m,h,_,_=source('ndc',[[ndc]])
    ingest(tmp_path,'ndc',http=h,manifest=m,min_free_gb=0);build_identity(tmp_path)
    m,h,requests,_=source('event',[[report('a')],[report('b')]])
    ingest(tmp_path,'event',http=h,manifest=m,max_files=1,min_free_gb=0)
    def local_ingest(root,kind,**kwargs):
        kwargs['min_free_gb']=0
        return ingest(root,kind,http=h,manifest=m,**kwargs)
    monkeypatch.setattr(job,'ingest',local_ingest)
    monkeypatch.setattr(sys,'argv',['ingest_research','event','--root',str(tmp_path),'--resume','--normalize'])
    assert job.main()==0
    outputs=list((tmp_path/'normalized').rglob('*.parquet'))
    assert len(outputs)==2
    before={str(p):p.stat().st_mtime_ns for p in outputs}
    assert job.main()==0
    assert len(requests)==2
    assert before=={str(p):p.stat().st_mtime_ns for p in outputs}
    enforcement_manifest,enforcement_http,_,_=source('enforcement',[[{'recall_number':'fixture-recall'}]])
    ingest(tmp_path,'enforcement',http=enforcement_http,manifest=enforcement_manifest,min_free_gb=0)
    from app.jobs.audit_research import audit, require_complete
    checked=audit(tmp_path)
    require_complete(checked)
    unfinished=copy.deepcopy(checked)
    unfinished['ledger']['noncomplete_entries']=[{'url':'fixture','status':'running'}]
    with pytest.raises(ValueError,match='noncomplete_entries'):require_complete(unfinished)
    assert checked['normalization']['verified_files']==2
    assert checked['normalization']['verified_mentions']==2
    assert checked['normalization']['missing_partition_ids']==[]
    # Even a self-consistent checksum receipt must not certify missing rows.
    damaged=outputs[0]
    schema=pq.ParquetFile(damaged).schema_arrow
    pq.write_table(pa.Table.from_pylist([],schema=schema),damaged)
    from app.research.bulk import file_digest
    receipt=damaged.with_suffix('.json');saved=json.loads(receipt.read_text())
    saved['output_hash']=file_digest(damaged);receipt.write_text(json.dumps(saved))
    with pytest.raises(ValueError,match='integrity verification failed'):
        audit(tmp_path)
    assert job.main()==0
    assert pq.ParquetFile(damaged).metadata.num_rows==1
    assert len(requests)==2 # Repair only invalid normalization, never redownload source.


def test_complete_replay_records_zero_downloads_and_unchanged_artifacts(tmp_path,monkeypatch):
    from app.jobs import verify_research_replay as job
    from app.research.analysis import normalize_mentions
    from app.research.bulk import MANIFEST
    ndc={'product_id':'fixture','product_ndc':'12345-6789','generic_name':'Test Ingredient',
         'active_ingredients':[{'name':'Test Ingredient','strength':'1 mg'}],
         'dosage_form':'TABLET','route':['ORAL']}
    m,h,_,_=source('ndc',[[ndc]])
    ingest(tmp_path,'ndc',http=h,manifest=m,min_free_gb=0);build_identity(tmp_path)
    m,h,_,_=source('event',[[report('a')],[report('b')]])
    ingest(tmp_path,'event',http=h,manifest=m,max_files=1,min_free_gb=0)
    evidence=tmp_path/'evidence'
    with pytest.raises(ValueError,match='requires complete corpus'):job.verify(tmp_path,evidence)
    assert not json.loads((evidence/'replay-verification.json').read_text())['passed']
    ingest(tmp_path,'event',http=h,manifest=m,min_free_gb=0)
    normalize_mentions(tmp_path)
    original=httpx.Client
    def handler(request):
        assert str(request.url)==MANIFEST
        return httpx.Response(200,json=m)
    monkeypatch.setattr(job.httpx,'Client',lambda **kw:original(transport=httpx.MockTransport(handler),**kw))
    result=job.verify(tmp_path,evidence)
    assert result['passed'] and result['archive_requests']==0
    assert result['ingestion']['files_skipped_this_run']==2
    assert result['ingestion']['files_processed_this_run']==0
    assert result['changed_artifacts']==[]
    assert json.loads((evidence/'replay-before.json').read_text())==json.loads((evidence/'replay-after.json').read_text())


def test_partitioned_drug_join_preserves_combinations_mentions_and_selection(tmp_path):
    from app.research.analysis import connect_analytics,select_resolved_drugs
    products=[{'product_id':'combo','product_ndc':'11111-0001','generic_name':'Ingredient A / Ingredient B',
        'active_ingredients':[{'name':'Ingredient A','strength':'1 mg'},{'name':'Ingredient B','strength':'2 mg'}],
        'dosage_form':'TABLET','route':['ORAL']},
        {'product_id':'single','product_ndc':'22222-0002','generic_name':'Ingredient A',
         'active_ingredients':[{'name':'Ingredient A','strength':'1 mg'}],'dosage_form':'TABLET','route':['ORAL']}]
    m,h,_,_=source('ndc',[products]);ingest(tmp_path,'ndc',http=h,manifest=m,min_free_gb=0);build_identity(tmp_path)
    current=report('multi','2')
    current['patient']['drug']=[
        {'medicinalproduct':'Combination','drugcharacterization':'1','openfda':{'product_ndc':['11111-0001']}},
        {'medicinalproduct':'Combination','drugcharacterization':'2','openfda':{'product_ndc':['11111-0001']}},
        {'medicinalproduct':'Unresolvable fixture drug','drugcharacterization':'1'},
        {'medicinalproduct':'Single','drugcharacterization':'1','openfda':{'product_ndc':['22222-0002']}},
        {'medicinalproduct':'Ingredient A','drugcharacterization':'1','openfda':{'product_ndc':['99999-0009']}}]
    current['patient']['reaction']+=[copy.deepcopy(current['patient']['reaction'][0]),{},
                                   {'reactionmeddrapt':'Another fixture reaction'}]
    old=copy.deepcopy(current);old['safetyreportversion']='1'
    other=report('other',None)
    other['patient']['drug']=[{'medicinalproduct':'  INGREDIENT   A  ','drugcharacterization':'1'}]
    ambiguous=copy.deepcopy(other);ambiguous['safetyreportid']='ambiguous'
    ambiguous2=copy.deepcopy(ambiguous);ambiguous2['receiptdate']='20200210'
    m,h,_,_=source('event',[[old,current,ambiguous],[copy.deepcopy(current),other,ambiguous2]])
    ingest(tmp_path,'event',http=h,manifest=m,min_free_gb=0)
    prepared=prepare(tmp_path)
    assert prepared['latest_cases']==2 and prepared['excluded_ambiguous_cases']==1
    assert prepared['reports']['exact_duplicate_rows']==1
    index=IdentityIndex.load(tmp_path)
    ingredient_a=index.resolve({'product_ndc':['22222-0002']})[0][0]
    combo=set(index.resolve({'product_ndc':['11111-0001']})[0]);assert len(combo)==2
    with connect_analytics(tmp_path) as conn:
        selected=dict(conn.execute('SELECT case_id,report_uid FROM latest_reports').fetchall())
        expected={(selected['multi'],i,role,ingredient) for i,role in [(0,'1'),(1,'2')] for ingredient in combo}
        expected|={(selected['multi'],3,'1',ingredient_a),(selected['other'],0,'1',ingredient_a)}
        oracle=set(conn.execute('''SELECT DISTINCT d.report_uid,d.drug_index,d.role,unnest(n.ingredient_ids)
            FROM raw_drugs d JOIN normalized n USING(report_uid,drug_index)
            JOIN latest_reports r USING(report_uid)''').fetchall())
        assert oracle==expected
        for buckets in (1,3,16):
            select_resolved_drugs(conn,buckets)
            actual=conn.execute('SELECT report_uid,drug_index,role,ingredient_id FROM resolved_drugs').fetchall()
            assert len(actual)==len(expected)==6 and set(actual)==expected
            assert {row[0] for row in actual}==set(selected.values())
        assert conn.execute("SELECT count(*) FROM normalized WHERE resolution='unresolved_identifier'").fetchone()[0]>0
        assert conn.execute("SELECT count(*) FROM normalized WHERE resolution='unresolved_name'").fetchone()[0]>0
        reaction_oracle=set(conn.execute('''SELECT DISTINCT x.report_uid,x.normalized_term FROM raw_reactions x
            JOIN latest_reports r USING(report_uid) WHERE nullif(x.normalized_term,'') IS NOT NULL''').fetchall())
        assert len(reaction_oracle)==3
        from app.research.shards import materialize_reactions
        import shutil
        for buckets in (1,3):
            variant=tmp_path/f'reaction-buckets-{buckets}';variant.mkdir()
            for name in ('analysis-selected-checkpoint.json','event-latest.json'):
                shutil.copy2(tmp_path/name,variant/name)
            reactions=materialize_reactions(conn,variant,buckets=buckets)
            assert reactions['complete'] and reactions['union_integrity_passed']
            assert reactions['totals']['selected_unique_reaction_mentions']==5
            assert reactions['totals']['usable_reaction_mentions']==4
            assert reactions['totals']['invalid_or_empty_reaction_mentions']==1
            assert set(conn.execute('SELECT * FROM report_reactions').fetchall())==reaction_oracle
    from app.research.shards import checkpoint_resolved_drugs
    checkpoint=checkpoint_resolved_drugs(tmp_path,buckets=3)
    assert checkpoint['complete'] and checkpoint['union_integrity_passed']
    assert checkpoint['totals']['selected_unique_mentions']==6
    assert checkpoint['totals']['resolved_mentions']==4
    assert checkpoint['totals']['unresolved_mentions']==2
    assert checkpoint['totals']['combination_mentions']==2
    assert checkpoint['totals']['expected_ingredient_links']==6
    artifacts=list((tmp_path/'analysis-shards/resolved_drugs').glob('shard-*'))
    before={p.name:p.stat().st_mtime_ns for p in artifacts}
    assert checkpoint_resolved_drugs(tmp_path,buckets=3)['complete']
    assert before=={p.name:p.stat().st_mtime_ns for p in artifacts}
    damaged=next(p for p in artifacts if p.suffix=='.parquet');damaged.write_bytes(b'corrupt fixture')
    with pytest.raises(ValueError,match='checkpoint mismatch'):
        checkpoint_resolved_drugs(tmp_path,buckets=3)


def test_real_pipeline_fixture_dedupe_rolling_export_reproducibility(tmp_path):
    ndc={'product_id':'test-product','product_ndc':'12345-6789','generic_name':'Test Ingredient','brand_name':'Test Brand',
         'active_ingredients':[{'name':'Test Ingredient','strength':'1 mg/1'}],'dosage_form':'TABLET','route':['ORAL'],'packaging':[]}
    m,h,_,_=source('ndc',[[ndc]])
    ingest(tmp_path,'ndc',http=h,manifest=m,min_free_gb=0);identity=build_identity(tmp_path)
    assert identity['canonical_ingredients']==1 and identity['formulations']==1
    fixtures=[]
    for month in range(36):
        dt=f'{2020+month//12}{month%12+1:02d}10'
        for n in range(3):fixtures.append(report(f'case-{month}-{n}','1',dt))
    fixtures+=[copy.deepcopy(fixtures[0]),report('case-0-0','2','20200210')]
    fixtures[1]['patient']['reaction']*=2
    # Repeat the same source case across files as well as within version history.
    m,h,_,_=source('event',[fixtures[:55],fixtures[55:]]);ingest(tmp_path,'event',http=h,manifest=m,min_free_gb=0)
    result=prepare(tmp_path)
    assert result['reports']['raw_rows']==110 and result['latest_cases']==108
    assert result['reports']['exact_duplicate_rows']==1
    assert result['pairs']==1
    # Sharding must preserve cross-file revision selection and exact duplicates.
    from app.research.analysis import connect_analytics,select_latest_keys
    with connect_analytics(tmp_path) as conn:
        expected=set(conn.execute('SELECT * FROM latest_report_keys').fetchall())
        for buckets in (1,7):
            select_latest_keys(conn,buckets)
            assert set(conn.execute('SELECT * FROM latest_report_keys').fetchall())==expected
    resumed=prepare(tmp_path,resume_selection=True)
    assert resumed['latest_cases']==result['latest_cases'] and resumed['pairs']==result['pairs']
    with connect_analytics(tmp_path) as conn:
        conn.execute("UPDATE latest_reports SET serious=NOT serious WHERE case_id='case-0-0'")
    with pytest.raises(ValueError,match='checkpoint does not match'):
        prepare(tmp_path,resume_selection=True)
    with connect_analytics(tmp_path) as conn:
        conn.execute("UPDATE latest_reports SET serious=NOT serious WHERE case_id='case-0-0'")
    # All fixture files use the same archive folder, but dates span three years.
    # Receipt-date coverage must not inherit the source-folder quarter.
    assert len(result['source_partition_coverage'])==1
    assert len(result['receipt_quarter_coverage'])==12
    assert sum(r['raw_reports'] for r in result['receipt_year_coverage'])==110
    assert sum(r['selected_cases'] for r in result['receipt_quarter_coverage'])==108
    assert sum(r['co_report_incidences'] for r in result['receipt_year_coverage'])==108
    assert all(r['drug_reaction_pairs']==1 for r in result['receipt_year_coverage'])
    sparsity=diagnose_sparsity(tmp_path)
    assert sparsity['frequency_comparison'][0]['observed_rows']==3
    assert sparsity['frequency_comparison'][1]['observed_rows']==1
    assert sparsity['threshold_analysis'][0]['retained_pair_report_incidences']==9
    assert sparsity['threshold_analysis'][3]['retained_pairs']==0
    context=tmp_path/'context';context.mkdir()
    pq.write_table(pa.Table.from_pylist([{'kind':'labels','source_id':'test-label','ingredient_id':next(iter(IdentityIndex.load(tmp_path).mapping['ingredients'].values())),
        'source_date':'2020-01-01','available_at':'2026-09-26','classification':None,
        'boxed_warning_present':True,'warning_section_present':True}],schema=pa.schema([(k,pa.string()) for k in ['kind','source_id','ingredient_id','source_date','available_at','classification']]+[('boxed_warning_present',pa.bool_()),('warning_section_present',pa.bool_())])),context/'regulatory.parquet')
    export=tmp_path/'export'
    with pytest.raises(ValueError,match='Historical availability is unverified'):
        build_features(tmp_path,export)
    assert not export.exists()
    meta=build_features(tmp_path,export,exploratory=True)
    features=pq.read_table(export/'exploratory_features.parquet').to_pylist()
    assert not meta['training_ready']
    assert all(r['label_available'] is None for r in features)
    assert pq.read_table(export/'train.parquet').num_rows==0
    assert features[-1]['future_count_3'] is None
    assert features[2]['reports_previous_1_period']==3
    assert features[-1]['cumulative_reports_to_date']==108
    assert all(not r['historical_availability_verified'] for r in features)
    hashes={p.name:fingerprint(p.read_bytes().hex()) for p in export.glob('*.parquet')}
    build_features(tmp_path,export,exploratory=True)
    assert hashes=={p.name:fingerprint(p.read_bytes().hex()) for p in export.glob('*.parquet')}
