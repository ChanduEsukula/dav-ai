"""Snapshot-scoped, file-atomic official-source research ingestion.

No application DB access. SQLite is a small progress ledger; Parquet contains data.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path
import resource
import shutil
import sqlite3
import sys
import time
from urllib.parse import urlparse
import zipfile

import httpx
import pyarrow as pa
import pyarrow.parquet as pq
from app.services.pharma.bulk_labels import cache_file, fingerprint, stream_labels, file_digest

MANIFEST = 'https://api.fda.gov/download.json'
VERSION = 'research-v1'


def now():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path, value):
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,indent=2))
    temporary.replace(path)


def discover(manifest, kind):
    if kind not in ('ndc', 'event', 'enforcement'):
        raise ValueError('Unsupported research source')
    dataset = manifest['results']['drug'][kind]
    datetime.strptime(dataset['export_date'], '%Y-%m-%d')
    parts = dataset['partitions']
    if not isinstance(parts, list) or not parts:
        raise ValueError('Empty manifest')
    seen = set()
    for p in parts:
        u = urlparse(p['file'])
        if (u.scheme != 'https' or u.hostname != 'download.open.fda.gov' or u.username or u.password
            or u.port not in (None,443) or u.query or u.fragment or '..' in u.path
            or not u.path.startswith('/drug/'+kind+'/') or not u.path.endswith('.json.zip')
            or p['file'] in seen or type(p['records']) is not int or p['records'] < 0
            or float(p['size_mb']) < 0):
            raise ValueError('Invalid or duplicate official partition')
        seen.add(p['file'])
    if sum(p['records'] for p in parts) != dataset['total_records']:
        raise ValueError('Manifest counts disagree')
    return dataset


def text(x):
    return x.strip() if isinstance(x,str) and x.strip() else None


def texts(x):
    return sorted({v.strip() for v in x if isinstance(v,str) and v.strip()}) if isinstance(x,list) else []


def norm(x):
    return ' '.join(x.casefold().split()) if isinstance(x,str) else ''


def source_date(x):
    if not isinstance(x,str) or len(x)!=8 or not x.isdigit():
        return None
    try:
        return datetime.strptime(x,'%Y%m%d').date().isoformat()
    except ValueError:
        return None


def flag(x):
    return True if str(x)=='1' else False if str(x)=='2' else None


REPORT_FIELDS = ['report_uid','case_id','version_raw','source_hash','receivedate_raw','receiptdate_raw',
                 'first_received','last_received','transmissiondate_raw','transmission_date',
                 'companynumb','authoritynumb','duplicate','reportduplicate_json','country','reporter_qualification',
                 'source_url','export_date','observed_at','partition']
SCHEMAS = {
    'reports': pa.schema([(x,pa.string()) for x in REPORT_FIELDS]+[('version',pa.int64())]+
        [(x,pa.bool_()) for x in ['serious','death','hospitalization','disability','life_threatening','congenital','other_serious']]),
    'drugs': pa.schema([(x,pa.string()) for x in ['report_uid','medicinalproduct','role','drugstartdate_raw','drugenddate_raw',
        'indication','administration_route','dose_text']]+[('drug_index',pa.int32())]+
        [(x,pa.list_(pa.string())) for x in ['rxcui','product_ndc','package_ndc','substance_name','generic_name','brand_name']]),
    'reactions': pa.schema([(x,pa.string()) for x in ['report_uid','term','normalized_term','meddra_version','outcome']]+[('reaction_index',pa.int32())]),
    'ndc': pa.schema([(x,pa.string()) for x in ['source_id','source_url','export_date','observed_at','raw_json']]),
    'enforcement': pa.schema([(x,pa.string()) for x in ['source_id','source_url','export_date','observed_at','raw_json']]),
}


def extract(raw, kind, meta):
    if not isinstance(raw,dict):
        raise ValueError('Record is not an object')
    if kind != 'event':
        source_id=text(raw.get('product_id' if kind=='ndc' else 'recall_number'))
        if not source_id:
            raise ValueError('Missing source identity')
        return {kind:[{'source_id':source_id,'source_url':meta['source_url'],'export_date':meta['export_date'],
                      'observed_at':meta['observed_at'],'raw_json':json.dumps(raw,ensure_ascii=False,sort_keys=True)}]}
    case_id=text(raw.get('safetyreportid'))
    version=text(raw.get('safetyreportversion'))
    if not case_id:
        raise ValueError('Missing case identifier')
    content_hash=fingerprint(raw)
    uid=fingerprint([case_id,version,content_hash])
    report={x:None for x in REPORT_FIELDS}
    report.update(meta,report_uid=uid,case_id=case_id,version_raw=version,source_hash=content_hash,
        version=int(version) if version and version.isdigit() and len(version)<10 else None)
    for field in ['receivedate','receiptdate','transmissiondate']:
        report[field+'_raw']=text(raw.get(field))
    report.update(first_received=source_date(raw.get('receivedate')),last_received=source_date(raw.get('receiptdate')),
                  transmission_date=source_date(raw.get('transmissiondate')))
    for field in ['companynumb','authoritynumb','duplicate']:
        report[field]=text(raw.get(field))
    report['reportduplicate_json']=json.dumps(raw.get('reportduplicate'),sort_keys=True)
    primary=raw.get('primarysource') or {}
    if not isinstance(primary,dict):
        raise ValueError('Malformed primary source')
    report['country']=text(primary.get('reportercountry')) or text(raw.get('occurcountry'))
    report['reporter_qualification']=text(primary.get('qualification'))
    for target,source in {'serious':'serious','death':'seriousnessdeath','hospitalization':'seriousnesshospitalization',
        'disability':'seriousnessdisabling','life_threatening':'seriousnesslifethreatening',
        'congenital':'seriousnesscongenitalanomali','other_serious':'seriousnessother'}.items():
        report[target]=flag(raw.get(source))
    patient=raw.get('patient') or {}
    if not isinstance(patient,dict):
        raise ValueError('Malformed patient container')
    drugs=patient.get('drug') or []
    reactions=patient.get('reaction') or []
    if not isinstance(drugs,list) or not isinstance(reactions,list):
        raise ValueError('Malformed drug/reaction arrays')
    ds=[];rs=[]
    for n,d in enumerate(drugs):
        if not isinstance(d,dict) or not isinstance(d.get('openfda') or {},dict):
            raise ValueError('Malformed drug mention')
        o=d.get('openfda') or {}
        ds.append(dict(report_uid=uid,drug_index=n,medicinalproduct=text(d.get('medicinalproduct')),
            role=text(d.get('drugcharacterization')),drugstartdate_raw=text(d.get('drugstartdate')),
            drugenddate_raw=text(d.get('drugenddate')),indication=text(d.get('drugindication')),
            administration_route=text(d.get('drugadministrationroute')),dose_text=text(d.get('drugdosagetext')),
            **{k:texts(o.get(k)) for k in ['rxcui','product_ndc','package_ndc','substance_name','generic_name','brand_name']}))
    for n,r in enumerate(reactions):
        if not isinstance(r,dict):
            raise ValueError('Malformed reaction')
        rs.append(dict(report_uid=uid,reaction_index=n,term=text(r.get('reactionmeddrapt')),
            normalized_term=norm(r.get('reactionmeddrapt')) or None,
            meddra_version=text(r.get('reactionmeddraversionpt')),outcome=text(r.get('reactionoutcome'))))
    return {'reports':[report],'drugs':ds,'reactions':rs}


@contextmanager
def locked(root):
    root.mkdir(parents=True,exist_ok=True)
    with (root/'pipeline.lock').open('w') as f:
        fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        yield


def ingest(root, kind, *, max_files=None, quarter=None, discard_archives=False, min_free_gb=30,
           http=None, manifest=None, after_file=None, max_seconds=None, expected_dataset_key=None,
           before_files=None):
    root=Path(root)
    with locked(root):
        if before_files:
            before_files()
        if http is None:
            with httpx.Client(timeout=httpx.Timeout(180,connect=20),headers={'Accept-Encoding':'identity'}) as client:
                return _ingest(root,kind,max_files,quarter,discard_archives,min_free_gb,client,manifest,after_file,max_seconds,expected_dataset_key)
        return _ingest(root,kind,max_files,quarter,discard_archives,min_free_gb,http,manifest,after_file,max_seconds,expected_dataset_key)


def _ingest(root,kind,max_files,quarter,discard_archives,min_free_gb,http,manifest,after_file,max_seconds,expected_dataset_key=None):
    started=time.monotonic()
    supplied_manifest=manifest is not None
    if manifest is None:
        response=http.get(MANIFEST);response.raise_for_status();manifest=response.json()
    ds=discover(manifest,kind)
    key=fingerprint({'dataset':ds,'transform':VERSION})
    if expected_dataset_key is not None and key != expected_dataset_key:
        raise ValueError('Official manifest changed: refusing to restart or mix the pinned snapshot')
    snapshot=root/kind/key;snapshot.mkdir(parents=True,exist_ok=True)
    manifest_file=snapshot/'manifest.json'
    if not manifest_file.exists():
        manifest_file.write_text(json.dumps(manifest,indent=2))
        (snapshot/'snapshot.json').write_text(json.dumps({'observed_at':now(),'transform':VERSION,'dataset_key':key}))
    observed=json.loads((snapshot/'snapshot.json').read_text())['observed_at']
    ledger=sqlite3.connect(root/'checkpoints.sqlite')
    ledger.execute('CREATE TABLE IF NOT EXISTS files (dataset_key TEXT,url TEXT,status TEXT,receipt TEXT,error TEXT,PRIMARY KEY(dataset_key,url))')
    files=[];failed=[];processed=0;skipped=0;stop=None
    parts=sorted(ds['partitions'],key=lambda p:p['file'])
    durable={r['url']:r for p in snapshot.glob('files/quarter=*/*/receipt.json')
             if not p.parent.name.endswith('.partial') for r in [json.loads(p.read_text())]}
    def save_progress(last=None, error=None):
        missing=[p['file'] for p in parts if p['file'] not in durable]
        atomic_json(snapshot/'progress.json',{
            'updated_at':now(),'dataset_key':key,'files_complete':len(durable),
            'files_remaining':len(ds['partitions'])-len(durable),
            'raw_records':sum(r['records'] for r in durable.values()),
            'last_completed':last,'next_partition':missing[0] if missing else None,
            'error':error,'stop_reason':stop})
    if quarter:
        parts=[p for p in parts if '/'+quarter+'/' in p['file']]
        if not parts:raise ValueError('No files for requested quarter')
    for part in parts:
        file_key=fingerprint(part['file'])[:24]
        partition=urlparse(part['file']).path.split('/')[-2]
        final=snapshot/'files'/('quarter='+partition)/file_key
        receipt_path=final/'receipt.json'
        if receipt_path.exists():
            receipt=json.loads(receipt_path.read_text())
            if receipt['url']!=part['file'] or receipt['records']!=part['records']:
                raise ValueError('Completed receipt does not match source manifest')
            for name,digest in receipt['outputs'].items():
                if file_digest(final/name)!=digest:
                    raise ValueError('Completed research output checksum mismatch')
            skipped+=1;continue
        if max_files is not None and processed>=max_files:
            stop='max_files';break
        if max_seconds is not None and time.monotonic()-started>=max_seconds:
            stop='time_budget';break
        required=min_free_gb*1024**3+float(part['size_mb'])*1024**2*8
        if shutil.disk_usage(root).free<required:
            stop='disk_reserve';break
        stage=final.with_name(final.name+'.partial')
        shutil.rmtree(stage,ignore_errors=True);stage.mkdir(parents=True)
        cache=snapshot/'cache'/file_key
        writers={};counts={};errors=0;n=0;file_started=time.monotonic()
        ledger.execute('INSERT OR REPLACE INTO files VALUES (?,?,?,?,?)',(key,part['file'],'running',None,None));ledger.commit()
        try:
            path,download=cache_file(http,part,cache)
            with zipfile.ZipFile(path) as z:
                expanded=sum(i.file_size for i in z.infolist())
            tables=['reports','drugs','reactions'] if kind=='event' else [kind]
            buffers={t:[] for t in tables}
            for t in tables:
                writers[t]=pq.ParquetWriter(stage/(t+'.parquet'),SCHEMAS[t],compression='zstd')
                counts[t]=0
            def flush():
                for t,buffer in buffers.items():
                    if buffer:
                        writers[t].write_table(pa.Table.from_pylist(buffer,schema=SCHEMAS[t]))
                        counts[t]+=len(buffer);buffer.clear()
            with (stage/'quarantine.jsonl').open('w') as quarantine:
                for n,raw in enumerate(stream_labels(path),1):
                    try:
                        rows=extract(raw,kind,{'source_url':part['file'],'export_date':ds['export_date'],
                            'observed_at':observed,'partition':partition})
                        for t,values in rows.items():buffers[t].extend(values)
                    except (ValueError,TypeError,KeyError,AttributeError) as exc:
                        errors+=1
                        quarantine.write(json.dumps({'ordinal':n,'error':str(exc),'raw':raw},ensure_ascii=False)+'\n')
                    if n%100==0:flush()
                flush()
            if n!=part['records']:raise ValueError(f'Manifest count mismatch {n} != {part["records"]}')
            for writer in writers.values():writer.close()
            writers={}
            for table in tables:
                if pq.ParquetFile(stage/(table+'.parquet')).metadata.num_rows!=counts[table]:
                    raise ValueError('Durable Parquet row count mismatch')
            receipt={'url':part['file'],'records':n,'valid_records':n-errors,'quarantined':errors,
                'download':download,'expanded_bytes':expanded,'counts':counts,'seconds':time.monotonic()-file_started,
                'outputs':{p.name:file_digest(p) for p in stage.iterdir() if p.is_file()},'completed_at':now()}
            receipt['parquet_bytes']=sum(p.stat().st_size for p in stage.glob('*.parquet'))
            (stage/'receipt.json').write_text(json.dumps(receipt,indent=2))
            final.parent.mkdir(parents=True,exist_ok=True);stage.replace(final)
            ledger.execute('INSERT OR REPLACE INTO files VALUES (?,?,?,?,?)',(key,part['file'],'complete',json.dumps(receipt),None));ledger.commit()
            durable[part['file']]=receipt
            save_progress(last=part['file'])
            if discard_archives:path.unlink()
            files.append(receipt);processed+=1
            print(json.dumps({'kind':kind,'file':part['file'],'records':n,'quarantined':errors,
                              'seconds':round(receipt['seconds'],2)}),flush=True)
            if after_file:after_file(processed)
        except Exception as exc:
            for writer in writers.values():writer.close()
            failure={'url':part['file'],'error':type(exc).__name__,'detail':str(exc)[:250]}
            ledger.execute('INSERT OR REPLACE INTO files VALUES (?,?,?,?,?)',(key,part['file'],'failed',None,json.dumps(failure)));ledger.commit()
            failed.append(failure)
            print(json.dumps(failure),flush=True)
            stop='partition_failure'
            save_progress(error=failure)
            break
    # A changed versionless upstream cannot be silently certified as one snapshot.
    if not supplied_manifest:
        try:
            response=http.get(MANIFEST);response.raise_for_status()
            if fingerprint(discover(response.json(),kind))!=fingerprint(ds):
                failed.append({'error':'ManifestChangedDuringRun'})
                stop='manifest_verification_failed'
        except (httpx.HTTPError,ValueError) as exc:
            # Preserve the durable batch summary even when a network failure
            # prevents the final upstream check. This run cannot be certified.
            failed.append({'url':MANIFEST,'error':'ManifestVerificationFailed',
                           'detail':type(exc).__name__+': '+str(exc)[:250]})
            if stop!='partition_failure':stop='manifest_verification_failed'
    receipts=[json.loads(p.read_text()) for p in snapshot.glob('files/quarter=*/*/receipt.json') if not p.parent.name.endswith('.partial')]
    result={'dataset_key':key,'kind':kind,'export_date':ds['export_date'],'source_records':ds['total_records'],
        'files_available':len(ds['partitions']),'files_complete':len(receipts),'files_processed_this_run':processed,
        'files_skipped_this_run':skipped,'raw_records':sum(r['records'] for r in receipts),
        'quarantined':sum(r['quarantined'] for r in receipts),'failures':failed,'stop_reason':stop,
        'complete':len(receipts)==len(ds['partitions']) and not failed,
        'parquet_bytes':sum(r['parquet_bytes'] for r in receipts),'download_bytes':sum(r['download']['bytes'] for r in receipts),
        'expanded_bytes':sum(r['expanded_bytes'] for r in receipts),'seconds_this_run':round(time.monotonic()-started,2),
        'file_seconds_total':sum(r['seconds'] for r in receipts),'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),
        'snapshot_path':str(snapshot),'observed_at':observed}
    atomic_json(snapshot/'summary.json',result)
    atomic_json(root/(kind+'-latest.json'),{'snapshot_path':str(snapshot),'dataset_key':key})
    save_progress(last=max(durable.values(),key=lambda r:r['completed_at'])['url'] if durable else None,
                  error=failed or None)
    ledger.close()
    return result
