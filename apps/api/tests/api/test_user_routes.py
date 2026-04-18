"""Tests for authenticated user and workspace routes."""

# pyright: reportMissingImports=false, reportUnknownParameterType=false, reportMissingParameterType=false, reportUnusedParameter=false, reportUnknownMemberType=false, reportUntypedFunctionDecorator=false, reportPrivateUsage=false, reportAny=false, reportUnknownVariableType=false, reportUnknownArgumentType=false

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest
from fastapi.testclient import TestClient

from ai_visibility.storage.types import WorkspaceRecord


def _workspace_row(*, workspace_id: str, slug: str, brand_name: str, created_at: datetime) -> SimpleNamespace:
    return SimpleNamespace(
        id=workspace_id,
        slug=slug,
        brandName=brand_name,
        city="",
        region="",
        country="",
        createdAt=created_at,
        updatedAt=created_at,
    )


@pytest.fixture
def clean_user_repo(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, mock_prisma):
    from ai_visibility.api import onboarding_routes, user_routes
    from ai_visibility.storage.repositories import user_repo as user_repo_module

    storage_path = tmp_path / "user_associations.json"
    monkeypatch.setattr(user_repo_module, "_storage_path", storage_path)
    onboarding_routes._workspace_metadata.clear()

    async def _fake_get_prisma():
        return mock_prisma

    monkeypatch.setattr(user_routes, "get_prisma", _fake_get_prisma)
    monkeypatch.setattr(onboarding_routes, "get_prisma", _fake_get_prisma)
    return storage_path


@pytest.fixture
def workspace_store(mock_prisma, clean_user_repo):
    workspaces: dict[str, WorkspaceRecord] = {}
    schedules: dict[str, str] = {}

    async def create(*, data: dict[str, object]):
        workspace_id = cast(str, data["id"])
        created_at = cast(datetime, data["createdAt"])
        row = _workspace_row(
            workspace_id=workspace_id,
            slug=cast(str, data["slug"]),
            brand_name=cast(str, data["brandName"]),
            created_at=created_at,
        )
        workspaces[cast(str, data["slug"])] = {
            "id": workspace_id,
            "slug": cast(str, data["slug"]),
            "brand_name": cast(str, data["brandName"]),
            "city": cast(str, data.get("city", "")),
            "region": cast(str, data.get("region", "")),
            "country": cast(str, data.get("country", "")),
            "created_at": created_at.isoformat(),
            "scan_schedule": "daily",
        }
        return row

    async def find_unique(*, where: dict[str, object]):
        slug = cast(str, where["slug"])
        record = workspaces.get(slug)
        if record is None:
            return None
        return _workspace_row(
            workspace_id=record["id"],
            slug=record["slug"],
            brand_name=record["brand_name"],
            created_at=datetime.fromisoformat(record["created_at"]),
        )

    async def query_raw(query: str, *params: object):
        if 'WHERE "workspace_id" = $1 LIMIT 1' in query:
            workspace_id = cast(str, params[0])
            if workspace_id in schedules:
                return [{"scan_schedule": schedules[workspace_id]}]
            return []
        if 'SELECT "workspace_id", "scan_schedule"' in query:
            return [
                {"workspace_id": workspace_id, "scan_schedule": schedule}
                for workspace_id, schedule in schedules.items()
            ]
        return []

    async def execute_raw(query: str, *params: object):
        if 'INSERT INTO "ai_vis_workspace_schedules"' in query:
            schedules[cast(str, params[0])] = cast(str, params[1])
        return None

    mock_prisma.aivisworkspace.create.side_effect = create
    mock_prisma.aivisworkspace.find_unique.side_effect = find_unique
    mock_prisma.query_raw.side_effect = query_raw
    mock_prisma.execute_raw.side_effect = execute_raw

    return workspaces


@pytest.fixture
def seed_workspaces(auth_client: TestClient, workspace_store):
    first = auth_client.post(
        "/api/v1/workspaces",
        json={"name": "Acme", "slug": "acme", "description": "Acme workspace"},
    )
    second = auth_client.post(
        "/api/v1/workspaces",
        json={"name": "Bravo", "slug": "bravo", "description": "Bravo workspace"},
    )
    assert first.status_code == 201
    assert second.status_code == 201
    return workspace_store


def test_me_unauth_returns_401(unauth_client: TestClient, clean_user_repo) -> None:
    response = unauth_client.get("/api/v1/me")

    assert response.status_code in {401, 403}


def test_me_returns_user_id_from_jwt(auth_client: TestClient, clean_user_repo) -> None:
    response = auth_client.get("/api/v1/me")

    assert response.status_code == 200
    assert response.json()["user_id"] == "user_test_abc123"


def test_me_zero_workspaces(auth_client: TestClient, clean_user_repo) -> None:
    response = auth_client.get("/api/v1/me")

    assert response.status_code == 200
    assert response.json()["workspace_count"] == 0
    assert response.json()["has_completed_onboarding"] is False


def test_me_with_workspaces(auth_client: TestClient, seed_workspaces) -> None:
    response = auth_client.get("/api/v1/me")

    assert response.status_code == 200
    assert response.json()["workspace_count"] == 2
    assert response.json()["has_completed_onboarding"] is True


def test_workspaces_mine_empty(auth_client: TestClient, clean_user_repo) -> None:
    response = auth_client.get("/api/v1/workspaces/mine")

    assert response.status_code == 200
    assert response.json() == []


def test_workspaces_mine_returns_user_workspaces(auth_client: TestClient, seed_workspaces) -> None:
    response = auth_client.get("/api/v1/workspaces/mine")

    assert response.status_code == 200
    payload = response.json()
    assert [item["slug"] for item in payload] == ["acme", "bravo"]


def test_create_workspace_valid(auth_client: TestClient, workspace_store) -> None:
    response = auth_client.post(
        "/api/v1/workspaces",
        json={"name": "Acme", "slug": "acme", "description": "Acme workspace"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["slug"] == "acme"
    assert payload["name"] == "Acme"


def test_create_workspace_unauth(unauth_client: TestClient, clean_user_repo) -> None:
    response = unauth_client.post(
        "/api/v1/workspaces",
        json={"name": "Acme", "slug": "acme", "description": "Acme workspace"},
    )

    assert response.status_code in {401, 403}


def test_create_workspace_duplicate_slug(auth_client: TestClient, seed_workspaces) -> None:
    response = auth_client.post(
        "/api/v1/workspaces",
        json={"name": "Acme Duplicate", "slug": "acme", "description": "Duplicate slug"},
    )

    assert response.status_code == 409
