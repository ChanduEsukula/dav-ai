from app.db.audit_repository import save_audit_event


def _example_audit_event():
    return {
        "audit_id": "00000000-0000-0000-0000-000000000001",
        "module": "RecallRadar",
        "source_id": "openfda_drug_enforcement",
        "source_name": "openFDA Drug Enforcement API",
        "endpoint": "https://api.fda.gov/drug/enforcement.json",
        "query": "eye drops",
        "query_params": {"q": "eye drops", "limit": 5},
        "retrieval_timestamp": "2026-05-01T20:00:00+00:00",
        "upstream_status": "success",
        "record_count": 5,
        "transform_version": "recall-transform-v0.1",
        "score_version": "recall-risk-v0.1",
        "disclaimer_version": "disclaimer-v0.1",
        "error_message": None,
        "created_at": "2026-05-01T20:00:01+00:00",
    }


def test_save_audit_event_skips_when_database_missing(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    result = save_audit_event(_example_audit_event())

    assert result == {
        "status": "skipped",
        "reason": "database_not_configured",
    }


def test_save_audit_event_returns_saved_when_insert_succeeds(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/medsignal",
    )

    class MockCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def execute(self, query, params):
            assert "insert into audit_events" in query
            assert params["audit_id"] == "00000000-0000-0000-0000-000000000001"
            assert params["source_id"] == "openfda_drug_enforcement"

    class MockConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def cursor(self):
            return MockCursor()

    def mock_connect(*args, **kwargs):
        return MockConnection()

    monkeypatch.setattr("app.db.audit_repository.psycopg.connect", mock_connect)

    result = save_audit_event(_example_audit_event())

    assert result == {
        "status": "saved",
        "reason": "audit_event_persisted",
    }


def test_save_audit_event_fails_softly_when_insert_fails(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/medsignal",
    )

    def mock_connect(*args, **kwargs):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr("app.db.audit_repository.psycopg.connect", mock_connect)

    result = save_audit_event(_example_audit_event())

    assert result == {
        "status": "error",
        "reason": "audit_event_persistence_failed",
    }