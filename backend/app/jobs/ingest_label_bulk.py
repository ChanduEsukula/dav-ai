"""Discover and import the current official label corpus; reruns resume committed batches."""
import argparse
import json
from pathlib import Path
import resource
import sys
from app.services.pharma.bulk_labels import import_labels


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache-dir',type=Path,default=Path('data/pharma_bulk_cache'))
    parser.add_argument('--batch-size',type=int,default=100)
    parser.add_argument('--max-records',type=int)
    parser.add_argument('--max-files',type=int)
    args=parser.parse_args(argv)
    result=import_labels(**vars(args))
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    result['peak_rss_mb']=round(peak/(1024**2 if sys.platform=='darwin' else 1024),2)
    print(json.dumps(result,indent=2))
    return int(result['status']=='failed' or bool(result['errors']))


if __name__=='__main__':
    raise SystemExit(main())
