"""Contract tests for invalid mention rejection."""

import pytest
from pydantic import ValidationError


def test_mention_rejects_invalid_mention_type():
    """Mention rejects invalid mention_type values."""
    from ai_visibility.models.mention import Mention, CitationRecord

    citation = CitationRecord(
        url="https://example.com",
        domain="example.com",
        status="found",
    )

    with pytest.raises(ValidationError):
        Mention(
            id="mention_123",
            run_id="run_123",
            brand_id="brand_123",
            mention_type="invalid_type",  # Invalid
            text="Some text",
            citation=citation,
        )


def test_citation_record_rejects_invalid_status():
    """CitationRecord rejects invalid status values."""
    from ai_visibility.models.mention import CitationRecord

    with pytest.raises(ValidationError):
        CitationRecord(
            url="https://example.com",
            domain="example.com",
            status="invalid_status",  # Invalid
        )


def test_run_rejects_invalid_status():
    """Run rejects invalid status values."""
    from ai_visibility.models.run import Run
    from datetime import datetime

    now = datetime.utcnow()

    with pytest.raises(ValidationError):
        Run(
            id="run_123",
            workspace_id="ws_123",
            provider="openai",
            model="gpt-4",
            prompt_version="pv_123",
            parser_version="parser_v1",
            citations=[],
            status="invalid_status",  # Invalid
            started_at=now,
            completed_at=now,
        )


def test_degraded_state_rejects_invalid_error_code():
    """DegradedState rejects invalid error codes."""
    from ai_visibility.models.degraded import DegradedState, FailedProvider

    with pytest.raises(ValidationError):
        FailedProvider(
            provider="openai",
            error_code="invalid_error_code",  # Invalid
            error_message="Some error",
        )


def test_mention_requires_citation():
    """Mention requires citation field."""
    from ai_visibility.models.mention import Mention

    with pytest.raises(ValidationError):
        Mention(
            id="mention_123",
            run_id="run_123",
            brand_id="brand_123",
            mention_type="explicit",
            text="Some text",
            # Missing citation
        )


def test_run_requires_workspace_id():
    """Run requires workspace_id field."""
    from ai_visibility.models.run import Run
    from datetime import datetime

    now = datetime.utcnow()

    with pytest.raises(ValidationError):
        Run(
            id="run_123",
            # Missing workspace_id
            provider="openai",
            model="gpt-4",
            prompt_version="pv_123",
            parser_version="parser_v1",
            citations=[],
            status="completed",
            started_at=now,
            completed_at=now,
        )


def test_run_requires_provider():
    """Run requires provider field."""
    from ai_visibility.models.run import Run
    from datetime import datetime

    now = datetime.utcnow()

    with pytest.raises(ValidationError):
        Run(
            id="run_123",
            workspace_id="ws_123",
            # Missing provider
            model="gpt-4",
            prompt_version="pv_123",
            parser_version="parser_v1",
            citations=[],
            status="completed",
            started_at=now,
            completed_at=now,
        )


def test_run_requires_model():
    """Run requires model field."""
    from ai_visibility.models.run import Run
    from datetime import datetime

    now = datetime.utcnow()

    with pytest.raises(ValidationError):
        Run(
            id="run_123",
            workspace_id="ws_123",
            provider="openai",
            # Missing model
            prompt_version="pv_123",
            parser_version="parser_v1",
            citations=[],
            status="completed",
            started_at=now,
            completed_at=now,
        )


def test_run_requires_prompt_version():
    """Run requires prompt_version field."""
    from ai_visibility.models.run import Run
    from datetime import datetime

    now = datetime.utcnow()

    with pytest.raises(ValidationError):
        Run(
            id="run_123",
            workspace_id="ws_123",
            provider="openai",
            model="gpt-4",
            # Missing prompt_version
            parser_version="parser_v1",
            citations=[],
            status="completed",
            started_at=now,
            completed_at=now,
        )


def test_run_requires_parser_version():
    """Run requires parser_version field."""
    from ai_visibility.models.run import Run
    from datetime import datetime

    now = datetime.utcnow()

    with pytest.raises(ValidationError):
        Run(
            id="run_123",
            workspace_id="ws_123",
            provider="openai",
            model="gpt-4",
            prompt_version="pv_123",
            # Missing parser_version
            citations=[],
            status="completed",
            started_at=now,
            completed_at=now,
        )


def test_run_requires_citations():
    """Run requires citations field."""
    from ai_visibility.models.run import Run
    from datetime import datetime

    now = datetime.utcnow()

    with pytest.raises(ValidationError):
        Run(
            id="run_123",
            workspace_id="ws_123",
            provider="openai",
            model="gpt-4",
            prompt_version="pv_123",
            parser_version="parser_v1",
            # Missing citations
            status="completed",
            started_at=now,
            completed_at=now,
        )


def test_workspace_create_requires_name():
    """WorkspaceCreate requires name field."""
    from ai_visibility.models.workspace import WorkspaceCreate

    with pytest.raises(ValidationError):
        WorkspaceCreate(
            # Missing name
            slug="acme",
        )


def test_workspace_create_requires_slug():
    """WorkspaceCreate requires slug field."""
    from ai_visibility.models.workspace import WorkspaceCreate

    with pytest.raises(ValidationError):
        WorkspaceCreate(
            name="Acme Corp",
            # Missing slug
        )


def test_brand_requires_workspace_id():
    """Brand requires workspace_id field."""
    from ai_visibility.models.brand import Brand

    with pytest.raises(ValidationError):
        Brand(
            id="brand_123",
            # Missing workspace_id
            name="Acme",
            domain="acme.com",
        )


def test_competitor_requires_workspace_id():
    """Competitor requires workspace_id field."""
    from ai_visibility.models.brand import Competitor

    with pytest.raises(ValidationError):
        Competitor(
            id="comp_123",
            # Missing workspace_id
            name="TechCorp",
            domain="techcorp.com",
        )


def test_metric_snapshot_requires_formula_version():
    """MetricSnapshot requires formula_version field."""
    from ai_visibility.models.metric import MetricSnapshot

    with pytest.raises(ValidationError):
        MetricSnapshot(
            id="metric_123",
            workspace_id="ws_123",
            brand_id="brand_123",
            # Missing formula_version
            visibility_score=85.5,
            mention_count=42,
        )
