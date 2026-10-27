"""Tests create/drop only a randomly named database on an explicitly supplied server."""
import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo
import pytest

ROOT = Path(__file__).resolve().parents[3]

def migrate(url, direction, revision):
    # Alembic's logging.fileConfig must not mutate pytest/application loggers.
    env = dict(os.environ, DATABASE_URL=url)
    subprocess.run([sys.executable, '-m', 'alembic', '-c', str(ROOT / 'alembic.ini'),
                    direction, revision], cwd=ROOT, env=env, check=True,
                   capture_output=True, text=True)



@pytest.fixture(scope='session')
def postgres_url():
    admin_url = os.getenv('PHARMA_TEST_DATABASE_URL')
    if not admin_url:
        pytest.skip('Set PHARMA_TEST_DATABASE_URL to a PostgreSQL server with CREATEDB permission')
    database = 'davai_test_' + uuid4().hex
    with psycopg.connect(admin_url, autocommit=True) as conn:
        conn.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(database)))
    url = make_conninfo(admin_url, dbname=database)
    # Alembic expects a URL, not libpq keyword syntax.
    from sqlalchemy.engine import URL
    from psycopg.conninfo import conninfo_to_dict
    params = conninfo_to_dict(url)
    migration_url = URL.create('postgresql+psycopg', username=params.get('user'),
        password=params.get('password'), host=params.get('host'),
        port=int(params['port']) if params.get('port') else None, database=database,
        query={k: v for k, v in params.items() if k not in ('user', 'password', 'host', 'port', 'dbname')})
    migration_url_text = migration_url.render_as_string(hide_password=False)
    try:
        migrate(migration_url_text, 'upgrade', 'head')
        yield url, migration_url_text
    finally:
        with psycopg.connect(admin_url, autocommit=True) as conn:
            conn.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(database)))


@pytest.fixture
def pharma_db(postgres_url, isolate_database_url, monkeypatch):
    url, _ = postgres_url
    monkeypatch.setenv('DATABASE_URL', url)
    with psycopg.connect(url) as conn:
        conn.execute('TRUNCATE pharma.ingestion_runs CASCADE')
    return url


@pytest.fixture
def ndc_record():
    # Synthetic unit-test fixture; never used to populate the public catalog.
    return {
        'product_id': 'test-product-1', 'product_ndc': '12345-6789',
        'generic_name': 'Example Ingredient', 'brand_name': 'Example Brand',
        'active_ingredients': [{'name': 'EXAMPLE INGREDIENT', 'strength': '10 mg/1'}],
        'dosage_form': 'TABLET', 'route': ['ORAL'], 'labeler_name': 'Example Labeler',
        'packaging': [{'package_ndc': '12345-6789-01'}],
        'openfda': {'rxcui': ['1234567']}, 'marketing_start_date': '20240101',
    }


@pytest.fixture
def migrate_database():
    return migrate
