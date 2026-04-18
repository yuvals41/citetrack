"""
Golden Contract for AI Visibility scan service.

These Pydantic models define the job input/output/progress shapes.
Both the worker (worker_job.py) and the SDK stay in sync with these definitions.
"""

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

try:
    from solaraai_job_sdk import BaseJobInput
except ImportError:
    BaseJobInput = BaseModel  # type: ignore[assignment,misc]


class PromptDefinition(BaseModel):
    """A single prompt to send to AI providers."""

    id: str
    template: str
    category: str = "custom"
    version: str = "1.0.0"


class LocationContext(BaseModel):
    """Geographic context for location-aware scanning."""

    country_code: str = ""
    country_name: str = ""
    city: str = ""
    region: str = ""


class ScanInput(BaseJobInput):
    """Input for an AI Visibility scan job. Fully self-contained."""

    brand_name: str = Field(..., description="Brand name as it should appear in prompts")
    domain: str = Field(..., description="Brand website domain")

    providers: list[str] = Field(
        ...,
        description="AI providers to scan: openai, anthropic, gemini, perplexity, grok, google_ai_overview, google_ai_mode_serpapi",
    )
    prompts: list[PromptDefinition] = Field(..., description="Prompts to send to each provider")

    competitors: list[str] = Field(default_factory=list, description="Competitor names for comparison prompts")
    location: LocationContext = Field(default_factory=LocationContext)

    max_prompts_per_provider: int = Field(default=3, description="Max prompts per provider")


class MentionResult(BaseModel):
    """A single mention/response from an AI provider."""

    provider: str
    model_name: str = ""
    prompt_id: str
    prompt_text: str
    raw_response: str
    brand_mentioned: bool = False
    brand_position: Optional[int] = None
    sentiment: Optional[str] = None
    sentiment_score: Optional[float] = None
    citations: list[dict[str, Any]] = Field(default_factory=list)
    reasoning: Optional[str] = None


class ScanMetrics(BaseModel):
    """Aggregated metrics from a scan."""

    visibility_score: float = 0.0
    citation_coverage: float = 0.0
    avg_position: float = 0.0
    total_prompts: int = 0
    total_mentioned: int = 0
    total_citations: int = 0


class ScanOutput(BaseModel):
    """Output from a completed AI Visibility scan."""

    job_id: str = ""
    status: str = "success"
    error: Optional[str] = None
    duration: float = 0.0

    mentions: list[MentionResult] = Field(default_factory=list)
    metrics: ScanMetrics = Field(default_factory=ScanMetrics)
    provider_results: dict[str, dict[str, Any]] = Field(default_factory=dict)


class ScanProgress(BaseModel):
    """Progress events emitted during scanning."""

    stage: Literal["queued", "scanning", "extracting", "complete"] = "queued"
    provider: Optional[str] = None
    prompts_completed: int = 0
    prompts_total: int = 0
    message: Optional[str] = None
