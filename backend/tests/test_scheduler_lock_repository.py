"""Tests for scheduler lock repository behavior."""

from datetime import datetime, timedelta, timezone

from app.db.scheduler_lock_repository import SchedulerLockRepository


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
