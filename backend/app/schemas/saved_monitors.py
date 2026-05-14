"""Schemas for Saved Monitors v2."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


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


class SavedMonitorCreate(BaseModel):
    """Request body for creating a saved monitor."""

    name: str = Field(..., min_length=2, max_length=120)
    query: str = Field(..., min_length=2, max_length=200)
    module: SavedMonitorModule


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


class SavedMonitorRun(BaseModel):
    """Saved monitor manual run-history response model."""

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
