"""Measure a real completed-corpus resume, retaining before/after artifact evidence."""
import argparse
import json
from pathlib import Path
import time

import httpx

from app.jobs.audit_research import require
from app.research.analysis import normalize_mentions
from app.research.bulk import MANIFEST, atomic_json, file_digest, ingest, now
from app.research.identity import snapshot


def inventory(root, source, normalized):
    paths=[source/'manifest.json', source/'snapshot.json', root/'identity/mapping.json.gz']
    for directory in (source/'files',source/'cache',normalized):
        paths.extend(p for p in directory.rglob('*') if p.is_file())
    return {str(p.relative_to(root)):{'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns,
                                    'sha256':file_digest(p)} for p in sorted(paths)}


def verify(root, output):
    root=Path(root);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    source=snapshot(root,'event')
    mapping=json.loads((root/'identity/summary.json').read_text())['mapping_hash']
    normalized=root/'normalized'/mapping/source.name
    manifest=json.loads((source/'manifest.json').read_text())['results']['drug']['event']
    started=time.monotonic();requests=[];before=None

    def before_files():
        nonlocal before
        receipts=[json.loads(p.read_text()) for p in source.glob('files/quarter=*/*/receipt.json')
                  if not p.parent.name.endswith('.partial')]
        require({r['url'] for r in receipts}=={p['file'] for p in manifest['partitions']},'replay requires complete corpus')
        require(len(receipts)==len(manifest['partitions']),'duplicate receipts')
        require(sum(r['records'] for r in receipts)==manifest['total_records'],'replay record total')
        require(not list(source.glob('files/quarter=*/*.partial')),'source staging')
        require(not list(normalized.glob('*.partial')),'normalization staging')
        require(len(list(normalized.glob('*.json')))==len(receipts),'replay requires complete normalization')
        before=inventory(root,source,normalized)
        atomic_json(output/'replay-before.json',before)
        normalize_mentions(root)

    def record(request):
        requests.append({'method':request.method,'url':str(request.url)})
        # A completed-corpus verification must never fetch an archive, even if
        # a regression tries to do so. Persist that attempt as a failed check.
        require(str(request.url)==MANIFEST,'unexpected replay archive request')

    result={'started_at':now(),'dataset_key':source.name,'passed':False}
    try:
        with httpx.Client(timeout=httpx.Timeout(180,connect=20),headers={'Accept-Encoding':'identity'},
                          event_hooks={'request':[record]}) as http:
            replay=ingest(root,'event',http=http,expected_dataset_key=source.name,
                          discard_archives=True,min_free_gb=40,before_files=before_files)
        after=inventory(root,source,normalized)
        atomic_json(output/'replay-after.json',after)
        changed=sorted(k for k in before.keys()|after.keys() if before.get(k)!=after.get(k))
        result.update(ingestion=replay,changed_artifacts=changed,verified_artifacts=len(after))
        require(not changed,'replay rewrote a corpus/normalization artifact')
        require(replay['complete'] and not replay['failures'],'replay manifest verification')
        require(replay['files_processed_this_run']==0,'replay processed a completed file')
        require(replay['files_skipped_this_run']==len(manifest['partitions']),'replay skipped file count')
        require(len(requests)==2 and all(r['url']==MANIFEST for r in requests),'replay network requests')
        result['passed']=True
    except Exception as exc:
        result['error']=type(exc).__name__+': '+str(exc)
        raise
    finally:
        result.update(completed_at=now(),seconds=time.monotonic()-started,requests=requests,
                      archive_requests=sum(r['url']!=MANIFEST for r in requests))
        atomic_json(output/'replay-verification.json',result)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path('data/research'))
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(verify(args.root,args.output_dir),indent=2))


if __name__=='__main__':main()
