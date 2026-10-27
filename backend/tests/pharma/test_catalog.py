import asyncio
from copy import deepcopy
from uuid import uuid4

import httpx
import psycopg
import pytest

from app.db.pharma.drug_repository import DrugRepository
from app.db.pharma.ingestion_run_repository import IngestionRunRepository
from app.services.pharma.ndc_ingestion import SOURCE, ingest_catalog, normalize_ndc_record
from app.services.pharma.normalization import resolve_drug


class FixtureNDC:
    def __init__(self, records):
        self.records = records

    async def fetch(self, name, max_records):
        return self.records, {'available': len(self.records), 'fetched': len(self.records), 'truncated': False}


def insert(record):
    run_id = IngestionRunRepository().start(SOURCE, {})
    return DrugRepository().upsert(normalize_ndc_record(record, run_id))[0]


def test_full_migration_and_downgrade(pharma_db, postgres_url, migrate_database):
    with psycopg.connect(pharma_db) as conn:
        assert conn.execute('SELECT version_num FROM alembic_version').fetchone()[0] == '20260926_0018'
        tables = conn.execute("SELECT tablename FROM pg_tables WHERE schemaname='pharma'").fetchall()
        assert len(tables) == 11
        assert conn.execute("SELECT to_regclass('public.saved_monitors')").fetchone()[0]
    _, migration_url = postgres_url
    migrate_database(migration_url, 'downgrade', '20260630_0015')
    migrate_database(migration_url, 'upgrade', 'head')


def test_insert_upsert_search_and_update(pharma_db, ndc_record):
    repo = DrugRepository()
    run_id = IngestionRunRepository().start(SOURCE, {})
    record = normalize_ndc_record(ndc_record, run_id)
    first, action = repo.upsert(record)
    assert action == 'inserted'
    changed = deepcopy(ndc_record)
    changed['brand_name'] = 'Updated Brand'
    record = normalize_ndc_record(changed, run_id)
    second, action = repo.upsert(record)
    assert action == 'updated' and first['id'] == second['id']
    assert second['brand_names'] == ['Updated Brand']
    assert len(repo.list_overviews()) == 1
    assert not repo.find_by_normalized_name('example brand')
    assert repo.find_by_id(first['id'])['source_record_id'] == ndc_record['product_id']
    for matches in [repo.find_by_normalized_name(' EXAMPLE  ingredient '),
                    repo.find_by_normalized_name('updated BRAND'),
                    repo.find_by_ndc('12345-6789'), repo.find_by_ndc('12345-6789-01'),
                    repo.find_by_rxcui('1234567'), repo.search('ingredient'), repo.search('brand'),
                    repo.search('12345-6789-01'), repo.search('1234567')]:
        assert len(matches) == 1 and matches[0]['id'] == first['id']
    assert not repo.search("%' OR true --")
    assert not repo.find_by_ndc('not-an-ndc')
    assert not repo.find_by_rxcui('unknown')


def test_constraints(pharma_db, ndc_record):
    row = insert(ndc_record)
    with pytest.raises(psycopg.errors.UniqueViolation), psycopg.connect(pharma_db) as conn:
        conn.execute('''INSERT INTO pharma.drugs (generic_name, normalized_generic_name, source,
            source_record_id, ingestion_run_id) VALUES ('x', 'x', %s, %s, %s)''',
            (SOURCE, row['source_record_id'], row['ingestion_run_id']))
    with pytest.raises(psycopg.errors.ForeignKeyViolation), psycopg.connect(pharma_db) as conn:
        conn.execute("INSERT INTO pharma.drug_label_links VALUES (%s, %s, 'name', 'x')", (row['id'], uuid4()))
    with pytest.raises(psycopg.errors.ForeignKeyViolation), psycopg.connect(pharma_db) as conn:
        conn.execute('''INSERT INTO pharma.drugs (generic_name, normalized_generic_name, source,
            source_record_id, ingestion_run_id) VALUES ('x', 'x', %s, 'new', %s)''', (SOURCE, uuid4()))
    with pytest.raises(psycopg.errors.CheckViolation), psycopg.connect(pharma_db) as conn:
        conn.execute("UPDATE pharma.ingestion_runs SET records_fetched=-1 WHERE id=%s", (row['ingestion_run_id'],))
    with psycopg.connect(pharma_db) as conn:
        label_id = conn.execute('''INSERT INTO pharma.drug_labels (title, source, source_record_id,
            ingestion_run_id) VALUES ('test', %s, 'label', %s) RETURNING id''',
            (SOURCE, row['ingestion_run_id'])).fetchone()[0]
        conn.execute("INSERT INTO pharma.drug_label_links VALUES (%s, %s, 'name', 'x')", (row['id'], label_id))
    with pytest.raises(psycopg.errors.UniqueViolation), psycopg.connect(pharma_db) as conn:
        conn.execute("INSERT INTO pharma.drug_label_links VALUES (%s, %s, 'name', 'x')", (row['id'], label_id))


def test_duplicate_ingestion_and_source_provenance(pharma_db, ndc_record):
    client = FixtureNDC([ndc_record])
    first = asyncio.run(ingest_catalog(['example'], client=client))
    second = asyncio.run(ingest_catalog(['example', 'another query'], client=client))
    assert first['counts']['inserted'] == 1
    assert second['counts']['inserted'] == 0
    assert second['counts']['updated'] == 1
    rows = DrugRepository().list_overviews()
    assert len(rows) == 1
    assert rows[0]['raw_json'] == ndc_record
    assert rows[0]['source_updated_at'] is None
    assert rows[0]['ingested_at']
    assert 'api.fda.gov/drug/ndc.json?' in rows[0]['source_url']
    run = IngestionRunRepository().find_by_id(second['run_id'])
    assert run['status'] == 'succeeded' and run['finished_at']


def test_failed_and_partial_ingestion_preserve_old_records(pharma_db, ndc_record):
    old = insert(ndc_record)

    class Broken:
        async def fetch(self, name, max_records):
            if name == 'working':
                return [ndc_record], {'available': 1, 'truncated': False}
            raise httpx.ConnectError('upstream unavailable')

    result = asyncio.run(ingest_catalog(['broken'], client=Broken()))
    assert result['status'] == 'failed'
    assert DrugRepository().find_by_id(old['id'])['raw_json'] == ndc_record
    result = asyncio.run(ingest_catalog(['working', 'broken'], client=Broken()))
    assert result['status'] == 'partial'
    assert IngestionRunRepository().find_by_id(result['run_id'])['coverage']['broken']['status'] == 'failed'
    result = asyncio.run(ingest_catalog(['bad'], client=FixtureNDC([{'generic_name': 'missing identifiers'}])))
    assert result['status'] == 'failed' and result['counts']['unresolved'] == 1
    assert len(DrugRepository().list_overviews()) == 1


def test_resolution_ambiguity_and_conflict(pharma_db, ndc_record):
    first = insert(ndc_record)
    repo = DrugRepository()
    assert resolve_drug(repo, rxcui='1234567').drug['id'] == first['id']
    assert resolve_drug(repo, ndc='12345-6789').method == 'ndc'
    assert resolve_drug(repo, name=' EXAMPLE Brand ').method == 'name'
    assert resolve_drug(repo, ndc='00000-0000').reason == 'unresolved'
    other = deepcopy(ndc_record)
    other.update(product_id='second', product_ndc='54321-1111')
    other['packaging'] = []
    other['openfda'] = {'rxcui': ['7654321']}
    insert(other)
    assert resolve_drug(repo, name='example ingredient').reason == 'ambiguous'
    assert resolve_drug(repo, ndc='12345-6789', name='example ingredient').drug['id'] == first['id']
    assert resolve_drug(repo, rxcui='1234567', ndc='54321-1111').reason == 'conflicting_identifiers'


def test_offline_repository_uses_database_only(pharma_db, ndc_record, monkeypatch):
    row = insert(ndc_record)
    def forbidden(*args, **kwargs):
        raise AssertionError('Search must not contact upstream')
    monkeypatch.setattr(httpx.AsyncClient, 'get', forbidden)
    repo = DrugRepository()
    for q in ['example ingredient', 'Example Brand', '12345-6789', '1234567']:
        assert repo.search(q)[0]['id'] == row['id']
    body = repo.find_by_id(row['id'])
    assert body['source'] == SOURCE
    assert repo.find_by_id(uuid4()) is None
    assert repo.search('absent') == []
