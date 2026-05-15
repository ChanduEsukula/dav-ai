"""Schemas for Saved Monitors v2."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class SavedMonitorModule(str, Enum):
    """Allowed modules for saved monitors."""

    RECALLRADAR = "recallradar"
    DRUGSIGNAL = "drugsignal"


class SavedMonitorStatus(str, Enum):
    """Saved monitor status values."""

    NOT_CHECKED = "not_checked"
    CHECKED = "checked"
    ERROR = "error"


class SavedMonitorRunStatus(str, Enum):
    """Saved monitor run-history status values."""

    SUCCESS = "success"
    ERROR = "error"


class SavedMonitorScheduledStatus(str, Enum):
    """Saved monitor scheduled refresh status values."""

    SUCCESS = "success"
    ERROR = "error"
    SKIPPED = "skipped"


class SavedMonitorCreate(BaseModel):
    """Request body for creating a saved monitor."""

    name: str = Field(..., min_length=2, max_length=120)
    query: str = Field(..., min_length=2, max_length=200)
    module: SavedMonitorModule


class SavedMonitorScheduleUpdate(BaseModel):
    """Request body for future saved monitor schedule updates.

    This model is backend foundation only. Scheduled refresh UI and protected
    schedule-update routes should be added in a later sprint.
    """

    refresh_enabled: bool
    refresh_interval_minutes: Optional[int] = None
    next_run_at: Optional[datetime] = None

    @field_validator("refresh_interval_minutes")
    @classmethod
    def validate_refresh_interval(cls, value: Optional[int]) -> Optional[int]:
        """Require positive refresh intervals when one is provided."""

        if value is not None and value <= 0:
            raise ValueError("refresh_interval_minutes must be greater than 0")
        return value


class SavedMonitor(BaseModel):
    """Saved monitor response model."""

    id: UUID
    name: str
    query: str
    module: SavedMonitorModule
    created_at: datetime
    last_checked_at: Optional[datetime] = None
    latest_audit_id: Optional[str] = None
    latest_score: Optional[int] = None
    previous_score: Optional[int] = None
    latest_record_count: Optional[int] = None
    previous_record_count: Optional[int] = None
    status: SavedMonitorStatus = SavedMonitorStatus.NOT_CHECKED
    refresh_enabled: bool = False
    refresh_interval_minutes: Optional[int] = None
    next_run_at: Optional[datetime] = None
    last_scheduled_run_at: Optional[datetime] = None
    last_scheduled_status: Optional[SavedMonitorScheduledStatus] = None


class SavedMonitorRun(BaseModel):
    """Saved monitor manual or scheduled run-history response model."""

    run_id: UUID
    monitor_id: UUID
    module: SavedMonitorModule
    query: str
    status: SavedMonitorRunStatus
    record_count: Optional[int] = None
    score: Optional[int] = None
    score_label: Optional[str] = None
    audit_id: Optional[str] = None
    created_at: datetime
    error_message: Optional[str] = None