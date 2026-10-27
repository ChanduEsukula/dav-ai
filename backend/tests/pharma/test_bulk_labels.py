import io
import json
import zipfile
from copy import deepcopy

import httpx
import psycopg
import pytest
from app.services.pharma.bulk_labels import MANIFEST_URL, discover_labels, import_labels, stream_labels
from app.services.pharma.ndc_ingestion import normalize_ndc_record, SOURCE
from app.db.pharma.drug_repository import DrugRepository
from app.db.pharma.ingestion_run_repository import IngestionRunRepository

URL='https://download.open.fda.gov/drug/label/drug-label-0001-of-0001.json.zip'


def archive(records):
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('labels.json',json.dumps({'meta':{},'results':records}))
    return buffer.getvalue()


def manifest(n):
    return {'results':{'drug':{'label':{'export_date':'2026-09-25','total_records':n,
        'partitions':[{'file':URL,'records':n,'size_mb':'0.01'}]}}}}


def client(records, calls=None):
    def handler(request):
        if calls is not None: calls.append(str(request.url))
        return httpx.Response(200,json=manifest(len(records))) if str(request.url)==MANIFEST_URL else httpx.Response(200,content=archive(records))
    return httpx.Client(transport=httpx.MockTransport(handler))


def label(i, ndc='12345-6789'):
    return {'id':str(i),'set_id':'set-'+str(i),'effective_time':'20260101','version':'1',
            'boxed_warning':['Official test fixture warning'], 'openfda':{'product_ndc':[ndc],'brand_name':['Fixture label']}}


def seed(ndc_record):
    run=IngestionRunRepository().start(SOURCE,{})
    return DrugRepository().upsert(normalize_ndc_record(ndc_record,run))[0]


def test_discovery_uses_source_counts_and_rejects_foreign_urls():
    assert discover_labels(manifest(3))['total_records']==3
    data=manifest(3);data['results']['drug']['label']['partitions'][0]['file']='https://evil.example/labels.zip'
    with pytest.raises(ValueError):discover_labels(data)
    data=manifest(3);data['results']['drug']['label']['total_records']=4
    with pytest.raises(ValueError):discover_labels(data)


def test_streaming_parser(tmp_path):
    path=tmp_path/'labels.zip';path.write_bytes(archive([label(1),label(2)]))
    iterator=stream_labels(path)
    assert iter(iterator) is iterator
    assert next(iterator)['id']=='1'
    assert next(iterator)['id']=='2'
    with pytest.raises(StopIteration):next(iterator)


def test_bulk_resume_malformed_unresolved_and_provenance(pharma_db,ndc_record,tmp_path):
    drug=seed(ndc_record)
    records=[label(1),{'no_source_id':'bad'},label(2,'99999-1111'),{'id':'no-title'}]
    with client(records) as http:
        first=import_labels(cache_dir=tmp_path,http=http,batch_size=1,max_records=2)
        assert first['counts_this_invocation']['inserted']==1
        assert first['counts_this_invocation']['failed']==1
        assert not first['complete']
        second=import_labels(cache_dir=tmp_path,http=http,batch_size=1)
        assert second['complete'] and second['cumulative_counts']['fetched']==4
        assert second['cumulative_counts']['inserted']==3
        assert second['cumulative_counts']['unresolved']==2
        replay=import_labels(cache_dir=tmp_path,http=http)
        assert replay['counts_this_invocation']['fetched']==0
    with psycopg.connect(pharma_db) as conn:
        rows=conn.execute('SELECT source,source_record_id,raw_json,source_url,title FROM pharma.drug_labels ORDER BY source_record_id').fetchall()
        assert len(rows)==3 and rows[0][0]=='openfda_drug_label'
        assert rows[0][2]==records[0] and rows[0][3].startswith('https://api.fda.gov/drug/label.json?')
        assert rows[-1][-1] is None
        assert conn.execute('SELECT drug_id FROM pharma.drug_label_links').fetchall()==[(drug['id'],)]


def test_interrupt_commits_records_and_checkpoint_together(pharma_db,tmp_path):
    records=[label(i) for i in range(4)]
    def interrupt(position):raise KeyboardInterrupt()
    with client(records) as http:
        with pytest.raises(KeyboardInterrupt):import_labels(cache_dir=tmp_path,http=http,batch_size=2,after_batch=interrupt)
        result=import_labels(cache_dir=tmp_path,http=http,batch_size=2)
        assert result['counts_this_invocation']['inserted']==2
        assert result['cumulative_counts']['inserted']==4
        assert result['complete']
    with psycopg.connect(pharma_db) as conn:
        assert conn.execute('SELECT count(*) FROM pharma.drug_labels').fetchone()[0]==4


def test_new_export_upserts_without_duplicates(pharma_db,tmp_path):
    records=[label(1)]
    with client(records) as http: import_labels(cache_dir=tmp_path,http=http)
    changed=deepcopy(records);changed[0]['boxed_warning']=['Updated fixture warning']
    def handler(request):
        data=manifest(1);data['results']['drug']['label']['export_date']='2026-09-26'
        return httpx.Response(200,json=data) if str(request.url)==MANIFEST_URL else httpx.Response(200,content=archive(changed))
    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        result=import_labels(cache_dir=tmp_path,http=http)
    assert result['counts_this_invocation']['updated']==1 and result['counts_this_invocation']['inserted']==0
    with psycopg.connect(pharma_db) as conn:
        assert conn.execute('SELECT raw_json FROM pharma.drug_labels').fetchone()[0]==changed[0]


def test_corrupt_download_preserves_existing(pharma_db,tmp_path):
    with client([label(1)]) as http:import_labels(cache_dir=tmp_path,http=http)
    def handler(request):
        data=manifest(2)
        return httpx.Response(200,json=data) if str(request.url)==MANIFEST_URL else httpx.Response(200,content=b'not a zip')
    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        result=import_labels(cache_dir=tmp_path,http=http)
    assert result['status']=='failed' and result['errors']
    with psycopg.connect(pharma_db) as conn:
        assert conn.execute('SELECT count(*) FROM pharma.drug_labels').fetchone()[0]==1
