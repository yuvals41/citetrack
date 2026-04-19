# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUntypedFunctionDecorator=false

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from ai_visibility.storage.repositories.user_repo import UserRepository


TEST_USER_ID = "user_test_abc123"
SLUG = "acme"


@pytest.fixture(autouse=True)
def _user_owns_slug(monkeypatch: pytest.MonkeyPatch) -> None:
    def _owns(self: UserRepository, user_id: str, workspace_slug: str) -> bool:
        return user_id == TEST_USER_ID and workspace_slug == SLUG

    monkeypatch.setattr(UserRepository, "user_owns_workspace", _owns)


@pytest.fixture
def mock_workspace_record() -> dict[str, Any]:
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
def patched_prisma(mock_workspace_record: dict[str, Any]) -> AsyncIterator[MagicMock]:
    mock_prisma = MagicMock()
    mock_prisma.aivisworkspace.find_unique = AsyncMock(return_value=MagicMock(**mock_workspace_record))
    mock_prisma.aivisworkspace.update = AsyncMock()
    mock_prisma.query_raw = AsyncMock(return_value=[])
    mock_prisma.execute_raw = AsyncMock(return_value=None)
    with patch("ai_visibility.api.settings_routes.get_prisma", new=AsyncMock(return_value=mock_prisma)):
        yield mock_prisma


def test_get_settings_unauth_returns_401(unauth_client: TestClient) -> None:
    response = unauth_client.get(f"/api/v1/workspaces/{SLUG}/settings")
    assert response.status_code in (401, 403)


def test_get_settings_other_workspace_is_forbidden(auth_client: TestClient) -> None:
    response = auth_client.get("/api/v1/workspaces/not-mine/settings")
    assert response.status_code == 403


def test_get_settings_returns_defaults(
    auth_client: TestClient, patched_prisma: MagicMock, mock_workspace_record: dict[str, Any]
) -> None:
    with patch(
        "ai_visibility.storage.repositories.workspace_repo.WorkspaceRepository.get_by_slug",
        new=AsyncMock(return_value=mock_workspace_record),
    ):
        with patch(
            "ai_visibility.storage.repositories.workspace_repo.WorkspaceRepository.get_scan_schedule",
            new=AsyncMock(return_value="daily"),
        ):
            response = auth_client.get(f"/api/v1/workspaces/{SLUG}/settings")
    assert response.status_code == 200
    body = response.json()
    assert body["workspace_slug"] == SLUG
    assert body["name"] == "Acme Corp"
    assert body["scan_schedule"] == "daily"


def test_put_settings_updates_name(
    auth_client: TestClient, patched_prisma: MagicMock, mock_workspace_record: dict[str, Any]
) -> None:
    updated = {**mock_workspace_record, "brand_name": "Acme 2"}
    with patch(
        "ai_visibility.storage.repositories.workspace_repo.WorkspaceRepository.update_by_slug",
        new=AsyncMock(return_value=updated),
    ):
        with patch(
            "ai_visibility.storage.repositories.workspace_repo.WorkspaceRepository.get_scan_schedule",
            new=AsyncMock(return_value="daily"),
        ):
            response = auth_client.put(
                f"/api/v1/workspaces/{SLUG}/settings",
                json={"name": "Acme 2"},
            )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Acme 2"


def test_put_settings_rejects_invalid_schedule(auth_client: TestClient, patched_prisma: MagicMock) -> None:
    response = auth_client.put(
        f"/api/v1/workspaces/{SLUG}/settings",
        json={"scan_schedule": "hourly"},
    )
    assert response.status_code == 422


def test_put_settings_other_workspace_is_forbidden(auth_client: TestClient) -> None:
    response = auth_client.put(
        "/api/v1/workspaces/not-mine/settings",
        json={"name": "hi"},
    )
    assert response.status_code == 403
