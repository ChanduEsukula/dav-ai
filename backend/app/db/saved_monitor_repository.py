"""Repository for Saved Monitors v2.

Uses PostgreSQL/Supabase when DATABASE_URL is configured. Falls back to
in-memory storage when the database is not configured or an operation fails.
This keeps local/test development safe while enabling persistence in deployed
environments after the saved_monitors table is created.
"""

from __future__ import annotations

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
    SavedMonitorRun,
    SavedMonitorRunStatus,
    SavedMonitorStatus,
)

logger = logging.getLogger("medtrek.saved_monitors")


class SavedMonitorRepository:
    """Saved monitor repository with PostgreSQL persistence and memory fallback."""

    def __init__(self) -> None:
        self._items: dict[UUID, SavedMonitor] = {}
        self._runs: dict[UUID, list[SavedMonitorRun]] = {}

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

    def _row_to_run(self, row) -> SavedMonitorRun:
        return SavedMonitorRun(
            run_id=row["run_id"],
            monitor_id=row["monitor_id"],
            module=SavedMonitorModule(row["module"]),
            query=row["query"],
            status=SavedMonitorRunStatus(row["status"]),
            record_count=row["record_count"],
            score=row["score"],
            score_label=row["score_label"],
            audit_id=str(row["audit_id"]) if row["audit_id"] else None,
            created_at=row["created_at"],
            error_message=row["error_message"],
        )

    def _list_memory(self) -> list[SavedMonitor]:
        return sorted(
            self._items.values(),
            key=lambda monitor: monitor.created_at,
            reverse=True,
        )

    def _list_runs_memory(self, monitor_id: UUID) -> list[SavedMonitorRun]:
        return sorted(
            self._runs.get(monitor_id, []),
            key=lambda run: run.created_at,
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

    def exists_by_module_and_query(
        self,
        *,
        module: SavedMonitorModule,
        query: str,
    ) -> bool:
        """Return True when a saved monitor already exists for module/query."""

        normalized_query = query.strip().lower()

        database_url = self._database_url()
        if not database_url:
            return any(
                monitor.module == module
                and monitor.query.strip().lower() == normalized_query
                for monitor in self._items.values()
            )

        try:
            with psycopg.connect(database_url, row_factory=dict_row) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        select 1
                        from saved_monitors
                        where module = %(module)s
                          and lower(trim(query)) = %(query)s
                        limit 1
                        """,
                        {
                            "module": module.value,
                            "query": normalized_query,
                        },
                    )
                    row = cursor.fetchone()

            return row is not None

        except Exception:
            logger.exception(
                "saved_monitor_duplicate_check_failed",
                extra={"event": "saved_monitor_duplicate_check_failed"},
            )
            return any(
                monitor.module == module
                and monitor.query.strip().lower() == normalized_query
                for monitor in self._items.values()
            )

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

    def create_run(
        self,
        monitor: SavedMonitor,
        *,
        status: SavedMonitorRunStatus,
        record_count: int | None = None,
        score: int | None = None,
        score_label: str | None = None,
        audit_id: str | None = None,
        error_message: str | None = None,
    ) -> SavedMonitorRun:
        """Persist one manual saved monitor run-history row."""

        run = SavedMonitorRun(
            run_id=uuid4(),
            monitor_id=monitor.id,
            module=monitor.module,
            query=monitor.query,
            status=status,
            record_count=record_count,
            score=score,
            score_label=score_label,
            audit_id=audit_id,
            created_at=datetime.now(timezone.utc),
            error_message=error_message,
        )

        database_url = self._database_url()
        if not database_url:
            self._runs.setdefault(monitor.id, []).append(run)
            return run

        try:
            with psycopg.connect(database_url, row_factory=dict_row) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        insert into saved_monitor_runs (
                            run_id,
                            monitor_id,
                            module,
                            query,
                            status,
                            record_count,
                            score,
                            score_label,
                            audit_id,
                            created_at,
                            error_message
                        )
                        values (
                            %(run_id)s,
                            %(monitor_id)s,
                            %(module)s,
                            %(query)s,
                            %(status)s,
                            %(record_count)s,
                            %(score)s,
                            %(score_label)s,
                            %(audit_id)s,
                            %(created_at)s,
                            %(error_message)s
                        )
                        """,
                        {
                            "run_id": run.run_id,
                            "monitor_id": run.monitor_id,
                            "module": run.module.value,
                            "query": run.query,
                            "status": run.status.value,
                            "record_count": run.record_count,
                            "score": run.score,
                            "score_label": run.score_label,
                            "audit_id": run.audit_id,
                            "created_at": run.created_at,
                            "error_message": run.error_message,
                        },
                    )

            return run

        except Exception:
            logger.exception(
                "saved_monitor_run_create_failed",
                extra={
                    "event": "saved_monitor_run_create_failed",
                    "monitor_id": str(monitor.id),
                },
            )
            self._runs.setdefault(monitor.id, []).append(run)
            return run

    def list_runs(self, monitor_id: UUID, limit: int = 10) -> list[SavedMonitorRun]:
        """Return recent manual run-history rows for one saved monitor."""

        safe_limit = max(1, min(limit, 50))
        database_url = self._database_url()
        if not database_url:
            return self._list_runs_memory(monitor_id)[:safe_limit]

        try:
            with psycopg.connect(database_url, row_factory=dict_row) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        select
                            run_id,
                            monitor_id,
                            module,
                            query,
                            status,
                            record_count,
                            score,
                            score_label,
                            audit_id,
                            created_at,
                            error_message
                        from saved_monitor_runs
                        where monitor_id = %(monitor_id)s
                        order by created_at desc
                        limit %(limit)s
                        """,
                        {
                            "monitor_id": monitor_id,
                            "limit": safe_limit,
                        },
                    )
                    rows = cursor.fetchall()

            return [self._row_to_run(row) for row in rows]

        except Exception:
            logger.exception(
                "saved_monitor_run_list_failed",
                extra={
                    "event": "saved_monitor_run_list_failed",
                    "monitor_id": str(monitor_id),
                },
            )
            return self._list_runs_memory(monitor_id)[:safe_limit]

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
                self._runs.pop(monitor_id, None)

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
            self._runs.pop(monitor_id, None)
            return True

    def clear(self) -> None:
        """Clear all saved monitors. Used by tests."""

        self._items.clear()
        self._runs.clear()

        database_url = self._database_url()
        if not database_url:
            return

        try:
            with psycopg.connect(database_url, row_factory=dict_row) as connection:
                with connection.cursor() as cursor:
                    try:
                        cursor.execute("delete from saved_monitor_runs")
                    except Exception:
                        logger.exception(
                            "saved_monitor_runs_clear_failed",
                            extra={"event": "saved_monitor_runs_clear_failed"},
                        )
                        connection.rollback()
                    cursor.execute("delete from saved_monitors")

        except Exception:
            logger.exception(
                "saved_monitor_clear_failed",
                extra={"event": "saved_monitor_clear_failed"},
            )


saved_monitor_repository = SavedMonitorRepository()
