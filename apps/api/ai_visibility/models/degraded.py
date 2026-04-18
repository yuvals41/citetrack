from enum import Enum

from pydantic import BaseModel, Field


class ErrorCode(str, Enum):
    MISSING_API_KEY = "missing_api_key"
    PROVIDER_TIMEOUT = "provider_timeout"
    PARSE_FAILURE = "parse_failure"
    RATE_LIMIT = "rate_limit"
    UNKNOWN = "unknown"


class FailedProvider(BaseModel):
    provider: str = Field(..., min_length=1, description="Provider name")
    error_code: ErrorCode = Field(..., description="Error code")
    error_message: str = Field(..., min_length=1, description="Human-readable error message")


class DegradedState(BaseModel):
    id: str = Field(..., description="Unique degraded state ID")
    workspace_id: str = Field(..., description="Workspace ID (multi-tenant scoping key)")
    is_degraded: bool = Field(..., description="Whether system is degraded")
    failed_providers: list[FailedProvider] = Field(..., description="List of failed providers")
    message: str = Field(..., min_length=1, description="Degradation message")
