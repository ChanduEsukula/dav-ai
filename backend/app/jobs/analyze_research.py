"""Analyze completed research partitions; export only after complete ingestion.

Even a complete current snapshot does not establish historical availability.
Training partitions remain empty until that independent requirement is satisfied.
"""
import argparse
import json
from pathlib import Path

from app.research.analysis import prepare, build_features, diagnose_sparsity


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path('data/research'))
    parser.add_argument('--export',action='store_true')
    parser.add_argument('--exploratory',action='store_true',help='Explicitly allow retrospective diagnostic exports; never certifies training readiness')
    parser.add_argument('--sparsity',action='store_true')
    parser.add_argument('--export-dir',type=Path,default=Path('data/ml'))
    args=parser.parse_args()
    result=prepare(args.root)
    if args.sparsity:
        result['sparsity']=diagnose_sparsity(args.root)
    if args.export:
        result['export']=build_features(args.root,args.export_dir,exploratory=args.exploratory)
    print(json.dumps(result,indent=2,default=str))


if __name__=='__main__':main()
