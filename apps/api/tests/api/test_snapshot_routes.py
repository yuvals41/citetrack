from __future__ import annotations

# pyright: reportMissingImports=false

from types import SimpleNamespace
from typing import cast

import pytest
from fastapi.testclient import TestClient

from ai_visibility.api import routes as routes_module
from ai_visibility.metrics.engine import TrendPoint, TrendSeries
from ai_visibility.metrics.snapshot import (
    ActionQueue,
    FindingsSummary,
    MentionTypeItem,
    OverviewSnapshot,
    ProviderBreakdownItem,
    SnapshotBreakdowns,
)


class _ForbiddenRepository:
    def __init__(self, *_args: object, **_kwargs: object) -> None:
        msg = "snapshot routes must not call live repository paths"
        raise AssertionError(msg)


class _SnapshotRepoStub:
    async def get_overview_snapshot(self, workspace: str) -> OverviewSnapshot:
        return OverviewSnapshot(
            workspace=workspace,
            run_count=2,
            latest_run_id="run-2",
            formula_version="1.0.0",
            prompt_version="v1",
            model="gpt-4.1",
            visibility_score=0.75,
            citation_coverage=0.4,
            competitor_wins=1,
            total_prompts=10,
            trend_delta=0.12,
            comparison_status="ok",
        )

    async def get_trend_series(self, _workspace: str) -> list[TrendSeries]:
        return [
            TrendSeries(
                formula_version="1.0.0",
                prompt_version="v1",
                model="gpt-4.1",
                comparison_status="ok",
                points=[
                    TrendPoint(
                        run_id="run-1",
                        workspace_id="ws-1",
                        formula_version="1.0.0",
                        prompt_version="v1",
                        model="gpt-4.1",
                        visibility_score=0.63,
                        citation_coverage=0.33,
                        competitor_wins=2,
                        total_prompts=10,
                        mentioned_count=6,
                        comparison_status="ok",
                    ),
                    TrendPoint(
                        run_id="run-2",
                        workspace_id="ws-1",
                        formula_version="1.0.0",
                        prompt_version="v1",
                        model="gpt-4.1",
                        visibility_score=0.75,
                        citation_coverage=0.4,
                        competitor_wins=1,
                        total_prompts=10,
                        mentioned_count=7,
                        comparison_status="ok",
                        delta_visibility_score=0.12,
                        delta_citation_coverage=0.07,
                        delta_competitor_wins=-1,
                    ),
                ],
            )
        ]

    def get_findings_summary(self, workspace: str) -> FindingsSummary:
        return FindingsSummary(
            workspace=workspace,
            total_findings=1,
            items=[
                {
                    "reason_code": "schema_missing",
                    "confidence": 0.9,
                    "applicability": "all",
                    "evidence": [{"check": "schema_presence", "value": 0, "source": "fixture"}],
                }
            ],
        )

    async def get_breakdowns(self, workspace: str) -> SnapshotBreakdowns:
        return SnapshotBreakdowns(
            workspace=workspace,
            provider_breakdown=[
                ProviderBreakdownItem(provider="anthropic", responses=3, mentions=3),
                ProviderBreakdownItem(provider="openai", responses=0, mentions=0),
            ],
            mention_types=[
                MentionTypeItem(label="mentioned", count=3),
                MentionTypeItem(label="not_mentioned", count=0),
            ],
            total_responses=3,
        )

    async def get_action_queue(self, workspace: str) -> ActionQueue:
        return ActionQueue(
            workspace=workspace,
            total_actions=1,
            items=[
                {
                    "action_id": "add_schema_markup",
                    "recommendation_code": "add_schema_markup",
                    "reason": "No schema markup detected",
                    "impact": "Missing schema reduces AI citation probability",
                    "next_step": "Add FAQ schema",
                    "confidence": 0.9,
                    "rules_version": "v1",
                    "applicability": "all",
                }
            ],
        )


def test_snapshot_routes_return_precomputed_models(
    monkeypatch: pytest.MonkeyPatch,
    auth_client: TestClient,
) -> None:
    async def _stub_repo() -> _SnapshotRepoStub:
        return _SnapshotRepoStub()

    monkeypatch.setattr(routes_module, "_snapshot_repository", _stub_repo)
    monkeypatch.setattr(routes_module, "RunRepository", _ForbiddenRepository)
    monkeypatch.setattr(routes_module, "WorkspaceRepository", _ForbiddenRepository)

    overview = auth_client.get("/api/v1/snapshot/overview?workspace=default")
    trend = auth_client.get("/api/v1/snapshot/trend?workspace=default")
    findings = auth_client.get("/api/v1/snapshot/findings?workspace=default")
    actions = auth_client.get("/api/v1/snapshot/actions?workspace=default")

    assert overview.status_code == 200
    assert overview.json()["workspace"] == "default"
    assert overview.json()["latest_run_id"] == "run-2"

    assert trend.status_code == 200
    trend_payload = cast(dict[str, object], trend.json())
    assert trend_payload["workspace"] == "default"
    trend_items = cast(list[dict[str, object]], trend_payload["items"])
    assert len(trend_items) == 1
    trend_points = cast(list[dict[str, object]], trend_items[0]["points"])
    assert trend_points[1]["delta_visibility_score"] == 0.12

    assert findings.status_code == 200
    assert findings.json()["total_findings"] == 1
    assert findings.json()["items"][0]["reason_code"] == "schema_missing"

    assert actions.status_code == 200
    assert actions.json()["total_actions"] == 1
    assert actions.json()["items"][0]["action_id"] == "add_schema_markup"

    breakdowns = auth_client.get("/api/v1/snapshot/breakdowns?workspace=default")
    assert breakdowns.status_code == 200
    bd_payload = cast(dict[str, object], breakdowns.json())
    assert bd_payload["workspace"] == "default"
    assert bd_payload["total_responses"] == 3
    bd_providers = cast(list[dict[str, object]], bd_payload["provider_breakdown"])
    assert {p["provider"] for p in bd_providers} == {"anthropic", "openai"}
    mention_types = cast(list[dict[str, object]], bd_payload["mention_types"])
    assert {mt["label"] for mt in mention_types} == {"mentioned", "not_mentioned"}


def test_breakdowns_repo_pads_missing_providers_when_scans_exist() -> None:
    import asyncio
    from ai_visibility.metrics.snapshot import DISPLAY_PROVIDERS, SnapshotRepository

    class _FakePrisma:
        class aivisscanjob:
            @staticmethod
            async def find_many(**_kwargs):
                return [SimpleNamespace(id="job-1")]

        class aivisscanexecution:
            @staticmethod
            async def find_many(**_kwargs):
                return [SimpleNamespace(id="exec-1", provider="anthropic")]

        class aivispromptexecution:
            @staticmethod
            async def find_many(**_kwargs):
                return [SimpleNamespace(id="pe-1"), SimpleNamespace(id="pe-2")]

        class aivisobservation:
            @staticmethod
            async def find_many(**_kwargs):
                return [
                    SimpleNamespace(brandMentioned=True),
                    SimpleNamespace(brandMentioned=False),
                ]

    class _FakeMetricRepo:
        prisma = _FakePrisma()

        async def list_by_workspace(self, *_a, **_k):
            return []

    class _FakeWorkspaceRepo:
        async def get_by_slug(self, *_a, **_k):
            return None

    repo = SnapshotRepository(
        prisma=_FakePrisma(),
        metric_repo=cast(object, _FakeMetricRepo()),
        workspace_repo=cast(object, _FakeWorkspaceRepo()),
    )

    result = asyncio.run(repo.get_breakdowns("any-slug"))

    returned_providers = {item.provider for item in result.provider_breakdown}
    assert set(DISPLAY_PROVIDERS) <= returned_providers
    anthropic_item = next(item for item in result.provider_breakdown if item.provider == "anthropic")
    assert anthropic_item.responses == 2
    assert anthropic_item.mentions == 1
    openai_item = next(item for item in result.provider_breakdown if item.provider == "openai")
    assert openai_item.responses == 0
    assert openai_item.mentions == 0


def test_breakdowns_repo_returns_empty_when_no_scans_exist() -> None:
    import asyncio
    from ai_visibility.metrics.snapshot import SnapshotRepository

    class _FakePrisma:
        class aivisscanjob:
            @staticmethod
            async def find_many(**_kwargs):
                return []

    class _FakeMetricRepo:
        prisma = _FakePrisma()

        async def list_by_workspace(self, *_a, **_k):
            return []

    class _FakeWorkspaceRepo:
        async def get_by_slug(self, *_a, **_k):
            return None

    repo = SnapshotRepository(
        prisma=_FakePrisma(),
        metric_repo=cast(object, _FakeMetricRepo()),
        workspace_repo=cast(object, _FakeWorkspaceRepo()),
    )

    result = asyncio.run(repo.get_breakdowns("empty-slug"))
    assert result.provider_breakdown == []
    assert result.total_responses == 0


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/snapshot/overview?workspace=default",
        "/api/v1/snapshot/trend?workspace=default",
        "/api/v1/snapshot/findings?workspace=default",
        "/api/v1/snapshot/actions?workspace=default",
        "/api/v1/snapshot/breakdowns?workspace=default",
    ],
)
def test_snapshot_routes_require_auth(path: str, unauth_client: TestClient) -> None:
    response = unauth_client.get(path)

    assert response.status_code in {401, 403}
