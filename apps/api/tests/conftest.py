"""Pytest configuration and shared fixtures for ai-visibility tests."""

import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def _stub_row(**overrides: object) -> SimpleNamespace:
    """Return a SimpleNamespace that satisfies any ``_*_from_model`` converter.

    Every field used across workspace_repo, run_repo, mention_repo,
    metric_repo, and scan_evidence_repo is pre-populated with a sensible
    default.  Individual tests can override via ``return_value`` or
    ``side_effect`` as needed.
    """
    now = datetime.now(timezone.utc)
    defaults: dict[str, object] = {
        "id": str(uuid.uuid4()),
        "slug": "stub",
        "brandName": "Stub Brand",
        "city": "",
        "region": "",
        "country": "",
        "createdAt": now,
        "updatedAt": now,
        # Run fields
        "workspaceId": str(uuid.uuid4()),
        "brandId": str(uuid.uuid4()),
        "status": "completed",
        "provider": "openai",
        "mentionCount": 0,
        "visibilityScore": 0.0,
        "startedAt": now,
        "completedAt": now,
        # Mention fields
        "runId": str(uuid.uuid4()),
        "promptTemplate": "",
        "llmResponse": "",
        "mentioned": False,
        "sentiment": "neutral",
        "rank": 0,
        "citationUrl": "",
        "context": "",
        "modelName": "",
        "modelVersion": "",
        "promptVersion": "",
        # Metric snapshot fields
        "formulaVersion": "v1",
        "citationCoverage": 0.0,
        "competitorWins": 0,
        # Scan evidence fields
        "scanJobId": str(uuid.uuid4()),
        "scanExecutionId": str(uuid.uuid4()),
        "promptExecutionId": str(uuid.uuid4()),
        "observationId": str(uuid.uuid4()),
        "template": "",
        "renderedPrompt": "",
        "strategyVersion": "v1",
        "executionMs": 0,
        "rawResponse": "",
        "adapter": "stub",
        "promptExecutionCitationId": str(uuid.uuid4()),
        "url": "",
        "text": "",
        "kind": "citation",
        "name": "",
        "period": "daily",
        "description": "",
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_model_mock() -> MagicMock:
    model = MagicMock()
    model.create = AsyncMock(side_effect=lambda **kw: _stub_row())
    model.find_unique = AsyncMock(return_value=None)
    model.find_first = AsyncMock(return_value=None)
    model.find_many = AsyncMock(return_value=[])
    model.update = AsyncMock(side_effect=lambda **kw: _stub_row())
    model.upsert = AsyncMock(side_effect=lambda **kw: _stub_row())
    model.delete = AsyncMock(return_value=None)
    model.delete_many = AsyncMock(return_value=None)
    model.count = AsyncMock(return_value=0)
    return model


@pytest.fixture
def mock_prisma() -> MagicMock:
    """Mock Prisma client with all ai-visibility models (async CRUD methods)."""
    prisma = MagicMock()
    prisma.is_connected.return_value = True

    prisma.aivisworkspace = _make_model_mock()
    prisma.aivisrun = _make_model_mock()
    prisma.aivismention = _make_model_mock()
    prisma.aivismetricsnapshot = _make_model_mock()
    prisma.aivisscanevidence = _make_model_mock()

    prisma.aivisscanjob = _make_model_mock()
    prisma.aivisscanexecution = _make_model_mock()
    prisma.aivispromptexecution = _make_model_mock()
    prisma.aivisobservation = _make_model_mock()
    prisma.aivispromptexecutioncitation = _make_model_mock()

    prisma.query_raw = AsyncMock(return_value=[])
    prisma.execute_raw = AsyncMock(return_value=None)
    prisma.disconnect = AsyncMock(return_value=None)
    prisma.connect = AsyncMock(return_value=None)

    return prisma


@pytest.fixture
def patch_get_prisma(mock_prisma: MagicMock):
    """Patch get_prisma() to return mock_prisma for the test duration."""

    async def _fake_get_prisma():
        return mock_prisma

    with (
        patch("ai_visibility.storage.prisma_connection.get_prisma", new=_fake_get_prisma),
        patch("ai_visibility.runs.orchestrator.get_prisma", new=_fake_get_prisma),
        patch("ai_visibility.cli.get_prisma", new=_fake_get_prisma),
    ):
        yield mock_prisma
