from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from ai_visibility.cli import list_workspaces
from ai_visibility.storage.repositories.workspace_repo import WorkspaceRepository
from ai_visibility.storage.types import WorkspaceRecord


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _configure_workspace_store(mock_prisma):
    store: dict[str, WorkspaceRecord] = {}
    schedules: dict[str, str] = {}

    async def create_workspace(*, data):
        store[data["id"]] = {
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

    async def find_unique(*, where):
        target = None
        if "slug" in where:
            target = next((workspace for workspace in store.values() if workspace["slug"] == where["slug"]), None)
        elif "id" in where:
            target = store.get(where["id"])
        if target is None:
            return None
        return SimpleNamespace(
            id=target["id"],
            slug=target["slug"],
            brandName=target["brand_name"],
            city=target["city"],
            region=target["region"],
            country=target["country"],
            createdAt=_dt(target["created_at"]),
        )

    async def find_many(*, order):
        _ = order
        ordered = sorted(store.values(), key=lambda workspace: (workspace["created_at"], workspace["id"]))
        return [
            SimpleNamespace(
                id=workspace["id"],
                slug=workspace["slug"],
                brandName=workspace["brand_name"],
                city=workspace["city"],
                region=workspace["region"],
                country=workspace["country"],
                createdAt=_dt(workspace["created_at"]),
            )
            for workspace in ordered
        ]

    async def execute_raw(query, *args):
        if 'INSERT INTO "ai_vis_workspace_schedules"' in query:
            workspace_id, schedule = args
            schedules[str(workspace_id)] = str(schedule)
        return None

    async def query_raw(query, *args):
        if 'SELECT "scan_schedule" FROM "ai_vis_workspace_schedules"' in query:
            workspace_id = str(args[0])
            if workspace_id in schedules:
                return [{"scan_schedule": schedules[workspace_id]}]
            return []
        if 'SELECT "workspace_id", "scan_schedule" FROM "ai_vis_workspace_schedules"' in query:
            return [
                {"workspace_id": workspace_id, "scan_schedule": schedule}
                for workspace_id, schedule in schedules.items()
            ]
        return []

    mock_prisma.workspace.create.side_effect = create_workspace
    mock_prisma.workspace.find_unique.side_effect = find_unique
    mock_prisma.workspace.find_many.side_effect = find_many
    mock_prisma.execute_raw.side_effect = execute_raw
    mock_prisma.query_raw.side_effect = query_raw

    return WorkspaceRepository(mock_prisma), store


@pytest.fixture
def workspace_repo_with_store(mock_prisma):
    return _configure_workspace_store(mock_prisma)


@pytest.mark.asyncio
async def test_workspace_repository_create_get_by_slug_and_list_all(tmp_path: Path, workspace_repo_with_store) -> None:
    _ = tmp_path
    repo, _store = workspace_repo_with_store

    workspace_one: WorkspaceRecord = {
        "id": "ws_1",
        "slug": "acme",
        "brand_name": "Acme",
        "city": "Austin",
        "region": "TX",
        "country": "US",
        "created_at": "2026-03-08T10:00:00",
        "scan_schedule": "daily",
    }
    workspace_two: WorkspaceRecord = {
        "id": "ws_2",
        "slug": "globex",
        "brand_name": "Globex",
        "city": "",
        "region": "",
        "country": "",
        "created_at": "2026-03-08T11:00:00",
        "scan_schedule": "daily",
    }

    _ = await repo.create(workspace_one)
    _ = await repo.create(workspace_two)

    assert await repo.get_by_slug("acme") == workspace_one
    assert await repo.list_all() == [workspace_one, workspace_two]


@pytest.mark.asyncio
async def test_list_workspaces_cli_returns_seeded_workspaces_as_json(tmp_path: Path, patch_get_prisma) -> None:
    _ = tmp_path
    mock_prisma = patch_get_prisma
    repo, _store = _configure_workspace_store(mock_prisma)

    _ = await repo.create(
        {
            "id": "ws_1",
            "slug": "acme",
            "brand_name": "Acme",
            "city": "",
            "region": "",
            "country": "",
            "created_at": "2026-03-08T10:00:00",
            "scan_schedule": "daily",
        }
    )
    _ = await repo.create(
        {
            "id": "ws_2",
            "slug": "globex",
            "brand_name": "Globex",
            "city": "",
            "region": "",
            "country": "",
            "created_at": "2026-03-08T11:00:00",
            "scan_schedule": "daily",
        }
    )

    result = await list_workspaces("json")

    assert result == {
        "status": "success",
        "total_count": 2,
        "workspaces": [
            {
                "id": "ws_1",
                "slug": "acme",
                "brand_name": "Acme",
                "city": "",
                "region": "",
                "country": "",
                "created_at": "2026-03-08T10:00:00",
                "scan_schedule": "daily",
            },
            {
                "id": "ws_2",
                "slug": "globex",
                "brand_name": "Globex",
                "city": "",
                "region": "",
                "country": "",
                "created_at": "2026-03-08T11:00:00",
                "scan_schedule": "daily",
            },
        ],
    }
