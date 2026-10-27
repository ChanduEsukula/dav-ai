"""Bounded Week 2 ingestion; uses the existing NDC catalog in PostgreSQL."""
import argparse
import asyncio
from datetime import date
import json
from pathlib import Path

from app.services.pharma.safety_ingestion import ingest_safety
from app.services.pharma.communications_ingestion import CONFIG, ingest_communications


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources', nargs='+', choices=['labels', 'recalls', 'adverse_events', 'communications'],
                        default=['labels', 'recalls', 'adverse_events', 'communications'])
    parser.add_argument('--limit-per-query', type=int, default=10)
    parser.add_argument('--sample-start', default='2024-01-01')
    parser.add_argument('--sample-end', default=date.today().isoformat())
    parser.add_argument('--communications-config', type=Path, default=CONFIG)
    args = parser.parse_args(argv)
    if not 1 <= args.limit_per_query <= 1000:
        parser.error('--limit-per-query must be 1–1000')
    try:
        if date.fromisoformat(args.sample_start) > date.fromisoformat(args.sample_end):
            raise ValueError()
    except ValueError:
        parser.error('Provide an ordered ISO date sample window')
    return args


async def execute(args):
    results = []
    for source in dict.fromkeys(args.sources):
        if source == 'communications':
            result = await ingest_communications(config=args.communications_config)
        else:
            result = await ingest_safety(source, limit=args.limit_per_query, start=args.sample_start, end=args.sample_end)
        results.append(result)
        print(json.dumps(result), flush=True)
    return results


def main(argv=None):
    results = asyncio.run(execute(parse_args(argv)))
    return int(any(result['status'] == 'failed' for result in results))


if __name__ == '__main__':
    raise SystemExit(main())
