from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


UserRole = Literal[
    "consumer",
    "pharmacy",
    "clinic",
    "public_health_analyst",
    "student_researcher",
]

AlertFrequency = Literal["none", "weekly", "monthly"]
ReportStyle = Literal["simple", "technical", "pharmacy_clinic"]


class UserProfile(BaseModel):
    user_id: UUID
    role: UserRole | None = None
    state: str | None = None
    zip_code: str | None = None
    alert_interests: list[str] = Field(default_factory=list)
    alert_frequency: AlertFrequency | None = None
    report_style: ReportStyle | None = None
    created_at: datetime
    updated_at: datetime


class UserProfileUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    role: UserRole | None = None
    state: str | None = Field(default=None, max_length=2)
    zip_code: str | None = Field(default=None, max_length=10)
    alert_interests: list[str] = Field(default_factory=list, max_length=12)
    alert_frequency: AlertFrequency | None = None
    report_style: ReportStyle | None = None

    @field_validator("state")
    @classmethod
    def normalize_state(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return value.strip().upper()

    @field_validator("zip_code")
    @classmethod
    def normalize_zip_code(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        cleaned = value.strip()
        if len(cleaned) < 5:
            raise ValueError("ZIP code must be at least 5 characters when provided.")
        return cleaned

    @field_validator("alert_interests")
    @classmethod
    def normalize_alert_interests(cls, values: list[str]) -> list[str]:
        cleaned: list[str] = []
        for value in values:
            normalized = " ".join(value.strip().split())
            if normalized and normalized not in cleaned:
                cleaned.append(normalized)
        return cleaned[:12]
