"""Routes for Saved Monitors v2 backend foundation."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.db.saved_monitor_repository import saved_monitor_repository
from app.schemas.saved_monitors import SavedMonitor, SavedMonitorCreate

router = APIRouter(prefix="/api/v1/saved-monitors", tags=["saved-monitors"])


@router.get("", response_model=list[SavedMonitor])
def list_saved_monitors() -> list[SavedMonitor]:
    """List saved monitors."""

    return saved_monitor_repository.list()


@router.post(
    "",
    response_model=SavedMonitor,
    status_code=status.HTTP_201_CREATED,
)
def create_saved_monitor(payload: SavedMonitorCreate) -> SavedMonitor:
    """Create a saved monitor.

    This foundation stores monitor definitions only. It does not run searches,
    schedule refreshes, send alerts, or call openFDA yet.
    """

    return saved_monitor_repository.create(payload)


@router.delete("/{monitor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_monitor(monitor_id: UUID) -> None:
    """Delete a saved monitor by ID."""

    deleted = saved_monitor_repository.delete(monitor_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved monitor not found",
        )
