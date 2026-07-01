"""Tests for scheduler lock repository behavior."""

from datetime import datetime, timedelta, timezone

import pytest

from app.db.scheduler_lock_repository import (
    SchedulerLockPersistenceError,
    SchedulerLockRepository,
)


def test_acquire_new_lock_succeeds():
    repository = SchedulerLockRepository()
    now = datetime.now(timezone.utc)

    acquired = repository.acquire_lock(
        lock_name="saved-monitor-refresh",
        locked_by="job-1",
        locked_until=now + timedelta(minutes=15),
        now=now,
    )

    lock = repository.get_lock("saved-monitor-refresh")

    assert acquired is True
    assert lock is not None
    assert lock.lock_name == "saved-monitor-refresh"
    assert lock.locked_by == "job-1"
    assert lock.locked_until == now + timedelta(minutes=15)


def test_active_lock_blocks_another_job():
    repository = SchedulerLockRepository()
    now = datetime.now(timezone.utc)

    first = repository.acquire_lock(
        lock_name="saved-monitor-refresh",
        locked_by="job-1",
        locked_until=now + timedelta(minutes=15),
        now=now,
    )

    second = repository.acquire_lock(
        lock_name="saved-monitor-refresh",
        locked_by="job-2",
        locked_until=now + timedelta(minutes=15),
        now=now + timedelta(minutes=1),
    )

    lock = repository.get_lock("saved-monitor-refresh")

    assert first is True
    assert second is False
    assert lock is not None
    assert lock.locked_by == "job-1"


def test_expired_lock_can_be_taken_over():
    repository = SchedulerLockRepository()
    now = datetime.now(timezone.utc)

    repository.acquire_lock(
        lock_name="saved-monitor-refresh",
        locked_by="job-1",
        locked_until=now - timedelta(minutes=1),
        now=now - timedelta(minutes=20),
    )

    acquired = repository.acquire_lock(
        lock_name="saved-monitor-refresh",
        locked_by="job-2",
        locked_until=now + timedelta(minutes=15),
        now=now,
    )

    lock = repository.get_lock("saved-monitor-refresh")

    assert acquired is True
    assert lock is not None
    assert lock.locked_by == "job-2"
    assert lock.locked_until == now + timedelta(minutes=15)


def test_owner_can_release_lock():
    repository = SchedulerLockRepository()
    now = datetime.now(timezone.utc)

    repository.acquire_lock(
        lock_name="saved-monitor-refresh",
        locked_by="job-1",
        locked_until=now + timedelta(minutes=15),
        now=now,
    )

    released = repository.release_lock(
        lock_name="saved-monitor-refresh",
        locked_by="job-1",
    )

    assert released is True
    assert repository.get_lock("saved-monitor-refresh") is None


def test_non_owner_cannot_release_lock():
    repository = SchedulerLockRepository()
    now = datetime.now(timezone.utc)

    repository.acquire_lock(
        lock_name="saved-monitor-refresh",
        locked_by="job-1",
        locked_until=now + timedelta(minutes=15),
        now=now,
    )

    released = repository.release_lock(
        lock_name="saved-monitor-refresh",
        locked_by="job-2",
    )

    lock = repository.get_lock("saved-monitor-refresh")

    assert released is False
    assert lock is not None
    assert lock.locked_by == "job-1"


def test_release_missing_lock_returns_false():
    repository = SchedulerLockRepository()

    released = repository.release_lock(
        lock_name="saved-monitor-refresh",
        locked_by="job-1",
    )

    assert released is False


def test_db_lock_failure_falls_back_to_memory_locally(monkeypatch):
    repository = SchedulerLockRepository(use_database=True)
    now = datetime.now(timezone.utc)
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@example.com/db")
    monkeypatch.delenv("DAVAI_ENV", raising=False)

    def mock_connect(*args, **kwargs):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(
        "app.db.scheduler_lock_repository.psycopg.connect",
        mock_connect,
    )

    acquired = repository.acquire_lock(
        lock_name="saved-monitor-refresh",
        locked_by="job-1",
        locked_until=now + timedelta(minutes=15),
        now=now,
    )

    assert acquired is True
    assert repository.get_lock("saved-monitor-refresh") is not None


def test_db_lock_failure_fails_closed_in_deployed_environment(monkeypatch):
    repository = SchedulerLockRepository(use_database=True)
    now = datetime.now(timezone.utc)
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@example.com/db")
    monkeypatch.setenv("DAVAI_ENV", "production")

    def mock_connect(*args, **kwargs):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(
        "app.db.scheduler_lock_repository.psycopg.connect",
        mock_connect,
    )

    with pytest.raises(SchedulerLockPersistenceError, match="deployed mode"):
        repository.acquire_lock(
            lock_name="saved-monitor-refresh",
            locked_by="job-1",
            locked_until=now + timedelta(minutes=15),
            now=now,
        )


def test_db_lock_requires_database_in_deployed_environment(monkeypatch):
    repository = SchedulerLockRepository(use_database=True)
    now = datetime.now(timezone.utc)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DAVAI_ENV", "production")

    with pytest.raises(SchedulerLockPersistenceError, match="DATABASE_URL"):
        repository.acquire_lock(
            lock_name="saved-monitor-refresh",
            locked_by="job-1",
            locked_until=now + timedelta(minutes=15),
            now=now,
        )
