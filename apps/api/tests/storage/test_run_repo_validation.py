import sqlite3
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from ai_visibility.storage.repositories.run_repo import RunRepository
from ai_visibility.storage.repositories.workspace_repo import WorkspaceRepository
from ai_visibility.storage.types import RunRecord, WorkspaceRecord


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@pytest.fixture
def repos(mock_prisma):
    workspaces: dict[str, WorkspaceRecord] = {}
    runs: dict[str, RunRecord] = {}

    async def workspace_create(*, data):
        slug_exists = any(workspace["slug"] == data["slug"] for workspace in workspaces.values())
        if data["id"] in workspaces or slug_exists:
            raise sqlite3.IntegrityError("workspace already exists")
        workspaces[data["id"]] = {
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
        if "id" in where:
            workspace = workspaces.get(where["id"])
            if workspace is None:
                return None
            return SimpleNamespace(
                id=workspace["id"],
                slug=workspace["slug"],
                brandName=workspace["brand_name"],
                city=workspace.get("city", ""),
                region=workspace.get("region", ""),
                country=workspace.get("country", ""),
                createdAt=_parse_iso(workspace["created_at"]),
            )
        return None

    async def run_create(*, data):
        if data["id"] in runs:
            raise sqlite3.IntegrityError("run already exists")
        runs[data["id"]] = {
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
        workspace_runs = [run for run in runs.values() if run["workspace_id"] == where["workspaceId"]]
        workspace_runs.sort(key=lambda run: (run["created_at"], run["id"]), reverse=True)
        return [
            SimpleNamespace(
                id=run["id"],
                workspaceId=run["workspace_id"],
                provider=run["provider"],
                model=run["model"],
                promptVersion=run["prompt_version"],
                parserVersion=run["parser_version"],
                status=run["status"].upper(),
                createdAt=_parse_iso(run["created_at"]),
                rawResponse=run["raw_response"],
                error=run["error"],
            )
            for run in workspace_runs
        ]

    async def run_find_first(*, where, order):
        listed = await run_find_many(where=where, order=order)
        return listed[0] if listed else None

    mock_prisma.aivisworkspace.create.side_effect = workspace_create
    mock_prisma.aivisworkspace.find_unique.side_effect = workspace_find_unique
    mock_prisma.aivisrun.create.side_effect = run_create
    mock_prisma.aivisrun.find_many.side_effect = run_find_many
    mock_prisma.aivisrun.find_first.side_effect = run_find_first

    return WorkspaceRepository(mock_prisma), RunRepository(mock_prisma)


def _workspace() -> WorkspaceRecord:
    return {
        "id": "ws_1",
        "slug": "acme",
        "brand_name": "Acme",
        "city": "",
        "region": "",
        "country": "",
        "created_at": "2026-03-13T10:00:00",
        "scan_schedule": "daily",
    }


def _run(*, run_id: str, workspace_id: str) -> RunRecord:
    return {
        "id": run_id,
        "workspace_id": workspace_id,
        "provider": "openai",
        "model": "gpt-4.1",
        "prompt_version": "1.0.0",
        "parser_version": "parser-v1",
        "status": "completed",
        "created_at": "2026-03-13T11:00:00",
        "raw_response": "raw payload",
        "error": None,
    }


@pytest.mark.asyncio
async def test_create_with_valid_workspace_id_persists_run(tmp_path: Path, repos) -> None:
    _ = tmp_path
    workspace_repo, run_repo = repos
    _ = await workspace_repo.create(_workspace())

    created = await run_repo.create(_run(run_id="run_1", workspace_id="ws_1"))
    runs = await run_repo.list_by_workspace("ws_1")

    assert created is True
    assert len(runs) == 1
    assert runs[0]["id"] == "run_1"


@pytest.mark.asyncio
async def test_create_with_invalid_workspace_id_raises_value_error(tmp_path: Path, repos) -> None:
    _ = tmp_path
    _, run_repo = repos

    with pytest.raises(ValueError, match="Workspace not found: missing_ws"):
        _ = await run_repo.create(_run(run_id="run_1", workspace_id="missing_ws"))


@pytest.mark.asyncio
async def test_create_with_all_fields_populated_is_persisted_exactly(tmp_path: Path, repos) -> None:
    _ = tmp_path
    workspace_repo, run_repo = repos
    _ = await workspace_repo.create(_workspace())

    run: RunRecord = {
        "id": "run_full",
        "workspace_id": "ws_1",
        "provider": "anthropic",
        "model": "claude-3-7-sonnet",
        "prompt_version": "2.1.0",
        "parser_version": "parser-v3",
        "status": "failed",
        "created_at": "2026-03-13T12:30:00",
        "raw_response": "complete raw output",
        "error": "provider timeout",
    }

    _ = await run_repo.create(run)
    latest = await run_repo.get_latest_by_workspace("ws_1")
    assert latest == run


@pytest.mark.asyncio
async def test_create_duplicate_run_id_raises_integrity_error(tmp_path: Path, repos) -> None:
    _ = tmp_path
    workspace_repo, run_repo = repos
    _ = await workspace_repo.create(_workspace())
    _ = await run_repo.create(_run(run_id="run_1", workspace_id="ws_1"))

    with pytest.raises(sqlite3.IntegrityError):
        _ = await run_repo.create(_run(run_id="run_1", workspace_id="ws_1"))
