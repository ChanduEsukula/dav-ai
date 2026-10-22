"""Regressions for verified hardening defects; no original data is modified."""
import asyncio
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sqlite3
from threading import Event

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.routes import reports
from app.services import report_limits
from app.db.pharma import release_connection as release
from scripts import manage_pharma_artifact as manager

URL = "/api/v1/reports/pharmaceutical"


def test_report_redirect_body_limit_and_private_errors(monkeypatch, caplog):
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(URL + "/", content=b"x" * 4097, follow_redirects=False)
    assert response.status_code == 413
    assert "no-store" in response.headers["cache-control"]
    response = client.post(URL + "/", json={"name": "Reader", "product_id": "x"}, follow_redirects=False)
    assert response.status_code == 307 and "no-store" in response.headers["cache-control"]
    reports._attempts.clear()
    def broken(_):
        raise RuntimeError("Private Report Identifier")
    monkeypatch.setattr(reports, "drug_evidence", broken)
    response = client.post(URL, json={"name": "Private Report Identifier", "product_id": "x"})
    assert response.status_code == 500
    assert response.json() == {"detail": "Report generation failed"}
    assert "no-store" in response.headers["cache-control"]
    assert "Private Report Identifier" not in caplog.text
    assert reports._slots.acquire(False) and reports._slots.acquire(False)
    reports._slots.release(); reports._slots.release()


def test_private_outer_boundary_covers_unhandled_application_error():
    async def failing(scope, receive, send):
        from starlette.responses import Response
        await Response("Internal Server Error", status_code=500)(scope, receive, send)
    client = TestClient(report_limits.ReportPrivacyMiddleware(failing))
    response = client.post(URL)
    assert response.status_code == 500 and "no-store" in response.headers["cache-control"]


def test_validation_does_not_reflect_personal_fields_or_accept_query_fields():
    client = TestClient(app)
    response = client.post(URL, json={"product_id": "x", "name": "Sensitive Example", "age": 999})
    assert response.status_code == 422
    assert "Sensitive Example" not in response.text and "999" not in response.text
    response = client.post(URL + "?name=SensitiveExample", json={"product_id": "x", "name": "Reader"})
    assert response.status_code == 400 and "no-store" in response.headers["cache-control"]


def test_body_timeout_oversized_chunk_and_single_delivery(monkeypatch):
    monkeypatch.setattr(report_limits, "BODY_TIMEOUT_SECONDS", 0.01)
    async def run():
        messages = []
        scope = {"type": "http", "method": "POST", "path": URL, "headers": []}
        async def send(m): messages.append(m)
        async def slow():
            await asyncio.sleep(1)
        async def forbidden(*_): raise AssertionError("Must reject before app")
        await report_limits.ReportPrivacyMiddleware(forbidden)(scope, slow, send)
        assert messages[0]["status"] == 408
        messages.clear()
        async def oversized(): return {"type": "http.request", "body": b"x" * 4097}
        await report_limits.ReportPrivacyMiddleware(forbidden)(scope, oversized, send)
        assert messages[0]["status"] == 413
        delivered = 0
        async def receive():
            nonlocal delivered
            delivered += 1
            return {"type": "http.request", "body": b"{}"} if delivered == 1 else {"type": "http.disconnect"}
        async def consumer(scope, receive, send):
            assert (await receive())["body"] == b"{}"
            assert (await receive())["type"] == "http.disconnect"
        await report_limits.ReportPrivacyMiddleware(consumer)(scope, receive, send)
    asyncio.run(run())


def test_cors_and_request_id_bounds():
    client = TestClient(app)
    response = client.get("/health", headers={"X-Request-ID": "x" * 200})
    assert len(response.headers["x-request-id"]) == 36
    response = client.options(URL, headers={"Origin": "https://untrusted.example", "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in response.headers


def compatible_db(path):
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE products (id TEXT)")
    con.execute("CREATE TABLE release_manifest(release_id,contract_id,policy_version,build_version)")
    con.execute("INSERT INTO release_manifest VALUES (?,?,?,?)", (
        'dav-ai-pharma-v1-phase4b-communications-20261006', 'dav-ai-pharma-release-v1', '1.0.0', 'fixture'))
    con.execute("PRAGMA user_version=4")
    con.commit();con.close()


def test_replacement_between_verification_and_open_is_rejected_and_closed(tmp_path, monkeypatch):
    original = tmp_path / 'db.sqlite';replacement = tmp_path / 'new.sqlite'
    compatible_db(original);compatible_db(replacement)
    monkeypatch.setenv("DAV_AI_PHARMA_RELEASE_DB", str(original))
    monkeypatch.setattr(release, "REQUIRED_TABLES", {'products','release_manifest'})
    monkeypatch.setattr(release, "EXPECTED_BYTES", original.stat().st_size)
    opened = []
    connect = release.sqlite3.connect
    def racing(*args, **kwargs):
        con = connect(*args, **kwargs)
        opened.append(con)
        replacement.replace(original)
        return con
    monkeypatch.setattr(release, "_verify_checksum", lambda *_: None)
    monkeypatch.setattr(release.sqlite3, "connect", racing)
    with pytest.raises(release.PharmaceuticalReleaseUnavailable):release.connect_release()
    with pytest.raises(sqlite3.ProgrammingError):opened[0].execute("SELECT 1")


def test_cold_verification_is_serialized_and_warm_access_does_not_rehash(tmp_path, monkeypatch):
    path = tmp_path / 'db.sqlite';compatible_db(path)
    monkeypatch.setenv("DAV_AI_PHARMA_RELEASE_DB", str(path))
    monkeypatch.setattr(release, "REQUIRED_TABLES", {'products','release_manifest'})
    monkeypatch.setattr(release, "EXPECTED_BYTES", path.stat().st_size)
    from functools import lru_cache
    calls = []
    @lru_cache(maxsize=4)
    def verify(*args):
        import time
        calls.append(args);time.sleep(.02)
    monkeypatch.setattr(release, "_verify_checksum", verify)
    def read(_):
        with closing(release.connect_release()) as con:assert con.execute('SELECT 1').fetchone()[0] == 1
    with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(read, range(4)))
    read(None)
    assert len(calls) == 1


def test_unsupported_schema_and_missing_formulations_fail(tmp_path):
    path=tmp_path/'db.sqlite';compatible_db(path)
    with closing(sqlite3.connect(path)) as con:
        con.row_factory=sqlite3.Row
        with pytest.raises(release.PharmaceuticalReleaseUnavailable):release._validate_release(con)
    assert 'formulations' in release.REQUIRED_TABLES


def test_offline_selection_rollback_failure_and_publication_denial(tmp_path, monkeypatch):
    db1=tmp_path/'one.sqlite';db1.write_bytes(b'one');db1.chmod(0o444)
    db2=tmp_path/'two.sqlite';db2.write_bytes(b'two');db2.chmod(0o444)
    def verification(path):
        import hashlib
        return {"database_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"publication_validated":False}
    monkeypatch.setattr(manager,'verify_artifact',verification)
    root=tmp_path/'registry'
    first=manager.prepare(db1,root);second=manager.prepare(db2,root)
    assert manager.select(root,first)['active']==first
    assert manager.select(root,second)['previous']==first
    assert manager.select(root,rollback=True)['active']==first
    before=(root/'active.json').read_bytes()
    db2.chmod(0o644);db2.write_bytes(b'corrupt');db2.chmod(0o444)
    with pytest.raises(ValueError):manager.select(root,second)
    assert (root/'active.json').read_bytes()==before
    assert json.loads(before)['publication_authorized'] is False
    with pytest.raises(ValueError):manager.select(root,'../../bad')
    # Even a successfully verified offline candidate cannot bypass the deployed guard.
    monkeypatch.setenv('DAVAI_ENV','production')
    with pytest.raises(release.PharmaceuticalReleaseUnavailable):release.connect_release()


def test_failed_atomic_selection_preserves_pointer(tmp_path, monkeypatch):
    state=tmp_path/'active.json';state.write_text('{"active":"original"}')
    previous=state.read_bytes()
    def failed(*_):raise OSError('simulated interrupted publication')
    monkeypatch.setattr(manager.os,'replace',failed)
    with pytest.raises(OSError):manager.atomic_json(state,{'active':'new'})
    assert state.read_bytes()==previous
    assert not list(tmp_path.glob('.pending-*'))


def test_pdf_output_limit_is_enforced_before_buffer_allocation(monkeypatch):
    from app.services import report_pdf
    monkeypatch.setattr(report_pdf, 'MAX_PDF_BYTES', 10)
    output=report_pdf.LimitedPDFBuffer()
    output.write(b'12345')
    with pytest.raises(ValueError):output.write(b'123456')
    assert output.getvalue()==b'12345'


def test_required_release_gate_rejects_skips_and_empty_selection():
    from types import SimpleNamespace
    from backend.tests import conftest as gates
    reporter=SimpleNamespace(stats={'passed':[], 'skipped':[SimpleNamespace(nodeid='critical')]}, write_line=lambda *a,**k:None)
    config=SimpleNamespace(getoption=lambda _:True, pluginmanager=SimpleNamespace(getplugin=lambda _:reporter),
                           _release_integration_nodes={'critical'})
    session=SimpleNamespace(config=config,exitstatus=0)
    gates.pytest_sessionfinish(session,0)
    assert session.exitstatus==1
    # A passed call followed by a skipped teardown must not qualify either.
    reporter.stats['passed']=[SimpleNamespace(nodeid='critical',when='call')]
    session.exitstatus=0
    gates.pytest_sessionfinish(session,0)
    assert session.exitstatus==1
    with pytest.raises(pytest.UsageError):gates.pytest_collection_modifyitems(config,[])


def test_required_release_gate_accepts_only_completed_critical_checks():
    from types import SimpleNamespace
    from backend.tests import conftest as gates
    reporter=SimpleNamespace(stats={'passed':[SimpleNamespace(nodeid='critical',when='call')]}, write_line=lambda *a,**k:None)
    config=SimpleNamespace(getoption=lambda _:True, pluginmanager=SimpleNamespace(getplugin=lambda _:reporter),
                           _release_integration_nodes={'critical'})
    session=SimpleNamespace(config=config,exitstatus=0)
    gates.pytest_sessionfinish(session,0)
    assert session.exitstatus==0
