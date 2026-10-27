"""Persist validated per-shard evidence for an already completed analytical drug join."""
import argparse
import json
from pathlib import Path
from app.research.shards import checkpoint_resolved_drugs


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path('data/research'))
    p.add_argument('--origin-log',type=Path)
    a=p.parse_args()
    result=checkpoint_resolved_drugs(a.root,origin_log=a.origin_log)
    print(json.dumps({'complete':result['complete'],'source_table':result['source_table'],'totals':result['totals']},indent=2))


if __name__=='__main__':main()
