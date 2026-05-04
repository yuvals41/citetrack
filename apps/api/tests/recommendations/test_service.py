from __future__ import annotations

# pyright: reportMissingImports=false, reportArgumentType=false

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from ai_visibility.metrics.snapshot import OverviewSnapshot, SnapshotBreakdowns
from ai_visibility.recommendations.service import RecommendationsService
from ai_visibility.storage.repositories.brand_repo import BrandRepository
from ai_visibility.storage.repositories.recommendation_repo import RecommendationRepository
from ai_visibility.storage.repositories.workspace_repo import WorkspaceRepository


class _SnapshotRepoStub:
    def __init__(self, *, visibility_score: float = 0.4, citation_coverage: float = 0.05) -> None:
        self._visibility_score = visibility_score
        self._citation_coverage = citation_coverage

    async def get_overview_snapshot(self, workspace: str) -> OverviewSnapshot:
        return OverviewSnapshot(
            workspace=workspace,
            run_count=1,
            latest_run_id="run-1",
            visibility_score=self._visibility_score,
            citation_coverage=self._citation_coverage,
        )

    async def get_breakdowns(self, workspace: str) -> SnapshotBreakdowns:
        return SnapshotBreakdowns(
            workspace=workspace,
            provider_breakdown=[],
            mention_types=[],
            total_responses=2,
        )


def _workspace_row(slug: str, workspace_id: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=workspace_id,
        slug=slug,
        brandName=slug.title(),
        city="",
        region="",
        country="",
        createdAt=datetime.now(timezone.utc),
    )


def _brand_row(workspace_id: str) -> SimpleNamespace:
    return SimpleNamespace(
        id="brand-1",
        workspaceId=workspace_id,
        name="Solara AI",
        domain="solara.ai",
        createdAt=datetime.now(timezone.utc),
        updatedAt=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_generate_and_persist_happy_path(
    monkeypatch: pytest.MonkeyPatch,
    mock_prisma: MagicMock,
) -> None:
    mock_prisma.workspace.find_unique.return_value = _workspace_row("solara-ai", "ws-1")
    mock_prisma.query_raw.return_value = []
    mock_prisma.brand.find_first.return_value = _brand_row("ws-1")
    mock_prisma.scanjob.find_first.return_value = SimpleNamespace(id="job-1")
    mock_prisma.scanexecution.find_many.return_value = [SimpleNamespace(id="exec-1")]
    mock_prisma.promptexecution.find_many.return_value = [
        SimpleNamespace(id="pe-1", promptText="Prompt where brand was absent"),
        SimpleNamespace(id="pe-2", promptText="Prompt where brand was present"),
    ]
    mock_prisma.observation.find_many.return_value = [
        SimpleNamespace(promptExecutionId="pe-1", brandMentioned=False),
        SimpleNamespace(promptExecutionId="pe-2", brandMentioned=True),
    ]

    async def _fake_generate(**kwargs: object) -> list[dict[str, str]]:
        assert kwargs["brand_name"] == "Solara AI"
        assert kwargs["absent_prompts"] == ["Prompt where brand was absent"]
        assert kwargs["mentioned_prompts"] == ["Prompt where brand was present"]
        return [
            {
                "recommendation_code": "expand_faq_coverage",
                "reason": "Only 40% of prompts mention the brand.",
                "next_step": "Expand FAQ coverage",
                "impact": "high",
            },
            {
                "recommendation_code": "add_review_sources",
                "reason": "AI cites third-party domains more often than the brand site.",
                "next_step": "Add review source coverage",
                "impact": "medium",
            },
        ]

    monkeypatch.setattr("ai_visibility.recommendations.service.generate_recommendations", _fake_generate)

    service = RecommendationsService(
        prisma=mock_prisma,
        snapshot_repo=_SnapshotRepoStub(),
        workspace_repo=WorkspaceRepository(mock_prisma),
        brand_repo=BrandRepository(mock_prisma),
        rec_repo=RecommendationRepository(mock_prisma),
    )

    inserted = await service.generate_and_persist("solara-ai", run_id="run-1")

    assert inserted == 2
    assert mock_prisma.recommendation.create.await_count == 2
    first_payload = mock_prisma.recommendation.create.await_args_list[0].kwargs["data"]
    assert first_payload["title"] == "Expand FAQ coverage"
    assert first_payload["description"] == "Only 40% of prompts mention the brand."
    assert first_payload["priority"] == "high"


@pytest.mark.asyncio
async def test_generate_and_persist_claude_failure_falls_back(
    monkeypatch: pytest.MonkeyPatch,
    mock_prisma: MagicMock,
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    mock_prisma.workspace.find_unique.return_value = _workspace_row("solara-ai", "ws-1")
    mock_prisma.query_raw.return_value = []
    mock_prisma.brand.find_first.return_value = _brand_row("ws-1")
    mock_prisma.scanjob.find_first.return_value = None

    service = RecommendationsService(
        prisma=mock_prisma,
        snapshot_repo=_SnapshotRepoStub(visibility_score=0.2, citation_coverage=0.0),
        workspace_repo=WorkspaceRepository(mock_prisma),
        brand_repo=BrandRepository(mock_prisma),
        rec_repo=RecommendationRepository(mock_prisma),
    )

    inserted = await service.generate_and_persist("solara-ai", run_id="run-1")

    assert inserted >= 1
    first_payload = mock_prisma.recommendation.create.await_args_list[0].kwargs["data"]
    assert first_payload["priority"] in {"high", "medium", "low"}
    assert isinstance(first_payload["title"], str) and first_payload["title"]


@pytest.mark.asyncio
async def test_generate_and_persist_no_brand(
    mock_prisma: MagicMock,
) -> None:
    mock_prisma.workspace.find_unique.return_value = _workspace_row("solara-ai", "ws-1")
    mock_prisma.query_raw.return_value = []
    mock_prisma.brand.find_first.return_value = None

    service = RecommendationsService(
        prisma=mock_prisma,
        snapshot_repo=_SnapshotRepoStub(),
        workspace_repo=WorkspaceRepository(mock_prisma),
        brand_repo=BrandRepository(mock_prisma),
        rec_repo=RecommendationRepository(mock_prisma),
    )

    inserted = await service.generate_and_persist("solara-ai", run_id="run-1")

    assert inserted == 0
    mock_prisma.recommendation.create.assert_not_called()
