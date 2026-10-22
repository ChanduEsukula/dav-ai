"""API/PDF contract, privacy, release-gate, and real-release journey regressions."""
from io import BytesIO
import json
from pathlib import Path
import sqlite3
from urllib.parse import quote

from fastapi.testclient import TestClient
from pypdf import PdfReader
import pytest

from app.main import app
from app.routes import reports
from app.schemas.reports import PharmaceuticalReportRequest
from app.services.report_pdf import build_pharmaceutical_pdf
from app.db.pharma import release_connection as release
from app.services.pharma.evidence import official_source

CLIENT = TestClient(app)
URL = "/api/v1/reports/pharmaceutical"
ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def evidence():
    return json.loads((ROOT / "frontend/src/test/evidence.json").read_text())


@pytest.fixture(autouse=True)
def reset_limiter():
    reports._attempts.clear()
    yield
    reports._attempts.clear()


def extract(data):
    return "\n".join(page.extract_text() for page in PdfReader(BytesIO(data)).pages)


def test_pdf_shared_evidence_content_and_private_headers(evidence, monkeypatch, caplog):
    seen = []
    monkeypatch.setattr(reports, "drug_evidence", lambda product: seen.append(product) or evidence)
    response = CLIENT.post(URL, json={"product_id": evidence["drug"]["id"], "name": "Reader <b>Example</b> & Co", "age": 42})
    assert response.status_code == 200
    assert response.content.startswith(b"%PDF")
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"] == 'attachment; filename="dav-ai-evidence-report.pdf"'
    assert "no-store" in response.headers["cache-control"]
    assert response.headers["x-content-type-options"] == "nosniff"
    text = extract(response.content)
    for expected in ["Reader <b>Example</b> & Co", "Age (identification only): 42", evidence["drug"]["product_ndcs"][0],
                     evidence["release"]["release_id"], "Monthly reporting trends", "not product-specific", "never been recalled",
                     str(evidence["adverse_events"]["records"][0]["analytics"]["report_count"]), "Reference URL"]:
        assert expected in text
    assert "Reader" not in caplog.text
    assert "Reader" not in repr(reports._attempts)
    assert seen == [evidence["drug"]["id"]]


@pytest.mark.parametrize("patch", [
    {"name": ""}, {"name": "   "}, {"name": "x" * 101}, {"name": "a\x00b"},
    {"age": -1}, {"age": 121}, {"age": 1.5}, {"age": "42"}, {"age": True},
    {"url": "https://example.com"}, {"path": "/etc/passwd"}, {"product_id": ""},
])
def test_invalid_report_fields_are_rejected_before_evidence_lookup(patch, monkeypatch):
    def forbidden(*args):
        raise AssertionError("Invalid fields must not resolve evidence")
    monkeypatch.setattr(reports, "drug_evidence", forbidden)
    response = CLIENT.post(URL, json={"name": "Reader", "product_id": "drug-id", **patch})
    assert response.status_code == 422
    assert "no-store" in response.headers["cache-control"]


@pytest.mark.parametrize("age", [None, 0, 120])
def test_optional_age_and_bounds(age, evidence):
    request = PharmaceuticalReportRequest(product_id=evidence["drug"]["id"], name="=SUM(1,2)", age=age)
    text = extract(build_pharmaceutical_pdf(request, evidence))
    assert "=SUM(1,2)" in text
    assert ("Age (identification only)" in text) == (age is not None)


def test_missing_source_links_and_analytics_remain_explicit(evidence):
    evidence["drug"]["provenance"]["source_url"] = None
    evidence["release"]["sources"] = []
    evidence["adverse_events"]["records"][0]["analytics"] = None
    text = extract(build_pharmaceutical_pdf(PharmaceuticalReportRequest(product_id="x", name="Reader"), evidence))
    assert "No stored ingredient analytics available" in text
    assert "Identity reference URL: N/A" in text


def test_pdf_linked_recall_content_distinguishes_firm_and_labeler(evidence):
    evidence["recalls"]["records"] = [{"recall_number": "D-EXAMPLE", "recalling_firm": "Recall Firm",
        "reason_for_recall": "Example reason", "classification": "Class II", "report_date": "2024-01-01"}]
    text = extract(build_pharmaceutical_pdf(PharmaceuticalReportRequest(product_id="x", name="Reader"), evidence))
    for value in ["D-EXAMPLE", "Recalling firm: Recall Firm", "Class II", "2024-01-01", "NDC-listed labeler"]:
        assert value in text


def test_unavailable_artifact_unknown_product_and_oversized_evidence(evidence, monkeypatch):
    monkeypatch.setattr(reports, "drug_evidence", lambda _: None)
    assert CLIENT.post(URL, json={"product_id": "missing", "name": "Reader"}).status_code == 404
    def unavailable(_):
        raise release.PharmaceuticalReleaseUnavailable("not mounted")
    monkeypatch.setattr(reports, "drug_evidence", unavailable)
    assert CLIENT.post(URL, json={"product_id": "missing", "name": "Reader"}).status_code == 503
    evidence["recalls"]["records"] = [{}] * 201
    monkeypatch.setattr(reports, "drug_evidence", lambda _: evidence)
    assert CLIENT.post(URL, json={"product_id": "x", "name": "Reader"}).status_code == 413


def test_rate_body_and_concurrency_limits(evidence, monkeypatch):
    monkeypatch.setattr(reports, "drug_evidence", lambda _: evidence)
    # Rate test exercises admission without repeatedly rendering.
    monkeypatch.setattr(reports, "build_pharmaceutical_pdf", lambda *_: b"%PDF-test")
    for _ in range(5):
        assert CLIENT.post(URL, json={"product_id": "x", "name": "Reader"}).status_code == 200
    response = CLIENT.post(URL, json={"product_id": "x", "name": "Reader"})
    assert response.status_code == 429 and response.headers["retry-after"] == "60"
    assert CLIENT.post(URL, content=b"x" * 4097).status_code == 413
    reports._attempts.clear()
    assert reports._slots.acquire(False) and reports._slots.acquire(False)
    try:
        assert CLIENT.post(URL, json={"product_id": "x", "name": "Reader"}).status_code == 429
    finally:
        reports._slots.release(); reports._slots.release()
    assert CLIENT.post(URL, json={"product_id": "x", "name": "Reader"}).status_code == 200


def test_chunked_body_limit():
    response = CLIENT.post(URL, content=iter([b"x" * 2048, b"x" * 2049]))
    assert response.status_code == 413


@pytest.mark.parametrize("env", ["prod", "production", "staging", "preview"])
def test_deployed_environment_denies_all_evidence_and_pdf(env, monkeypatch, evidence):
    monkeypatch.setenv("DAVAI_ENV", env)
    for path in ["/ready", "/api/coverage", "/api/drugs/search?q=Xanax", "/api/drugs/x/evidence", "/api/drugs/x/safety"]:
        assert CLIENT.get(path).status_code == 503
    assert CLIENT.post(URL, json={"product_id": evidence["drug"]["id"], "name": "Reader"}).status_code == 503
    assert CLIENT.get("/health").status_code == 200


def test_missing_incompatible_and_tampered_release_fail_closed(tmp_path, monkeypatch):
    monkeypatch.setenv("DAV_AI_PHARMA_RELEASE_DB", str(tmp_path / "missing.sqlite"))
    assert CLIENT.get("/ready").status_code == 503
    path = tmp_path / "incompatible.sqlite"
    con = sqlite3.connect(path); con.execute("CREATE TABLE products (id TEXT)"); con.close()
    monkeypatch.setenv("DAV_AI_PHARMA_RELEASE_DB", str(path))
    assert CLIENT.get("/ready").status_code == 503
    with pytest.raises(release.PharmaceuticalReleaseUnavailable):
        release._verify_checksum(str(path), path.stat().st_size, path.stat().st_mtime_ns, path.stat().st_ctime_ns)
    assert path.stat().st_size < 20000


def test_removed_routes_are_absent_from_contract():
    paths = app.openapi()["paths"]
    assert len(paths) == 11
    assert not any(any(word in p for word in ("auth", "ask", "monitor", "cosmetic", "assistant", "semaglutide")) for p in paths)
    assert URL in paths


@pytest.mark.parametrize("url", ["http://fda.gov/a", "https://fda.gov.evil.test/", "https://user@fda.gov/a", "file:///etc/passwd", "https://api.fda.gov:8443/a"])
def test_source_url_allowlist(url):
    assert official_source(url) is None


@pytest.mark.release_artifact
def test_real_release_search_to_pdf_without_upstream(monkeypatch):
    if not release.release_database_path().is_file():
        pytest.fail("Required release artifact is not mounted; use -m 'not release_artifact' for source-only checks")
    import httpx
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", lambda *_: pytest.fail("No upstream HTTP"))
    selected = None
    for query in ["Xanax", "alprazolam", "semaglutide", "0004-0259"]:
        response = CLIENT.get("/api/drugs/search", params={"q": query})
        assert response.status_code == 200 and response.json()["results"]
        selected = response.json()["results"][0]
    product_path = "/api/drugs/" + quote(selected["id"], safe="")
    detail = CLIENT.get(product_path)
    assert detail.status_code == 200
    assert detail.json()["provenance"]["source"] == "openfda_ndc_directory"
    evidence = CLIENT.get(product_path + "/evidence")
    assert evidence.status_code == 200
    assert evidence.json()["release"]["publication_authorized"] is False
    response = CLIENT.post(URL, json={"product_id": selected["id"], "name": "Regression Reader"})
    assert response.status_code == 200
    assert selected["product_ndcs"][0] in extract(response.content)
