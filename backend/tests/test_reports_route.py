from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.reports import SafetyIntelligenceReportRequest
from app.services.report_pdf import build_safety_intelligence_pdf


client = TestClient(app)


def report_payload(module: str = "both", query: str = "metformin") -> dict:
    return {
        "prepared_for": "Demo reviewer",
        "organization": "DAV AI Portfolio",
        "role": "student_researcher",
        "query": query,
        "module": module,
        "purpose": "Demo report",
    }


def foodradar_result_payload() -> dict:
    return {
        "module": "FoodRadar",
        "query": "protein powder",
        "count": 1,
        "source_name": "FoodRadar multi-source search",
        "endpoint": "openFDA Food Enforcement + USDA FSIS Recall API",
        "retrieval_timestamp": "2026-06-08T00:00:00+00:00",
        "search_strategy_used": "normalized_keyword",
        "public_data_disclaimer": (
            "Public recall data only. No matching public records found does not mean the product is safe."
        ),
        "limitations": [
            "No matching public records found does not mean the product is safe.",
            "Verify exact product, package, lot code, and official notice.",
        ],
        "audit": {"audit_id": "audit-foodradar-1"},
        "sources_checked": [
            {
                "source_id": "openfda_food_enforcement",
                "source_name": "openFDA Food Enforcement",
                "source_type": "FDA_FOOD_ENFORCEMENT",
                "endpoint": "https://api.fda.gov/food/enforcement.json",
                "upstream_status": "ok",
                "record_count": 1,
            }
        ],
        "results": [
            {
                "product_description": "Demo protein powder",
                "classification": "Class II",
                "status": "Ongoing",
                "recalling_firm": "Demo Foods",
                "recall_initiation_date": "20260601",
                "reason_for_recall": "Undeclared allergen",
                "risk_score": {
                    "score": 72,
                    "label": "Elevated",
                    "score_version": "recall-review-priority-v0.2",
                },
            }
        ],
    }


def cosmetic_signal_result_payload() -> dict:
    return {
        "module": "CosmeticSignal",
        "query": "sunscreen",
        "count": 1,
        "source_name": "openFDA Cosmetic Event",
        "endpoint": "https://api.fda.gov/cosmetic/event.json",
        "audit": {"audit_id": "audit-cosmeticsignal-1"},
        "signal_score": {
            "score": 41,
            "label": "Moderate",
            "review_priority": "Monitor",
            "data_confidence": "Public reports only",
            "score_version": "cosmetic-signal-score-v0.1",
        },
        "results": [
            {
                "product_description": "Demo sunscreen",
                "brand_name": "Demo Beauty",
                "report_date": "20260601",
                "event": "rash",
                "outcome": "reported",
                "source": "openFDA",
            }
        ],
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

    def fake_build_pdf(
        request,
        recall_result,
        drug_signal_result,
        everyday_safety_result=None,
        cosmetic_signal_result=None,
    ):
        assert request.query == "metformin"
        assert recall_result == {"module": "RecallRadar", "query": "metformin"}
        assert drug_signal_result == {"module": "DrugSignal", "query": "metformin"}
        assert everyday_safety_result is None
        assert cosmetic_signal_result is None
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
        'attachment; filename="dav-ai-public-data-report-metformin.pdf"'
    )
    assert response.content.startswith(b"%PDF-1.4")


def test_create_foodradar_safety_intelligence_report_returns_pdf(monkeypatch):
    async def fake_everyday_safety_search(
        category: str,
        query: str,
        limit: int,
        request_id: str | None = None,
    ):
        assert category == "food_supplement"
        assert query == "protein powder"
        assert limit == 5
        assert request_id is not None
        return foodradar_result_payload()

    def fake_build_pdf(
        request,
        recall_result,
        drug_signal_result,
        everyday_safety_result=None,
        cosmetic_signal_result=None,
    ):
        assert request.query == "protein powder"
        assert request.module == "foodradar"
        assert recall_result is None
        assert drug_signal_result is None
        assert everyday_safety_result is not None
        assert everyday_safety_result["module"] == "FoodRadar"
        assert cosmetic_signal_result is None
        assert "does not mean the product is safe" in everyday_safety_result["public_data_disclaimer"]
        return b"%PDF-1.4\nDAV AI FoodRadar report\n%%EOF"

    monkeypatch.setattr(
        "app.routes.reports.execute_everyday_safety_search",
        fake_everyday_safety_search,
    )
    monkeypatch.setattr("app.routes.reports.build_safety_intelligence_pdf", fake_build_pdf)

    response = client.post(
        "/api/v1/reports/safety-intelligence",
        json=report_payload(module="foodradar", query="protein powder"),
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"] == (
        'attachment; filename="dav-ai-public-data-report-protein-powder.pdf"'
    )
    assert response.content.startswith(b"%PDF-1.4")


def test_create_cosmeticsignal_safety_intelligence_report_returns_pdf(monkeypatch):
    async def fake_cosmetic_signal_search(
        query: str,
        limit: int,
        request_id: str | None = None,
    ):
        assert query == "sunscreen"
        assert limit == 10
        assert request_id is not None
        return cosmetic_signal_result_payload()

    def fake_build_pdf(
        request,
        recall_result,
        drug_signal_result,
        everyday_safety_result=None,
        cosmetic_signal_result=None,
    ):
        assert request.query == "sunscreen"
        assert request.module == "cosmeticsignal"
        assert recall_result is None
        assert drug_signal_result is None
        assert everyday_safety_result is None
        assert cosmetic_signal_result is not None
        assert cosmetic_signal_result["module"] == "CosmeticSignal"
        return b"%PDF-1.4\nDAV AI CosmeticSignal report\n%%EOF"

    monkeypatch.setattr(
        "app.routes.reports.execute_cosmetic_signal_search",
        fake_cosmetic_signal_search,
    )
    monkeypatch.setattr("app.routes.reports.build_safety_intelligence_pdf", fake_build_pdf)

    response = client.post(
        "/api/v1/reports/safety-intelligence",
        json=report_payload(module="cosmeticsignal", query="sunscreen"),
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"] == (
        'attachment; filename="dav-ai-public-data-report-sunscreen.pdf"'
    )
    assert response.content.startswith(b"%PDF-1.4")


def test_foodradar_pdf_uses_food_specific_safety_boundary():
    report_pdf_path = Path(__file__).resolve().parents[1] / "app/services/report_pdf.py"
    report_pdf_source = report_pdf_path.read_text()

    assert "FOODRADAR_DISCLAIMER" in report_pdf_source
    assert "Food and supplement recall records do not prove" in report_pdf_source
    assert "FAERS reports " in report_pdf_source
    assert "do not prove causation" in report_pdf_source
    assert report_pdf_source.count("disclaimer=FOODRADAR_DISCLAIMER") == 2


def test_cosmeticsignal_pdf_uses_cosmetic_specific_safety_boundary():
    report_pdf_path = Path(__file__).resolve().parents[1] / "app/services/report_pdf.py"
    report_pdf_source = report_pdf_path.read_text()

    assert "COSMETICSIGNAL_DISCLAIMER" in report_pdf_source
    assert "cosmetic adverse-event report data" in report_pdf_source
    assert "do not prove product danger" in report_pdf_source
    assert "disclaimer=COSMETICSIGNAL_DISCLAIMER" in report_pdf_source


def test_build_foodradar_safety_intelligence_pdf_returns_valid_pdf_bytes():
    request = SafetyIntelligenceReportRequest(
        prepared_for="Demo reviewer",
        organization="DAV AI Portfolio",
        role="student_researcher",
        query="protein powder",
        module="foodradar",
        purpose="PDF builder regression test",
    )

    pdf_bytes = build_safety_intelligence_pdf(
        request=request,
        everyday_safety_result=foodradar_result_payload(),
    )

    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 1000
    assert b"%%EOF" in pdf_bytes


def test_build_cosmeticsignal_safety_intelligence_pdf_returns_valid_pdf_bytes():
    request = SafetyIntelligenceReportRequest(
        prepared_for="Demo reviewer",
        organization="DAV AI Portfolio",
        role="student_researcher",
        query="sunscreen",
        module="cosmeticsignal",
        purpose="PDF builder regression test",
    )

    pdf_bytes = build_safety_intelligence_pdf(
        request=request,
        cosmetic_signal_result=cosmetic_signal_result_payload(),
    )

    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 1000
    assert b"%%EOF" in pdf_bytes


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
