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
    HistoricalRunItem,
    MentionTypeItem,
    OverviewSnapshot,
    ProviderBreakdownItem,
    SnapshotBreakdowns,
    SourceAttributionItem,
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
            source_attribution=[
                SourceAttributionItem(domain="example.com", count=2),
                SourceAttributionItem(domain="acme.com", count=1),
            ],
            historical_mentions=[
                HistoricalRunItem(run_id="job-1", run_date="2026-04-19T20:30:00", responses=3, mentions=3),
            ],
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
                return [SimpleNamespace(id="job-1", createdAt=None)]

        class aivisscanexecution:
            @staticmethod
            async def find_many(**_kwargs):
                return [SimpleNamespace(id="exec-1", scanJobId="job-1", provider="anthropic")]

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

        class aivispromptexecutioncitation:
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


def test_extract_domain_handles_common_url_shapes() -> None:
    from ai_visibility.metrics.snapshot import _extract_domain

    assert _extract_domain("https://www.example.com/foo") == "example.com"
    assert _extract_domain("http://blog.acme.com/path?q=1") == "blog.acme.com"
    assert _extract_domain("https://docs.example.com/") == "docs.example.com"
    assert _extract_domain("//cdn.example.net/a") == "cdn.example.net"
    assert _extract_domain("") == ""


def test_breakdowns_repo_aggregates_source_attribution() -> None:
    import asyncio
    from ai_visibility.metrics.snapshot import SnapshotRepository

    class _FakePrisma:
        class aivisscanjob:
            @staticmethod
            async def find_many(**_kwargs):
                return [SimpleNamespace(id="job-1", createdAt=None)]

        class aivisscanexecution:
            @staticmethod
            async def find_many(**_kwargs):
                return [SimpleNamespace(id="exec-1", scanJobId="job-1", provider="anthropic")]

        class aivispromptexecution:
            @staticmethod
            async def find_many(**_kwargs):
                return [SimpleNamespace(id="pe-1"), SimpleNamespace(id="pe-2")]

        class aivisobservation:
            @staticmethod
            async def find_many(**_kwargs):
                return [
                    SimpleNamespace(brandMentioned=True),
                    SimpleNamespace(brandMentioned=True),
                ]

        class aivispromptexecutioncitation:
            @staticmethod
            async def find_many(**_kwargs):
                return [
                    SimpleNamespace(url="https://example.com/a"),
                    SimpleNamespace(url="https://example.com/b"),
                    SimpleNamespace(url="https://acme.com/x"),
                    SimpleNamespace(url="https://www.example.com/c"),
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

    result = asyncio.run(repo.get_breakdowns("any"))

    domains = [item.domain for item in result.source_attribution]
    counts = {item.domain: item.count for item in result.source_attribution}
    assert domains[0] == "example.com"
    assert counts["example.com"] == 3
    assert counts["acme.com"] == 1


def test_breakdowns_repo_builds_historical_mentions_sorted_by_date() -> None:
    import asyncio
    from datetime import datetime, timezone
    from ai_visibility.metrics.snapshot import SnapshotRepository

    created_first = datetime(2026, 4, 19, 20, 0, 0, tzinfo=timezone.utc)
    created_second = datetime(2026, 4, 20, 14, 0, 0, tzinfo=timezone.utc)

    class _FakePrisma:
        class aivisscanjob:
            @staticmethod
            async def find_many(**_kwargs):
                return [
                    SimpleNamespace(id="job-b", createdAt=created_second),
                    SimpleNamespace(id="job-a", createdAt=created_first),
                ]

        class aivisscanexecution:
            @staticmethod
            async def find_many(**_kwargs):
                return [
                    SimpleNamespace(id="exec-b", scanJobId="job-b", provider="anthropic"),
                    SimpleNamespace(id="exec-a", scanJobId="job-a", provider="anthropic"),
                ]

        class aivispromptexecution:
            @staticmethod
            async def find_many(**kwargs):
                where = kwargs.get("where", {})
                exec_ids = where.get("scanExecutionId", {}).get("in", [])
                if "exec-b" in exec_ids:
                    return [SimpleNamespace(id="pe-b1"), SimpleNamespace(id="pe-b2")]
                if "exec-a" in exec_ids:
                    return [SimpleNamespace(id="pe-a1")]
                return []

        class aivisobservation:
            @staticmethod
            async def find_many(**kwargs):
                where = kwargs.get("where", {})
                pe_ids = where.get("promptExecutionId", {}).get("in", [])
                return [SimpleNamespace(brandMentioned=True) for _ in pe_ids]

        class aivispromptexecutioncitation:
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

    result = asyncio.run(repo.get_breakdowns("any"))

    assert [item.run_id for item in result.historical_mentions] == ["job-a", "job-b"]
    assert result.historical_mentions[0].responses == 1
    assert result.historical_mentions[1].responses == 2


def test_breakdowns_repo_builds_top_pages_filtered_to_brand_domain() -> None:
    import asyncio
    from ai_visibility.metrics.snapshot import SnapshotRepository

    class _FakePrisma:
        class aivisscanjob:
            @staticmethod
            async def find_many(**_kwargs):
                return [SimpleNamespace(id="job-1", createdAt=None)]

        class aivisscanexecution:
            @staticmethod
            async def find_many(**_kwargs):
                return [SimpleNamespace(id="exec-1", scanJobId="job-1", provider="anthropic")]

        class aivispromptexecution:
            @staticmethod
            async def find_many(**_kwargs):
                return [SimpleNamespace(id="pe-1", rawResponse="")]

        class aivisobservation:
            @staticmethod
            async def find_many(**_kwargs):
                return []

        class aivispromptexecutioncitation:
            @staticmethod
            async def find_many(**_kwargs):
                return [
                    SimpleNamespace(url="https://acme.com/pricing"),
                    SimpleNamespace(url="https://acme.com/pricing"),
                    SimpleNamespace(url="https://docs.acme.com/guide"),
                    SimpleNamespace(url="https://example.com/blog"),
                ]

        class aivisbrand:
            @staticmethod
            async def find_many(**_kwargs):
                return [SimpleNamespace(name="Acme", domain="acme.com")]

        class aiviscompetitor:
            @staticmethod
            async def find_many(**_kwargs):
                return []

    class _FakeMetricRepo:
        prisma = _FakePrisma()

        async def list_by_workspace(self, *_a, **_k):
            return []

    class _FakeWorkspaceRepo:
        async def get_by_slug(self, *_a, **_k):
            return {"id": "ws-1"}

    repo = SnapshotRepository(
        prisma=_FakePrisma(),
        metric_repo=cast(object, _FakeMetricRepo()),
        workspace_repo=cast(object, _FakeWorkspaceRepo()),
    )

    result = asyncio.run(repo.get_breakdowns("any"))

    urls = [item.url for item in result.top_pages]
    counts = {item.url: item.count for item in result.top_pages}
    assert "https://acme.com/pricing" in urls
    assert counts["https://acme.com/pricing"] == 2
    assert "https://docs.acme.com/guide" in urls
    assert "https://example.com/blog" not in urls


def test_breakdowns_repo_builds_competitor_comparison_via_text_match() -> None:
    import asyncio
    from ai_visibility.metrics.snapshot import SnapshotRepository

    class _FakePrisma:
        class aivisscanjob:
            @staticmethod
            async def find_many(**_kwargs):
                return [SimpleNamespace(id="job-1", createdAt=None)]

        class aivisscanexecution:
            @staticmethod
            async def find_many(**_kwargs):
                return [SimpleNamespace(id="exec-1", scanJobId="job-1", provider="anthropic")]

        class aivispromptexecution:
            @staticmethod
            async def find_many(**_kwargs):
                return [
                    SimpleNamespace(
                        id="pe-1",
                        rawResponse="Acme is great. Beta is also fine. Beta again.",
                    ),
                    SimpleNamespace(
                        id="pe-2",
                        rawResponse="I recommend Acme over Gamma.",
                    ),
                ]

        class aivisobservation:
            @staticmethod
            async def find_many(**_kwargs):
                return []

        class aivispromptexecutioncitation:
            @staticmethod
            async def find_many(**_kwargs):
                return []

        class aivisbrand:
            @staticmethod
            async def find_many(**_kwargs):
                return [SimpleNamespace(name="Acme", domain="acme.com")]

        class aiviscompetitor:
            @staticmethod
            async def find_many(**_kwargs):
                return [
                    SimpleNamespace(name="Beta", domain="beta.com"),
                    SimpleNamespace(name="Gamma", domain="gamma.com"),
                    SimpleNamespace(name="Delta", domain="delta.com"),
                ]

    class _FakeMetricRepo:
        prisma = _FakePrisma()

        async def list_by_workspace(self, *_a, **_k):
            return []

    class _FakeWorkspaceRepo:
        async def get_by_slug(self, *_a, **_k):
            return {"id": "ws-1"}

    repo = SnapshotRepository(
        prisma=_FakePrisma(),
        metric_repo=cast(object, _FakeMetricRepo()),
        workspace_repo=cast(object, _FakeWorkspaceRepo()),
    )

    result = asyncio.run(repo.get_breakdowns("any"))

    by_name = {item.name: item for item in result.competitor_comparison}
    assert by_name["Acme"].mentions == 2
    assert by_name["Acme"].is_brand is True
    assert by_name["Beta"].mentions == 1
    assert by_name["Gamma"].mentions == 1
    assert by_name["Delta"].mentions == 0
    assert result.competitor_comparison[0].name == "Acme"


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
