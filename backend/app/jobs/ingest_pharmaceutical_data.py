"""Run from the repository root: PYTHONPATH=backend python -m app.jobs.ingest_pharmaceutical_data."""
import argparse
import asyncio
import json
from pathlib import Path

from app.services.pharma.ndc_ingestion import DEFAULT_CATALOG, ingest_catalog, load_catalog


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description='Ingest a bounded openFDA NDC catalog into PostgreSQL')
    parser.add_argument('--catalog', type=Path, default=DEFAULT_CATALOG)
    parser.add_argument('--max-records-per-drug', type=int, default=25)
    args = parser.parse_args(argv)
    if not 1 <= args.max_records_per_drug <= 1000:
        parser.error('--max-records-per-drug must be between 1 and 1000')
    return args


def main(argv=None):
    args = parse_args(argv)
    result = asyncio.run(ingest_catalog(load_catalog(args.catalog),
                                      max_records_per_drug=args.max_records_per_drug))
    print(json.dumps(result, indent=2))
    return 1 if result['status'] == 'failed' else 0


if __name__ == '__main__':
    raise SystemExit(main())
