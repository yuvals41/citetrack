from enum import Enum
from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field


class LifecycleStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED_WITH_PARTIAL_FAILURES = "completed_with_partial_failures"
    FAILED = "failed"
    COMPLETED = "completed"


ScanJobStatus = Literal[
    "queued",
    "running",
    "completed_with_partial_failures",
    "failed",
    "completed",
]
ScanMode = Literal["onboarding", "scheduled"]
ExecutionStatus = Literal[
    "queued",
    "running",
    "completed_with_partial_failures",
    "failed",
    "completed",
]


class ScanJob(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    workspace_slug: str = Field(..., min_length=1)
    strategy_version: str = Field(..., min_length=1)
    prompt_version: str = Field(..., min_length=1)
    created_at: str = Field(..., min_length=1)
    status: ScanJobStatus
    scan_mode: ScanMode


class ScanExecution(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    scan_job_id: str = Field(..., min_length=1)
    provider: str = Field(..., min_length=1)
    model_name: str = Field(..., min_length=1)
    model_version: str = Field(..., min_length=1)
    executed_at: str = Field(..., min_length=1)
    status: ExecutionStatus


class PromptExecution(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    scan_execution_id: str = Field(..., min_length=1)
    prompt_id: str = Field(..., min_length=1)
    prompt_text: str = Field(..., min_length=1)
    raw_response: str = Field(..., min_length=1)
    executed_at: str = Field(..., min_length=1)
    parser_version: str = Field(..., min_length=1)


class Observation(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    prompt_execution_id: str = Field(..., min_length=1)
    brand_mentioned: bool
    brand_position: int | None = None
    response_excerpt: str = Field(..., min_length=1)
    strategy_version: str = Field(..., min_length=1)


class Citation(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    prompt_execution_id: str = Field(..., min_length=1)
    url: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    cited_text: str | None = None


class DiagnosticFinding(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    workspace_slug: str = Field(..., min_length=1)
    finding_type: str = Field(..., min_length=1)
    reason_code: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence_refs: list[str] = Field(..., min_length=1)
    created_at: str = Field(..., min_length=1)
    rule_version: str = Field(..., min_length=1)
    applicability_context: str = Field(..., min_length=1)


class RecommendationItem(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    workspace_slug: str = Field(..., min_length=1)
    finding_id: str | None = None
    code: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)
    evidence_refs: list[str] = Field(..., min_length=1)
    impact: str = Field(..., min_length=1)
    next_step: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)
    rule_version: str = Field(..., min_length=1)


class SnapshotVersion(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    strategy_version: str = Field(..., min_length=1)
    model_version: str = Field(..., min_length=1)
    rule_version: str = Field(..., min_length=1)
    created_at: str = Field(..., min_length=1)
