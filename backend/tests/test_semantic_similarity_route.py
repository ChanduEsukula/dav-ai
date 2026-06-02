from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_semantic_similarity_preview_route_returns_matches():
    response = client.post(
        "/api/v1/semantic-similarity/preview",
        json={
            "query_text": "eye drops contamination recall",
            "candidates": [
                {
                    "record_id": "recall-1",
                    "text": "eye drops recalled after contamination signal in public recall data",
                    "source_name": "openFDA Drug Enforcement API",
                },
                {
                    "record_id": "recall-2",
                    "text": "tablet packaging label update",
                    "source_name": "openFDA Drug Enforcement API",
                },
            ],
            "max_matches": 2,
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["matches"][0]["record_id"] == "recall-1"
    assert body["matches"][0]["similarity_score"] > 0
    assert body["preview_version"] == "semantic-similarity-preview-v0.1"
    assert body["is_production_ml"] is False


def test_semantic_similarity_preview_route_rejects_unsafe_text():
    response = client.post(
        "/api/v1/semantic-similarity/preview",
        json={
            "query_text": "public recall",
            "candidates": [
                {
                    "record_id": "bad-record",
                    "text": "this is safe for you",
                }
            ],
        },
    )

    assert response.status_code == 400
    assert "unsafe wording" in response.json()["detail"]


def test_semantic_similarity_preview_route_limits_matches():
    response = client.post(
        "/api/v1/semantic-similarity/preview",
        json={
            "query_text": "aspirin recall",
            "candidates": [
                {
                    "record_id": f"record-{index}",
                    "text": "aspirin recall public record",
                }
                for index in range(10)
            ],
            "max_matches": 3,
        },
    )

    assert response.status_code == 200
    assert len(response.json()["matches"]) == 3
