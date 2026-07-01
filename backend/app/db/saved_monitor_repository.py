"""Repository for Saved Monitors v2.

Uses PostgreSQL/Supabase when DATABASE_URL is configured. Falls back to
in-memory storage when the database is not configured. Local/test instances may
also fall back after database failures, but deployed environments fail closed.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4

import psycopg
from psycopg.rows import dict_row

from app.db.database import get_database_url, is_deployed_environment
from app.schemas.saved_monitors import (
    SavedMonitor,
    SavedMonitorCreate,
    SavedMonitorModule,
    SavedMonitorRun,
    SavedMonitorRunStatus,
    SavedMonitorScheduledStatus,
    SavedMonitorStatus,
)

logger = logging.getLogger("dav_ai.saved_monitors")


class SavedMonitorPersistenceError(RuntimeError):
    """Raised when configured durable persistence fails in deployed mode."""


class SavedMonitorRepository:
    """Saved monitor repository with PostgreSQL persistence and memory fallback."""

    def __init__(self) -> None:
        self._items: dict[UUID, SavedMonitor] = {}
        self._runs: dict[UUID, list[SavedMonitorRun]] = {}

    def _database_url(self) -> str | None:
        return get_database_url()

    def _handle_database_failure(
        self,
        *,
        event: str,
        exc: Exception,
        extra: dict[str, str] | None = None,
    ) -> None:
        log_extra = {"event": event}
        if extra:
            log_extra.update(extra)

        logger.exception(event, extra=log_extra)

        if is_deployed_environment():
            raise SavedMonitorPersistenceError(
                "Saved monitor database operation failed in deployed mode."
            ) from exc

    def _row_to_monitor(self, row) -> SavedMonitor:
        return SavedMonitor(
            id=row["id"],
            user_id=row.get("user_id"),
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
            refresh_enabled=row.get("refresh_enabled", False),
            refresh_interval_minutes=row.get("refresh_interval_minutes"),
            next_run_at=row.get("next_run_at"),
            last_scheduled_run_at=row.get("last_scheduled_run_at"),
            last_scheduled_status=(
                SavedMonitorScheduledStatus(row["last_scheduled_status"])
                if row.get("last_scheduled_status")
                else None
            ),
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

    def _monitor_select_columns(self) -> str:
        return """
            id,
            user_id,
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
            status,
            refresh_enabled,
            refresh_interval_minutes,
            next_run_at,
            last_scheduled_run_at,
            last_scheduled_status
        """

    def _monitor_belongs_to_user(
        self,
        monitor: SavedMonitor,
        user_id: UUID | None,
    ) -> bool:
        if user_id is None:
            return True
        return monitor.user_id == user_id

    def _list_memory(self, user_id: UUID | None = None) -> list[SavedMonitor]:
        return sorted(
            [
                monitor
                for monitor in self._items.values()
                if self._monitor_belongs_to_user(monitor, user_id)
            ],
            key=lambda monitor: monitor.created_at,
            reverse=True,
        )

    def _list_runs_memory(self, monitor_id: UUID) -> list[SavedMonitorRun]:
        return sorted(
            self._runs.get(monitor_id, []),
            key=lambda run: run.created_at,
            reverse=True,
        )

    def list(self, user_id: UUID | None = None) -> list[SavedMonitor]:
        """Return saved monitors sorted by newest first."""

        database_url = self._database_url()
        if not database_url:
            return self._list_memory(user_id)

        try:
            with psycopg.connect(database_url, row_factory=dict_row) as connection:
                with connection.cursor() as cursor:
                    if user_id is None:
                        cursor.execute(
                            f"""
                            select
                                {self._monitor_select_columns()}
                            from saved_monitors
                            order by created_at desc
                            """
                        )
                    else:
                        cursor.execute(
                            f"""
                            select
                                {self._monitor_select_columns()}
                            from saved_monitors
                            where user_id = %(user_id)s
                            order by created_at desc
                            """,
                            {"user_id": user_id},
                        )
                    rows = cursor.fetchall()

            return [self._row_to_monitor(row) for row in rows]

        except Exception as exc:
            self._handle_database_failure(event="saved_monitor_list_failed", exc=exc)
            return self._list_memory(user_id)

    def list_saved_monitors(self, user_id: UUID) -> list[SavedMonitor]:
        """Return saved monitors owned by one authenticated user."""

        return self.list(user_id=user_id)

    def get(
        self,
        monitor_id: UUID,
        *,
        user_id: UUID | None = None,
    ) -> SavedMonitor | None:
        """Return one saved monitor by ID."""

        database_url = self._database_url()
        if not database_url:
            monitor = self._items.get(monitor_id)
            if monitor is None or not self._monitor_belongs_to_user(monitor, user_id):
                return None
            return monitor

        try:
            with psycopg.connect(database_url, row_factory=dict_row) as connection:
                with connection.cursor() as cursor:
                    if user_id is None:
                        cursor.execute(
                            f"""
                            select
                                {self._monitor_select_columns()}
                            from saved_monitors
                            where id = %(id)s
                            """,
                            {"id": monitor_id},
                        )
                    else:
                        cursor.execute(
                            f"""
                            select
                                {self._monitor_select_columns()}
                            from saved_monitors
                            where id = %(id)s
                              and user_id = %(user_id)s
                            """,
                            {
                                "id": monitor_id,
                                "user_id": user_id,
                            },
                        )
                    row = cursor.fetchone()

            if row is None:
                return None

            return self._row_to_monitor(row)

        except Exception as exc:
            self._handle_database_failure(
                event="saved_monitor_get_failed",
                exc=exc,
                extra={"monitor_id": str(monitor_id)},
            )
            monitor = self._items.get(monitor_id)
            if monitor is None or not self._monitor_belongs_to_user(monitor, user_id):
                return None
            return monitor

    def get_saved_monitor(
        self,
        user_id: UUID,
        monitor_id: UUID,
    ) -> SavedMonitor | None:
        """Return one saved monitor only when owned by the user."""

        return self.get(monitor_id, user_id=user_id)

    def exists_by_module_and_query(
        self,
        *,
        module: SavedMonitorModule,
        query: str,
        user_id: UUID | None = None,
    ) -> bool:
        """Return True when a saved monitor already exists for module/query."""

        normalized_query = query.strip().lower()

        database_url = self._database_url()
        if not database_url:
            return any(
                monitor.module == module
                and monitor.query.strip().lower() == normalized_query
                and self._monitor_belongs_to_user(monitor, user_id)
                for monitor in self._items.values()
            )

        try:
            with psycopg.connect(database_url, row_factory=dict_row) as connection:
                with connection.cursor() as cursor:
                    if user_id is None:
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
                    else:
                        cursor.execute(
                            """
                            select 1
                            from saved_monitors
                            where user_id = %(user_id)s
                              and module = %(module)s
                              and lower(trim(query)) = %(query)s
                            limit 1
                            """,
                            {
                                "user_id": user_id,
                                "module": module.value,
                                "query": normalized_query,
                            },
                        )
                    row = cursor.fetchone()

            return row is not None

        except Exception as exc:
            self._handle_database_failure(
                event="saved_monitor_duplicate_check_failed",
                exc=exc,
            )
            return any(
                monitor.module == module
                and monitor.query.strip().lower() == normalized_query
                and self._monitor_belongs_to_user(monitor, user_id)
                for monitor in self._items.values()
            )

    def create(
        self,
        payload: SavedMonitorCreate,
        *,
        user_id: UUID | None = None,
    ) -> SavedMonitor:
        """Create a saved monitor with default not-checked state."""

        monitor = SavedMonitor(
            id=uuid4(),
            user_id=user_id,
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
            refresh_enabled=False,
            refresh_interval_minutes=None,
            next_run_at=None,
            last_scheduled_run_at=None,
            last_scheduled_status=None,
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
                            user_id,
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
                            status,
                            refresh_enabled,
                            refresh_interval_minutes,
                            next_run_at,
                            last_scheduled_run_at,
                            last_scheduled_status
                        )
                        values (
                            %(id)s,
                            %(user_id)s,
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
                            %(status)s,
                            %(refresh_enabled)s,
                            %(refresh_interval_minutes)s,
                            %(next_run_at)s,
                            %(last_scheduled_run_at)s,
                            %(last_scheduled_status)s
                        )
                        """,
                        {
                            "id": monitor.id,
                            "user_id": monitor.user_id,
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
                            "refresh_enabled": monitor.refresh_enabled,
                            "refresh_interval_minutes": monitor.refresh_interval_minutes,
                            "next_run_at": monitor.next_run_at,
                            "last_scheduled_run_at": monitor.last_scheduled_run_at,
                            "last_scheduled_status": (
                                monitor.last_scheduled_status.value
                                if monitor.last_scheduled_status
                                else None
                            ),
                        },
                    )

            return monitor

        except Exception as exc:
            self._handle_database_failure(
                event="saved_monitor_create_failed",
                exc=exc,
            )
            self._items[monitor.id] = monitor
            return monitor

    def create_saved_monitor(
        self,
        user_id: UUID,
        payload: SavedMonitorCreate,
    ) -> SavedMonitor:
        """Create a saved monitor owned by one authenticated user."""

        return self.create(payload, user_id=user_id)

    def list_due_for_refresh(
        self,
        *,
        now: datetime,
        limit: int = 10,
    ) -> list[SavedMonitor]:
        """Return enabled saved monitors due for scheduled refresh."""

        safe_limit = max(1, min(limit, 50))

        database_url = self._database_url()
        if not database_url:
            due_monitors = [
                monitor
                for monitor in self._items.values()
                if monitor.refresh_enabled
                and monitor.next_run_at is not None
                and monitor.next_run_at <= now
            ]
            return sorted(due_monitors, key=lambda monitor: monitor.next_run_at)[
                :safe_limit
            ]

        try:
            with psycopg.connect(database_url, row_factory=dict_row) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"""
                        select
                            {self._monitor_select_columns()}
                        from saved_monitors
                        where refresh_enabled = true
                          and next_run_at is not null
                          and next_run_at <= %(now)s
                        order by next_run_at asc
                        limit %(limit)s
                        """,
                        {
                            "now": now,
                            "limit": safe_limit,
                        },
                    )
                    rows = cursor.fetchall()

            return [self._row_to_monitor(row) for row in rows]

        except Exception as exc:
            self._handle_database_failure(
                event="saved_monitor_due_list_failed",
                exc=exc,
            )
            due_monitors = [
                monitor
                for monitor in self._items.values()
                if monitor.refresh_enabled
                and monitor.next_run_at is not None
                and monitor.next_run_at <= now
            ]
            return sorted(due_monitors, key=lambda monitor: monitor.next_run_at)[
                :safe_limit
            ]

    def update_schedule_after_run(
        self,
        monitor_id: UUID,
        *,
        next_run_at: datetime | None,
        last_scheduled_run_at: datetime,
        last_scheduled_status: SavedMonitorScheduledStatus,
    ) -> SavedMonitor | None:
        """Update scheduling metadata after a scheduled refresh attempt."""

        existing = self.get(monitor_id)
        if existing is None:
            return None

        updated = existing.model_copy(
            update={
                "next_run_at": next_run_at,
                "last_scheduled_run_at": last_scheduled_run_at,
                "last_scheduled_status": last_scheduled_status,
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
                            next_run_at = %(next_run_at)s,
                            last_scheduled_run_at = %(last_scheduled_run_at)s,
                            last_scheduled_status = %(last_scheduled_status)s
                        where id = %(id)s
                        """,
                        {
                            "id": monitor_id,
                            "next_run_at": updated.next_run_at,
                            "last_scheduled_run_at": updated.last_scheduled_run_at,
                            "last_scheduled_status": (
                                updated.last_scheduled_status.value
                                if updated.last_scheduled_status
                                else None
                            ),
                        },
                    )

            return updated

        except Exception as exc:
            self._handle_database_failure(
                event="saved_monitor_schedule_update_failed",
                exc=exc,
                extra={"monitor_id": str(monitor_id)},
            )
            self._items[monitor_id] = updated
            return updated

    def update_after_run(
        self,
        monitor_id: UUID,
        *,
        user_id: UUID | None = None,
        latest_audit_id: str | None,
        latest_score: int | None,
        latest_record_count: int | None,
    ) -> SavedMonitor | None:
        """Update a saved monitor after a manual or scheduled run check."""

        existing = self.get(monitor_id, user_id=user_id)
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
                    params = {
                        "id": monitor_id,
                        "user_id": user_id,
                        "previous_score": updated.previous_score,
                        "previous_record_count": updated.previous_record_count,
                        "latest_audit_id": updated.latest_audit_id,
                        "latest_score": updated.latest_score,
                        "latest_record_count": updated.latest_record_count,
                        "last_checked_at": updated.last_checked_at,
                        "status": updated.status.value,
                    }
                    user_filter = (
                        "and user_id = %(user_id)s"
                        if user_id is not None
                        else ""
                    )
                    cursor.execute(
                        f"""
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
                        {user_filter}
                        """,
                        params,
                    )

            return updated

        except Exception as exc:
            self._handle_database_failure(
                event="saved_monitor_update_after_run_failed",
                exc=exc,
                extra={"monitor_id": str(monitor_id)},
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
        """Persist one saved monitor run-history row."""

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

        except Exception as exc:
            self._handle_database_failure(
                event="saved_monitor_run_create_failed",
                exc=exc,
                extra={"monitor_id": str(monitor.id)},
            )
            self._runs.setdefault(monitor.id, []).append(run)
            return run

    def record_run(
        self,
        user_id: UUID,
        monitor_id: UUID,
        *,
        status: SavedMonitorRunStatus,
        record_count: int | None = None,
        score: int | None = None,
        score_label: str | None = None,
        audit_id: str | None = None,
        error_message: str | None = None,
    ) -> SavedMonitorRun | None:
        """Persist one run-history row only when the user owns the monitor."""

        monitor = self.get_saved_monitor(user_id, monitor_id)
        if monitor is None:
            return None

        return self.create_run(
            monitor,
            status=status,
            record_count=record_count,
            score=score,
            score_label=score_label,
            audit_id=audit_id,
            error_message=error_message,
        )

    def list_runs(
        self,
        monitor_id: UUID,
        limit: int = 10,
        *,
        user_id: UUID | None = None,
    ) -> list[SavedMonitorRun]:
        """Return recent run-history rows for one saved monitor."""

        safe_limit = max(1, min(limit, 50))

        if user_id is not None and self.get(monitor_id, user_id=user_id) is None:
            return []

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

        except Exception as exc:
            self._handle_database_failure(
                event="saved_monitor_run_list_failed",
                exc=exc,
                extra={"monitor_id": str(monitor_id)},
            )
            return self._list_runs_memory(monitor_id)[:safe_limit]

    def mark_error(
        self,
        monitor_id: UUID,
        *,
        user_id: UUID | None = None,
    ) -> SavedMonitor | None:
        """Mark a saved monitor run as failed."""

        existing = self.get(monitor_id, user_id=user_id)
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
                    params = {
                        "id": monitor_id,
                        "user_id": user_id,
                        "last_checked_at": updated.last_checked_at,
                        "status": updated.status.value,
                    }
                    user_filter = (
                        "and user_id = %(user_id)s"
                        if user_id is not None
                        else ""
                    )
                    cursor.execute(
                        f"""
                        update saved_monitors
                        set
                            last_checked_at = %(last_checked_at)s,
                            status = %(status)s
                        where id = %(id)s
                        {user_filter}
                        """,
                        params,
                    )

            return updated

        except Exception as exc:
            self._handle_database_failure(
                event="saved_monitor_mark_error_failed",
                exc=exc,
                extra={"monitor_id": str(monitor_id)},
            )
            self._items[monitor_id] = updated
            return updated

    def delete(
        self,
        monitor_id: UUID,
        *,
        user_id: UUID | None = None,
    ) -> bool:
        """Delete a saved monitor. Returns True when deleted."""

        database_url = self._database_url()
        if not database_url:
            monitor = self._items.get(monitor_id)
            if monitor is None or not self._monitor_belongs_to_user(monitor, user_id):
                return False

            del self._items[monitor_id]
            self._runs.pop(monitor_id, None)
            return True

        try:
            with psycopg.connect(database_url, row_factory=dict_row) as connection:
                with connection.cursor() as cursor:
                    if user_id is None:
                        cursor.execute(
                            """
                            delete from saved_monitors
                            where id = %(id)s
                            """,
                            {"id": monitor_id},
                        )
                    else:
                        cursor.execute(
                            """
                            delete from saved_monitors
                            where id = %(id)s
                              and user_id = %(user_id)s
                            """,
                            {
                                "id": monitor_id,
                                "user_id": user_id,
                            },
                        )
                    deleted = cursor.rowcount > 0

            if deleted:
                self._items.pop(monitor_id, None)
                self._runs.pop(monitor_id, None)

            return deleted

        except Exception as exc:
            self._handle_database_failure(
                event="saved_monitor_delete_failed",
                exc=exc,
                extra={"monitor_id": str(monitor_id)},
            )

            monitor = self._items.get(monitor_id)
            if monitor is None or not self._monitor_belongs_to_user(monitor, user_id):
                return False

            del self._items[monitor_id]
            self._runs.pop(monitor_id, None)
            return True

    def delete_saved_monitor(self, user_id: UUID, monitor_id: UUID) -> bool:
        """Delete one saved monitor only when owned by the user."""

        return self.delete(monitor_id, user_id=user_id)

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
                    except Exception as exc:
                        self._handle_database_failure(
                            event="saved_monitor_runs_clear_failed",
                            exc=exc,
                        )
                        connection.rollback()
                    cursor.execute("delete from saved_monitors")

        except Exception as exc:
            self._handle_database_failure(
                event="saved_monitor_clear_failed",
                exc=exc,
            )


saved_monitor_repository = SavedMonitorRepository()
