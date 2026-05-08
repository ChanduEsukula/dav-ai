"""In-memory repository for Saved Monitors v2 foundation.

This repository is intentionally lightweight for the first backend foundation.
It can later be replaced with a PostgreSQL-backed repository without changing
the route contract.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.schemas.saved_monitors import (
    SavedMonitor,
    SavedMonitorCreate,
    SavedMonitorStatus,
)


class InMemorySavedMonitorRepository:
    """Simple in-memory saved monitor repository."""

    def __init__(self) -> None:
        self._items: dict[UUID, SavedMonitor] = {}

    def list(self) -> list[SavedMonitor]:
        """Return saved monitors sorted by newest first."""

        return sorted(
            self._items.values(),
            key=lambda monitor: monitor.created_at,
            reverse=True,
        )

    def get(self, monitor_id: UUID) -> SavedMonitor | None:
        """Return one saved monitor by ID."""

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

        existing = self._items.get(monitor_id)
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
        self._items[monitor_id] = updated
        return updated

    def mark_error(self, monitor_id: UUID) -> SavedMonitor | None:
        """Mark a saved monitor run as failed."""

        existing = self._items.get(monitor_id)
        if existing is None:
            return None

        updated = existing.model_copy(
            update={
                "last_checked_at": datetime.now(timezone.utc),
                "status": SavedMonitorStatus.ERROR,
            }
        )
        self._items[monitor_id] = updated
        return updated

    def delete(self, monitor_id: UUID) -> bool:
        """Delete a saved monitor. Returns True when deleted."""

        if monitor_id not in self._items:
            return False

        del self._items[monitor_id]
        return True

    def clear(self) -> None:
        """Clear all saved monitors. Used by tests."""

        self._items.clear()


saved_monitor_repository = InMemorySavedMonitorRepository()
