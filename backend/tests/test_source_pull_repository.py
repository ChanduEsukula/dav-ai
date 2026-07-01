import pytest

from app.db import source_pull_repository


def test_build_payload_hash_is_stable_for_key_order():
    first_payload = {
        "results": [{"b": 2, "a": 1}],
        "meta": {"total": 1},
    }
    second_payload = {
        "meta": {"total": 1},
        "results": [{"a": 1, "b": 2}],
    }

    assert source_pull_repository.build_payload_hash(first_payload) == (
        source_pull_repository.build_payload_hash(second_payload)
    )


def _example_audit_event():
    return {
        "audit_id": "11111111-1111-1111-1111-111111111111",
        "source_id": "openfda_drug_enforcement",
        "source_name": "openFDA Drug Enforcement API",
        "endpoint": "https://api.fda.gov/drug/enforcement.json",
        "query": "aspirin",
        "query_params": {"q": "aspirin", "limit": 5},
        "retrieval_timestamp": "2026-05-21T10:00:00+00:00",
        "upstream_status": "success",
        "record_count": 1,
        "transform_version": "recall-transform-v0.1",
        "created_at": "2026-05-21T10:00:00+00:00",
    }


def test_save_source_pull_with_snapshot_skips_when_database_not_configured(monkeypatch):
    monkeypatch.setattr(source_pull_repository, "get_database_url", lambda: None)
    monkeypatch.delenv("DAVAI_ENV", raising=False)

    result = source_pull_repository.save_source_pull_with_snapshot(
        audit_event=_example_audit_event(),
        raw_payload={"results": [{"recall_number": "R-1"}]},
        request_id="test-request",
    )

    assert result["status"] == "skipped"
    assert result["reason"] == "database_not_configured"
    assert result["pull_id"] is None
    assert result["snapshot_id"] is None
    assert len(result["payload_hash"]) == 64


def test_save_source_pull_requires_database_in_deployed_environment(monkeypatch):
    monkeypatch.setattr(source_pull_repository, "get_database_url", lambda: None)
    monkeypatch.setenv("DAVAI_ENV", "production")

    with pytest.raises(
        source_pull_repository.SourcePullPersistenceError,
        match="DATABASE_URL must be configured",
    ):
        source_pull_repository.save_source_pull_with_snapshot(
            audit_event=_example_audit_event(),
            raw_payload={"results": [{"recall_number": "R-1"}]},
            request_id="test-request",
        )


def test_save_source_pull_fails_closed_in_deployed_environment(monkeypatch):
    monkeypatch.setattr(
        source_pull_repository,
        "get_database_url",
        lambda: "postgresql://user:password@localhost:5432/dav_ai",
    )
    monkeypatch.setenv("DAVAI_ENV", "production")

    def mock_connect(*args, **kwargs):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(source_pull_repository.psycopg, "connect", mock_connect)

    with pytest.raises(
        source_pull_repository.SourcePullPersistenceError,
        match="deployed mode",
    ):
        source_pull_repository.save_source_pull_with_snapshot(
            audit_event=_example_audit_event(),
            raw_payload={"results": [{"recall_number": "R-1"}]},
            request_id="test-request",
        )
