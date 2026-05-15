"""Repository for scheduler lock / lease protection.

This repository provides a small lock abstraction for scheduled jobs such as
Saved Monitor refresh. It currently supports an in-memory fallback for local
development and tests. A database-backed implementation can be added after the
scheduler_locks table is introduced.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SchedulerLock:
    """Represents an active scheduler lock."""

    lock_name: str
    locked_by: str
    locked_until: datetime
    created_at: datetime
    updated_at: datetime


class SchedulerLockRepository:
    """Scheduler lock repository with in-memory lease behavior."""

    def __init__(self) -> None:
        self._locks: dict[str, SchedulerLock] = {}

    def acquire_lock(
        self,
        *,
        lock_name: str,
        locked_by: str,
        locked_until: datetime,
        now: datetime,
    ) -> bool:
        """Acquire a lock when absent or expired.

        Returns True when the lock is acquired.
        Returns False when another active lock exists.
        """

        existing = self._locks.get(lock_name)

        if existing is not None and existing.locked_until > now:
            return False

        created_at = existing.created_at if existing else now

        self._locks[lock_name] = SchedulerLock(
            lock_name=lock_name,
            locked_by=locked_by,
            locked_until=locked_until,
            created_at=created_at,
            updated_at=now,
        )

        return True

    def release_lock(self, *, lock_name: str, locked_by: str) -> bool:
        """Release a lock only when owned by the current job."""

        existing = self._locks.get(lock_name)

        if existing is None:
            return False

        if existing.locked_by != locked_by:
            return False

        del self._locks[lock_name]
        return True

    def get_lock(self, lock_name: str) -> SchedulerLock | None:
        """Return the current lock for inspection/testing."""

        return self._locks.get(lock_name)

    def clear(self) -> None:
        """Clear in-memory locks for tests."""

        self._locks.clear()


scheduler_lock_repository = SchedulerLockRepository()
