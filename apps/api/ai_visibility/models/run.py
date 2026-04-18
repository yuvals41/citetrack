"""Run domain models — LLM execution records."""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from ai_visibility.models.mention import CitationRecord


class RunStatus(str, Enum):
    """Enum for run status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_PARTIAL_FAILURES = "completed_with_partial_failures"
    FAILED = "failed"


class RunResult(BaseModel):
    """RunResult model — output from a single LLM run."""

    workspace_id: str = Field(..., description="Workspace ID (multi-tenant scoping key)")
    provider: str = Field(..., min_length=1, description="LLM provider (openai, anthropic, etc.)")
    model: str = Field(..., min_length=1, description="Model name (gpt-4, claude-3, etc.)")
    prompt_version: str = Field(..., min_length=1, description="Prompt version ID used")
    parser_version: str = Field(..., min_length=1, description="Parser version ID used")
    citations: list[CitationRecord] = Field(..., description="List of citations found")
    raw_response: str | None = Field(default=None, description="Raw LLM response text")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "workspace_id": "ws_123",
                "provider": "openai",
                "model": "gpt-4",
                "prompt_version": "pv_123",
                "parser_version": "parser_v1",
                "citations": [
                    {
                        "url": "https://example.com",
                        "domain": "example.com",
                        "status": "found",
                    }
                ],
                "raw_response": "Raw LLM output...",
            }
        }


class Run(BaseModel):
    """Run model — complete LLM execution record."""

    id: str = Field(..., description="Unique run ID")
    workspace_id: str = Field(..., description="Workspace ID (multi-tenant scoping key)")
    provider: str = Field(..., min_length=1, description="LLM provider (openai, anthropic, etc.)")
    model: str = Field(..., min_length=1, description="Model name (gpt-4, claude-3, etc.)")
    prompt_version: str = Field(..., min_length=1, description="Prompt version ID used")
    parser_version: str = Field(..., min_length=1, description="Parser version ID used")
    citations: list[CitationRecord] = Field(..., description="List of citations found")
    status: RunStatus = Field(..., description="Run status")
    started_at: datetime = Field(..., description="Run start timestamp")
    completed_at: datetime | None = Field(default=None, description="Run completion timestamp")
    error_message: str | None = Field(default=None, description="Error message if failed")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": "run_123",
                "workspace_id": "ws_123",
                "provider": "openai",
                "model": "gpt-4",
                "prompt_version": "pv_123",
                "parser_version": "parser_v1",
                "citations": [
                    {
                        "url": "https://example.com",
                        "domain": "example.com",
                        "status": "found",
                    }
                ],
                "status": "completed",
                "started_at": "2026-03-08T10:00:00",
                "completed_at": "2026-03-08T10:05:00",
                "error_message": None,
            }
        }
