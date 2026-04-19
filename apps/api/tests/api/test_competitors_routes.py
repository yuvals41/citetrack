from __future__ import annotations

# pyright: reportMissingImports=false, reportUnknownParameterType=false, reportMissingParameterType=false, reportUnusedParameter=false, reportUnknownMemberType=false, reportUntypedFunctionDecorator=false, reportPrivateUsage=false, reportAny=false, reportUnknownVariableType=false, reportUnknownArgumentType=false

from datetime import datetime
from types import SimpleNamespace
from typing import cast
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient


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


def _competitor_row(
    *,
    competitor_id: str,
    workspace_id: str,
    name: str,
    domain: str,
    created_at: datetime,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=competitor_id,
        workspaceId=workspace_id,
        name=name,
        domain=domain,
        createdAt=created_at,
        updatedAt=created_at,
    )


@pytest.fixture
def competitor_store(monkeypatch: pytest.MonkeyPatch, mock_prisma: MagicMock):
    from ai_visibility.api import competitors_routes, user_routes

    workspaces: dict[str, dict[str, str]] = {}
    competitors: dict[str, dict[str, object]] = {}

    async def _fake_get_prisma():
        return mock_prisma

    monkeypatch.setattr(competitors_routes, "get_prisma", _fake_get_prisma)
    monkeypatch.setattr(user_routes, "get_prisma", _fake_get_prisma)

    async def workspace_create(*, data: dict[str, object]):
        workspace_id = cast(str, data["id"])
        created_at = cast(datetime, data["createdAt"])
        workspaces[cast(str, data["slug"])] = {
            "id": workspace_id,
            "slug": cast(str, data["slug"]),
            "brand_name": cast(str, data["brandName"]),
            "created_at": created_at.isoformat(),
        }
        return _workspace_row(
            workspace_id=workspace_id,
            slug=cast(str, data["slug"]),
            brand_name=cast(str, data["brandName"]),
            created_at=created_at,
        )

    async def workspace_find_unique(*, where: dict[str, object]):
        if "slug" in where:
            record = workspaces.get(cast(str, where["slug"]))
        else:
            wanted_id = cast(str, where["id"])
            record = next((item for item in workspaces.values() if item["id"] == wanted_id), None)
        if record is None:
            return None
        return _workspace_row(
            workspace_id=record["id"],
            slug=record["slug"],
            brand_name=record["brand_name"],
            created_at=datetime.fromisoformat(record["created_at"]),
        )

    async def competitor_find_many(*, where: dict[str, object], order: object | None = None):
        _ = order
        workspace_id = cast(str, where["workspaceId"])
        rows = [item for item in competitors.values() if item["workspace_id"] == workspace_id]
        rows.sort(key=lambda item: (cast(datetime, item["created_at"]), cast(str, item["id"])))
        return [
            _competitor_row(
                competitor_id=cast(str, row["id"]),
                workspace_id=cast(str, row["workspace_id"]),
                name=cast(str, row["name"]),
                domain=cast(str, row["domain"]),
                created_at=cast(datetime, row["created_at"]),
            )
            for row in rows
        ]

    async def competitor_find_first(*, where: dict[str, object]):
        workspace_id = cast(str, where["workspaceId"])
        domain = cast(str, where["domain"])
        row = next(
            (
                item
                for item in competitors.values()
                if item["workspace_id"] == workspace_id and item["domain"] == domain
            ),
            None,
        )
        if row is None:
            return None
        return _competitor_row(
            competitor_id=cast(str, row["id"]),
            workspace_id=cast(str, row["workspace_id"]),
            name=cast(str, row["name"]),
            domain=cast(str, row["domain"]),
            created_at=cast(datetime, row["created_at"]),
        )

    async def competitor_create(*, data: dict[str, object]):
        competitor_id = cast(str, data["id"])
        created_at = cast(datetime, data["createdAt"])
        competitors[competitor_id] = {
            "id": competitor_id,
            "workspace_id": cast(str, data["workspaceId"]),
            "name": cast(str, data["name"]),
            "domain": cast(str, data["domain"]),
            "created_at": created_at,
        }
        return _competitor_row(
            competitor_id=competitor_id,
            workspace_id=cast(str, data["workspaceId"]),
            name=cast(str, data["name"]),
            domain=cast(str, data["domain"]),
            created_at=created_at,
        )

    async def competitor_find_unique(*, where: dict[str, object]):
        row = competitors.get(cast(str, where["id"]))
        if row is None:
            return None
        return _competitor_row(
            competitor_id=cast(str, row["id"]),
            workspace_id=cast(str, row["workspace_id"]),
            name=cast(str, row["name"]),
            domain=cast(str, row["domain"]),
            created_at=cast(datetime, row["created_at"]),
        )

    async def competitor_delete(*, where: dict[str, object]):
        _ = competitors.pop(cast(str, where["id"]), None)
        return None

    async def query_raw(query: str, *params: object):
        _ = params
        if 'WHERE "workspace_id" = $1 LIMIT 1' in query:
            return []
        if 'SELECT "workspace_id", "scan_schedule"' in query:
            return []
        return []

    async def execute_raw(query: str, *params: object):
        _ = (query, params)
        return None

    mock_prisma.aivisworkspace.create.side_effect = workspace_create
    mock_prisma.aivisworkspace.find_unique.side_effect = workspace_find_unique
    mock_prisma.aiviscompetitor.find_many.side_effect = competitor_find_many
    mock_prisma.aiviscompetitor.find_first.side_effect = competitor_find_first
    mock_prisma.aiviscompetitor.create.side_effect = competitor_create
    mock_prisma.aiviscompetitor.find_unique.side_effect = competitor_find_unique
    mock_prisma.aiviscompetitor.delete.side_effect = competitor_delete
    mock_prisma.query_raw.side_effect = query_raw
    mock_prisma.execute_raw.side_effect = execute_raw

    return {"workspaces": workspaces, "competitors": competitors}


@pytest.fixture
def workspace_slug(auth_client: TestClient, competitor_store) -> str:
    response = auth_client.post(
        "/api/v1/workspaces",
        json={"name": "Acme", "slug": "acme", "description": "Acme workspace"},
    )
    assert response.status_code == 201
    return "acme"


def test_get_competitors_unauth_returns_401(unauth_client: TestClient, competitor_store) -> None:
    response = unauth_client.get("/api/v1/workspaces/acme/competitors")
    assert response.status_code in {401, 403}


def test_get_competitors_empty(auth_client: TestClient, workspace_slug: str) -> None:
    response = auth_client.get(f"/api/v1/workspaces/{workspace_slug}/competitors")
    assert response.status_code == 200
    assert response.json() == {"workspace": workspace_slug, "items": [], "degraded": None}


def test_get_competitors_populated(auth_client: TestClient, workspace_slug: str) -> None:
    create_one = auth_client.post(
        f"/api/v1/workspaces/{workspace_slug}/competitors",
        json={"name": "Rival One", "domain": "rival-one.com"},
    )
    create_two = auth_client.post(
        f"/api/v1/workspaces/{workspace_slug}/competitors",
        json={"name": "Rival Two", "domain": "rival-two.com"},
    )

    assert create_one.status_code == 201
    assert create_two.status_code == 201

    response = auth_client.get(f"/api/v1/workspaces/{workspace_slug}/competitors")
    payload = response.json()

    assert response.status_code == 200
    assert payload["workspace"] == workspace_slug
    assert len(payload["items"]) == 2
    assert payload["items"][0]["name"] == "Rival One"
    assert payload["items"][1]["domain"] == "rival-two.com"


def test_post_competitor_valid(auth_client: TestClient, workspace_slug: str) -> None:
    response = auth_client.post(
        f"/api/v1/workspaces/{workspace_slug}/competitors",
        json={"name": "Example", "domain": "example.com"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["name"] == "Example"
    assert payload["domain"] == "example.com"
    assert payload["workspace_id"]


def test_post_competitor_duplicate_domain_returns_409(auth_client: TestClient, workspace_slug: str) -> None:
    first = auth_client.post(
        f"/api/v1/workspaces/{workspace_slug}/competitors",
        json={"name": "Example", "domain": "example.com"},
    )
    second = auth_client.post(
        f"/api/v1/workspaces/{workspace_slug}/competitors",
        json={"name": "Example Copy", "domain": "https://example.com/path"},
    )

    assert first.status_code == 201
    assert second.status_code == 409


def test_post_competitor_invalid_domain_returns_422(auth_client: TestClient, workspace_slug: str) -> None:
    response = auth_client.post(
        f"/api/v1/workspaces/{workspace_slug}/competitors",
        json={"name": "Broken", "domain": "not a domain"},
    )
    assert response.status_code == 422


def test_post_competitor_normalizes_domain(auth_client: TestClient, workspace_slug: str) -> None:
    response = auth_client.post(
        f"/api/v1/workspaces/{workspace_slug}/competitors",
        json={"name": "Example", "domain": "https://example.com/foo"},
    )

    assert response.status_code == 201
    assert response.json()["domain"] == "example.com"


def test_delete_competitor_unauth_returns_401(
    auth_client: TestClient,
    unauth_client: TestClient,
    workspace_slug: str,
) -> None:
    created = auth_client.post(
        f"/api/v1/workspaces/{workspace_slug}/competitors",
        json={"name": "Example", "domain": "example.com"},
    )
    competitor_id = created.json()["id"]

    response = unauth_client.delete(f"/api/v1/workspaces/{workspace_slug}/competitors/{competitor_id}")
    assert response.status_code in {401, 403}


def test_delete_competitor_existing_and_nonexistent(auth_client: TestClient, workspace_slug: str) -> None:
    created = auth_client.post(
        f"/api/v1/workspaces/{workspace_slug}/competitors",
        json={"name": "Example", "domain": "example.com"},
    )
    competitor_id = created.json()["id"]

    deleted = auth_client.delete(f"/api/v1/workspaces/{workspace_slug}/competitors/{competitor_id}")
    missing = auth_client.delete(f"/api/v1/workspaces/{workspace_slug}/competitors/missing-id")

    assert deleted.status_code == 204
    assert missing.status_code == 404
