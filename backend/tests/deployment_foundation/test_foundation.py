"""Health-only boundary, never a pharmaceutical/agent server or auth replacement."""
import asyncio
import json
import sys

import httpx
import pytest

from deployment.foundation.app import ConfigurationError, FoundationApplication, validate_environment

VALID = {"DAVAI_ENV": "staging", "DAVAI_FOUNDATION_MODE": "deny", "PORT": "8080"}


@pytest.mark.parametrize("mode", ["staging", "production"])
@pytest.mark.parametrize("path", ["/", "/ready", "/api/drugs/search?q=Xanax", "/api/local/research/sessions",
                                 "/api/local/research/sessions/opaque/research", "/api/jobs/batch", "/openapi.json"])
def test_all_business_routes_deny_in_hosted_modes(mode, path):
    async def scenario():
        app = FoundationApplication({**VALID, "DAVAI_ENV": mode, "PUBLICATION_VALIDATED": "true"})
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="https://foundation.invalid") as client:
            for method in ("GET", "POST", "OPTIONS"):
                response = await client.request(method, path, content=b'{"owner_id":"fake","enable":true}')
                assert response.status_code == 503
                assert response.json()["code"] == "serving_not_authorized"
                assert response.json()["pharmaceutical_serving"] is False
                assert response.headers["cache-control"] == "no-store"
                assert "access-control-allow-origin" not in response.headers
    asyncio.run(scenario())


def test_health_is_not_readiness_or_authorization():
    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=FoundationApplication(VALID)), base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200 and response.json()["research_jobs"] is False
            assert (await client.head("/health")).content == b""
            assert (await client.get("/ready")).status_code == 503
    asyncio.run(scenario())


@pytest.mark.parametrize("changes", [
    {"DAVAI_ENV": "local"}, {"DAVAI_ENV": ""}, {"DAVAI_FOUNDATION_MODE": "serve"},
    {"DAVAI_FOUNDATION_MODE": "demo"}, {"DAV_AI_PHARMA_RELEASE_DB": "/tmp/snapshot.sqlite"},
    {"DAV_AI_PHARMA_ARTIFACT_ROOT": ""}, {"DATABASE_URL": "sensitive"},
    {"GOOGLE_APPLICATION_CREDENTIALS": "/tmp/key.json"}, {"OLLAMA_HOST": "http://model"},
    {"APP_ENV": "local"}, {"PORT": "80"}, {"PORT": "8080;command"}, {"PORT": "99999"},
])
def test_invalid_or_data_bearing_environment_fails_closed(changes):
    with pytest.raises(ConfigurationError):
        validate_environment({**VALID, **changes})
    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=FoundationApplication({**VALID, **changes})), base_url="http://test") as client:
            assert (await client.get("/health")).status_code == 503
    asyncio.run(scenario())


def test_lifespan_rejects_missing_hosted_configuration():
    async def scenario():
        sent = []
        async def receive():
            return {"type": "lifespan.startup"}
        async def send(event):
            sent.append(event)
        await FoundationApplication({})( {"type": "lifespan"}, receive, send)
        assert sent == [{"type": "lifespan.startup.failed", "message": "Invalid deny-only foundation configuration"}]
    asyncio.run(scenario())


def test_logs_discard_attacker_controlled_text_and_credentials(capsys):
    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=FoundationApplication(VALID)), base_url="http://test") as client:
            await client.post("/api/secret-path?prompt=private-question", content=b'private-body', headers={
                "Authorization": "Bearer private-capability", "Cookie": "private-cookie", "X-Request-ID": "private-id\tforged"})
    asyncio.run(scenario())
    output = capsys.readouterr().out
    assert not any(secret in output for secret in ("secret-path", "private-question", "private-body", "private-capability", "private-cookie", "private-id"))
    event = json.loads(output)
    assert set(event) == {"severity", "event", "request_id", "route_class", "status", "duration_ms"}
    assert event["route_class"] == "denied" and len(event["request_id"]) == 32


def test_denied_request_body_is_never_consumed():
    async def scenario():
        sent = []
        async def receive():
            raise AssertionError("Deny-only endpoints must not consume untrusted request bodies")
        async def send(event):
            sent.append(event)
        await FoundationApplication(VALID)({"type": "http", "method": "POST", "path": "/api/jobs"}, receive, send)
        assert sent[0]["status"] == 503
    asyncio.run(scenario())


def test_foundation_import_does_not_load_application_or_agent():
    # Isolated interpreter avoids unrelated tests' imported modules.
    import subprocess
    result = subprocess.run([sys.executable, "-c", "import sys; import deployment.foundation.app; assert not any(m in sys.modules for m in ['app.main', 'app.local_research.api', 'app.agent.workflow', 'sqlite3'])"], capture_output=True)
    assert result.returncode == 0


@pytest.mark.parametrize("mode", ["staging", "production"])
def test_original_frozen_connection_guard_still_denies(monkeypatch, mode):
    from app.db.pharma.release_connection import PharmaceuticalReleaseUnavailable, connect_release
    monkeypatch.setenv("DAVAI_ENV", mode)
    monkeypatch.setenv("DAVAI_FOUNDATION_MODE", "deny")
    monkeypatch.setenv("PUBLICATION_VALIDATED", "true")
    with pytest.raises(PharmaceuticalReleaseUnavailable, match="not authorized"):
        connect_release()
