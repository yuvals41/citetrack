from enum import Enum

from pydantic import BaseModel, Field


class DegradedReason(str, Enum):
    MISSING_API_KEY = "missing_api_key"
    PROVIDER_FAILURE = "provider_failure"
    EMPTY_HISTORY = "empty_history"
    PARSE_FAILURE = "parse_failure"
    SCHEDULER_MISS = "scheduler_miss"
    WORKSPACE_NOT_FOUND = "workspace_not_found"


class DegradedState(BaseModel):
    reason: DegradedReason
    message: str = Field(..., min_length=1)
    recoverable: bool
    context: dict[str, object] | None = None


def is_degraded(state: DegradedState | None) -> bool:
    return state is not None
