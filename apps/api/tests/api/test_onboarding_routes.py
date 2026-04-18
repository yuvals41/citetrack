"""Tests for onboarding completion route."""

# pyright: reportMissingImports=false, reportUnknownParameterType=false, reportMissingParameterType=false, reportUnusedParameter=false, reportUnknownMemberType=false, reportUntypedFunctionDecorator=false, reportPrivateUsage=false, reportAny=false, reportUnknownVariableType=false, reportUnknownArgumentType=false

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest
from fastapi.testclient import TestClient

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
