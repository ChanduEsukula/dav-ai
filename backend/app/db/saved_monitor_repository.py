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
