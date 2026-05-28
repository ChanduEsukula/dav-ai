"""Tests for Saved Monitors v2 backend foundation."""

from fastapi.testclient import TestClient

from app.db.saved_monitor_repository import saved_monitor_repository
from app.main import app

client = TestClient(app)


RECALL_AUDIT_ID = "11111111-1111-1111-1111-111111111111"
DRUG_AUDIT_ID = "22222222-2222-2222-2222-222222222222"
FIRST_AUDIT_ID = "33333333-3333-3333-3333-333333333333"
SECOND_AUDIT_ID = "44444444-4444-4444-4444-444444444444"


def setup_function() -> None:
    saved_monitor_repository.clear()


def test_create_saved_monitor() -> None:
    response = client.post(
        "/api/v1/saved-monitors",
        json={
            "name": "Eye drops monitor",
            "query": "eye drops",
            "module": "recallradar",
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert data["id"]
    assert data["name"] == "Eye drops monitor"
    assert data["query"] == "eye drops"
    assert data["module"] == "recallradar"
    assert data["created_at"]
    assert data["last_checked_at"] is None
    assert data["latest_audit_id"] is None
    assert data["latest_score"] is None
    assert data["previous_score"] is None
    assert data["latest_record_count"] is None
    assert data["previous_record_count"] is None
    assert data["status"] == "not_checked"


def test_reject_duplicate_saved_monitor_same_module_and_query() -> None:
    first_response = client.post(
        "/api/v1/saved-monitors",
        json={
            "name": "Eye drops monitor",
            "query": "eye drops",
            "module": "recallradar",
        },
    )

    duplicate_response = client.post(
        "/api/v1/saved-monitors",
        json={
            "name": "Duplicate eye drops monitor",
            "query": "eye drops",
            "module": "recallradar",
        },
    )

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 409
    assert (
        duplicate_response.json()["detail"]
        == "A saved monitor already exists for this module and query."
    )


def test_reject_duplicate_saved_monitor_with_normalized_query() -> None:
    first_response = client.post(
        "/api/v1/saved-monitors",
        json={
            "name": "Eye drops monitor",
            "query": "eye drops",
            "module": "recallradar",
        },
    )

    duplicate_response = client.post(
        "/api/v1/saved-monitors",
        json={
            "name": "Duplicate eye drops monitor",
            "query": "  Eye Drops  ",
            "module": "recallradar",
        },
    )

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 409
    assert (
        duplicate_response.json()["detail"]
        == "A saved monitor already exists for this module and query."
    )


def test_allow_same_query_for_different_saved_monitor_module() -> None:
    recall_response = client.post(
        "/api/v1/saved-monitors",
        json={
            "name": "Metformin recall monitor",
            "query": "metformin",
            "module": "recallradar",
        },
    )

    drug_signal_response = client.post(
        "/api/v1/saved-monitors",
        json={
            "name": "Metformin drug signal monitor",
            "query": "metformin",
            "module": "drugsignal",
        },
    )

    assert recall_response.status_code == 201
    assert drug_signal_response.status_code == 201


def test_list_saved_monitors() -> None:
    client.post(
        "/api/v1/saved-monitors",
        json={
            "name": "Metformin monitor",
            "query": "metformin",
            "module": "drugsignal",
        },
    )

    response = client.get("/api/v1/saved-monitors")

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 1
    assert data[0]["name"] == "Metformin monitor"
    assert data[0]["query"] == "metformin"
    assert data[0]["module"] == "drugsignal"


def test_delete_saved_monitor() -> None:
    create_response = client.post(
        "/api/v1/saved-monitors",
        json={
            "name": "Baby formula monitor",
            "query": "baby formula",
            "module": "recallradar",
        },
    )
    monitor_id = create_response.json()["id"]

    delete_response = client.delete(f"/api/v1/saved-monitors/{monitor_id}")

    assert delete_response.status_code == 204

    list_response = client.get("/api/v1/saved-monitors")
    assert list_response.status_code == 200
    assert list_response.json() == []


def test_delete_saved_monitor_not_found() -> None:
    response = client.delete("/api/v1/saved-monitors/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json()["detail"] == "Saved monitor not found"


def test_reject_invalid_module() -> None:
    response = client.post(
        "/api/v1/saved-monitors",
        json={
            "name": "Invalid module monitor",
            "query": "eye drops",
            "module": "invalid",
        },
    )

    assert response.status_code == 422


def test_reject_too_short_query() -> None:
    response = client.post(
        "/api/v1/saved-monitors",
        json={
            "name": "Short query monitor",
            "query": "x",
            "module": "recallradar",
        },
    )

    assert response.status_code == 422


def test_reject_too_short_name() -> None:
    response = client.post(
        "/api/v1/saved-monitors",
        json={
            "name": "x",
            "query": "eye drops",
            "module": "recallradar",
        },
    )

    assert response.status_code == 422


def test_run_recallradar_saved_monitor(monkeypatch) -> None:
    async def fake_search_recalls(
        query: str,
        limit: int,
        request_id: str | None = None,
    ):
        return {
            "query": query,
            "count": 5,
            "audit": {
                "audit_id": RECALL_AUDIT_ID,
            },
            "results": [
                {
                    "risk_score": {
                        "score": 52,
                        "label": "Medium",
                    }
                }
            ],
        }

    monkeypatch.setattr(
        "app.routes.saved_monitors.execute_recall_search",
        fake_search_recalls,
    )

    create_response = client.post(
        "/api/v1/saved-monitors",
        json={
            "name": "Eye drops monitor",
            "query": "eye drops",
            "module": "recallradar",
        },
    )
    monitor_id = create_response.json()["id"]

    run_response = client.post(f"/api/v1/saved-monitors/{monitor_id}/run")

    assert run_response.status_code == 200
    data = run_response.json()

    assert data["status"] == "checked"
    assert data["latest_audit_id"] == RECALL_AUDIT_ID
    assert data["latest_score"] == 52
    assert data["latest_record_count"] == 5
    assert data["previous_score"] is None
    assert data["previous_record_count"] is None
    assert data["last_checked_at"] is not None

    runs_response = client.get(f"/api/v1/saved-monitors/{monitor_id}/runs")
    assert runs_response.status_code == 200
    runs = runs_response.json()

    assert len(runs) == 1
    assert runs[0]["monitor_id"] == monitor_id
    assert runs[0]["module"] == "recallradar"
    assert runs[0]["query"] == "eye drops"
    assert runs[0]["status"] == "success"
    assert runs[0]["record_count"] == 5
    assert runs[0]["score"] == 52
    assert runs[0]["score_label"] == "Medium"
    assert runs[0]["audit_id"] == RECALL_AUDIT_ID
    assert runs[0]["created_at"]
    assert runs[0]["error_message"] is None
    assert runs[0]["payload_change"]["label"] == "unknown"


def test_run_drugsignal_saved_monitor(monkeypatch) -> None:
    async def fake_search_drug_events(
        query: str,
        limit: int,
        request_id: str | None = None,
    ):
        return {
            "query": query,
            "count": 10,
            "audit": {
                "audit_id": DRUG_AUDIT_ID,
            },
            "intelligence_score": {
                "score": 80,
                "label": "High",
            },
        }

    monkeypatch.setattr(
        "app.routes.saved_monitors.execute_drug_signal_search",
        fake_search_drug_events,
    )

    create_response = client.post(
        "/api/v1/saved-monitors",
        json={
            "name": "Metformin monitor",
            "query": "metformin",
            "module": "drugsignal",
        },
    )
    monitor_id = create_response.json()["id"]

    run_response = client.post(f"/api/v1/saved-monitors/{monitor_id}/run")

    assert run_response.status_code == 200
    data = run_response.json()

    assert data["status"] == "checked"
    assert data["latest_audit_id"] == DRUG_AUDIT_ID
    assert data["latest_score"] == 80
    assert data["latest_record_count"] == 10
    assert data["previous_score"] is None
    assert data["previous_record_count"] is None
    assert data["last_checked_at"] is not None

    runs_response = client.get(f"/api/v1/saved-monitors/{monitor_id}/runs")
    assert runs_response.status_code == 200
    runs = runs_response.json()

    assert len(runs) == 1
    assert runs[0]["module"] == "drugsignal"
    assert runs[0]["query"] == "metformin"
    assert runs[0]["status"] == "success"
    assert runs[0]["record_count"] == 10
    assert runs[0]["score"] == 80
    assert runs[0]["score_label"] == "High"
    assert runs[0]["audit_id"] == DRUG_AUDIT_ID
    assert runs[0]["payload_change"]["label"] == "unknown"


def test_run_saved_monitor_preserves_previous_values(monkeypatch) -> None:
    calls = 0

    async def fake_search_recalls(
        query: str,
        limit: int,
        request_id: str | None = None,
    ):
        nonlocal calls
        calls += 1

        if calls == 1:
            return {
                "query": query,
                "count": 5,
                "audit": {"audit_id": FIRST_AUDIT_ID},
                "results": [{"risk_score": {"score": 52}}],
            }

        return {
            "query": query,
            "count": 7,
            "audit": {"audit_id": SECOND_AUDIT_ID},
            "results": [{"risk_score": {"score": 61}}],
        }

    monkeypatch.setattr(
        "app.routes.saved_monitors.execute_recall_search",
        fake_search_recalls,
    )

    create_response = client.post(
        "/api/v1/saved-monitors",
        json={
            "name": "Eye drops monitor",
            "query": "eye drops",
            "module": "recallradar",
        },
    )
    monitor_id = create_response.json()["id"]

    first_run = client.post(f"/api/v1/saved-monitors/{monitor_id}/run")
    second_run = client.post(f"/api/v1/saved-monitors/{monitor_id}/run")

    assert first_run.status_code == 200
    assert second_run.status_code == 200

    data = second_run.json()

    assert data["latest_audit_id"] == SECOND_AUDIT_ID
    assert data["latest_score"] == 61
    assert data["latest_record_count"] == 7
    assert data["previous_score"] == 52
    assert data["previous_record_count"] == 5

    runs_response = client.get(f"/api/v1/saved-monitors/{monitor_id}/runs")
    assert runs_response.status_code == 200
    runs = runs_response.json()

    assert [run["audit_id"] for run in runs] == [SECOND_AUDIT_ID, FIRST_AUDIT_ID]


def test_list_saved_monitor_runs_includes_payload_change_status(monkeypatch) -> None:
    calls = 0

    async def fake_search_recalls(
        query: str,
        limit: int,
        request_id: str | None = None,
    ):
        nonlocal calls
        calls += 1

        if calls == 1:
            return {
                "query": query,
                "count": 5,
                "audit": {"audit_id": FIRST_AUDIT_ID},
                "results": [{"risk_score": {"score": 52}}],
            }

        return {
            "query": query,
            "count": 7,
            "audit": {"audit_id": SECOND_AUDIT_ID},
            "results": [{"risk_score": {"score": 61}}],
        }

    def fake_get_source_pull_by_audit_id(audit_id: str, request_id: str | None = None):
        payload_hashes = {
            FIRST_AUDIT_ID: "a" * 64,
            SECOND_AUDIT_ID: "b" * 64,
        }
        return (
            "saved",
            {
                "audit_id": audit_id,
                "payload_hash": payload_hashes[audit_id],
            },
        )

    monkeypatch.setattr(
        "app.routes.saved_monitors.execute_recall_search",
        fake_search_recalls,
    )
    monkeypatch.setattr(
        "app.routes.saved_monitors.get_source_pull_by_audit_id",
        fake_get_source_pull_by_audit_id,
    )

    create_response = client.post(
        "/api/v1/saved-monitors",
        json={
            "name": "Eye drops monitor",
            "query": "eye drops",
            "module": "recallradar",
        },
    )
    monitor_id = create_response.json()["id"]

    assert client.post(f"/api/v1/saved-monitors/{monitor_id}/run").status_code == 200
    assert client.post(f"/api/v1/saved-monitors/{monitor_id}/run").status_code == 200

    runs_response = client.get(f"/api/v1/saved-monitors/{monitor_id}/runs")

    assert runs_response.status_code == 200
    runs = runs_response.json()

    assert [run["audit_id"] for run in runs] == [SECOND_AUDIT_ID, FIRST_AUDIT_ID]

    latest_change = runs[0]["payload_change"]
    assert latest_change["label"] == "changed"
    assert latest_change["latest_hash"] == "b" * 64
    assert latest_change["previous_hash"] == "a" * 64
    assert "differs" in latest_change["reason"]
    assert "operational public-data review signal" in latest_change["safety_note"]

    older_change = runs[1]["payload_change"]
    assert older_change["label"] == "first_seen"
    assert older_change["latest_hash"] == "a" * 64
    assert older_change["previous_hash"] is None


def test_list_saved_monitor_runs_payload_change_unknown_when_source_pull_missing(monkeypatch) -> None:
    async def fake_search_recalls(
        query: str,
        limit: int,
        request_id: str | None = None,
    ):
        return {
            "query": query,
            "count": 5,
            "audit": {"audit_id": FIRST_AUDIT_ID},
            "results": [{"risk_score": {"score": 52}}],
        }

    monkeypatch.setattr(
        "app.routes.saved_monitors.execute_recall_search",
        fake_search_recalls,
    )
    monkeypatch.setattr(
        "app.routes.saved_monitors.get_source_pull_by_audit_id",
        lambda audit_id, request_id=None: ("skipped", None),
    )

    create_response = client.post(
        "/api/v1/saved-monitors",
        json={
            "name": "Eye drops monitor",
            "query": "eye drops",
            "module": "recallradar",
        },
    )
    monitor_id = create_response.json()["id"]

    assert client.post(f"/api/v1/saved-monitors/{monitor_id}/run").status_code == 200

    runs_response = client.get(f"/api/v1/saved-monitors/{monitor_id}/runs")

    assert runs_response.status_code == 200
    runs = runs_response.json()

    assert len(runs) == 1
    assert runs[0]["payload_change"]["label"] == "unknown"
    assert runs[0]["payload_change"]["latest_hash"] is None
    assert runs[0]["payload_change"]["previous_hash"] is None
    assert "Latest payload hash is missing" in runs[0]["payload_change"]["reason"]


def test_list_saved_monitor_runs_payload_change_unavailable_for_error_run(monkeypatch) -> None:
    async def fake_search_recalls(
        query: str,
        limit: int,
        request_id: str | None = None,
    ):
        raise RuntimeError("openFDA unavailable")

    monkeypatch.setattr(
        "app.routes.saved_monitors.execute_recall_search",
        fake_search_recalls,
    )

    create_response = client.post(
        "/api/v1/saved-monitors",
        json={
            "name": "Eye drops monitor",
            "query": "eye drops",
            "module": "recallradar",
        },
    )
    monitor_id = create_response.json()["id"]

    assert client.post(f"/api/v1/saved-monitors/{monitor_id}/run").status_code == 502

    runs_response = client.get(f"/api/v1/saved-monitors/{monitor_id}/runs")

    assert runs_response.status_code == 200
    runs = runs_response.json()

    assert len(runs) == 1
    assert runs[0]["status"] == "error"
    assert runs[0]["audit_id"] is None
    assert runs[0]["payload_change"]["label"] == "unavailable"
    assert "unavailable" in runs[0]["payload_change"]["reason"].lower()


def test_list_saved_monitor_runs_empty_state() -> None:
    create_response = client.post(
        "/api/v1/saved-monitors",
        json={
            "name": "Eye drops monitor",
            "query": "eye drops",
            "module": "recallradar",
        },
    )
    monitor_id = create_response.json()["id"]

    response = client.get(f"/api/v1/saved-monitors/{monitor_id}/runs")

    assert response.status_code == 200
    assert response.json() == []


def test_list_saved_monitor_runs_not_found() -> None:
    response = client.get("/api/v1/saved-monitors/00000000-0000-0000-0000-000000000000/runs")

    assert response.status_code == 404
    assert response.json()["detail"] == "Saved monitor not found"


def test_failed_saved_monitor_run_records_history(monkeypatch) -> None:
    async def fake_search_recalls(
        query: str,
        limit: int,
        request_id: str | None = None,
    ):
        raise RuntimeError("openFDA unavailable")

    monkeypatch.setattr(
        "app.routes.saved_monitors.execute_recall_search",
        fake_search_recalls,
    )

    create_response = client.post(
        "/api/v1/saved-monitors",
        json={
            "name": "Eye drops monitor",
            "query": "eye drops",
            "module": "recallradar",
        },
    )
    monitor_id = create_response.json()["id"]

    run_response = client.post(f"/api/v1/saved-monitors/{monitor_id}/run")

    assert run_response.status_code == 502

    list_response = client.get("/api/v1/saved-monitors")
    assert list_response.status_code == 200
    assert list_response.json()[0]["status"] == "error"

    runs_response = client.get(f"/api/v1/saved-monitors/{monitor_id}/runs")
    assert runs_response.status_code == 200
    runs = runs_response.json()

    assert len(runs) == 1
    assert runs[0]["status"] == "error"
    assert runs[0]["module"] == "recallradar"
    assert runs[0]["query"] == "eye drops"
    assert runs[0]["record_count"] == 0
    assert runs[0]["score"] is None
    assert runs[0]["score_label"] is None
    assert runs[0]["audit_id"] is None
    assert "openFDA unavailable" in runs[0]["error_message"]
    assert runs[0]["payload_change"]["label"] == "unavailable"


def test_run_saved_monitor_not_found() -> None:
    response = client.post("/api/v1/saved-monitors/00000000-0000-0000-0000-000000000000/run")

    assert response.status_code == 404
    assert response.json()["detail"] == "Saved monitor not found"


def test_saved_monitor_insight_returns_insufficient_history():
    create_response = client.post(
        "/api/v1/saved-monitors",
        json={
            "name": "Insight aspirin monitor",
            "query": "aspirin insight route",
            "module": "recallradar",
        },
    )
    assert create_response.status_code == 201

    monitor = create_response.json()

    response = client.get(f"/api/v1/saved-monitors/{monitor['id']}/insights")

    assert response.status_code == 200
    data = response.json()

    assert data["monitor_id"] == monitor["id"]
    assert data["label"] == "insufficient_history"
    assert data["headline"] == "Insufficient history"
    assert data["confidence"] == "low"
    assert data["insight_version"] == "monitor-insight-v0.1"
    assert "not medical advice" in data["limitation"]


def test_saved_monitor_insight_returns_404_for_unknown_monitor():
    response = client.get(
        "/api/v1/saved-monitors/11111111-1111-1111-1111-111111111111/insights"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Saved monitor not found"


def test_run_regional_health_pulse_saved_monitor(monkeypatch) -> None:
    def fake_regional_health_search(
        region: str,
        category: str,
        request_id: str | None = None,
    ):
        class FakeResponse:
            def model_dump(self):
                return {
                    "region": region,
                    "category": category,
                    "record_count": 2,
                    "latest_value": 46,
                    "audit": {
                        "audit_id": "33333333-3333-4333-8333-333333333333",
                    },
                    "signal": {
                        "trend_label": "Increasing",
                    },
                }

        return FakeResponse()

    monkeypatch.setattr(
        "app.routes.saved_monitors.execute_regional_health_search",
        fake_regional_health_search,
    )

    create_response = client.post(
        "/api/v1/saved-monitors",
        json={
            "name": "Minnesota respiratory monitor",
            "query": "MN respiratory",
            "module": "regional_health_pulse",
        },
    )
    monitor_id = create_response.json()["id"]

    run_response = client.post(f"/api/v1/saved-monitors/{monitor_id}/run")

    assert run_response.status_code == 200
    data = run_response.json()

    assert data["status"] == "checked"
    assert data["latest_audit_id"] == "33333333-3333-4333-8333-333333333333"
    assert data["latest_score"] == 46
    assert data["latest_record_count"] == 2

    runs_response = client.get(f"/api/v1/saved-monitors/{monitor_id}/runs")
    assert runs_response.status_code == 200
    runs = runs_response.json()

    assert len(runs) == 1
    assert runs[0]["module"] == "regional_health_pulse"
    assert runs[0]["query"] == "MN respiratory"
    assert runs[0]["status"] == "success"
    assert runs[0]["record_count"] == 2
    assert runs[0]["score"] == 46
    assert runs[0]["score_label"] == "Increasing"
    assert runs[0]["audit_id"] == "33333333-3333-4333-8333-333333333333"
    assert runs[0]["payload_change"]["label"] == "unknown"


def test_run_regional_health_pulse_saved_monitor_validates_query_format() -> None:
    create_response = client.post(
        "/api/v1/saved-monitors",
        json={
            "name": "Invalid Health Pulse monitor",
            "query": "MN",
            "module": "regional_health_pulse",
        },
    )
    monitor_id = create_response.json()["id"]

    run_response = client.post(f"/api/v1/saved-monitors/{monitor_id}/run")

    assert run_response.status_code == 422
    assert "Regional Health Pulse saved monitor query" in run_response.json()["detail"]