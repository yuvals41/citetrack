# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUntypedFunctionDecorator=false, reportUnknownParameterType=false, reportMissingParameterType=false, reportUnusedParameter=false, reportUnknownMemberType=false, reportAny=false, reportUnknownArgumentType=false, reportUnusedImport=false, reportAttributeAccessIssue=false, reportUnusedFunction=false

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from ai_visibility.storage.repositories.brand_alias_repo import BrandAliasRepository
from ai_visibility.storage.repositories.user_repo import UserRepository


TEST_USER_ID = "user_test_abc123"
SLUG = "acme"


def _brand_row(
    *,
    brand_id: str,
    workspace_id: str,
    name: str,
    domain: str,
    aliases: list[str],
) -> SimpleNamespace:
    return SimpleNamespace(
        id=brand_id,
        workspaceId=workspace_id,
        name=name,
        domain=domain,
        aliases=aliases,
    )


@pytest.fixture(autouse=True)
def _user_owns_slug(monkeypatch: pytest.MonkeyPatch) -> None:
    def _owns(self: UserRepository, user_id: str, workspace_slug: str) -> bool:
        return user_id == TEST_USER_ID and workspace_slug == SLUG

    monkeypatch.setattr(UserRepository, "user_owns_workspace", _owns)


@pytest.fixture(autouse=True)
def _isolated_alias_storage(monkeypatch: pytest.MonkeyPatch, tmp_path):
    storage = tmp_path / "brand_aliases.json"
    monkeypatch.setattr(
        "ai_visibility.storage.repositories.brand_alias_repo._storage_path",
        storage,
    )
    return storage


@pytest.fixture
def mock_workspace_record() -> dict[str, str]:
    return {
        "id": "ws_1",
        "slug": SLUG,
        "brand_name": "Acme Corp",
        "city": "",
        "region": "",
        "country": "",
        "created_at": datetime(2026, 4, 19, tzinfo=timezone.utc).isoformat(),
    }


@pytest.fixture
def patched_prisma(monkeypatch: pytest.MonkeyPatch, mock_workspace_record: dict[str, str]) -> MagicMock:
    store: dict[str, object] = {"brand": None}
    mock_prisma = MagicMock()

    async def find_first(*, where: dict[str, object], order: object | None = None):
        _ = (where, order)
        return store["brand"]

    async def create(*, data: dict[str, object]):
        ws_val = data.get("workspaceId")
        if ws_val is None:
            ws_val = cast(dict[str, object], cast(dict[str, object], data["workspace"])["connect"])["id"]
        row = _brand_row(
            brand_id=str(data["id"]),
            workspace_id=str(ws_val),
            name=str(data["name"]),
            domain=str(data["domain"]),
            aliases=[str(alias) for alias in cast(list[object], data.get("aliases", []))],
        )
        store["brand"] = row
        return row

    async def update(*, where: dict[str, object], data: dict[str, object]):
        brand = store["brand"]
        if brand is None:
            raise AssertionError("update called without existing brand")
        row = _brand_row(
            brand_id=str(where["id"]),
            workspace_id=str(cast(SimpleNamespace, brand).workspaceId),
            name=str(data["name"]),
            domain=str(data["domain"]),
            aliases=[str(alias) for alias in cast(list[object], data.get("aliases", []))],
        )
        store["brand"] = row
        return row

    mock_prisma.brand.find_first.side_effect = find_first
    mock_prisma.brand.find_many = AsyncMock(return_value=[])
    mock_prisma.brand.create.side_effect = create
    mock_prisma.brand.update.side_effect = update

    monkeypatch.setattr(
        "ai_visibility.api.brands_routes.get_prisma",
        AsyncMock(return_value=mock_prisma),
    )
    monkeypatch.setattr(
        "ai_visibility.storage.repositories.workspace_repo.WorkspaceRepository.get_by_slug",
        AsyncMock(return_value=mock_workspace_record),
    )

    mock_prisma._brand_store = store
    return mock_prisma


def test_get_brand_unauth_returns_401(unauth_client: TestClient) -> None:
    response = unauth_client.get(f"/api/v1/workspaces/{SLUG}/brand")
    assert response.status_code in (401, 403)


def test_get_brand_other_workspace_is_forbidden(auth_client: TestClient) -> None:
    response = auth_client.get("/api/v1/workspaces/not-mine/brand")
    assert response.status_code == 403


def test_get_brand_missing_returns_404(auth_client: TestClient, patched_prisma: MagicMock) -> None:
    response = auth_client.get(f"/api/v1/workspaces/{SLUG}/brand")
    assert response.status_code == 404
    assert response.json()["detail"] == "Brand not found"


def test_get_brand_existing_returns_200(auth_client: TestClient, patched_prisma: MagicMock) -> None:
    patched_prisma._brand_store["brand"] = _brand_row(
        brand_id="brand_1",
        workspace_id="ws_1",
        name="Acme",
        domain="acme.com",
        aliases=[],
    )
    _ = BrandAliasRepository().set_aliases("ws_1", ["Acme AI"])

    response = auth_client.get(f"/api/v1/workspaces/{SLUG}/brand")

    assert response.status_code == 200
    assert response.json() == {
        "id": "brand_1",
        "workspace_id": "ws_1",
        "name": "Acme",
        "domain": "acme.com",
        "aliases": ["Acme AI"],
        "degraded": None,
    }


def test_put_brand_creates_when_missing(auth_client: TestClient, patched_prisma: MagicMock) -> None:
    response = auth_client.put(
        f"/api/v1/workspaces/{SLUG}/brand",
        json={"name": "Acme", "domain": "https://acme.com/path", "aliases": [" Acme AI "]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Acme"
    assert body["domain"] == "acme.com"
    assert body["aliases"] == ["Acme AI"]


def test_put_brand_updates_existing_idempotently(auth_client: TestClient, patched_prisma: MagicMock) -> None:
    patched_prisma._brand_store["brand"] = _brand_row(
        brand_id="brand_1",
        workspace_id="ws_1",
        name="Acme",
        domain="acme.com",
        aliases=[],
    )

    first = auth_client.put(
        f"/api/v1/workspaces/{SLUG}/brand",
        json={"name": "Acme 2", "domain": "acme.io", "aliases": ["Acme"]},
    )
    second = auth_client.put(
        f"/api/v1/workspaces/{SLUG}/brand",
        json={"name": "Acme 2", "domain": "acme.io", "aliases": ["Acme"]},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == "brand_1"
    assert second.json() == first.json()


def test_put_brand_invalid_domain_returns_422(auth_client: TestClient, patched_prisma: MagicMock) -> None:
    response = auth_client.put(
        f"/api/v1/workspaces/{SLUG}/brand",
        json={"name": "Broken", "domain": "not a domain", "aliases": []},
    )
    assert response.status_code == 422


def test_put_brand_other_workspace_is_forbidden(auth_client: TestClient) -> None:
    response = auth_client.put(
        "/api/v1/workspaces/not-mine/brand",
        json={"name": "Acme", "domain": "acme.com", "aliases": []},
    )
    assert response.status_code == 403
