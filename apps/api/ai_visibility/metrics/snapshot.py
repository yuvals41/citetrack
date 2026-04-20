from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, cast

from pydantic import BaseModel

from ai_visibility.metrics.engine import FORMULA_VERSION, MetricsEngine, MetricSnapshot, TrendSeries
from ai_visibility.recommendations.engine import RecommendationResult, RecommendationsEngine
from ai_visibility.storage.repositories.metric_repo import MetricRepository
from ai_visibility.storage.repositories.run_repo import RunRepository
from ai_visibility.storage.repositories.workspace_repo import WorkspaceRepository
from ai_visibility.storage.types import MetricSnapshotRecord, RunRecord

Prisma = Any

DISPLAY_PROVIDERS: tuple[str, ...] = (
    "openai",
    "anthropic",
    "perplexity",
    "gemini",
    "grok",
    "google_ai_overview",
)


class OverviewSnapshot(BaseModel):
    workspace: str
    run_count: int
    latest_run_id: str | None = None
    formula_version: str = FORMULA_VERSION
    prompt_version: str | None = None
    model: str | None = None
    visibility_score: float = 0.0
    citation_coverage: float = 0.0
    competitor_wins: int = 0
    total_prompts: int = 0
    trend_delta: float = 0.0
    comparison_status: str = "ok"


class FindingsSummary(BaseModel):
    workspace: str
    total_findings: int
    items: list[dict[str, object]]


class ActionQueue(BaseModel):
    workspace: str
    total_actions: int
    items: list[dict[str, object]]


class ProviderBreakdownItem(BaseModel):
    provider: str
    responses: int
    mentions: int


class MentionTypeItem(BaseModel):
    label: str
    count: int


class SnapshotBreakdowns(BaseModel):
    workspace: str
    provider_breakdown: list[ProviderBreakdownItem]
    mention_types: list[MentionTypeItem]
    total_responses: int


class SnapshotRepository:
    def __init__(
        self,
        *,
        prisma: Prisma,
        workspace_repo: WorkspaceRepository | None = None,
        run_repo: RunRepository | None = None,
        metric_repo: MetricRepository | None = None,
        metrics_engine: MetricsEngine | None = None,
        findings_by_workspace: Mapping[str, Sequence[Mapping[str, object]]] | None = None,
        actions_by_workspace: Mapping[str, Sequence[Mapping[str, object]]] | None = None,
    ) -> None:
        self._workspace_repo: WorkspaceRepository = workspace_repo or WorkspaceRepository(prisma)
        self._run_repo: RunRepository = run_repo or RunRepository(prisma)
        self._metric_repo: MetricRepository = metric_repo or MetricRepository(prisma)
        self._metrics_engine: MetricsEngine = metrics_engine or MetricsEngine()
        self._recommendations_engine: RecommendationsEngine = RecommendationsEngine()
        self._findings_by_workspace: Mapping[str, Sequence[Mapping[str, object]]] = findings_by_workspace or {}
        self._actions_by_workspace: Mapping[str, Sequence[Mapping[str, object]]] = actions_by_workspace or {}

    async def get_overview_snapshot(self, workspace: str) -> OverviewSnapshot:
        workspace_row = await self._workspace_repo.get_by_slug(workspace)
        if workspace_row is None:
            return OverviewSnapshot(workspace=workspace, run_count=0)

        runs = await self._run_repo.list_by_workspace(workspace_row["id"])
        snapshots = await self._load_metric_snapshots(workspace_row["id"], runs)
        if not snapshots:
            return OverviewSnapshot(workspace=workspace, run_count=len(runs))

        latest = snapshots[-1]
        trend_delta = 0.0
        comparison_status = "ok"
        if len(snapshots) > 1:
            previous = snapshots[-2]
            comparison = self._metrics_engine.compare(previous, latest)
            comparison_status = comparison.comparison_status
            if comparison.comparison_status == "ok":
                trend_delta = self._metrics_engine.trend_delta(latest, previous)

        return OverviewSnapshot(
            workspace=workspace,
            run_count=len(runs),
            latest_run_id=latest.run_id,
            formula_version=latest.formula_version,
            prompt_version=latest.prompt_version,
            model=latest.model,
            visibility_score=latest.visibility_score,
            citation_coverage=latest.citation_coverage,
            competitor_wins=latest.competitor_wins,
            total_prompts=latest.total_prompts,
            trend_delta=trend_delta,
            comparison_status=comparison_status,
        )

    async def get_trend_series(self, workspace: str) -> list[TrendSeries]:
        workspace_row = await self._workspace_repo.get_by_slug(workspace)
        if workspace_row is None:
            return []

        runs = await self._run_repo.list_by_workspace(workspace_row["id"])
        snapshots = await self._load_metric_snapshots(workspace_row["id"], runs)
        return self._metrics_engine.build_trend_series(snapshots)

    def get_findings_summary(self, workspace: str) -> FindingsSummary:
        findings = [dict(item) for item in self._findings_by_workspace.get(workspace, [])]
        return FindingsSummary(workspace=workspace, total_findings=len(findings), items=findings)

    async def get_breakdowns(self, workspace: str) -> SnapshotBreakdowns:
        prisma = self._metric_repo.prisma
        scan_jobs = await prisma.aivisscanjob.find_many(where={"workspaceSlug": workspace})
        if not scan_jobs:
            return SnapshotBreakdowns(
                workspace=workspace,
                provider_breakdown=[],
                mention_types=[],
                total_responses=0,
            )

        job_ids = [j.id for j in scan_jobs]
        executions = await prisma.aivisscanexecution.find_many(
            where={"scanJobId": {"in": job_ids}},
        )

        provider_to_exec_ids: dict[str, list[str]] = {}
        for exec_row in executions:
            provider_to_exec_ids.setdefault(exec_row.provider, []).append(exec_row.id)

        provider_items: list[ProviderBreakdownItem] = []
        total_mentioned = 0
        total_responses = 0
        for provider, exec_ids in provider_to_exec_ids.items():
            prompt_execs = await prisma.aivispromptexecution.find_many(
                where={"scanExecutionId": {"in": exec_ids}},
            )
            responses = len(prompt_execs)
            mentions = 0
            if prompt_execs:
                pe_ids = [pe.id for pe in prompt_execs]
                observations = await prisma.aivisobservation.find_many(
                    where={"promptExecutionId": {"in": pe_ids}},
                )
                mentions = sum(1 for obs in observations if bool(obs.brandMentioned))
            provider_items.append(ProviderBreakdownItem(provider=provider, responses=responses, mentions=mentions))
            total_responses += responses
            total_mentioned += mentions

        if total_responses > 0:
            seen = {item.provider for item in provider_items}
            for display_provider in DISPLAY_PROVIDERS:
                if display_provider not in seen:
                    provider_items.append(ProviderBreakdownItem(provider=display_provider, responses=0, mentions=0))

        provider_items.sort(key=lambda item: (-item.responses, item.provider))
        mention_types = [
            MentionTypeItem(label="mentioned", count=total_mentioned),
            MentionTypeItem(label="not_mentioned", count=max(0, total_responses - total_mentioned)),
        ]

        return SnapshotBreakdowns(
            workspace=workspace,
            provider_breakdown=provider_items,
            mention_types=mention_types,
            total_responses=total_responses,
        )

    async def get_action_queue(self, workspace: str) -> ActionQueue:
        precomputed_actions = self._actions_by_workspace.get(workspace)
        if precomputed_actions is not None:
            items = [dict(item) for item in precomputed_actions]
            return ActionQueue(workspace=workspace, total_actions=len(items), items=items)

        findings_summary = self.get_findings_summary(workspace)
        recommendation_models = self._recommendations_engine.generate_from_findings(findings_summary.items)
        recommendation_items = [self._recommendation_to_action(item) for item in recommendation_models]
        return ActionQueue(
            workspace=workspace,
            total_actions=len(recommendation_items),
            items=recommendation_items,
        )

    async def _load_metric_snapshots(self, workspace_id: str, runs: list[RunRecord]) -> list[MetricSnapshot]:
        metric_records = await self._metric_repo.list_by_workspace(workspace_id)
        if not metric_records:
            return []

        runs_sorted = sorted(runs, key=lambda r: r["created_at"])
        snapshots: list[MetricSnapshot] = []
        for idx, record in enumerate(metric_records):
            run = runs_sorted[idx] if idx < len(runs_sorted) else None
            snapshots.append(self._record_to_snapshot(record, run))

        return snapshots

    def _record_to_snapshot(self, record: MetricSnapshotRecord, run: RunRecord | None) -> MetricSnapshot:
        total_prompts = self._safe_prompt_count(record)
        mentioned_count = self._safe_mentioned_count(record)
        return MetricSnapshot(
            workspace_id=record["workspace_id"],
            run_id=record["id"],
            formula_version=record["formula_version"],
            visibility_score=float(record["visibility_score"]),
            citation_coverage=float(record["citation_coverage"]),
            competitor_wins=int(record["competitor_wins"]),
            total_prompts=total_prompts,
            mentioned_count=mentioned_count,
            prompt_version=run["prompt_version"] if run else None,
            model=run["model"] if run else None,
        )

    def _safe_prompt_count(self, record: MetricSnapshotRecord) -> int:
        mention_count = int(record["mention_count"])
        return mention_count if mention_count >= 0 else 0

    def _safe_mentioned_count(self, record: MetricSnapshotRecord) -> int:
        mention_count = int(record["mention_count"])
        if mention_count < 0:
            return 0
        visibility_score = float(record["visibility_score"])
        estimated = int(round(visibility_score * mention_count))
        return max(0, min(mention_count, estimated))

    def _recommendation_to_action(self, recommendation: RecommendationResult) -> dict[str, object]:
        payload = cast(dict[str, object], recommendation.model_dump())
        payload["action_id"] = payload["recommendation_code"]
        return payload
