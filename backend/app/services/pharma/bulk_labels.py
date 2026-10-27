"""Official label bulk import: bounded memory, verified ZIP cache, atomic checkpoints."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from urllib.parse import urlparse
import zipfile

import httpx
import ijson
import psycopg
from psycopg.types.json import Jsonb

from app.db.pharma.connection import connect
from app.db.pharma.ingestion_run_repository import IngestionRunRepository
from app.db.pharma.safety_repository import SafetyRepository
from app.services.pharma.safety_matching import CatalogIndex, match_mentions
from app.services.pharma.safety_records import normalize_record, SOURCES

MANIFEST_URL = 'https://api.fda.gov/download.json'
SOURCE = SOURCES['labels'][0]
COUNTERS = ('fetched', 'inserted', 'updated', 'unchanged', 'failed', 'unresolved', 'linked', 'links')
MAX_DOWNLOAD_BYTES = 3 * 1024**3


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def discover_labels(manifest):
    dataset = manifest['results']['drug']['label']
    files = dataset['partitions']
    if not files or not isinstance(dataset['total_records'], int) or not dataset['export_date']:
        raise ValueError('Invalid official label manifest')
    seen = set()
    for part in files:
        url = urlparse(part['file'])
        if (url.scheme != 'https' or url.hostname != 'download.open.fda.gov' or
            url.username or url.password or url.port not in (None, 443) or url.query or url.fragment or
            not url.path.startswith('/drug/label/') or not url.path.endswith('.json.zip') or
            '..' in url.path or part['file'] in seen or not isinstance(part['records'], int) or part['records'] < 0):
            raise ValueError('Invalid official label partition')
        seen.add(part['file'])
    if sum(p['records'] for p in files) != dataset['total_records']:
        raise ValueError('Manifest partition totals disagree')
    return dataset


def file_digest(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def verify_zip(path):
    with zipfile.ZipFile(path) as archive:
        members = archive.infolist()
        if len(members) != 1 or not members[0].filename.endswith('.json') or members[0].file_size > 50 * 1024**3:
            raise ValueError('Unexpected label ZIP contents or expanded size')
        if archive.testzip() is not None:
            raise ValueError('Label ZIP CRC validation failed')


def cache_file(http, part, directory):
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / Path(urlparse(part['file']).path).name
    receipt_path = target.with_suffix('.receipt.json')
    if target.exists() and receipt_path.exists():
        receipt = json.loads(receipt_path.read_text())
        if receipt.get('url') == part['file'] and file_digest(target) == receipt.get('sha256'):
            return target, receipt
    partial = target.with_suffix('.partial')
    size = 0
    digest = hashlib.sha256()
    try:
        with http.stream('GET', part['file'], follow_redirects=False) as response:
            response.raise_for_status()
            if response.is_redirect:
                raise ValueError('Unexpected bulk file redirect')
            expected = response.headers.get('content-length')
            with partial.open('wb') as out:
                for block in response.iter_bytes(1024 * 1024):
                    size += len(block)
                    if size > MAX_DOWNLOAD_BYTES:
                        raise ValueError('Bulk partition exceeds configured byte limit')
                    digest.update(block)
                    out.write(block)
            if expected and size != int(expected):
                raise ValueError('Incomplete bulk download')
            sha = digest.hexdigest()
            if part.get('sha256') and part['sha256'].lower() != sha:
                raise ValueError('Official SHA256 mismatch')
            verify_zip(partial)
            receipt = {'url': part['file'], 'bytes': size, 'sha256': sha,
                       'etag': response.headers.get('etag'), 'last_modified': response.headers.get('last-modified'),
                       'downloaded_at': datetime.now(timezone.utc).isoformat(),
                       'verification': 'HTTP content length when supplied; ZIP CRC; local SHA256; source SHA256 when supplied'}
        partial.replace(target)
        receipt_path.write_text(json.dumps(receipt, indent=2))
        return target, receipt
    finally:
        partial.unlink(missing_ok=True)


def stream_labels(path):
    with zipfile.ZipFile(path) as archive:
        if len(archive.infolist()) != 1:
            raise ValueError('Expected one JSON member')
        with archive.open(archive.infolist()[0]) as stream:
            yield from ijson.items(stream, 'results.item', use_float=True)


def save_progress(conn, key, url, processed, counts, status, error=None):
    conn.execute('''UPDATE pharma.bulk_label_files SET processed=%s, counts=%s, status=%s,
        error=%s, updated_at=now() WHERE dataset_key=%s AND file_url=%s''',
        (processed, Jsonb(counts), status, error, key, url))


def import_labels(*, cache_dir, batch_size=100, max_records=None, max_files=None, http=None,
                  after_batch=None):
    """Bounds pause rather than discard progress. Resume with identical manifest/catalog.

    after_batch is a test-only interruption hook after commit; never supplies evidence.
    """
    if not 1 <= batch_size <= 1000 or (max_records is not None and max_records < 1) or (max_files is not None and max_files < 1):
        raise ValueError('Invalid resource bound')
    if http is None:
        with httpx.Client(timeout=httpx.Timeout(120, connect=20), headers={'Accept-Encoding': 'identity'}) as client:
            return import_labels(cache_dir=cache_dir, batch_size=batch_size, max_records=max_records,
                                 max_files=max_files, http=client, after_batch=after_batch)
    started = time.monotonic()
    response = http.get(MANIFEST_URL)
    response.raise_for_status()
    manifest = response.json()
    dataset = discover_labels(manifest)
    repo = SafetyRepository()
    drugs = repo.catalog()
    index = CatalogIndex(drugs)
    # A catalog change requires relinking even when the export is unchanged.
    catalog_key = fingerprint([{k: d[k] for k in ('id','rxcui','product_ndcs','package_ndcs','normalized_names')} for d in drugs])
    key = fingerprint({'dataset': dataset, 'catalog': catalog_key})
    cache = Path(cache_dir) / fingerprint(dataset)
    cache.mkdir(parents=True, exist_ok=True)
    (cache / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    runs = IngestionRunRepository()
    run_id = runs.start(SOURCE, {'mode': 'bulk', 'dataset_key': key, 'export_date': dataset['export_date'],
        'manifest_url': MANIFEST_URL, 'drug_ids': [str(d['id']) for d in drugs],
        'source_total_records': dataset['total_records'], 'source_files': len(dataset['partitions'])})
    invocation = dict.fromkeys(COUNTERS, 0)
    errors = []
    files_visited = 0
    with connect() as conn:
        # Prevent simultaneous workers from racing checkpoints for this export/catalog.
        locked = conn.execute('SELECT pg_try_advisory_lock(hashtextextended(%s, 0)) AS locked', (key,)).fetchone()['locked']
        conn.commit()
        if not locked:
            runs.finish(run_id, status='failed', counts=invocation, coverage={}, error_summary='Bulk import already running')
            raise ValueError('Bulk import already running for this dataset/catalog')
        before_size = conn.execute('SELECT pg_database_size(current_database()) AS bytes').fetchone()['bytes']
        conn.commit()
        try:
            for part in dataset['partitions']:
                if (max_files is not None and files_visited >= max_files) or (max_records is not None and invocation['fetched'] >= max_records):
                    break
                url = part['file']
                with conn.transaction():
                    conn.execute('''INSERT INTO pharma.bulk_label_files(dataset_key,file_url,source_export_date,expected_records,ingestion_run_id)
                        VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING''', (key,url,dataset['export_date'],part['records'],run_id))
                    progress = conn.execute('SELECT * FROM pharma.bulk_label_files WHERE dataset_key=%s AND file_url=%s', (key,url)).fetchone()
                if progress['status'] in ('succeeded','partial') and progress['processed'] == part['records']:
                    continue
                files_visited += 1
                position = progress['processed']
                counts = {k: progress['counts'].get(k,0) for k in COUNTERS}
                try:
                    path, receipt = cache_file(http, part, cache)
                    with conn.transaction():
                        if progress['sha256'] and progress['sha256'] != receipt['sha256']:
                            raise ValueError('Partition changed within export; refresh manifest and use a new cache')
                        conn.execute('UPDATE pharma.bulk_label_files SET sha256=%s,status=\'running\' WHERE dataset_key=%s AND file_url=%s', (receipt['sha256'],key,url))
                    batch = []
                    def commit_batch():
                        nonlocal position
                        delta = dict.fromkeys(COUNTERS,0)
                        with conn.transaction():
                            for raw in batch:
                                delta['fetched'] += 1
                                try:
                                    normalized = normalize_record('labels', raw, run_id)
                                    links = match_mentions(index, 'labels', raw)
                                    # A bad record cannot poison the batch transaction.
                                    with conn.transaction():
                                        action = repo.upsert('labels', normalized, links, connection=conn)
                                    delta[action] += 1
                                    delta['unresolved' if not links else 'linked'] += 1
                                    delta['links'] += len(links)
                                except (ValueError, TypeError, KeyError, AttributeError, psycopg.DataError, psycopg.IntegrityError):
                                    delta['failed'] += 1
                            next_counts = {k: counts[k]+delta[k] for k in COUNTERS}
                            save_progress(conn,key,url,position+len(batch),next_counts,'running')
                        position += len(batch)
                        counts.update(next_counts)
                        for k in COUNTERS: invocation[k] += delta[k]
                        batch.clear()
                        if after_batch: after_batch(position)
                    seen = 0
                    paused = False
                    for seen, raw in enumerate(stream_labels(path), 1):
                        if seen <= position: continue
                        if max_records is not None and invocation['fetched']+len(batch) >= max_records:
                            paused = True
                            break
                        batch.append(raw)
                        if len(batch) >= batch_size: commit_batch()
                    if batch: commit_batch()
                    if not paused and seen != part['records']:
                        raise ValueError(f'Partition count mismatch: expected {part["records"]}, parsed {seen}')
                    with conn.transaction():
                        save_progress(conn,key,url,position,counts,
                            'running' if paused else 'partial' if counts['failed'] else 'succeeded')
                except Exception as exc:
                    errors.append({'file':url,'error':type(exc).__name__, 'detail':str(exc)[:200] if isinstance(exc,ValueError) else None})
                    with conn.transaction(): save_progress(conn,key,url,position,counts,'failed',type(exc).__name__)
            rows = conn.execute('SELECT * FROM pharma.bulk_label_files WHERE dataset_key=%s', (key,)).fetchall()
            conn.commit()
            totals = {k:sum(r['counts'].get(k,0) for r in rows) for k in COUNTERS}
            complete = len(rows)==len(dataset['partitions']) and all(r['status'] in ('succeeded','partial') and r['processed']==r['expected_records'] for r in rows)
            # Confirm the export did not change while we were reading versionless URLs.
            final = http.get(MANIFEST_URL); final.raise_for_status()
            if fingerprint(discover_labels(final.json())) != fingerprint(dataset):
                errors.append({'error':'ManifestChangedDuringImport'})
                complete = False
            status = 'succeeded' if complete and not totals['failed'] and not errors else 'partial' if totals['fetched'] else 'failed'
            coverage = {'bulk': {'drug_ids':[str(d['id']) for d in drugs], 'status':status,
                'available':dataset['total_records'],'fetched':totals['fetched'], 'truncated':not complete,
                'source_dataset_updated_at':dataset['export_date'], 'files_complete':sum(r['status'] in ('succeeded','partial') for r in rows),
                'files_discovered':len(dataset['partitions']), 'totals':totals, 'errors':errors}}
            runs.finish(run_id,status=status,counts=invocation,coverage=coverage,error_summary='; '.join(e['error'] for e in errors) or None)
            after_size = conn.execute('SELECT pg_database_size(current_database()) AS bytes').fetchone()['bytes']
            return {'run_id':str(run_id),'dataset_key':key,'status':status,'source':SOURCE,
                'export_date':dataset['export_date'],'source_total_records':dataset['total_records'],
                'files_discovered':len(dataset['partitions']), 'counts_this_invocation':invocation,
                'cumulative_counts':totals,'complete':complete,'errors':errors,
                'elapsed_seconds':round(time.monotonic()-started,2),
                'database_bytes_before':before_size,'database_bytes_after':after_size,
                'database_bytes_growth':after_size-before_size}
        except BaseException as exc:
            conn.rollback()
            runs.finish(run_id,status='failed',counts=invocation,coverage={},error_summary=type(exc).__name__)
            raise
        finally:
            conn.execute('SELECT pg_advisory_unlock(hashtextextended(%s, 0))', (key,))
            conn.commit()
