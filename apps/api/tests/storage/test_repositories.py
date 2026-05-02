from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from ai_visibility.storage.repositories.mention_repo import MentionRepository
from ai_visibility.storage.repositories.metric_repo import MetricRepository
from ai_visibility.storage.repositories.run_repo import RunRepository
from ai_visibility.storage.repositories.workspace_repo import WorkspaceRepository
from ai_visibility.storage.types import MentionRecord, MetricSnapshotRecord, RunRecord, WorkspaceRecord


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@pytest.mark.asyncio
async def test_run_repository_create_list_latest_and_dedup(tmp_path: Path, mock_prisma) -> None:
    _ = tmp_path
    workspace_repo = WorkspaceRepository(mock_prisma)
    run_repo = RunRepository(mock_prisma)

    workspace_store: dict[str, WorkspaceRecord] = {}
    run_store: dict[str, RunRecord] = {}

    async def workspace_create(*, data):
        workspace_store[data["id"]] = {
            "id": data["id"],
            "slug": data["slug"],
            "brand_name": data["brandName"],
            "city": data.get("city", ""),
            "region": data.get("region", ""),
            "country": data.get("country", ""),
            "created_at": data["createdAt"].isoformat(),
            "scan_schedule": "daily",
        }
        return SimpleNamespace(
            id=data["id"],
            slug=data["slug"],
            brandName=data["brandName"],
            city=data.get("city", ""),
            region=data.get("region", ""),
            country=data.get("country", ""),
            createdAt=data["createdAt"],
        )

    async def workspace_find_unique(*, where):
        workspace = workspace_store.get(where.get("id", ""))
        if workspace is None:
            return None
        return SimpleNamespace(
            id=workspace["id"],
            slug=workspace["slug"],
            brandName=workspace["brand_name"],
            city=workspace["city"],
            region=workspace["region"],
            country=workspace["country"],
            createdAt=_dt(workspace["created_at"]),
        )

    async def run_create(*, data):
        if data["id"] in run_store:
            raise ValueError("duplicate")
        run_store[data["id"]] = {
            "id": data["id"],
            "workspace_id": data["workspaceId"],
            "provider": data["provider"],
            "model": data["model"],
            "prompt_version": data["promptVersion"],
            "parser_version": data["parserVersion"],
            "status": str(data["status"]).lower(),
            "created_at": data["createdAt"].isoformat(),
            "raw_response": data["rawResponse"],
            "error": data["error"],
        }
        return SimpleNamespace(
            id=data["id"],
            workspaceId=data["workspaceId"],
            provider=data["provider"],
            model=data["model"],
            promptVersion=data["promptVersion"],
            parserVersion=data["parserVersion"],
            status=str(data["status"]),
            createdAt=data["createdAt"],
            rawResponse=data["rawResponse"],
            error=data["error"],
        )

    async def run_find_many(*, where, order):
        _ = order
        rows = [run for run in run_store.values() if run["workspace_id"] == where["workspaceId"]]
        rows.sort(key=lambda run: (run["created_at"], run["id"]), reverse=True)
        return [
            SimpleNamespace(
                id=run["id"],
                workspaceId=run["workspace_id"],
                provider=run["provider"],
                model=run["model"],
                promptVersion=run["prompt_version"],
                parserVersion=run["parser_version"],
                status=run["status"].upper(),
                createdAt=_dt(run["created_at"]),
                rawResponse=run["raw_response"],
                error=run["error"],
            )
            for run in rows
        ]

    async def run_find_first(*, where, order):
        rows = await run_find_many(where=where, order=order)
        return rows[0] if rows else None

    mock_prisma.workspace.create.side_effect = workspace_create
    mock_prisma.workspace.find_unique.side_effect = workspace_find_unique
    mock_prisma.run.create.side_effect = run_create
    mock_prisma.run.find_many.side_effect = run_find_many
    mock_prisma.run.find_first.side_effect = run_find_first

    workspace: WorkspaceRecord = {
        "id": "ws_1",
        "slug": "acme",
        "brand_name": "Acme",
        "city": "",
        "region": "",
        "country": "",
        "created_at": "2026-03-08T10:00:00",
        "scan_schedule": "daily",
    }
    _ = await workspace_repo.create(workspace)

    run_one: RunRecord = {
        "id": "run_1",
        "workspace_id": "ws_1",
        "provider": "openai",
        "model": "gpt-4.1",
        "prompt_version": "1.0.0",
        "parser_version": "parser-v1",
        "status": "completed",
        "created_at": "2026-03-08T10:00:00",
        "raw_response": "first response",
        "error": None,
    }
    run_two: RunRecord = {
        "id": "run_2",
        "workspace_id": "ws_1",
        "provider": "anthropic",
        "model": "claude-3-7-sonnet",
        "prompt_version": "1.0.1",
        "parser_version": "parser-v2",
        "status": "completed",
        "created_at": "2026-03-08T11:00:00",
        "raw_response": "second response",
        "error": None,
    }

    assert await run_repo.create(run_one) is True
    with pytest.raises(ValueError):
        _ = await run_repo.create({**run_one, "provider": "google"})
    assert await run_repo.create(run_two) is True

    runs = await run_repo.list_by_workspace("ws_1")
    assert runs == [run_two, run_one]
    assert await run_repo.get_latest_by_workspace("ws_1") == run_two


@pytest.mark.asyncio
async def test_mention_repository_bulk_create_and_list_by_run(tmp_path: Path, mock_prisma) -> None:
    _ = tmp_path
    mention_repo = MentionRepository(mock_prisma)

    store: dict[str, MentionRecord] = {}

    async def mention_create(*, data):
        store[data["id"]] = cast(
            MentionRecord,
            cast(
                object,
                {
                    "id": data["id"],
                    "workspace_id": data["workspaceId"],
                    "run_id": data["runId"],
                    "brand_id": data["brandId"],
                    "mention_type": data["mentionType"],
                    "text": data["text"],
                    "citation": {
                        "url": data["citationUrl"],
                        "domain": data["citationDomain"],
                        "status": str(data["citationStatus"]).lower(),
                    },
                },
            ),
        )
        return SimpleNamespace(
            id=data["id"],
            workspaceId=data["workspaceId"],
            runId=data["runId"],
            brandId=data["brandId"],
            mentionType=data["mentionType"],
            text=data["text"],
            citationUrl=data["citationUrl"],
            citationDomain=data["citationDomain"],
            citationStatus=data["citationStatus"],
        )

    async def mention_find_many(*, where, order):
        _ = order
        rows = [mention for mention in store.values() if mention["run_id"] == where["runId"]]
        rows.sort(key=lambda mention: mention["id"])
        return [
            SimpleNamespace(
                id=mention["id"],
                workspaceId=mention["workspace_id"],
                runId=mention["run_id"],
                brandId=mention["brand_id"],
                mentionType=mention["mention_type"],
                text=mention["text"],
                citationUrl=mention["citation"]["url"],
                citationDomain=mention["citation"]["domain"],
                citationStatus=mention["citation"]["status"].upper(),
            )
            for mention in rows
        ]

    mock_prisma.mention.create.side_effect = mention_create
    mock_prisma.mention.find_many.side_effect = mention_find_many

    mentions: list[MentionRecord] = [
        {
            "id": "mention_1",
            "workspace_id": "ws_1",
            "run_id": "run_1",
            "brand_id": "brand_1",
            "mention_type": "explicit",
            "text": "Acme is recommended.",
            "citation": {
                "url": "https://example.com/acme",
                "domain": "example.com",
                "status": "found",
            },
        },
        {
            "id": "mention_2",
            "workspace_id": "ws_1",
            "run_id": "run_1",
            "brand_id": "brand_1",
            "mention_type": "comparative",
            "text": "Acme beats WidgetCo.",
            "citation": {
                "url": None,
                "domain": None,
                "status": "no_citation",
            },
        },
    ]

    await mention_repo.create_bulk(mentions)
    assert await mention_repo.list_by_run("run_1") == mentions


@pytest.mark.asyncio
async def test_metric_repository_upsert_and_get_latest_by_workspace(tmp_path: Path, mock_prisma) -> None:
    _ = tmp_path
    metric_repo = MetricRepository(mock_prisma)

    store: dict[str, MetricSnapshotRecord] = {}

    async def metric_upsert(*, where, data):
        metric_id = where["id"]
        payload = data["update"] if metric_id in store else data["create"]
        store[metric_id] = {
            "id": metric_id,
            "workspace_id": payload["workspaceId"],
            "brand_id": payload["brandId"],
            "formula_version": payload["formulaVersion"],
            "visibility_score": float(payload["visibilityScore"]),
            "citation_coverage": float(payload["citationCoverage"]),
            "mention_count": int(payload["mentionCount"]),
            "competitor_wins": int(payload["competitorWins"]),
            "created_at": payload["createdAt"].isoformat(),
        }
        metric = store[metric_id]
        return SimpleNamespace(
            id=metric["id"],
            workspaceId=metric["workspace_id"],
            brandId=metric["brand_id"],
            formulaVersion=metric["formula_version"],
            visibilityScore=metric["visibility_score"],
            citationCoverage=metric["citation_coverage"],
            mentionCount=metric["mention_count"],
            competitorWins=metric["competitor_wins"],
            createdAt=_dt(metric["created_at"]),
        )

    async def metric_find_first(*, where, order, skip=0):
        _ = order
        rows = [metric for metric in store.values() if metric["workspace_id"] == where["workspaceId"]]
        rows.sort(key=lambda metric: (metric["created_at"], metric["id"]), reverse=True)
        if skip >= len(rows):
            return None
        metric = rows[skip]
        return SimpleNamespace(
            id=metric["id"],
            workspaceId=metric["workspace_id"],
            brandId=metric["brand_id"],
            formulaVersion=metric["formula_version"],
            visibilityScore=metric["visibility_score"],
            citationCoverage=metric["citation_coverage"],
            mentionCount=metric["mention_count"],
            competitorWins=metric["competitor_wins"],
            createdAt=_dt(metric["created_at"]),
        )

    mock_prisma.metricsnapshot.upsert.side_effect = metric_upsert
    mock_prisma.metricsnapshot.find_first.side_effect = metric_find_first

    _ = await metric_repo.upsert_snapshot(
        {
            "id": "metric_1",
            "workspace_id": "ws_1",
            "brand_id": "brand_1",
            "formula_version": "v1",
            "visibility_score": 61.5,
            "citation_coverage": 0.3,
            "mention_count": 9,
            "competitor_wins": 0,
            "created_at": "2026-03-08T10:00:00",
        }
    )
    _ = await metric_repo.upsert_snapshot(
        {
            "id": "metric_2",
            "workspace_id": "ws_1",
            "brand_id": "brand_1",
            "formula_version": "v1",
            "visibility_score": 75.0,
            "citation_coverage": 0.6,
            "mention_count": 15,
            "competitor_wins": 0,
            "created_at": "2026-03-08T12:00:00",
        }
    )
    _ = await metric_repo.upsert_snapshot(
        {
            "id": "metric_2",
            "workspace_id": "ws_1",
            "brand_id": "brand_1",
            "formula_version": "v2",
            "visibility_score": 80.0,
            "citation_coverage": 0.75,
            "mention_count": 16,
            "competitor_wins": 0,
            "created_at": "2026-03-08T12:00:00",
        }
    )

    expected: MetricSnapshotRecord = {
        "id": "metric_2",
        "workspace_id": "ws_1",
        "brand_id": "brand_1",
        "formula_version": "v2",
        "visibility_score": 80.0,
        "citation_coverage": 0.75,
        "mention_count": 16,
        "competitor_wins": 0,
        "created_at": "2026-03-08T12:00:00",
    }

    assert await metric_repo.get_latest_by_workspace("ws_1") == expected
    assert await metric_repo.get_previous_by_workspace("ws_1") is not None
