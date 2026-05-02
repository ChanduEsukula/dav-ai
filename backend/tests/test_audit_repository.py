from app.db.audit_repository import save_audit_event


def test_save_audit_event_skips_when_database_missing(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    result = save_audit_event(
        {
            "audit_id": "example-audit-id",
            "module": "RecallRadar",
        }
    )

    assert result == {
        "status": "skipped",
        "reason": "database_not_configured",
    }


def test_save_audit_event_returns_not_implemented_when_database_configured(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://user:password@localhost:5432/medsignal",
    )

    result = save_audit_event(
        {
            "audit_id": "example-audit-id",
            "module": "DrugSignal",
        }
    )

    assert result == {
        "status": "not_implemented",
        "reason": "database_configured_but_repository_not_implemented",
    }