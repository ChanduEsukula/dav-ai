"""Local HTTP boundary tests: fake repository/model, real ProductSession/workflow."""
import asyncio
from contextlib import asynccontextmanager
from dataclasses import replace
import socket
import time

import httpx
import pytest

from app.agent.contracts import Limits
from app.local_research.api import create_app
from .test_research import ResearchBackend

PAIRING = 'synthetic-local-pairing-' + 'x' * 48
ORIGIN = 'http://127.0.0.1:5173'
ROOT = '/api/local/research/sessions'


class Model:
    async def request(self, path):
        return {'models': [{'name': 'llama3.2:3b'}, {'name': 'not-approved'}]}

    async def chat(self, messages, tools):
        import json
        ref = json.loads(messages[-1]['content'])['selected_product_ref']
        return {'done': True, 'message': {'role': 'assistant', 'tool_calls': [
            {'function': {'name': t['function']['name'], 'arguments': {'product_ref': ref}}} for t in tools]}}


@asynccontextmanager
async def client(*, backend=None, limits=Limits(), max_sessions=8, model_factory=lambda _: Model()):
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        app = create_app(listener, PAIRING, backend_factory=lambda: backend or ResearchBackend(),
                         limits=limits, max_sessions=max_sessions, model_factory=model_factory)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app, client=('127.0.0.1', 1234)),
                    base_url=f'http://127.0.0.1:{listener.getsockname()[1]}',
                    headers={'Origin': ORIGIN}) as c:
                yield c, app.state.registry


def auth(value):
    return {'Authorization': 'Bearer ' + value}


async def created(c):
    response = await c.post(ROOT, json={}, headers=auth(PAIRING))
    assert response.status_code == 200, response.text
    result = response.json()
    return result['session_id'], auth(result['capability'])


async def confirmed(c, sid, headers):
    result = await c.post(f'{ROOT}/{sid}/resolve', json={'query': 'Xanax'}, headers=headers)
    assert result.status_code == 200, result.text
    assert result.json()['state'] == 'confirmation_required'
    p = result.json()['candidates'][0]
    assert not any(key in p for key in ('product_id', 'ingredient_ids', 'formulation_id'))
    response = await c.post(f'{ROOT}/{sid}/confirm', json={'product_ref': p['product_ref']}, headers=headers)
    assert response.status_code == 200, response.text
    return p['product_ref']


async def done(c, sid, headers):
    for _ in range(100):
        response = await c.get(f'{ROOT}/{sid}/result', headers=headers)
        if response.json().get('state') != 'running':
            return response.json()
        await asyncio.sleep(.005)
    raise AssertionError('Task did not finish')


@pytest.mark.parametrize('model', [None, 'llama3.2:3b'])
def test_complete_lifecycle_and_wire_projection(model):
    async def scenario():
        async with client() as (c, registry):
            sid, headers = await created(c)
            await confirmed(c, sid, headers)
            body = {'question': 'Evidence?', 'categories': ['labels', 'recalls', 'faers'], 'model': model}
            started = await c.post(f'{ROOT}/{sid}/research', json=body, headers=headers)
            assert started.json()['state'] == 'running'
            result = await done(c, sid, headers)
            assert result['state'] == 'completed', result
            assert result['briefing']['routing']['mode'] == ('model' if model else 'deterministic')
            payload = str(result)
            for key in ["'product_id'", "'formulation_id'", "'ingredient_ids'", "'ingredient_id'", "'id'"]:
                assert key not in payload
            assert result['briefing']['sections'][2]['evidence']['summary']['product_report_total'] is None
            assert registry.active == 0
            assert (await c.post(f'{ROOT}/{sid}/research', json=body, headers=headers)).status_code == 409
            assert (await c.post(f'{ROOT}/{sid}/close', json={}, headers=headers)).json()['state'] == 'closed'
            assert not registry.entries
    asyncio.run(scenario())


def test_pairing_ownership_singleton_and_confirmation():
    async def scenario():
        async with client() as (c, registry):
            assert (await c.post(ROOT, json={})).status_code == 401
            assert (await c.post(ROOT, json={}, headers=auth('wrong' * 10))).status_code == 403
            sid, headers = await created(c)
            other, foreign = await created(c)
            assert (await c.get(f'{ROOT}/{sid}/result', headers=foreign)).status_code == 403
            assert (await c.get(f'{ROOT}/{sid}/result', headers=auth(PAIRING))).status_code == 403
            result = await c.post(f'{ROOT}/{sid}/research', headers=headers,
                json={'question': 'recalls', 'categories': ['recalls']})
            assert result.json()['detail']['code'] == 'confirmation_required'
            search = (await c.post(f'{ROOT}/{sid}/resolve', json={'query': 'Xanax'}, headers=headers)).json()
            ref = search['candidates'][0]['product_ref']
            assert len(search['candidates']) == 1 and not registry.entries[sid].session.selected_ref
            assert (await c.post(f'{ROOT}/{other}/confirm', json={'product_ref': ref}, headers=foreign)).status_code == 409
            await c.post(f'{ROOT}/{sid}/resolve', json={'query': 'Xanax'}, headers=headers)
            assert (await c.post(f'{ROOT}/{sid}/confirm', json={'product_ref': ref}, headers=headers)).status_code == 409
            ref = await confirmed(c, sid, headers)
            assert (await c.post(f'{ROOT}/{sid}/confirm', json={'product_ref': ref}, headers=headers)).status_code == 409
            assert (await c.post(f'{ROOT}/{sid}/resolve', json={'query': 'Xanax'}, headers=headers)).status_code == 409
    asyncio.run(scenario())


@pytest.mark.parametrize('field,value', [('owner_id', 'owner'), ('product_id', 'raw-database-id'), ('session', {})])
def test_browser_cannot_supply_authority(field, value):
    async def scenario():
        async with client() as (c, _):
            response = await c.post(ROOT, json={field: value}, headers=auth(PAIRING))
            assert response.status_code == 422 and value not in response.json().values()
            sid, headers = await created(c)
            response = await c.post(f'{ROOT}/{sid}/confirm', headers=headers,
                                    json={'product_ref': 'p_fake', field: value})
            assert response.status_code == 422
    asyncio.run(scenario())


@pytest.mark.parametrize('header,value', [('Origin', 'https://evil.example'), ('Origin', 'null'),
    ('Host', 'evil.example'), ('X-Forwarded-For', '127.0.0.1')])
def test_origin_host_proxy_and_csrf_denial(header, value):
    async def scenario():
        async with client() as (c, _):
            assert (await c.post(ROOT, json={}, headers={**auth(PAIRING), header: value})).status_code == 403
    asyncio.run(scenario())


def test_bounds_expiry_and_cleanup():
    async def scenario():
        async with client(max_sessions=1) as (c, registry):
            sid, headers = await created(c)
            assert (await c.post(ROOT, json={}, headers=auth(PAIRING))).status_code == 429
            assert (await c.post(ROOT, content='x' * 8193, headers=auth(PAIRING))).status_code == 413
            registry.entries[sid].created = time.monotonic() - 601
            assert (await c.get(f'{ROOT}/{sid}/result', headers=headers)).status_code == 410
            assert not registry.entries
            await created(c)
    asyncio.run(scenario())


def test_changed_binding_denies_confirmation():
    async def scenario():
        backend = ResearchBackend()
        async with client(backend=backend) as (c, _):
            sid, headers = await created(c)
            result = (await c.post(f'{ROOT}/{sid}/resolve', json={'query': 'Xanax'}, headers=headers)).json()
            backend.repo.products[0]['strength'] = 'other'
            response = await c.post(f'{ROOT}/{sid}/confirm', json={'product_ref': result['candidates'][0]['product_ref']}, headers=headers)
            assert response.json()['detail']['code'] == 'product_binding_changed'
    asyncio.run(scenario())


def test_busy_cancel_and_shutdown_cleanup():
    class Blocking(Model):
        async def chat(self, messages, tools):
            await asyncio.sleep(100)
    async def scenario():
        async with client(model_factory=lambda _: Blocking()) as (c, registry):
            sid, headers = await created(c)
            await confirmed(c, sid, headers)
            body = {'question': 'recalls', 'categories': ['recalls'], 'model': 'llama3.2:3b'}
            await c.post(f'{ROOT}/{sid}/research', json=body, headers=headers)
            assert registry.active == 1
            assert (await c.post(ROOT, json={}, headers=auth(PAIRING))).status_code == 429
            assert (await c.post(f'{ROOT}/{sid}/research', json=body, headers=headers)).status_code == 409
            assert (await c.post(f'{ROOT}/{sid}/cancel', json={}, headers=headers)).json()['code'] == 'cancelled'
            assert not registry.entries and registry.active == 0
            sid, headers = await created(c)
            await confirmed(c, sid, headers)
            await c.post(f'{ROOT}/{sid}/research', json=body, headers=headers)
        assert not registry.entries and registry.active == 0
    asyncio.run(scenario())


def test_model_timeout_and_offline_model():
    class Slow(Model):
        async def chat(self, messages, tools):
            await asyncio.sleep(10)
    class Offline(Model):
        async def request(self, path):
            raise OSError('sensitive internal details')
    async def scenario():
        for factory, expected in [(lambda _: Slow(), 'timeout'), (lambda _: Offline(), 'model_unavailable')]:
            async with client(model_factory=factory, limits=replace(Limits(), model_timeout=.01)) as (c, registry):
                sid, headers = await created(c)
                await confirmed(c, sid, headers)
                await c.post(f'{ROOT}/{sid}/research', headers=headers,
                    json={'question': 'recalls', 'categories': ['recalls'], 'model': 'llama3.2:3b'})
                outcome = await done(c, sid, headers)
                assert outcome['code'] == expected
                assert registry.active == 0
    asyncio.run(scenario())


@pytest.mark.parametrize('environment', ['staging', 'production', 'preview'])
def test_hosted_creation_and_execution_denied(monkeypatch, environment):
    async def scenario():
        async with client() as (c, _):
            sid, headers = await created(c)
            monkeypatch.setenv('DAVAI_ENV', environment)
            for path in [ROOT, f'{ROOT}/{sid}/research']:
                response = await c.post(path, json={}, headers=headers)
                assert response.status_code == 403 and response.json()['detail']['code'] == 'hosted_serving_denied'
            with socket.socket() as listener:
                listener.bind(('127.0.0.1', 0))
                with pytest.raises(RuntimeError, match='denied'):
                    create_app(listener, PAIRING)
    asyncio.run(scenario())


def test_normal_application_never_mounts_local_routes():
    from app.main import app
    assert not any('/local/research' in route.path for route in app.routes)


def test_expiry_cancels_inflight_research_and_releases_admission():
    class Blocking(Model):
        async def chat(self, messages, tools):
            await asyncio.sleep(100)
    async def scenario():
        async with client(model_factory=lambda _: Blocking()) as (c, registry):
            sid, headers = await created(c)
            await confirmed(c, sid, headers)
            await c.post(f'{ROOT}/{sid}/research', headers=headers,
                json={'question': 'recalls', 'categories': ['recalls'], 'model': 'llama3.2:3b'})
            registry.entries[sid].created = time.monotonic() - 601
            assert (await c.get(f'{ROOT}/{sid}/result', headers=headers)).status_code == 410
            assert registry.active == 0 and not registry.entries
    asyncio.run(scenario())


def test_partial_source_failure_keeps_verified_sources():
    class Partial(ResearchBackend):
        async def execute(self, operation, arguments, *, timeout):
            if operation == 'labels_v2':
                raise OSError('private-path-and-internal-error')
            return await super().execute(operation, arguments, timeout=timeout)
    async def scenario():
        async with client(backend=Partial()) as (c, _):
            sid, headers = await created(c)
            await confirmed(c, sid, headers)
            await c.post(f'{ROOT}/{sid}/research', headers=headers,
                json={'question': 'evidence', 'categories': ['labels', 'recalls', 'faers']})
            result = await done(c, sid, headers)
            assert result['state'] == 'partial'
            assert result['briefing']['sections'][0]['status'] == 'failed'
            assert result['briefing']['sections'][1]['evidence']['records']
            assert 'private-path' not in str(result)
    asyncio.run(scenario())


def test_source_timeout_has_stable_code():
    class Slow(ResearchBackend):
        async def execute(self, operation, arguments, *, timeout):
            await asyncio.sleep(10)
    async def scenario():
        async with client(backend=Slow(), limits=replace(Limits(), tool_timeout=.01), max_sessions=1) as (c, registry):
            sid, headers = await created(c)
            result = await c.post(f'{ROOT}/{sid}/resolve', json={'query': 'Xanax'}, headers=headers)
            assert result.status_code == 504 and result.json()['detail']['code'] == 'timeout'
            assert registry.active == 0
            await created(c)  # Closed timeout sessions immediately release registry capacity.
    asyncio.run(scenario())


@pytest.mark.parametrize('environment', ['APP_ENV', 'ENVIRONMENT', 'PYTHON_ENV', 'RENDER'])
def test_other_hosting_markers_cannot_be_overridden(monkeypatch, environment):
    async def scenario():
        async with client() as (c, _):
            sid, headers = await created(c)
            monkeypatch.setenv(environment, 'true' if environment == 'RENDER' else 'production')
            monkeypatch.setenv('DAVAI_ENABLE_LOCAL_RESEARCH', '1')
            assert (await c.get(f'{ROOT}/{sid}/result', headers=headers)).status_code == 403
    asyncio.run(scenario())


def test_absent_origin_and_non_loopback_peers_are_denied():
    async def scenario():
        async with client() as (c, _):
            c.headers.pop('origin')
            assert (await c.post(ROOT, json={}, headers=auth(PAIRING))).status_code == 403
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', 0))
            app = create_app(listener, PAIRING)
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app, client=('192.0.2.1', 5555)),
                    base_url=f'http://127.0.0.1:{listener.getsockname()[1]}') as c:
                assert (await c.post(ROOT, json={}, headers={**auth(PAIRING), 'Origin': ORIGIN})).status_code == 403
        with socket.socket() as listener:
            with pytest.raises(ValueError):
                create_app(listener, PAIRING)
    asyncio.run(scenario())


def test_generated_frontend_contracts_match_serialization_schema():
    from pathlib import Path
    from app.local_research.export_types import generate
    root = Path(__file__).resolve().parents[3]
    assert (root / 'frontend/src/research/contracts.ts').read_text() == generate()


def test_slow_request_body_is_bounded_before_validation():
    async def body():
        yield b'{'
        await asyncio.sleep(6)
        yield b'}'
    async def scenario():
        async with client() as (c, registry):
            response = await c.post(ROOT, content=body(), headers=auth(PAIRING))
            assert response.status_code == 408
            assert response.json()['detail']['code'] == 'request_timeout'
            assert not registry.entries and registry.active == 0
    asyncio.run(scenario())
