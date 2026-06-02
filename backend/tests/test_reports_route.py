from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def report_payload(module: str = "both") -> dict:
    return {
        "prepared_for": "Demo reviewer",
        "organization": "DAV AI Portfolio",
        "role": "student_researcher",
        "query": "metformin",
        "module": module,
        "purpose": "Demo report",
    }


def test_create_safety_intelligence_report_returns_pdf(monkeypatch):
    async def fake_recall_search(
        query: str,
        limit: int,
        request_id: str | None = None,
    ):
        assert query == "metformin"
        assert limit == 5
        assert request_id is not None
        return {"module": "RecallRadar", "query": query}

    async def fake_drug_signal_search(
        query: str,
        limit: int,
        request_id: str | None = None,
    ):
        assert query == "metformin"
        assert limit == 5
        assert request_id is not None
        return {"module": "DrugSignal", "query": query}

    def fake_build_pdf(request, recall_result, drug_signal_result):
        assert request.query == "metformin"
        assert recall_result == {"module": "RecallRadar", "query": "metformin"}
        assert drug_signal_result == {"module": "DrugSignal", "query": "metformin"}
        return b"%PDF-1.4\nDAV AI report\n%%EOF"

    monkeypatch.setattr("app.routes.reports.execute_recall_search", fake_recall_search)
    monkeypatch.setattr("app.routes.reports.execute_drug_signal_search", fake_drug_signal_search)
    monkeypatch.setattr("app.routes.reports.build_safety_intelligence_pdf", fake_build_pdf)

    response = client.post(
        "/api/v1/reports/safety-intelligence",
        json=report_payload(),
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"] == (
        'attachment; filename="dav-ai-safety-report-metformin.pdf"'
    )
    assert response.content.startswith(b"%PDF-1.4")


def test_create_safety_intelligence_report_sanitizes_upstream_error(monkeypatch):
    async def fake_recall_search(
        query: str,
        limit: int,
        request_id: str | None = None,
    ):
        raise RuntimeError("openFDA report outage with upstream stack detail")

    monkeypatch.setattr("app.routes.reports.execute_recall_search", fake_recall_search)

    response = client.post(
        "/api/v1/reports/safety-intelligence",
        json=report_payload(module="recallradar"),
    )

    assert response.status_code == 502
    assert response.json()["detail"] == {
        "message": "Unable to retrieve source data for the report.",
        "code": "REPORT_SOURCE_DATA_UNAVAILABLE",
    }
    assert "openFDA report outage" not in response.text
