"""Bounded openFDA ingestion into existing pharmaceutical tables."""
import asyncio
from datetime import date
import json

import httpx

from app.db.pharma.ingestion_run_repository import IngestionRunRepository
from app.db.pharma.safety_repository import SafetyRepository
from app.services.pharma.safety_matching import CatalogIndex, match_mentions
from app.services.pharma.safety_records import SOURCES, normalize_record


class SafetyFDAClient:
    def __init__(self, http):
        self.http = http

    async def fetch(self, kind, expression, limit):
        rows = []
        total = 0
        last_updated = None
        while len(rows) < limit:
            params = {'search': expression, 'limit': min(100, limit - len(rows)), 'skip': len(rows)}
            if kind == 'adverse_events':
                params['sort'] = 'receivedate:desc'
            for attempt in range(3):
                try:
                    response = await self.http.get(SOURCES[kind][1], params=params)
                    if response.status_code == 404 and response.json().get('error', {}).get('code') == 'NOT_FOUND':
                        if rows:
                            raise ValueError('Source changed during pagination')
                        return [], {'available': 0, 'fetched': 0, 'truncated': False}
                    response.raise_for_status()
                    break
                except (httpx.TransportError, httpx.HTTPStatusError) as exc:
                    if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code not in (429, 500, 502, 503, 504):
                        raise
                    if attempt == 2:
                        raise
                    await asyncio.sleep(0.5 * 2 ** attempt)
            payload = response.json()
            page = payload.get('results')
            total = payload.get('meta', {}).get('results', {}).get('total')
            if not isinstance(page, list) or not page or not isinstance(total, int):
                raise ValueError('Invalid openFDA response')
            rows.extend(page)
            last_updated = payload.get('meta', {}).get('last_updated')
            if len(rows) >= total:
                break
        return rows, {'available': total, 'fetched': len(rows), 'truncated': len(rows) < total,
                      'source_dataset_updated_at': last_updated}


def queries(kind, drugs, start, end):
    groups = {}
    for drug in drugs:
        name = drug['generic_name']
        if kind == 'labels':
            for ndc in drug['product_ndcs']:
                query = 'openfda.product_ndc:' + json.dumps(ndc)
                groups.setdefault(query, []).append(str(drug['id']))
        else:
            quoted = json.dumps(name)
            if kind == 'recalls':
                query = f'(openfda.generic_name:{quoted} OR product_description:{quoted})'
            else:
                query = f'(patient.drug.openfda.generic_name:{quoted} OR patient.drug.medicinalproduct:{quoted}) AND receivedate:[{start.replace("-", "")} TO {end.replace("-", "")}]'
            groups.setdefault(query, []).append(str(drug['id']))
    return groups


async def ingest_safety(kind, *, limit=10, start='2024-01-01', end=None, client=None, repository=None):
    if kind not in ('labels', 'recalls', 'adverse_events') or not 1 <= limit <= 1000:
        raise ValueError('Unknown source or invalid limit (1–1000)')
    end = end or date.today().isoformat()
    if date.fromisoformat(start) > date.fromisoformat(end):
        raise ValueError('Sample start must not follow end')
    repository = repository or SafetyRepository()
    drugs = repository.catalog()
    if not drugs:
        raise ValueError('Ingest the NDC catalog first')
    runs = IngestionRunRepository()
    run_id = runs.start(SOURCES[kind][0], {'drug_ids': [str(d['id']) for d in drugs], 'limit_per_query': limit,
        'sample_window': {'field': 'receivedate', 'start': start, 'end': end} if kind == 'adverse_events' else None})
    coverage, records, errors = {}, {}, []
    counts = dict(fetched=0, inserted=0, updated=0, unresolved=0, failed=0)
    unchanged = 0
    index = CatalogIndex(drugs)

    async def collect(fetcher):
        for query, drug_ids in queries(kind, drugs, start, end).items():
            try:
                raw_records, info = await fetcher.fetch(kind, query, limit)
                coverage[query] = dict(info, drug_ids=drug_ids, status='succeeded')
                counts['fetched'] += len(raw_records)
            except (httpx.HTTPError, ValueError, TypeError) as exc:
                coverage[query] = {'drug_ids': drug_ids, 'status': 'failed'}
                errors.append(type(exc).__name__)
                continue
            for raw in raw_records:
                try:
                    normalized = normalize_record(kind, raw, run_id)
                except (ValueError, TypeError, KeyError, AttributeError):
                    counts['failed'] += 1
                    continue
                key = normalized['source_record_id']
                if kind == 'adverse_events' and key in records:
                    def version(r):
                        value = r['report_version'] or ''
                        return int(value) if value.isdigit() else -1
                    if version(records[key]) > version(normalized):
                        continue
                records[key] = normalized
    try:
        if client is not None:
            await collect(client)
        else:
            async with httpx.AsyncClient(timeout=25) as http:
                await collect(SafetyFDAClient(http))
        for record in records.values():
            links = match_mentions(index, kind, record['raw_json'])
            counts['unresolved'] += not bool(links)
            action = repository.upsert(kind, record, links)
            if action == 'unchanged':
                unchanged += 1
            else:
                counts[action] += 1
        successful_queries = sum(v['status'] == 'succeeded' for v in coverage.values())
        status = 'failed' if not successful_queries else ('partial' if errors or counts['failed'] or any(v.get('truncated') for v in coverage.values()) else 'succeeded')
    except Exception as exc:
        runs.finish(run_id, status='failed', counts=counts, coverage=coverage, error_summary=type(exc).__name__)
        raise
    runs.finish(run_id, status=status, counts=counts, coverage=coverage, error_summary=', '.join(errors)[:1000] or None)
    return {'source': SOURCES[kind][0], 'run_id': str(run_id), 'status': status, 'counts': counts,
            'older_versions_ignored': unchanged}
