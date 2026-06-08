from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


ReportRole = Literal[
    "consumer",
    "pharmacy",
    "clinic",
    "public_health_analyst",
    "student_researcher",
]

ReportModule = Literal[
    "recallradar",
    "drugsignal",
    "foodradar",
    "both",
]


class SafetyIntelligenceReportRequest(BaseModel):
    """Request body for a public-data safety intelligence PDF report.

    This schema intentionally avoids PHI fields.
    """

    prepared_for: str = Field(min_length=2, max_length=120)
    organization: str | None = Field(default=None, max_length=160)
    role: ReportRole
    query: str = Field(min_length=2, max_length=120)
    module: ReportModule
    purpose: str | None = Field(default=None, max_length=500)