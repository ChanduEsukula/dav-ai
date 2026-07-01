"""Repository for scheduler lock / lease protection.

This repository provides a small lock abstraction for scheduled jobs such as
Saved Monitor refresh.

When DATABASE_URL is configured and the scheduler_locks table exists, the
global repository uses database-backed locks so scheduled jobs are protected
across processes, deployments, and restarts.

Manually-created repository instances default to in-memory behavior for local
unit tests. The global singleton at the bottom opts into database-backed locks.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

import psycopg
from psycopg.rows import dict_row

from app.db.database import get_database_url

logger = logging.getLogger("dav_ai.scheduler_lock")


@dataclass(frozen=True)
class SchedulerLock:
    """Represents an active scheduler lock."""

    lock_name: str
    locked_by: str
    locked_until: datetime
    created_at: datetime
    updated_at: datetime


class SchedulerLockRepository:
    """Scheduler lock repository with DB-backed and in-memory lease behavior."""

    def __init__(self, *, use_database: bool = False) -> None:
        self._locks: dict[str, SchedulerLock] = {}
        self._use_database = use_database

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

        DB-backed behavior is preferred for the global repository when
        available. In-memory behavior is retained as a safe local/test fallback.
        """

        database_url = get_database_url() if self._use_database else None

        if database_url:
            try:
                return self._acquire_lock_db(
                    database_url=database_url,
                    lock_name=lock_name,
                    locked_by=locked_by,
                    locked_until=locked_until,
                    now=now,
                )
            except Exception:
                logger.exception(
                    "scheduler_lock_db_acquire_failed",
                    extra={
                        "event": "scheduler_lock_db_acquire_failed",
                        "lock_name": lock_name,
                    },
                )

        return self._acquire_lock_memory(
            lock_name=lock_name,
            locked_by=locked_by,
            locked_until=locked_until,
            now=now,
        )

    def release_lock(self, *, lock_name: str, locked_by: str) -> bool:
        """Release a lock only when owned by the current job."""

        database_url = get_database_url() if self._use_database else None

        if database_url:
            try:
                return self._release_lock_db(
                    database_url=database_url,
                    lock_name=lock_name,
                    locked_by=locked_by,
                )
            except Exception:
                logger.exception(
                    "scheduler_lock_db_release_failed",
                    extra={
                        "event": "scheduler_lock_db_release_failed",
                        "lock_name": lock_name,
                    },
                )

        return self._release_lock_memory(lock_name=lock_name, locked_by=locked_by)

    def get_lock(self, lock_name: str) -> SchedulerLock | None:
        """Return the current lock for inspection/testing."""

        database_url = get_database_url() if self._use_database else None

        if database_url:
            try:
                return self._get_lock_db(
                    database_url=database_url,
                    lock_name=lock_name,
                )
            except Exception:
                logger.exception(
                    "scheduler_lock_db_get_failed",
                    extra={
                        "event": "scheduler_lock_db_get_failed",
                        "lock_name": lock_name,
                    },
                )

        return self._locks.get(lock_name)

    def clear(self) -> None:
        """Clear in-memory locks for tests."""

        self._locks.clear()

    def _acquire_lock_memory(
        self,
        *,
        lock_name: str,
        locked_by: str,
        locked_until: datetime,
        now: datetime,
    ) -> bool:
        """Acquire an in-memory lock when absent or expired."""

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

    def _release_lock_memory(self, *, lock_name: str, locked_by: str) -> bool:
        """Release an in-memory lock only when owned by the current job."""

        existing = self._locks.get(lock_name)

        if existing is None:
            return False

        if existing.locked_by != locked_by:
            return False

        del self._locks[lock_name]
        return True

    def _acquire_lock_db(
        self,
        *,
        database_url: str,
        lock_name: str,
        locked_by: str,
        locked_until: datetime,
        now: datetime,
    ) -> bool:
        """Acquire a database-backed lock when absent or expired."""

        with psycopg.connect(database_url, row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select
                        lock_name,
                        locked_by,
                        locked_until,
                        created_at,
                        updated_at
                    from scheduler_locks
                    where lock_name = %(lock_name)s
                    for update
                    """,
                    {"lock_name": lock_name},
                )
                existing = cursor.fetchone()

                if existing is not None and existing["locked_until"] > now:
                    return False

                if existing is None:
                    cursor.execute(
                        """
                        insert into scheduler_locks (
                            lock_name,
                            locked_by,
                            locked_until,
                            created_at,
                            updated_at
                        )
                        values (
                            %(lock_name)s,
                            %(locked_by)s,
                            %(locked_until)s,
                            %(created_at)s,
                            %(updated_at)s
                        )
                        """,
                        {
                            "lock_name": lock_name,
                            "locked_by": locked_by,
                            "locked_until": locked_until,
                            "created_at": now,
                            "updated_at": now,
                        },
                    )
                else:
                    cursor.execute(
                        """
                        update scheduler_locks
                        set
                            locked_by = %(locked_by)s,
                            locked_until = %(locked_until)s,
                            updated_at = %(updated_at)s
                        where lock_name = %(lock_name)s
                        """,
                        {
                            "lock_name": lock_name,
                            "locked_by": locked_by,
                            "locked_until": locked_until,
                            "updated_at": now,
                        },
                    )

        return True

    def _release_lock_db(
        self,
        *,
        database_url: str,
        lock_name: str,
        locked_by: str,
    ) -> bool:
        """Release a database-backed lock only when owned by the current job."""

        with psycopg.connect(database_url, row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    delete from scheduler_locks
                    where lock_name = %(lock_name)s
                      and locked_by = %(locked_by)s
                    returning lock_name
                    """,
                    {
                        "lock_name": lock_name,
                        "locked_by": locked_by,
                    },
                )
                deleted = cursor.fetchone()

        return deleted is not None

    def _get_lock_db(
        self,
        *,
        database_url: str,
        lock_name: str,
    ) -> SchedulerLock | None:
        """Return the current database-backed lock for inspection/testing."""

        with psycopg.connect(database_url, row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select
                        lock_name,
                        locked_by,
                        locked_until,
                        created_at,
                        updated_at
                    from scheduler_locks
                    where lock_name = %(lock_name)s
                    """,
                    {"lock_name": lock_name},
                )
                row = cursor.fetchone()

        if row is None:
            return None

        return SchedulerLock(
            lock_name=row["lock_name"],
            locked_by=row["locked_by"],
            locked_until=row["locked_until"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


scheduler_lock_repository = SchedulerLockRepository(use_database=True)