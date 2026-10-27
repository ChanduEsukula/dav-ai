import asyncio
import json

from fastapi.testclient import TestClient
import httpx
import pytest

from app.main import app
from app.services.pharma.ndc_ingestion import NDCClient, load_catalog, normalize_ndc_record
from app.services.pharma.normalization import normalize_name, normalize_ndc, normalize_rxcui


def test_normalization_and_unknowns(ndc_record):
    assert normalize_name('  EXAMPLE\t Ingredient ') == 'example ingredient'
    assert normalize_ndc(' 01234-0567-08 ') == '01234-0567-08'
    assert normalize_ndc('123') is None
    assert normalize_rxcui(' 1234 ') == '1234'
    record = normalize_ndc_record(ndc_record, 'run')
    assert record['source_record_id'] == ndc_record['product_id']
    assert record['source_updated_at'] is None
    ndc_record['openfda']['rxcui'].append('98765')
    assert normalize_ndc_record(ndc_record, 'run')['rxcui'] is None


def test_catalog_config_has_no_size_cap(tmp_path):
    assert 30 <= len(load_catalog()) <= 50
    path = tmp_path / 'catalog.json'
    path.write_text(json.dumps({'drugs': [f'name {i}' for i in range(65)]}))
    assert len(load_catalog(path)) == 65
    path.write_text('{"drugs": [""]}')
    with pytest.raises(ValueError):
        load_catalog(path)


def test_client_pagination_and_truncation():
    requests = []
    def handler(request):
        requests.append(request)
        skip = int(request.url.params['skip'])
        limit = int(request.url.params['limit'])
        return httpx.Response(200, json={'meta': {'results': {'total': 150}},
                                        'results': [{'id': n} for n in range(skip, skip + limit)]})
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            return await NDCClient(http).fetch('example', 120)
    records, coverage = asyncio.run(run())
    assert len(records) == 120 and len(requests) == 2
    assert coverage['truncated'] is True
    assert requests[0].url.params['search'] == 'generic_name:"example"'


@pytest.mark.parametrize('response,empty', [
    (httpx.Response(404, json={'error': {'code': 'NOT_FOUND'}}), True),
    (httpx.Response(404, json={'error': {'code': 'INVALID_PATH'}}), False),
    (httpx.Response(200, json={'results': 'broken'}), False),
])
def test_client_empty_and_invalid_responses(response, empty):
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: response)) as http:
            return await NDCClient(http).fetch('example', 1)
    if empty:
        assert asyncio.run(run())[0] == []
    else:
        with pytest.raises((httpx.HTTPStatusError, ValueError)):
            asyncio.run(run())


def test_catalog_unavailable_returns_503(monkeypatch, tmp_path):
    missing_release = tmp_path / "missing-pharma-release.sqlite"

    monkeypatch.setenv(
        "DAV_AI_PHARMA_RELEASE_DB",
        str(missing_release),
    )

    client = TestClient(app)

    response = client.get(
        "/api/drugs/search?q=example"
    )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Pharmaceutical release is unavailable"
    )
