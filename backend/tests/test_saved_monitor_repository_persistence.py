from uuid import uuid4

import pytest

from app.db.saved_monitor_repository import (
    SavedMonitorPersistenceError,
    SavedMonitorRepository,
)
from app.schemas.saved_monitors import SavedMonitorCreate, SavedMonitorModule


def _raise_db_unavailable(*args, **kwargs):
    raise RuntimeError("database unavailable")


def test_saved_monitor_db_failure_can_fall_back_locally(monkeypatch):
    repo = SavedMonitorRepository()
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@example.com/db")
    monkeypatch.delenv("DAVAI_ENV", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("PYTHON_ENV", raising=False)
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.setattr(
        "app.db.saved_monitor_repository.psycopg.connect",
        _raise_db_unavailable,
    )

    monitor = repo.create(
        SavedMonitorCreate(
            name="Local fallback",
            query="metformin",
            module=SavedMonitorModule.DRUGSIGNAL,
        ),
        user_id=uuid4(),
    )

    assert repo.list() == [monitor]


def test_saved_monitor_db_failure_fails_closed_in_deployed_environment(monkeypatch):
    repo = SavedMonitorRepository()
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@example.com/db")
    monkeypatch.setenv("DAVAI_ENV", "production")
    monkeypatch.setattr(
        "app.db.saved_monitor_repository.psycopg.connect",
        _raise_db_unavailable,
    )

    with pytest.raises(SavedMonitorPersistenceError, match="deployed mode"):
        repo.list()
