from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ScanSchedule(str, Enum):
    OFF = "off"
    DAILY = "daily"
    WEEKLY = "weekly"


class WorkspaceSettings(BaseModel):
    workspace_slug: str
    name: str
    scan_schedule: ScanSchedule
    created_at: datetime | None = None
    degraded: dict[str, str] | None = None


class WorkspaceSettingsUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    scan_schedule: ScanSchedule | None = None
