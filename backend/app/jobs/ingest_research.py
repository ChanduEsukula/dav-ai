"""Official research bulk ingestion; isolated from the application database."""
import argparse
import json
from pathlib import Path
from app.research.bulk import ingest, fingerprint


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('kind',choices=['ndc','event','enforcement'])
    p.add_argument('--root',type=Path,default=Path('data/research'))
    p.add_argument('--max-files',type=int)
    p.add_argument('--quarter')
    p.add_argument('--discard-archives',action='store_true')
    p.add_argument('--min-free-gb',type=float,default=30)
    p.add_argument('--max-seconds',type=float)
    p.add_argument('--resume',action='store_true',help='Require the official manifest to match the existing snapshot')
    p.add_argument('--normalize',action='store_true',help='Checkpoint deterministic drug normalization after each event file (requires --resume)')
    a=p.parse_args()
    if (a.max_files is not None and a.max_files<1) or a.min_free_gb<1 or (a.max_seconds is not None and a.max_seconds<=0):p.error('Invalid resource limits')
    expected=json.loads((a.root/(a.kind+'-latest.json')).read_text())['dataset_key'] if a.resume else None
    after_file=before_files=None
    if a.normalize:
        if a.kind!='event' or not a.resume:p.error('--normalize requires event --resume')
        from app.research.analysis import normalize_mentions
        from app.research.identity import IdentityIndex
        index=None
        def before_files():
            nonlocal index
            index=IdentityIndex.load(a.root)
            normalize_mentions(a.root,index=index) # Reuses every verified normalization receipt.
        source=a.root/a.kind/expected
        def after_file(_):
            url=json.loads((source/'progress.json').read_text())['last_completed']
            path=source/'files'/('quarter='+url.split('/')[-2])/fingerprint(url)[:24]/'drugs.parquet'
            normalize_mentions(a.root,[path],index=index)
    r=ingest(a.root,a.kind,max_files=a.max_files,quarter=a.quarter,discard_archives=a.discard_archives,min_free_gb=a.min_free_gb,max_seconds=a.max_seconds,expected_dataset_key=expected,after_file=after_file,before_files=before_files)
    print(json.dumps(r,indent=2))
    return int(bool(r['failures']))


if __name__=='__main__':raise SystemExit(main())
