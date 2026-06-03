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
