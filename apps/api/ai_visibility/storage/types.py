from typing import Literal, NotRequired, TypedDict


ScanSchedule = Literal["daily", "weekly", "off"]


class WorkspaceRecord(TypedDict):
    id: str
    slug: str
    brand_name: str
    city: str
    region: str
    country: str
    created_at: str
    scan_schedule: NotRequired[ScanSchedule]


class RunRecord(TypedDict):
    id: str
    workspace_id: str
    provider: str
    model: str
    prompt_version: str
    parser_version: str
    status: str
    created_at: str
    raw_response: str | None
    error: str | None


class CitationRecord(TypedDict):
    url: str | None
    domain: str | None
    status: Literal["found", "no_citation"]


class MentionRecord(TypedDict):
    id: str
    workspace_id: str
    run_id: str
    brand_id: str
    mention_type: str
    text: str
    citation: CitationRecord


class MetricSnapshotRecord(TypedDict):
    id: str
    workspace_id: str
    brand_id: str
    formula_version: str
    visibility_score: float
    citation_coverage: float
    competitor_wins: int
    mention_count: int
    created_at: str


class RecommendationRecord(TypedDict):
    id: str
    workspace_id: str
    brand_id: str
    title: str
    description: str
    priority: str
    rule_triggers_json: str | None
    created_at: str


class ScanJobRecord(TypedDict):
    id: str
    workspace_slug: str
    strategy_version: str
    prompt_version: str
    created_at: str
    idempotency_key: str
    status: str
    scan_mode: str


class ScanExecutionRecord(TypedDict):
    id: str
    scan_job_id: str
    provider: str
    model_name: str
    model_version: str
    executed_at: str
    idempotency_key: str
    status: str


class PromptExecutionRecord(TypedDict):
    id: str
    scan_execution_id: str
    prompt_id: str
    prompt_text: str
    raw_response: str
    executed_at: str
    idempotency_key: str
    parser_version: str


class ObservationRecord(TypedDict):
    id: str
    prompt_execution_id: str
    brand_mentioned: bool
    brand_position: int | None
    response_excerpt: str
    idempotency_key: str
    strategy_version: str


class PromptExecutionCitationRecord(TypedDict):
    id: str
    prompt_execution_id: str
    url: str
    title: str
    cited_text: str | None
    idempotency_key: str
