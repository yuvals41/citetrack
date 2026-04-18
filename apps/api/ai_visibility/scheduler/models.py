from typing import Literal

from pydantic import BaseModel, field_validator


class ScheduleDefinition(BaseModel):
    workspace_slug: str
    interval_hours: int = 24
    provider: str = "openai"
    model: str | None = None
    enabled: bool = True

    @field_validator("interval_hours")
    @classmethod
    def validate_interval(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("interval_hours must be > 0")
        return value


class ExecutionResult(BaseModel):
    schedule_id: str
    workspace_slug: str
    status: Literal["executed", "skipped_duplicate", "skipped_not_due", "failed", "dry_run"]
    run_id: str | None = None
    error_message: str | None = None
