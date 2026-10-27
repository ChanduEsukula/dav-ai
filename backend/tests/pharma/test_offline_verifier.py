"""The verifier blocks every upstream provider and FDA request."""
import os
from pathlib import Path
import subprocess
import sys
import runpy

import pytest


def test_streamed_snapshot_detects_content_changes(pharma_db, ndc_record):
    import psycopg
    from app.db.pharma.drug_repository import DrugRepository
    from app.db.pharma.ingestion_run_repository import IngestionRunRepository
    from app.services.pharma.ndc_ingestion import SOURCE, normalize_ndc_record

    script = Path(__file__).resolve().parents[3] / 'scripts/verify_pharma_failed_refresh.py'
    snapshot = runpy.run_path(str(script))['snapshot']
    assert snapshot()['drugs']['count'] == 0
    run_id = IngestionRunRepository().start(SOURCE, {})
    row, _ = DrugRepository().upsert(normalize_ndc_record(ndc_record, run_id))
    before = snapshot()
    assert before == snapshot()
    assert before['drugs']['count'] == 1
    with psycopg.connect(pharma_db) as connection:
        connection.execute("UPDATE pharma.drugs SET generic_name='Changed test fixture' WHERE id=%s", (row['id'],))
    after = snapshot()
    assert after['drugs']['count'] == before['drugs']['count']
    assert after['drugs']['sha256'] != before['drugs']['sha256']
    assert all(after[key] == before[key] for key in before if key != 'drugs')


@pytest.mark.parametrize('live', ['0', '1'])
def test_offline_verifier_host_boundary(live, tmp_path):
    script = Path(__file__).resolve().parents[3] / 'scripts/pharma_offline_server.py'
    code = '''
import asyncio, httpx, runpy, sys
def original(self, request, *args, **kwargs):
    return httpx.Response(200, request=request)
async def original_async(self, request, *args, **kwargs):
    return original(self, request, *args, **kwargs)
httpx.Client.send = original
httpx.AsyncClient.send = original_async
runpy.run_path(sys.argv[1])
async def check():
    for url in ['https://api.fda.gov/drug/label.json',
                'https://download.open.fda.gov/drug/event/a.zip',
                'https://api.openai.com.evil.invalid/',
                'http://api.openai.com/',
                'https://api.openai.com/v1/chat/completions',
                'https://generativelanguage.googleapis.com/v1beta/models/test']:
        allowed = False
        for asynchronous in [False, True]:
            try:
                if asynchronous:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(url)
                else:
                    with httpx.Client() as client:
                        response = client.get(url)
            except httpx.ConnectError:
                assert not allowed
            else:
                assert allowed and response.status_code == 200
asyncio.run(check())
'''
    subprocess.run([sys.executable, '-c', code, str(script), live], check=True,
                   env={**os.environ, 'PHARMA_LIVE_ASK': live,
                        'PHARMA_OFFLINE_LOG': str(tmp_path / 'outbound.log')})
