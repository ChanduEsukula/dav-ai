from fastapi.testclient import TestClient

from app.main import app
from app.services.llm_provider import LLMProviderResponse


class SafeFakeProvider:
    async def generate_answer(self, *, system_prompt: str, user_prompt: str) -> LLMProviderResponse:
        return LLMProviderResponse(
            text="DAV AI found public-data context to review. Verify the source details and limitations.",
            provider="fake",
            model="safe-test-model",
        )


class UnsafeFakeProvider:
    async def generate_answer(self, *, system_prompt: str, user_prompt: str) -> LLMProviderResponse:
        return LLMProviderResponse(
            text="You should stop taking this medication because it is safe for you to do so.",
            provider="fake",
            model="unsafe-test-model",
        )


def recall_payload(question: str = "Explain these results") -> dict:
    return {
        "module": "recall",
        "question": question,
        "page_context": {
            "query": "eye drops",
            "count": 1,
            "source_name": "openFDA Drug Enforcement API",
            "endpoint": "https://api.fda.gov/drug/enforcement.json",
            "retrieval_timestamp": "2026-06-02T18:00:00Z",
            "audit_id": "audit-recall-1",
            "limitations": ["Public recall data only. Not medical advice."],
            "recall": {
                "top_results": [
                    {
                        "recall_number": "D-1234-2026",
                        "product_description": "Example Eye Drops",
                        "reason_for_recall": "Lack of assurance of sterility",
                        "classification": "Class II",
                        "status": "Ongoing",
                        "recall_initiation_date": "20260601",
                        "distribution_pattern": "Nationwide",
                        "recalling_firm": "Example Firm",
                        "risk_score_label": "High",
                        "risk_score_value": 82,
                    }
                ]
            },
        },
    }


def drug_payload(question: str = "Explain these reports") -> dict:
    return {
        "module": "drug_event",
        "question": question,
        "page_context": {
            "query": "metformin",
            "count": 2,
            "source_name": "openFDA Drug Event API",
            "endpoint": "https://api.fda.gov/drug/event.json",
            "retrieval_timestamp": "2026-06-02T18:00:00Z",
            "audit_id": "audit-drug-1",
            "limitations": ["Public-data safety intelligence only. Not medical advice."],
            "drug_event": {
                "intelligence_score": {
                    "score": 67,
                    "label": "High",
                    "review_priority": "Review",
                    "data_confidence": "Moderate",
                },
                "top_reactions": [
                    {
                        "reaction": "Gait disturbance",
                        "count": 2,
                    }
                ],
                "reaction_categories": [
                    {
                        "category": "Neurological",
                        "count": 2,
                        "reactions": ["Gait disturbance"],
                    }
                ],
                "faers_disclaimer": "FAERS adverse-event reports do not prove causation.",
            },
        },
    }


def public_safety_payload(question: str = "Explain these public safety results") -> dict:
    return {
        "module": "public_safety",
        "question": question,
        "page_context": {
            "query": "air fryer",
            "count": 1,
            "source_name": "DavAI Public Safety Search",
            "endpoint": "/api/v1/real-world-safety/search",
            "retrieval_timestamp": "2026-06-02T18:00:00Z",
            "audit_id": "audit-public-safety-1",
            "limitations": [
                "Public data only. Verify exact product identifiers with the official source."
            ],
            "public_safety": {
                "summary": {
                    "query_type": "consumer_product",
                    "recall_or_enforcement_found": True,
                    "reference_or_label_found": False,
                    "signal_report_found": False,
                    "plain_language_summary": "An official public safety record matched this search.",
                    "suggested_next_steps": [
                        "Verify the exact model and recall number.",
                        "Open the official source record.",
                    ],
                    "caveat": "No result or partial result is not a safety guarantee.",
                },
                "identifier_check": {
                    "user_message": "Verify model, lot, UPC, NDC, UDI, VIN, or recall number when available.",
                    "detected": [],
                    "to_verify": [
                        {
                            "type": "model",
                            "label": "Model number",
                            "value": "AF-100",
                            "source": "public safety result",
                            "reason": "Model numbers determine whether a specific unit is affected.",
                        }
                    ],
                },
                "sources_checked": [
                    {
                        "source_id": "cpsc_recalls",
                        "source_name": "CPSC Recalls",
                        "source_type": "consumer_product_recall",
                        "source_kind": "structured_api",
                        "upstream_status": "ok",
                        "record_count": 1,
                    }
                ],
                "sources_failed": [],
                "top_records": [
                    {
                        "title": "Example Air Fryer Recall",
                        "product_name": "Example Air Fryer",
                        "brand_name": "ExampleBrand",
                        "company_name": "Example Company",
                        "source_name": "CPSC Recalls",
                        "source_type": "consumer_product_recall",
                        "source_kind": "structured_api",
                        "category": "consumer_product",
                        "reason": "Fire and burn hazard",
                        "hazard_type": "fire",
                        "remedy": "Stop use and contact firm for remedy.",
                        "published_date": "2026-06-01",
                        "recall_number": "26-123",
                        "affected_models": ["AF-100"],
                        "affected_lots": [],
                        "record_url": "https://www.cpsc.gov/example",
                        "extraction_confidence": None,
                        "source_text_excerpt": "Example official recall excerpt.",
                    }
                ],
            },
        },
    }


def test_assistant_returns_safe_recall_answer(monkeypatch):
    monkeypatch.setattr(
        "app.services.assistant_service.get_assistant_provider",
        lambda: SafeFakeProvider(),
    )

    client = TestClient(app)
    response = client.post("/api/v1/assistant/chat", json=recall_payload())

    assert response.status_code == 200

    body = response.json()
    assert body["refused"] is False
    assert body["model_info"] == {"provider": "fake", "model": "safe-test-model"}
    assert "audit-recall-1" in str(body["source_citations"])
    assert "Example Eye Drops" in " ".join(body["bullets"])
    assert "Not medical advice" in " ".join(body["limitations"])


def test_assistant_returns_safe_drugsignal_answer(monkeypatch):
    monkeypatch.setattr(
        "app.services.assistant_service.get_assistant_provider",
        lambda: SafeFakeProvider(),
    )

    client = TestClient(app)
    response = client.post("/api/v1/assistant/chat", json=drug_payload("What does FAERS not prove?"))

    assert response.status_code == 200

    body = response.json()
    assert body["refused"] is False
    assert "audit-drug-1" in str(body["source_citations"])
    assert "Gait disturbance" in " ".join(body["bullets"])
    assert "do not prove causation" in " ".join(body["limitations"])



def test_assistant_returns_safe_public_safety_answer(monkeypatch):
    monkeypatch.setattr(
        "app.services.assistant_service.get_assistant_provider",
        lambda: SafeFakeProvider(),
    )

    client = TestClient(app)
    response = client.post("/api/v1/assistant/chat", json=public_safety_payload())

    assert response.status_code == 200

    body = response.json()
    assert body["refused"] is False
    assert body["model_info"] == {"provider": "fake", "model": "safe-test-model"}
    assert "audit-public-safety-1" in str(body["source_citations"])
    assert "Example Air Fryer Recall" in " ".join(body["bullets"])
    assert "not medical advice" in " ".join(body["limitations"]).lower()
    assert "safety guarantee" in " ".join(body["limitations"]).lower()

def test_assistant_refuses_medication_guidance(monkeypatch):
    def fail_if_called():
        raise AssertionError("LLM provider should not be called for unsafe questions.")

    monkeypatch.setattr("app.services.assistant_service.get_assistant_provider", fail_if_called)

    client = TestClient(app)
    response = client.post(
        "/api/v1/assistant/chat",
        json=drug_payload("Should I stop taking metformin?"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["refused"] is True
    assert body["refusal_reason"] == "medication guidance"
    assert "cannot provide medical advice" in body["answer"]


def test_assistant_refuses_safe_for_me_question(monkeypatch):
    monkeypatch.setattr(
        "app.services.assistant_service.get_assistant_provider",
        lambda: SafeFakeProvider(),
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/assistant/chat",
        json=recall_payload("Is this bottle safe for me?"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["refused"] is True
    assert body["refusal_reason"] == "personal safety assessment"


def test_assistant_refuses_personal_causation_question(monkeypatch):
    monkeypatch.setattr(
        "app.services.assistant_service.get_assistant_provider",
        lambda: SafeFakeProvider(),
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/assistant/chat",
        json=drug_payload("Did metformin cause my symptom?"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["refused"] is True
    assert body["refusal_reason"] == "personal causation claim"


def test_assistant_rejects_invalid_module():
    payload = recall_payload()
    payload["module"] = "regional_health"

    client = TestClient(app)
    response = client.post("/api/v1/assistant/chat", json=payload)

    assert response.status_code == 422


def test_assistant_uses_mock_provider_when_disabled(monkeypatch):
    monkeypatch.setenv("ASSISTANT_LLM_ENABLED", "false")

    client = TestClient(app)
    response = client.post("/api/v1/assistant/chat", json=recall_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["refused"] is False
    assert body["model_info"]["provider"] == "mock"
    assert body["model_info"]["model"] == "mock-assistant-v0.1"


def test_assistant_replaces_unsafe_llm_output(monkeypatch):
    monkeypatch.setattr(
        "app.services.assistant_service.get_assistant_provider",
        lambda: UnsafeFakeProvider(),
    )

    client = TestClient(app)
    response = client.post("/api/v1/assistant/chat", json=drug_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["refused"] is True
    assert body["refusal_reason"] == "unsafe generated output"
    assert "stop taking" not in body["answer"]
    assert body["model_info"] == {"provider": "fake", "model": "unsafe-test-model"}
