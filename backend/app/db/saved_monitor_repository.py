"""Repository for Saved Monitors v2.

Uses PostgreSQL/Supabase when DATABASE_URL is configured. Falls back to
in-memory storage when the database is not configured or an operation fails.
This keeps local/test development safe while enabling persistence in deployed
environments after the saved_monitors table is created.
"""

import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4

import psycopg
from psycopg.rows import dict_row

from app.db.database import get_database_url
from app.schemas.saved_monitors import (
    SavedMonitor,
    SavedMonitorCreate,
    SavedMonitorModule,
    SavedMonitorStatus,
)

logger = logging.getLogger("medtrek.saved_monitors")


class SavedMonitorRepository:
    """Saved monitor repository with PostgreSQL persistence and memory fallback."""

    def __init__(self) -> None:
        self._items: dict[UUID, SavedMonitor] = {}

    def _database_url(self) -> str | None:
        return get_database_url()

    def _row_to_monitor(self, row) -> SavedMonitor:
        return SavedMonitor(
            id=row["id"],
            name=row["name"],
            query=row["query"],
            module=SavedMonitorModule(row["module"]),
            created_at=row["created_at"],
            last_checked_at=row["last_checked_at"],
            latest_audit_id=str(row["latest_audit_id"]) if row["latest_audit_id"] else None,
            latest_score=row["latest_score"],
            previous_score=row["previous_score"],
            latest_record_count=row["latest_record_count"],
            previous_record_count=row["previous_record_count"],
            status=SavedMonitorStatus(row["status"]),
        )

    def _list_memory(self) -> list[SavedMonitor]:
        return sorted(
            self._items.values(),
            key=lambda monitor: monitor.created_at,
            reverse=True,
        )

    def list(self) -> list[SavedMonitor]:
        """Return saved monitors sorted by newest first."""

        database_url = self._database_url()
        if not database_url:
            return self._list_memory()

        try:
            with psycopg.connect(database_url, row_factory=dict_row) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        select
                            id,
                            name,
                            query,
                            module,
                            created_at,
                            last_checked_at,
                            latest_audit_id,
                            latest_score,
                            previous_score,
                            latest_record_count,
                            previous_record_count,
                            status
                        from saved_monitors
                        order by created_at desc
                        """
                    )
                    rows = cursor.fetchall()

            return [self._row_to_monitor(row) for row in rows]

        except Exception:
            logger.exception(
                "saved_monitor_list_failed",
                extra={"event": "saved_monitor_list_failed"},
            )
            return self._list_memory()

    def get(self, monitor_id: UUID) -> SavedMonitor | None:
        """Return one saved monitor by ID."""

        database_url = self._database_url()
        if not database_url:
            return self._items.get(monitor_id)

        try:
            with psycopg.connect(database_url, row_factory=dict_row) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        select
                            id,
                            name,
                            query,
                            module,
                            created_at,
                            last_checked_at,
                            latest_audit_id,
                            latest_score,
                            previous_score,
                            latest_record_count,
                            previous_record_count,
                            status
                        from saved_monitors
                        where id = %(id)s
                        """,
                        {"id": monitor_id},
                    )
                    row = cursor.fetchone()

            if row is None:
                return None

            return self._row_to_monitor(row)

        except Exception:
            logger.exception(
                "saved_monitor_get_failed",
                extra={
                    "event": "saved_monitor_get_failed",
                    "monitor_id": str(monitor_id),
                },
            )
            return self._items.get(monitor_id)

    def create(self, payload: SavedMonitorCreate) -> SavedMonitor:
        """Create a saved monitor with default not-checked state."""

        monitor = SavedMonitor(
            id=uuid4(),
            name=payload.name,
            query=payload.query,
            module=payload.module,
            created_at=datetime.now(timezone.utc),
            last_checked_at=None,
            latest_audit_id=None,
            latest_score=None,
            previous_score=None,
            latest_record_count=None,
            previous_record_count=None,
            status=SavedMonitorStatus.NOT_CHECKED,
        )

        database_url = self._database_url()
        if not database_url:
            self._items[monitor.id] = monitor
            return monitor

        try:
            with psycopg.connect(database_url, row_factory=dict_row) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        insert into saved_monitors (
                            id,
                            name,
                            query,
                            module,
                            created_at,
                            last_checked_at,
                            latest_audit_id,
                            latest_score,
                            previous_score,
                            latest_record_count,
                            previous_record_count,
                            status
                        )
                        values (
                            %(id)s,
                            %(name)s,
                            %(query)s,
                            %(module)s,
                            %(created_at)s,
                            %(last_checked_at)s,
                            %(latest_audit_id)s,
                            %(latest_score)s,
                            %(previous_score)s,
                            %(latest_record_count)s,
                            %(previous_record_count)s,
                            %(status)s
                        )
                        """,
                        {
                            "id": monitor.id,
                            "name": monitor.name,
                            "query": monitor.query,
                            "module": monitor.module.value,
                            "created_at": monitor.created_at,
                            "last_checked_at": monitor.last_checked_at,
                            "latest_audit_id": monitor.latest_audit_id,
                            "latest_score": monitor.latest_score,
                            "previous_score": monitor.previous_score,
                            "latest_record_count": monitor.latest_record_count,
                            "previous_record_count": monitor.previous_record_count,
                            "status": monitor.status.value,
                        },
                    )

            return monitor

        except Exception:
            logger.exception(
                "saved_monitor_create_failed",
                extra={"event": "saved_monitor_create_failed"},
            )
            self._items[monitor.id] = monitor
            return monitor

    def update_after_run(
        self,
        monitor_id: UUID,
        *,
        latest_audit_id: str | None,
        latest_score: int | None,
        latest_record_count: int | None,
    ) -> SavedMonitor | None:
        """Update a saved monitor after a manual run check."""

        existing = self.get(monitor_id)
        if existing is None:
            return None

        updated = existing.model_copy(
            update={
                "previous_score": existing.latest_score,
                "previous_record_count": existing.latest_record_count,
                "latest_audit_id": latest_audit_id,
                "latest_score": latest_score,
                "latest_record_count": latest_record_count,
                "last_checked_at": datetime.now(timezone.utc),
                "status": SavedMonitorStatus.CHECKED,
            }
        )

        database_url = self._database_url()
        if not database_url:
            self._items[monitor_id] = updated
            return updated

        try:
            with psycopg.connect(database_url, row_factory=dict_row) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        update saved_monitors
                        set
                            previous_score = %(previous_score)s,
                            previous_record_count = %(previous_record_count)s,
                            latest_audit_id = %(latest_audit_id)s,
                            latest_score = %(latest_score)s,
                            latest_record_count = %(latest_record_count)s,
                            last_checked_at = %(last_checked_at)s,
                            status = %(status)s
                        where id = %(id)s
                        """,
                        {
                            "id": monitor_id,
                            "previous_score": updated.previous_score,
                            "previous_record_count": updated.previous_record_count,
                            "latest_audit_id": updated.latest_audit_id,
                            "latest_score": updated.latest_score,
                            "latest_record_count": updated.latest_record_count,
                            "last_checked_at": updated.last_checked_at,
                            "status": updated.status.value,
                        },
                    )

            return updated

        except Exception:
            logger.exception(
                "saved_monitor_update_after_run_failed",
                extra={
                    "event": "saved_monitor_update_after_run_failed",
                    "monitor_id": str(monitor_id),
                },
            )
            self._items[monitor_id] = updated
            return updated

    def mark_error(self, monitor_id: UUID) -> SavedMonitor | None:
        """Mark a saved monitor run as failed."""

        existing = self.get(monitor_id)
        if existing is None:
            return None

        updated = existing.model_copy(
            update={
                "last_checked_at": datetime.now(timezone.utc),
                "status": SavedMonitorStatus.ERROR,
            }
        )

        database_url = self._database_url()
        if not database_url:
            self._items[monitor_id] = updated
            return updated

        try:
            with psycopg.connect(database_url, row_factory=dict_row) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        update saved_monitors
                        set
                            last_checked_at = %(last_checked_at)s,
                            status = %(status)s
                        where id = %(id)s
                        """,
                        {
                            "id": monitor_id,
                            "last_checked_at": updated.last_checked_at,
                            "status": updated.status.value,
                        },
                    )

            return updated

        except Exception:
            logger.exception(
                "saved_monitor_mark_error_failed",
                extra={
                    "event": "saved_monitor_mark_error_failed",
                    "monitor_id": str(monitor_id),
                },
            )
            self._items[monitor_id] = updated
            return updated

    def delete(self, monitor_id: UUID) -> bool:
        """Delete a saved monitor. Returns True when deleted."""

        database_url = self._database_url()
        if not database_url:
            if monitor_id not in self._items:
                return False

            del self._items[monitor_id]
            return True

        try:
            with psycopg.connect(database_url, row_factory=dict_row) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        delete from saved_monitors
                        where id = %(id)s
                        """,
                        {"id": monitor_id},
                    )
                    deleted = cursor.rowcount > 0

            if deleted:
                self._items.pop(monitor_id, None)

            return deleted

        except Exception:
            logger.exception(
                "saved_monitor_delete_failed",
                extra={
                    "event": "saved_monitor_delete_failed",
                    "monitor_id": str(monitor_id),
                },
            )

            if monitor_id not in self._items:
                return False

            del self._items[monitor_id]
            return True

    def clear(self) -> None:
        """Clear all saved monitors. Used by tests for in-memory state."""

        self._items.clear()


saved_monitor_repository = SavedMonitorRepository()
