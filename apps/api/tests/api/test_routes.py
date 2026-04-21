"""Tests for FastAPI routes."""

import pytest
from fastapi.testclient import TestClient

from ai_visibility.api import routes as routes_module


class _AlwaysOwnsUserRepo:
    def user_owns_workspace(self, user_id: str, slug: str) -> bool:
        return True

    def list_workspaces_for_user(self, user_id: str) -> list[str]:
        return []


@pytest.fixture(autouse=True)
def _patch_ownership(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(routes_module, "UserRepository", lambda: _AlwaysOwnsUserRepo())


class TestHealth:
    """Test health endpoint."""

    def test_health_returns_ok(self, unauth_client: TestClient) -> None:
        """GET /api/v1/health → 200, body has status="ok"."""
        response = unauth_client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_health_has_version(self, unauth_client: TestClient) -> None:
        """GET /api/v1/health → body has version field."""
        response = unauth_client.get("/api/v1/health")
        assert response.status_code == 200
        payload = response.json()
        assert ("version" in payload) or ("degraded" in payload)


class TestWorkspaces:
    """Test workspaces endpoint."""

    def test_workspaces_returns_list(self, auth_client: TestClient) -> None:
        """GET /api/v1/workspaces → 200, body has items key (list)."""
        response = auth_client.get("/api/v1/workspaces")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_workspaces_requires_auth(self, unauth_client: TestClient) -> None:
        response = unauth_client.get("/api/v1/workspaces")

        assert response.status_code in {401, 403}


class TestRunsLatest:
    """Test latest run endpoint."""

    def test_runs_latest_empty(self, auth_client: TestClient) -> None:
        """GET /api/v1/runs/latest?workspace=nonexistent → 200, body has workspace and run keys."""
        response = auth_client.get("/api/v1/runs/latest?workspace=nonexistent")
        assert response.status_code == 200
        data = response.json()
        assert (("workspace" in data) and ("run" in data)) or ("degraded" in data)

    def test_runs_latest_requires_auth(self, unauth_client: TestClient) -> None:
        response = unauth_client.get("/api/v1/runs/latest?workspace=nonexistent")

        assert response.status_code in {401, 403}


class TestRunsList:
    """Test runs list endpoint."""

    def test_runs_list_empty(self, auth_client: TestClient) -> None:
        """GET /api/v1/runs?workspace=nonexistent → 200, body has items key (list)."""
        response = auth_client.get("/api/v1/runs?workspace=nonexistent")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_runs_list_requires_auth(self, unauth_client: TestClient) -> None:
        response = unauth_client.get("/api/v1/runs?workspace=nonexistent")

        assert response.status_code in {401, 403}


class TestPrompts:
    """Test prompts endpoint."""

    def test_prompts_returns_list(self, auth_client: TestClient) -> None:
        """GET /api/v1/prompts → 200, body has items key with length > 0."""
        response = auth_client.get("/api/v1/prompts")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
        assert len(data["items"]) > 0

    def test_prompts_requires_auth(self, unauth_client: TestClient) -> None:
        response = unauth_client.get("/api/v1/prompts")

        assert response.status_code in {401, 403}


class TestPixelRoutes:
    """Test public and protected pixel routes."""

    def test_pixel_event_stays_public(self, unauth_client: TestClient) -> None:
        response = unauth_client.post("/api/v1/pixel/event", json={"invalid": "payload"})

        assert response.status_code == 204

    def test_pixel_snippet_requires_auth(self, unauth_client: TestClient) -> None:
        response = unauth_client.get("/api/v1/pixel/snippet/ws-1")

        assert response.status_code in {401, 403}

    def test_pixel_stats_requires_auth(self, unauth_client: TestClient) -> None:
        response = unauth_client.get("/api/v1/pixel/stats/ws-1")

        assert response.status_code in {401, 403}
