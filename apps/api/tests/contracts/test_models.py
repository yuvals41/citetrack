"""Contract tests for all domain models — TDD approach."""

import pytest
from datetime import datetime
from pydantic import ValidationError

# These imports will fail until models are implemented
# That's the point of TDD — tests drive implementation


def test_workspace_create_minimal():
    """Workspace creation with minimal required fields."""
    from ai_visibility.models.workspace import WorkspaceCreate

    ws = WorkspaceCreate(
        name="Acme Corp",
        slug="acme",
    )
    assert ws.name == "Acme Corp"
    assert ws.slug == "acme"


def test_workspace_create_with_description():
    """Workspace creation with optional description."""
    from ai_visibility.models.workspace import WorkspaceCreate

    ws = WorkspaceCreate(
        name="Acme Corp",
        slug="acme",
        description="Test workspace",
    )
    assert ws.description == "Test workspace"


def test_workspace_full_model():
    """Full Workspace model with ID and timestamps."""
    from ai_visibility.models.workspace import Workspace

    now = datetime.utcnow()
    ws = Workspace(
        id="ws_123",
        name="Acme Corp",
        slug="acme",
        created_at=now,
        updated_at=now,
    )
    assert ws.id == "ws_123"
    assert ws.name == "Acme Corp"
    assert ws.slug == "acme"
    assert ws.created_at == now
    assert ws.updated_at == now


def test_brand_model():
    """Brand model with workspace_id."""
    from ai_visibility.models.brand import Brand

    brand = Brand(
        id="brand_123",
        workspace_id="ws_123",
        name="Acme",
        domain="acme.com",
    )
    assert brand.id == "brand_123"
    assert brand.workspace_id == "ws_123"
    assert brand.name == "Acme"
    assert brand.domain == "acme.com"


def test_competitor_model():
    """Competitor model with workspace_id."""
    from ai_visibility.models.brand import Competitor

    comp = Competitor(
        id="comp_123",
        workspace_id="ws_123",
        name="TechCorp",
        domain="techcorp.com",
    )
    assert comp.id == "comp_123"
    assert comp.workspace_id == "ws_123"
    assert comp.name == "TechCorp"
    assert comp.domain == "techcorp.com"


def test_prompt_model():
    """Prompt model with workspace_id."""
    from ai_visibility.models.prompt import Prompt

    prompt = Prompt(
        id="prompt_123",
        workspace_id="ws_123",
        name="Market Analysis",
        text="Analyze the market for...",
    )
    assert prompt.id == "prompt_123"
    assert prompt.workspace_id == "ws_123"
    assert prompt.name == "Market Analysis"
    assert prompt.text == "Analyze the market for..."


def test_prompt_version_model():
    """PromptVersion model with version tracking."""
    from ai_visibility.models.prompt import PromptVersion

    pv = PromptVersion(
        id="pv_123",
        prompt_id="prompt_123",
        version=1,
        text="Analyze the market for...",
    )
    assert pv.id == "pv_123"
    assert pv.prompt_id == "prompt_123"
    assert pv.version == 1
    assert pv.text == "Analyze the market for..."


def test_prompt_set_model():
    """PromptSet model for grouping prompts."""
    from ai_visibility.models.prompt import PromptSet

    ps = PromptSet(
        id="ps_123",
        workspace_id="ws_123",
        name="Q1 Analysis",
        prompt_ids=["prompt_123", "prompt_456"],
    )
    assert ps.id == "ps_123"
    assert ps.workspace_id == "ws_123"
    assert ps.name == "Q1 Analysis"
    assert ps.prompt_ids == ["prompt_123", "prompt_456"]


def test_citation_record_with_url():
    """CitationRecord with URL and domain."""
    from ai_visibility.models.mention import CitationRecord

    citation = CitationRecord(
        url="https://example.com/article",
        domain="example.com",
        status="found",
    )
    assert citation.url == "https://example.com/article"
    assert citation.domain == "example.com"
    assert citation.status == "found"


def test_citation_record_no_citation():
    """CitationRecord with no_citation status."""
    from ai_visibility.models.mention import CitationRecord

    citation = CitationRecord(
        url=None,
        domain=None,
        status="no_citation",
    )
    assert citation.url is None
    assert citation.domain is None
    assert citation.status == "no_citation"


def test_mention_type_enum():
    """MentionType enum has all required values."""
    from ai_visibility.models.mention import MentionType

    assert MentionType.EXPLICIT == "explicit"
    assert MentionType.IMPLICIT == "implicit"
    assert MentionType.COMPARATIVE == "comparative"
    assert MentionType.ABSENT == "absent"


def test_mention_model():
    """Mention model with all required fields."""
    from ai_visibility.models.mention import Mention, MentionType, CitationRecord

    citation = CitationRecord(
        url="https://example.com",
        domain="example.com",
        status="found",
    )

    mention = Mention(
        id="mention_123",
        run_id="run_123",
        brand_id="brand_123",
        mention_type=MentionType.EXPLICIT,
        text="Acme is a leader in...",
        citation=citation,
    )
    assert mention.id == "mention_123"
    assert mention.run_id == "run_123"
    assert mention.brand_id == "brand_123"
    assert mention.mention_type == MentionType.EXPLICIT
    assert mention.text == "Acme is a leader in..."
    assert mention.citation.url == "https://example.com"


def test_run_status_enum():
    """RunStatus enum has all required values."""
    from ai_visibility.models.run import RunStatus

    assert RunStatus.PENDING == "pending"
    assert RunStatus.RUNNING == "running"
    assert RunStatus.COMPLETED == "completed"
    assert RunStatus.COMPLETED_WITH_PARTIAL_FAILURES == "completed_with_partial_failures"
    assert RunStatus.FAILED == "failed"


def test_run_result_model():
    """RunResult model with all required fields."""
    from ai_visibility.models.run import RunResult
    from ai_visibility.models.mention import CitationRecord

    citation = CitationRecord(
        url="https://example.com",
        domain="example.com",
        status="found",
    )

    result = RunResult(
        workspace_id="ws_123",
        provider="openai",
        model="gpt-4",
        prompt_version="pv_123",
        parser_version="parser_v1",
        citations=[citation],
        raw_response="Raw LLM output...",
    )
    assert result.workspace_id == "ws_123"
    assert result.provider == "openai"
    assert result.model == "gpt-4"
    assert result.prompt_version == "pv_123"
    assert result.parser_version == "parser_v1"
    assert len(result.citations) == 1
    assert result.citations[0].url == "https://example.com"


def test_run_model():
    """Run model with all required fields."""
    from ai_visibility.models.run import Run, RunStatus
    from ai_visibility.models.mention import CitationRecord

    now = datetime.utcnow()
    citation = CitationRecord(
        url="https://example.com",
        domain="example.com",
        status="found",
    )

    run = Run(
        id="run_123",
        workspace_id="ws_123",
        provider="openai",
        model="gpt-4",
        prompt_version="pv_123",
        parser_version="parser_v1",
        citations=[citation],
        status=RunStatus.COMPLETED,
        started_at=now,
        completed_at=now,
    )
    assert run.id == "run_123"
    assert run.workspace_id == "ws_123"
    assert run.provider == "openai"
    assert run.model == "gpt-4"
    assert run.prompt_version == "pv_123"
    assert run.parser_version == "parser_v1"
    assert len(run.citations) == 1
    assert run.status == RunStatus.COMPLETED


def test_metric_snapshot_model():
    """MetricSnapshot model with FormulaVersion constant."""
    from ai_visibility.models.metric import MetricSnapshot

    snapshot = MetricSnapshot(
        id="metric_123",
        workspace_id="ws_123",
        brand_id="brand_123",
        formula_version="v1.0",
        visibility_score=85.5,
        mention_count=42,
    )
    assert snapshot.id == "metric_123"
    assert snapshot.workspace_id == "ws_123"
    assert snapshot.brand_id == "brand_123"
    assert snapshot.formula_version == "v1.0"
    assert snapshot.visibility_score == 85.5
    assert snapshot.mention_count == 42


def test_competitor_comparison_model():
    """CompetitorComparison model."""
    from ai_visibility.models.metric import CompetitorComparison

    comp = CompetitorComparison(
        id="comp_123",
        workspace_id="ws_123",
        brand_id="brand_123",
        competitor_id="comp_456",
        visibility_delta=5.2,
        mention_delta=3,
    )
    assert comp.id == "comp_123"
    assert comp.workspace_id == "ws_123"
    assert comp.brand_id == "brand_123"
    assert comp.competitor_id == "comp_456"
    assert comp.visibility_delta == 5.2
    assert comp.mention_delta == 3


def test_recommendation_model():
    """Recommendation model."""
    from ai_visibility.models.recommendation import Recommendation

    rec = Recommendation(
        id="rec_123",
        workspace_id="ws_123",
        brand_id="brand_123",
        title="Increase content marketing",
        description="Your visibility is below competitors",
        priority="high",
    )
    assert rec.id == "rec_123"
    assert rec.workspace_id == "ws_123"
    assert rec.brand_id == "brand_123"
    assert rec.title == "Increase content marketing"
    assert rec.priority == "high"


def test_rule_trigger_model():
    """RuleTrigger model."""
    from ai_visibility.models.recommendation import RuleTrigger

    trigger = RuleTrigger(
        id="trigger_123",
        rule_name="low_visibility",
        threshold=50.0,
        current_value=45.5,
    )
    assert trigger.id == "trigger_123"
    assert trigger.rule_name == "low_visibility"
    assert trigger.threshold == 50.0
    assert trigger.current_value == 45.5


def test_error_code_enum():
    """ErrorCode enum has all required values."""
    from ai_visibility.models.degraded import ErrorCode

    assert ErrorCode.MISSING_API_KEY == "missing_api_key"
    assert ErrorCode.PROVIDER_TIMEOUT == "provider_timeout"
    assert ErrorCode.PARSE_FAILURE == "parse_failure"
    assert ErrorCode.RATE_LIMIT == "rate_limit"
    assert ErrorCode.UNKNOWN == "unknown"


def test_failed_provider_model():
    """FailedProvider model."""
    from ai_visibility.models.degraded import FailedProvider
    from ai_visibility.models.degraded import ErrorCode

    failed = FailedProvider(
        provider="openai",
        error_code=ErrorCode.PROVIDER_TIMEOUT,
        error_message="Request timed out after 30s",
    )
    assert failed.provider == "openai"
    assert failed.error_code == ErrorCode.PROVIDER_TIMEOUT
    assert failed.error_message == "Request timed out after 30s"


def test_degraded_state_model():
    """DegradedState model."""
    from ai_visibility.models.degraded import DegradedState, FailedProvider, ErrorCode

    failed = FailedProvider(
        provider="openai",
        error_code=ErrorCode.PROVIDER_TIMEOUT,
        error_message="Request timed out",
    )

    degraded = DegradedState(
        id="degraded_123",
        workspace_id="ws_123",
        is_degraded=True,
        failed_providers=[failed],
        message="Some providers are unavailable",
    )
    assert degraded.id == "degraded_123"
    assert degraded.workspace_id == "ws_123"
    assert degraded.is_degraded is True
    assert len(degraded.failed_providers) == 1
    assert degraded.failed_providers[0].provider == "openai"


def test_models_are_importable_from_package():
    """All models can be imported from ai_visibility.models."""
    from ai_visibility.models import (
        Workspace,
        WorkspaceCreate,
        Brand,
        Competitor,
        Prompt,
        PromptVersion,
        PromptSet,
        Mention,
        MentionType,
        CitationRecord,
        Run,
        RunStatus,
        RunResult,
        MetricSnapshot,
        CompetitorComparison,
        Recommendation,
        RuleTrigger,
        DegradedState,
        ErrorCode,
        FailedProvider,
    )

    # Just verify they're all importable
    assert Workspace is not None
    assert WorkspaceCreate is not None
    assert Brand is not None
    assert Competitor is not None
    assert Prompt is not None
    assert PromptVersion is not None
    assert PromptSet is not None
    assert Mention is not None
    assert MentionType is not None
    assert CitationRecord is not None
    assert Run is not None
    assert RunStatus is not None
    assert RunResult is not None
    assert MetricSnapshot is not None
    assert CompetitorComparison is not None
    assert Recommendation is not None
    assert RuleTrigger is not None
    assert DegradedState is not None
    assert ErrorCode is not None
    assert FailedProvider is not None
