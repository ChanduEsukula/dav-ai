import asyncio
from dataclasses import replace

import httpx
import pytest

from app.agent.backend import ProcessBackend
from app.agent.contracts import AgentRejected, Limits
from app.agent.model import OllamaClient


@pytest.mark.parametrize("response, expected", [
    (httpx.Response(200, content=b'{"done":true}'), None),
    (httpx.Response(302, headers={"Location": "https://example.com"}), "model_unavailable"),
    (httpx.Response(500, content=b'private exception'), "model_unavailable"),
    (httpx.Response(200, content=b'{"x":1,"x":2}'), "invalid_json"),
    (httpx.Response(200, content=b'x' * 101), "response_too_large"),
])
def test_ollama_transport_is_bounded_and_loopback_only(monkeypatch, response, expected):
    calls = []
    def handle(request):
        calls.append(request)
        return response
    original = httpx.AsyncClient
    def client(**kwargs):
        assert kwargs["trust_env"] is False and kwargs["follow_redirects"] is False
        return original(**kwargs, transport=httpx.MockTransport(handle))
    monkeypatch.setattr(httpx, "AsyncClient", client)
    async def scenario():
        model = OllamaClient(limits=replace(Limits(), max_response_bytes=100))
        if expected:
            with pytest.raises(AgentRejected, match=expected):
                await model.chat([], [])
        else:
            assert await model.chat([], []) == {"done": True}
    asyncio.run(scenario())
    assert len(calls) == 1
    assert str(calls[0].url) == "http://127.0.0.1:11434/api/chat"
    assert calls[0].method == "POST"


def test_unknown_model_and_endpoint_are_not_called():
    with pytest.raises(ValueError):
        OllamaClient("a-paid-cloud-model")
    with pytest.raises(AgentRejected, match="forbidden_model_endpoint"):
        asyncio.run(OllamaClient().request("/api/pull", {}))


def test_real_worker_invalid_query_and_hosted_denial(monkeypatch):
    backend = ProcessBackend()
    result = asyncio.run(backend.execute("resolve", {"query": ""}, timeout=10))
    assert result["status"] == "invalid_query"
    monkeypatch.setenv("DAVAI_ENV", "production")
    with pytest.raises(AgentRejected, match="evidence_unavailable"):
        asyncio.run(backend.execute("resolve", {"query": "Xanax"}, timeout=10))


def test_subprocess_is_killed_and_reaped_after_timeout(monkeypatch):
    class Process:
        returncode = None
        killed = False
        reaped = False
        async def communicate(self, data):
            await asyncio.sleep(10)
        def kill(self):
            self.killed = True
        async def wait(self):
            self.reaped = True
            self.returncode = -9
    process = Process()
    async def create(*args, **kwargs):
        assert args[1:3] == ("-m", "app.agent.worker")
        return process
    monkeypatch.setattr(asyncio, "create_subprocess_exec", create)
    with pytest.raises(TimeoutError):
        asyncio.run(ProcessBackend().execute("resolve", {"query": "Xanax"}, timeout=.01))
    assert process.killed and process.reaped


def test_synthesis_uses_local_json_schema_without_tools(monkeypatch):
    from app.agent.synthesis import Selection
    calls=[]
    async def request(self,path,payload):
        calls.append((path,payload));return {'done':True}
    monkeypatch.setattr(OllamaClient,'request',request)
    assert asyncio.run(OllamaClient().synthesize([{'role':'user','content':'bounded'}]))=={'done':True}
    path,payload=calls[0]
    assert path=='/api/chat' and payload['format']==Selection.model_json_schema()
    assert 'tools' not in payload and payload['stream'] is False
    assert payload['options']['temperature']==0 and payload['options']['seed']==7
