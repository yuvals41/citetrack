"""Tests for onboarding completion route."""

# pyright: reportMissingImports=false, reportUnknownParameterType=false, reportMissingParameterType=false, reportUnusedParameter=false, reportUnknownMemberType=false, reportUntypedFunctionDecorator=false, reportPrivateUsage=false, reportAny=false, reportUnknownVariableType=false, reportUnknownArgumentType=false

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest
from fastapi.testclient import TestClient

from ai_visibility.storage.repositories.user_repo import UserRepository
from ai_visibility.storage.repositories.workspace_repo import WorkspaceRepository
from ai_visibility.storage.types import WorkspaceRecord


@pytest.fixture
def onboarding_payload() -> dict[str, object]:
    return {
        "brand": {"name": "Acme Corp", "domain": "acme.com"},
        "competitors": [
            {"name": "Beta", "domain": "beta.com"},
            {"name": "Gamma", "domain": "gamma.com"},
        ],
        "engines": ["openai", "anthropic"],
    }


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

    scheduled_scans: list[tuple[str, str]] = []

    async def _fake_first_scan(workspace_slug: str, provider: str) -> None:
        scheduled_scans.append((workspace_slug, provider))

    monkeypatch.setattr(user_routes, "get_prisma", _fake_get_prisma)
    monkeypatch.setattr(onboarding_routes, "get_prisma", _fake_get_prisma)
    monkeypatch.setattr(onboarding_routes, "_fire_first_scan", _fake_first_scan)
    return SimpleNamespace(storage_path=storage_path, scheduled_scans=scheduled_scans)


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

    async def brand_find_many(**_kwargs):
        return []

    def _ws_id_from(data: dict[str, object]) -> str:
        flat = data.get("workspaceId")
        if flat:
            return cast(str, flat)
        ws = data.get("workspace")
        if isinstance(ws, dict):
            connect = ws.get("connect")
            if isinstance(connect, dict):
                return cast(str, connect.get("id", ""))
        return ""

    async def brand_create(**kwargs):
        data = kwargs.get("data", {})
        return SimpleNamespace(
            id=cast(str, data.get("id", "brand-1")),
            workspaceId=_ws_id_from(data),
            name=cast(str, data.get("name", "")),
            domain=cast(str, data.get("domain", "")),
            aliases=[],
            createdAt=cast(datetime, data.get("createdAt", datetime.now())),
        )

    async def competitor_create(**kwargs):
        data = kwargs.get("data", {})
        return SimpleNamespace(
            id=cast(str, data.get("id", "comp-1")),
            workspaceId=_ws_id_from(data),
            name=cast(str, data.get("name", "")),
            domain=cast(str, data.get("domain", "")),
            createdAt=cast(datetime, data.get("createdAt", datetime.now())),
            updatedAt=cast(datetime, data.get("createdAt", datetime.now())),
        )

    mock_prisma.workspace.create.side_effect = create
    mock_prisma.workspace.find_unique.side_effect = find_unique
    mock_prisma.query_raw.side_effect = query_raw
    mock_prisma.execute_raw.side_effect = execute_raw
    mock_prisma.brand.find_many.side_effect = brand_find_many
    mock_prisma.brand.create.side_effect = brand_create
    mock_prisma.competitor.create.side_effect = competitor_create

    return workspaces


def test_onboarding_unauth(unauth_client: TestClient, clean_user_repo, onboarding_payload) -> None:
    response = unauth_client.post("/api/v1/onboarding/complete", json=onboarding_payload)

    assert response.status_code in {401, 403}


def test_onboarding_creates_workspace(
    auth_client: TestClient,
    workspace_store,
    onboarding_payload,
) -> None:
    response = auth_client.post("/api/v1/onboarding/complete", json=onboarding_payload)

    assert response.status_code == 200
    assert response.json() == {"workspace_slug": "acme-corp"}


def test_onboarding_idempotent(
    auth_client: TestClient,
    workspace_store,
    onboarding_payload,
) -> None:
    first = auth_client.post("/api/v1/onboarding/complete", json=onboarding_payload)
    second = auth_client.post("/api/v1/onboarding/complete", json=onboarding_payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json() == {"workspace_slug": "acme-corp"}


def test_onboarding_schedules_first_scan(
    auth_client: TestClient,
    workspace_store,
    clean_user_repo,
    onboarding_payload,
) -> None:
    response = auth_client.post("/api/v1/onboarding/complete", json=onboarding_payload)
    assert response.status_code == 200
    assert clean_user_repo.scheduled_scans == [("acme-corp", "anthropic")]


def test_onboarding_idempotent_does_not_schedule_second_scan(
    auth_client: TestClient,
    workspace_store,
    clean_user_repo,
    onboarding_payload,
) -> None:
    auth_client.post("/api/v1/onboarding/complete", json=onboarding_payload)
    auth_client.post("/api/v1/onboarding/complete", json=onboarding_payload)
    assert clean_user_repo.scheduled_scans == [("acme-corp", "anthropic")]


def test_onboarding_invalid_domain(
    auth_client: TestClient,
    workspace_store,
    onboarding_payload,
) -> None:
    bad_payload = dict(onboarding_payload)
    bad_payload["brand"] = {"name": "Acme Corp", "domain": "not-a-domain"}

    response = auth_client.post("/api/v1/onboarding/complete", json=bad_payload)

    assert response.status_code == 422


def test_onboarding_too_many_competitors(
    auth_client: TestClient,
    workspace_store,
    onboarding_payload,
) -> None:
    too_many = dict(onboarding_payload)
    too_many["competitors"] = [{"name": f"Competitor {index}", "domain": f"comp{index}.com"} for index in range(6)]

    response = auth_client.post("/api/v1/onboarding/complete", json=too_many)

    assert response.status_code == 422


def test_onboarding_no_engines(
    auth_client: TestClient,
    workspace_store,
    onboarding_payload,
) -> None:
    missing_engines = dict(onboarding_payload)
    missing_engines["engines"] = []

    response = auth_client.post("/api/v1/onboarding/complete", json=missing_engines)

    assert response.status_code == 422


def test_onboarding_associates_user(
    auth_client: TestClient,
    workspace_store,
    onboarding_payload,
) -> None:
    create_response = auth_client.post("/api/v1/onboarding/complete", json=onboarding_payload)
    workspaces_response = auth_client.get("/api/v1/workspaces/mine")

    assert create_response.status_code == 200
    assert workspaces_response.status_code == 200
    assert [item["slug"] for item in workspaces_response.json()] == ["acme-corp"]


@pytest.mark.asyncio
async def test_resolve_available_slug_returns_base_when_unused() -> None:
    from ai_visibility.api.onboarding_routes import _resolve_available_slug

    user_repo = _FakeUserRepo(owners={})
    workspace_repo = _FakeWorkspaceRepo(slugs=set())

    resolved = await _resolve_available_slug(
        base_slug="acme",
        user_id="u-1",
        user_repo=cast(UserRepository, user_repo),
        workspace_repo=cast(WorkspaceRepository, workspace_repo),
    )

    assert resolved == "acme"


@pytest.mark.asyncio
async def test_resolve_available_slug_returns_base_when_owned_by_same_user() -> None:
    from ai_visibility.api.onboarding_routes import _resolve_available_slug

    user_repo = _FakeUserRepo(owners={"acme": "u-1"})
    workspace_repo = _FakeWorkspaceRepo(slugs={"acme"})

    resolved = await _resolve_available_slug(
        base_slug="acme",
        user_id="u-1",
        user_repo=cast(UserRepository, user_repo),
        workspace_repo=cast(WorkspaceRepository, workspace_repo),
    )

    assert resolved == "acme"


@pytest.mark.asyncio
async def test_resolve_available_slug_suffixes_on_collision_with_other_user() -> None:
    from ai_visibility.api.onboarding_routes import _resolve_available_slug

    user_repo = _FakeUserRepo(owners={"acme": "u-other"})
    workspace_repo = _FakeWorkspaceRepo(slugs={"acme"})

    resolved = await _resolve_available_slug(
        base_slug="acme",
        user_id="u-new",
        user_repo=cast(UserRepository, user_repo),
        workspace_repo=cast(WorkspaceRepository, workspace_repo),
    )

    assert resolved == "acme-2"


@pytest.mark.asyncio
async def test_resolve_available_slug_skips_multiple_taken_suffixes() -> None:
    from ai_visibility.api.onboarding_routes import _resolve_available_slug

    user_repo = _FakeUserRepo(
        owners={"acme": "u-a", "acme-2": "u-b", "acme-3": "u-c"},
    )
    workspace_repo = _FakeWorkspaceRepo(slugs={"acme", "acme-2", "acme-3"})

    resolved = await _resolve_available_slug(
        base_slug="acme",
        user_id="u-new",
        user_repo=cast(UserRepository, user_repo),
        workspace_repo=cast(WorkspaceRepository, workspace_repo),
    )

    assert resolved == "acme-4"


class _FakeUserRepo:
    def __init__(self, owners: dict[str, str]) -> None:
        self._owners = owners

    def get_workspace_owner(self, slug: str) -> str | None:
        return self._owners.get(slug)

    def user_owns_workspace(self, user_id: str, slug: str) -> bool:
        return self._owners.get(slug) == user_id


class _FakeWorkspaceRepo:
    def __init__(self, slugs: set[str]) -> None:
        self._slugs = slugs

    async def get_by_slug(self, slug: str):
        return SimpleNamespace(slug=slug) if slug in self._slugs else None
