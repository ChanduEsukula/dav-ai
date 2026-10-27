"""Small, bounded openFDA NDC ingestion. No request-time source calls."""
import asyncio
import json
from pathlib import Path
from urllib.parse import urlencode

import httpx

from app.db.pharma.drug_repository import DrugRepository
from app.db.pharma.ingestion_run_repository import IngestionRunRepository
from app.services.pharma.normalization import normalize_name, normalize_ndc, normalize_rxcui

SOURCE = 'openfda_ndc_directory'
ENDPOINT = 'https://api.fda.gov/drug/ndc.json'
DEFAULT_CATALOG = Path(__file__).resolve().parents[2] / 'config' / 'drug_catalog.json'


def load_catalog(path=DEFAULT_CATALOG):
    data = json.loads(Path(path).read_text())
    names = data.get('drugs')
    if not isinstance(names, list) or not names or any(not isinstance(n, str) or not normalize_name(n) for n in names):
        raise ValueError('Catalog must contain a non-empty drugs array of names')
    # No catalog-size limit. Dedupe configuration, retaining its order.
    return list(dict.fromkeys(normalize_name(n) for n in names))


def _texts(values):
    if not isinstance(values, list):
        return []
    return list(dict.fromkeys(v.strip() for v in values if isinstance(v, str) and v.strip()))


def normalize_ndc_record(record: dict, run_id) -> dict:
    generic = record.get('generic_name')
    source_id = record.get('product_id')
    ndc = record.get('product_ndc')
    if not isinstance(generic, str) or not normalize_name(generic):
        raise ValueError('Missing generic_name')
    if not isinstance(source_id, str) or not source_id.strip():
        raise ValueError('Missing product_id')
    if not isinstance(ndc, str) or not normalize_ndc(ndc):
        raise ValueError('Missing or invalid product_ndc')
    ingredients = record.get('active_ingredients') or []
    openfda = record.get('openfda') or {}
    brands = _texts([record.get('brand_name'), record.get('brand_name_base')])
    rxcuis = [value for value in _texts(openfda.get('rxcui', [])) if normalize_rxcui(value)]
    return {
        'generic_name': generic.strip(), 'normalized_generic_name': normalize_name(generic),
        'brand_names': brands,
        'normalized_names': list(dict.fromkeys(normalize_name(n) for n in [generic, *brands])),
        'active_ingredients': _texts([i.get('name') for i in ingredients]),
        'strength': '; '.join(f"{i.get('name', '')}: {i['strength']}" for i in ingredients if i.get('strength')) or None,
        'dosage_form': record.get('dosage_form'), 'routes': _texts(record.get('route', [])),
        'manufacturers': _texts([record.get('labeler_name'), *_texts(openfda.get('manufacturer_name', []))]),
        # Multiple harmonized RxCUIs are not collapsed into one invented mapping.
        'rxcui': rxcuis[0] if len(rxcuis) == 1 else None,
        'product_ndcs': [ndc.strip()],
        'package_ndcs': _texts([p.get('package_ndc') for p in record.get('packaging', [])
                              if isinstance(p.get('package_ndc'), str) and normalize_ndc(p['package_ndc'])]),
        'source': SOURCE, 'source_record_id': source_id.strip(),
        'source_url': ENDPOINT + '?' + urlencode({'search': 'product_id:' + json.dumps(source_id), 'limit': 1}),
        # NDC supplies marketing/listing dates, not a reliable per-record modified timestamp.
        'source_updated_at': None, 'ingestion_run_id': run_id, 'raw_json': record,
    }


class NDCClient:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def fetch(self, name: str, max_records: int):
        records = []
        total = None
        source_updated = None
        while len(records) < max_records:
            params = {'search': 'generic_name:' + json.dumps(name),
                      'limit': min(100, max_records - len(records)), 'skip': len(records)}
            for attempt in range(3):
                try:
                    response = await self.client.get(ENDPOINT, params=params)
                    if response.status_code == 404:
                        body = response.json()
                        if body.get('error', {}).get('code') == 'NOT_FOUND':
                            if records:
                                raise ValueError('NDC pagination changed during fetch')
                            return [], {'available': 0, 'fetched': 0, 'truncated': False}
                    if response.status_code == 429 or response.status_code >= 500:
                        response.raise_for_status()
                    break
                except (httpx.TransportError, httpx.HTTPStatusError):
                    if attempt == 2:
                        raise
                    await asyncio.sleep(0.5 * 2 ** attempt)
            response.raise_for_status()
            body = response.json()
            page = body.get('results')
            if not isinstance(page, list) or not page:
                raise ValueError('Invalid or unexpectedly empty NDC response')
            total = body.get('meta', {}).get('results', {}).get('total')
            if not isinstance(total, int) or total < 0:
                raise ValueError('Missing NDC result total')
            source_updated = body.get('meta', {}).get('last_updated')
            records.extend(page)
            if len(records) >= total:
                break
        return records, {'available': total, 'fetched': len(records),
                         'truncated': total > len(records), 'source_dataset_updated_at': source_updated}


async def ingest_catalog(names: list[str], *, max_records_per_drug=25, client=None,
                         drugs=None, runs=None):
    if not 1 <= max_records_per_drug <= 1000:
        raise ValueError('max_records_per_drug must be between 1 and 1000')
    names = list(dict.fromkeys(normalize_name(n) for n in names if normalize_name(n)))
    if not names:
        raise ValueError('Catalog is empty')
    drugs = drugs or DrugRepository()
    runs = runs or IngestionRunRepository()
    run_id = runs.start(SOURCE, {'drugs': names, 'max_records_per_drug': max_records_per_drug})
    counts = dict(fetched=0, inserted=0, updated=0, unresolved=0, failed=0)
    coverage = {}
    errors = []
    seen = set()

    async def process(fetcher):
        for name in names:
            try:
                records, info = await fetcher.fetch(name, max_records_per_drug)
                coverage[name] = info
            except (httpx.HTTPError, ValueError, TypeError, KeyError) as exc:
                # No URLs, credentials, or full upstream bodies in persisted errors.
                errors.append(f'{name}: {type(exc).__name__}')
                coverage[name] = {'status': 'failed'}
                continue
            counts['fetched'] += len(records)
            for record in records:
                try:
                    drug = normalize_ndc_record(record, run_id)
                except (ValueError, TypeError, KeyError, AttributeError):
                    counts['failed'] += 1
                    counts['unresolved'] += 1
                    continue
                key = drug['source_record_id']
                if key in seen:
                    continue
                seen.add(key)
                _, action = drugs.upsert(drug)
                counts[action] += 1

    try:
        if client is not None:
            await process(client)
        else:
            async with httpx.AsyncClient(timeout=20.0) as http:
                await process(NDCClient(http))
        incomplete = bool(errors or counts['failed']) or any(
            v.get('truncated') or v.get('available') == 0 for v in coverage.values())
        written = counts['inserted'] + counts['updated']
        status = ('partial' if written else 'failed') if incomplete else 'succeeded'
    except Exception as exc:
        # Committed earlier products stay available even after a database/fatal error.
        status = 'failed'
        errors.append(type(exc).__name__)
        runs.finish(run_id, status=status, counts=counts, coverage=coverage,
                    error_summary='; '.join(errors)[:2000])
        raise
    runs.finish(run_id, status=status, counts=counts, coverage=coverage,
                error_summary='; '.join(errors)[:2000] or None)
    return {'run_id': str(run_id), 'status': status, 'counts': counts, 'coverage': coverage}
