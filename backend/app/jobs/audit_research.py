"""Verify durable research receipts without downloading or reprocessing records."""
import argparse
import gzip
import json
from pathlib import Path
import shutil
import sqlite3

import pyarrow.parquet as pq

from app.research.bulk import discover, file_digest, fingerprint, now, VERSION


def require(condition, artifact):
    if not condition:
        raise ValueError('Research integrity verification failed: '+str(artifact))


def audit(root):
    root = Path(root)
    result = {'checked_at': now(), 'free_bytes': shutil.disk_usage(root).free, 'datasets': {}}
    for kind in ('ndc', 'enforcement', 'event'):
        pointer = json.loads((root / (kind + '-latest.json')).read_text())
        source = Path(pointer['snapshot_path'])
        manifest = discover(json.loads((source / 'manifest.json').read_text()), kind)
        require(fingerprint({'dataset':manifest,'transform':VERSION})==pointer['dataset_key'],source/'manifest.json')
        receipts = []
        retained_archives=[]
        upstream_checksum_files=0
        unexpected_artifacts=[]
        orphan_partitions=[]
        for directory in source.glob('files/quarter=*/*'):
            if directory.is_dir() and not directory.name.endswith('.partial') and not (directory/'receipt.json').exists():
                orphan_partitions.append(str(directory))
        parts = {p['file']: p for p in manifest['partitions']}
        for path in sorted(source.glob('files/quarter=*/*/receipt.json')):
            if path.parent.name.endswith('.partial'):
                continue
            receipt = json.loads(path.read_text())
            unexpected_artifacts.extend(str(p) for p in path.parent.iterdir()
                                        if p.name not in set(receipt['outputs'])|{'receipt.json'})
            require(receipt['url'] in parts,path)
            require(receipt['records'] == parts[receipt['url']]['records'],path)
            require(receipt['valid_records']+receipt['quarantined']==receipt['records'],path)
            require(receipt['download']['url']==receipt['url'],path)
            expected_sha=parts[receipt['url']].get('sha256')
            if expected_sha:
                require(receipt['download']['sha256']==expected_sha.lower(),path)
                upstream_checksum_files+=1
            archive=source/'cache'/fingerprint(receipt['url'])[:24]/Path(receipt['url']).name
            if archive.exists():
                require(file_digest(archive)==receipt['download']['sha256'],archive)
                require(archive.stat().st_size==receipt['download']['bytes'],archive)
                retained_archives.append(str(archive))
            for name, digest in receipt['outputs'].items():
                artifact = path.parent / name
                require(file_digest(artifact) == digest,artifact)
                if name.endswith('.parquet'):
                    require(pq.ParquetFile(artifact).metadata.num_rows == receipt['counts'][name[:-8]],artifact)
            receipts.append(receipt)
        urls = {r['url'] for r in receipts}
        require(len(urls) == len(receipts),source)
        remaining = [parts[url] for url in sorted(parts) if url not in urls]
        result['datasets'][kind] = {
            'snapshot': str(source), 'export_date': manifest['export_date'],
            'manifest_sha256':file_digest(source/'manifest.json'),
            'verified_retained_archives':retained_archives,
            'upstream_sha256_files':upstream_checksum_files,
            'discarded_archive_count':len(receipts)-len(retained_archives),
            'source_archive_verification':'Retained ZIPs rehashed; discarded ZIPs rely on recorded download/CRC/hash receipts, not a fresh source-byte audit.',
            'raw_partition_count':len(receipts),
            'orphan_partitions':orphan_partitions,
            'unexpected_partition_artifacts':unexpected_artifacts,
            'manifest_records': manifest['total_records'], 'manifest_files': len(parts),
            'completed_files': len(receipts), 'remaining_files': len(remaining),
            'raw_records': sum(r['records'] for r in receipts),
            'quarantined_records': sum(r['quarantined'] for r in receipts),
            'parquet_bytes': sum(r['parquet_bytes'] for r in receipts),
            'historical_download_bytes': sum(r['download']['bytes'] for r in receipts),
            'historical_expanded_bytes': sum(r['expanded_bytes'] for r in receipts),
            'processing_seconds': sum(r['seconds'] for r in receipts),
            'last_completed': max(receipts, key=lambda r: r['completed_at'])['url'] if receipts else None,
            'next_partition': remaining[0] if remaining else None,
            'remaining_listed_compressed_mb': sum(float(p['size_mb']) for p in remaining),
            'table_rows': {t: sum(r['counts'].get(t, 0) for r in receipts)
                           for t in sorted({t for r in receipts for t in r['counts']})},
        }
    with gzip.open(root / 'identity/mapping.json.gz', 'rt') as stream:
        mapping = json.load(stream)
    identity = json.loads((root / 'identity/summary.json').read_text())
    require(fingerprint(mapping) == identity['mapping_hash'],root/'identity/mapping.json.gz')
    for table, key in [('ingredients', 'canonical_ingredients'), ('formulations', 'formulations'),
                       ('products', 'raw_product_records')]:
        require(pq.ParquetFile(root / 'identity' / (table + '.parquet')).metadata.num_rows == identity[key],table)
    ingredients=pq.read_table(root/'identity/ingredients.parquet').to_pylist()
    require({r['canonical_name']:r['ingredient_id'] for r in ingredients}==mapping['ingredients'],'ingredients')
    for batch in pq.ParquetFile(root/'identity/formulations.parquet').iter_batches(batch_size=1000):
        for row in batch.to_pylist():
            require(row['formulation_id']=='formulation:'+fingerprint([
                json.loads(row['strengths_json']),row['dosage_form'],row['routes']])[:24],row['formulation_id'])
    result['identity'] = identity
    result['identity']['alias_counts'] = {k: len(v) for k, v in mapping['aliases'].items()}
    result['identity']['unambiguous_aliases'] = sum(len(groups)==1 for v in mapping['aliases'].values() for groups in v.values())
    event_source=Path(result['datasets']['event']['snapshot'])
    normalized=root/'normalized'/identity['mapping_hash']/event_source.name
    normalized_files=normalized_rows=0
    missing=[]
    for receipt_path in sorted(event_source.glob('files/quarter=*/*/receipt.json')):
        if receipt_path.parent.name.endswith('.partial'):
            continue
        source_drugs=receipt_path.parent/'drugs.parquet'
        output=normalized/(receipt_path.parent.name+'.parquet')
        receipt=output.with_suffix('.json')
        if not output.exists() or not receipt.exists():
            missing.append(receipt_path.parent.name)
            continue
        saved=json.loads(receipt.read_text())
        require(saved['input_hash']==file_digest(source_drugs),source_drugs)
        require(saved['output_hash']==file_digest(output),output)
        count=pq.ParquetFile(output).metadata.num_rows
        require(count==pq.ParquetFile(source_drugs).metadata.num_rows,output)
        normalized_files+=1
        normalized_rows+=count
    result['normalization']={'verified_files':normalized_files,'verified_mentions':normalized_rows,
                             'missing_partition_ids':missing,'mapping_hash':identity['mapping_hash']}
    expected_ids={p.parent.name for p in event_source.glob('files/quarter=*/*/receipt.json')
                  if not p.parent.name.endswith('.partial')}
    normalized_ids={p.stem for p in normalized.glob('*.parquet')}
    receipt_ids={p.stem for p in normalized.glob('*.json')}
    result['normalization'].update(partition_count=len(normalized_ids),receipt_count=len(receipt_ids),
        unexpected_partition_ids=sorted((normalized_ids|receipt_ids)-expected_ids),
        outputs_without_receipts=sorted(normalized_ids-receipt_ids),
        receipts_without_outputs=sorted(receipt_ids-normalized_ids),
        unexpected_artifacts=[str(p) for p in normalized.iterdir() if p.suffix not in ('.parquet','.json','.partial')])
    result['source_staging']=[str(p) for p in event_source.glob('files/quarter=*/*.partial')]
    result['normalization_staging']=[str(p) for p in normalized.glob('*.partial')]
    result['download_staging']=[str(p) for p in (event_source/'cache').rglob('*.partial')]
    result['ingestion_state']={name:json.loads((event_source/name).read_text()) if (event_source/name).exists() else None
                               for name in ('progress.json','summary.json')}
    with sqlite3.connect(f'file:{root / "checkpoints.sqlite"}?mode=ro',uri=True) as ledger:
        entries=ledger.execute('SELECT url,status,error FROM files WHERE dataset_key=?',(event_source.name,)).fetchall()
    committed={json.loads(p.read_text())['url'] for p in event_source.glob('files/quarter=*/*/receipt.json')
               if not p.parent.name.endswith('.partial')}
    result['ledger']={
        'status_counts':{state:sum(e[1]==state for e in entries) for state in sorted({e[1] for e in entries})},
        'noncomplete_entries':[{'url':u,'status':s,'error':e} for u,s,e in entries if s!='complete'],
        'committed_without_complete_ledger':sorted(committed-{u for u,s,e in entries if s=='complete'}),
        'complete_ledger_without_receipt':sorted({u for u,s,e in entries if s=='complete'}-committed)}
    context=root/'context/regulatory.parquet'
    if context.exists():
        ids={'labels':set(),'recalls':set()}
        row_counts={'labels':0,'recalls':0}
        for batch in pq.ParquetFile(context).iter_batches(batch_size=1000):
            for row in batch.to_pylist():
                ids[row['kind']].add(row['source_id']);row_counts[row['kind']]+=1
        result['context']={'resolved_source_ids':{k:len(v) for k,v in ids.items()},'ingredient_links':row_counts,
                           'sha256':file_digest(context)}
    result['storage_bytes'] = sum(p.stat().st_size for p in root.rglob('*') if p.is_file())
    result['cache_bytes'] = sum(p.stat().st_size for p in root.glob('*/*/cache/**/*') if p.is_file())
    # Archives may already have been discarded after verified durable conversion.
    result['retained_zip_bytes'] = sum(p.stat().st_size for p in root.rglob('*.zip'))
    return result


def require_complete(result):
    event=result['datasets']['event']
    require(event['completed_files']==event['manifest_files'],'incomplete event corpus')
    require(event['raw_records']==event['manifest_records'],'event record total')
    require(not event['orphan_partitions'] and not event['unexpected_partition_artifacts'],'unexpected raw artifacts')
    require(result['normalization']['verified_files']==event['manifest_files'],'incomplete normalization')
    for key in ('unexpected_partition_ids','outputs_without_receipts','receipts_without_outputs','unexpected_artifacts'):
        require(not result['normalization'][key],key)
    require(not result['source_staging'] and not result['normalization_staging']
            and not result['download_staging'],'unfinished staging')
    for key in ('noncomplete_entries','committed_without_complete_ledger','complete_ledger_without_receipt'):
        require(not result['ledger'][key],key)
    summary=result['ingestion_state']['summary.json']
    progress=result['ingestion_state']['progress.json']
    require(summary is not None and summary['complete'] and not summary['failures'],'ingestion summary incomplete or failed')
    require(progress is not None and not progress['error'] and progress['next_partition'] is None,'ingestion progress state')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('data/research'))
    parser.add_argument('--output', type=Path)
    parser.add_argument('--require-complete',action='store_true',help='Fail unless the entire event corpus, normalization and ledger agree')
    args = parser.parse_args()
    result = audit(args.root)
    if args.require_complete:require_complete(result)
    payload = json.dumps(result, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        partial = args.output.with_suffix('.partial')
        partial.write_text(payload + '\n')
        partial.replace(args.output)
    print(payload)


if __name__ == '__main__':
    main()
