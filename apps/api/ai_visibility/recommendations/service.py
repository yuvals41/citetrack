from __future__ import annotations

# pyright: reportMissingImports=false, reportExplicitAny=false, reportAny=false

import json
from typing import Any

from loguru import logger

from ai_visibility.analysis.actions import generate_recommendations
from ai_visibility.metrics.snapshot import SnapshotRepository
from ai_visibility.storage.repositories.brand_repo import BrandRepository
from ai_visibility.storage.repositories.recommendation_repo import RecommendationRepository
from ai_visibility.storage.repositories.workspace_repo import WorkspaceRepository

Prisma = Any


class RecommendationsService:
    def __init__(
        self,
        prisma: Prisma,
        snapshot_repo: SnapshotRepository,
        workspace_repo: WorkspaceRepository,
        brand_repo: BrandRepository,
        rec_repo: RecommendationRepository,
    ) -> None:
        self._prisma: Prisma = prisma
        self._snapshot_repo: SnapshotRepository = snapshot_repo
        self._workspace_repo: WorkspaceRepository = workspace_repo
        self._brand_repo: BrandRepository = brand_repo
        self._rec_repo: RecommendationRepository = rec_repo

    async def generate_and_persist(
        self,
        workspace_slug: str,
        run_id: str | None = None,
    ) -> int:
        try:
            workspace = await self._workspace_repo.get_by_slug(workspace_slug)
            if workspace is None:
                raise ValueError(f"Workspace not found: {workspace_slug}")

            brand = await self._brand_repo.get_primary_for_workspace(workspace["id"])
            if brand is None:
                logger.warning(
                    "recommendations.generate.skipped workspace={} run_id={} reason=no_brand",
                    workspace_slug,
                    run_id,
                )
                return 0

            overview = await self._snapshot_repo.get_overview_snapshot(workspace_slug)
            breakdowns = await self._snapshot_repo.get_breakdowns(workspace_slug)
            absent_prompts, mentioned_prompts = await self._load_prompt_coverage(workspace_slug)

            competitor_scores: list[dict[str, object]] = [
                {
                    "name": item.name,
                    "mentions": item.mentions,
                    "is_brand": item.is_brand,
                }
                for item in breakdowns.competitor_comparison
                if not item.is_brand
            ]
            source_domains = [item.domain for item in breakdowns.source_attribution]

            generated = await generate_recommendations(
                brand_name=brand.name,
                visibility_score=overview.visibility_score,
                citation_coverage=overview.citation_coverage,
                sentiment_data={},
                source_domains=source_domains,
                competitor_scores=competitor_scores,
                absent_prompts=absent_prompts,
                mentioned_prompts=mentioned_prompts,
            )

            normalized: list[dict[str, str]] = []
            for idx, recommendation in enumerate(generated, start=1):
                normalized_recommendation = _normalize_recommendation_payload(recommendation, idx)
                if normalized_recommendation is not None:
                    normalized.append(normalized_recommendation)
            if not normalized:
                logger.warning(
                    "recommendations.generate.empty workspace={} run_id={}",
                    workspace_slug,
                    run_id,
                )
                return 0

            inserted = await self._rec_repo.persist_batch(
                workspace_id=workspace["id"],
                brand_id=brand.id,
                recommendations=normalized,
            )
            logger.info(
                "recommendations.generate.persisted workspace={} run_id={} count={}",
                workspace_slug,
                run_id,
                inserted,
            )
            return inserted
        except Exception:
            logger.exception(
                "recommendations.generate.failed workspace={} run_id={}",
                workspace_slug,
                run_id,
            )
            raise

    async def _load_prompt_coverage(self, workspace_slug: str) -> tuple[list[str], list[str]]:
        scan_job = await self._prisma.scanjob.find_first(
            where={
                "workspaceSlug": workspace_slug,
                "status": {"in": ["COMPLETED", "COMPLETED_WITH_PARTIAL_FAILURES"]},
            },
            order=[{"createdAt": "desc"}, {"id": "desc"}],
        )
        if scan_job is None:
            return [], []

        scan_executions = await self._prisma.scanexecution.find_many(where={"scanJobId": scan_job.id})
        if not scan_executions:
            return [], []

        prompt_executions = await self._prisma.promptexecution.find_many(
            where={"scanExecutionId": {"in": [execution.id for execution in scan_executions]}}
        )
        if not prompt_executions:
            return [], []

        observations = await self._prisma.observation.find_many(
            where={"promptExecutionId": {"in": [prompt_execution.id for prompt_execution in prompt_executions]}}
        )
        mentioned_by_prompt_execution: dict[str, bool] = {}
        for observation in observations:
            prompt_execution_id = str(observation.promptExecutionId)
            mentioned_by_prompt_execution[prompt_execution_id] = mentioned_by_prompt_execution.get(
                prompt_execution_id, False
            ) or bool(observation.brandMentioned)

        absent_prompts: list[str] = []
        mentioned_prompts: list[str] = []
        for prompt_execution in prompt_executions:
            prompt_text = str(getattr(prompt_execution, "promptText", "") or "").strip()
            if not prompt_text:
                continue
            if mentioned_by_prompt_execution.get(str(prompt_execution.id), False):
                mentioned_prompts.append(prompt_text)
            else:
                absent_prompts.append(prompt_text)

        return absent_prompts[:10], mentioned_prompts[:10]


def _normalize_recommendation_payload(
    recommendation: dict[str, str],
    index: int,
) -> dict[str, str] | None:
    code = _first_text(
        recommendation.get("recommendation_code"),
        recommendation.get("code"),
        f"recommendation_{index}",
    )
    title = _first_text(
        recommendation.get("title"),
        recommendation.get("next_step"),
        recommendation.get("action"),
    )
    description = _first_text(
        recommendation.get("description"),
        recommendation.get("reason"),
    )
    if not title or not description:
        return None

    priority = _normalize_priority(
        recommendation.get("priority") or recommendation.get("impact") or recommendation.get("severity")
    )
    return {
        "title": title,
        "description": description,
        "priority": priority,
        "rule_triggers_json": json.dumps(
            {
                "recommendation_code": code,
                **recommendation,
            }
        ),
    }


def _first_text(*values: object) -> str:
    for value in values:
        if isinstance(value, str):
            normalized = value.strip()
            if normalized:
                return normalized
    return ""


def _normalize_priority(value: object) -> str:
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"high", "medium", "low"}:
            return normalized
    return "medium"
