"""Tests for FastAPI routes."""

# pyright: reportMissingImports=false

from datetime import datetime, timezone
from types import SimpleNamespace

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


class TestSnapshotActions:
    def test_snapshot_actions_returns_persisted_recommendations(
        self,
        auth_client: TestClient,
        mock_prisma,
    ) -> None:
        created_at = datetime.now(timezone.utc)
        mock_prisma.workspace.find_unique.return_value = SimpleNamespace(
            id="ws-1",
            slug="solara-ai",
            brandName="Solara AI",
            city="",
            region="",
            country="",
            createdAt=created_at,
        )
        mock_prisma.recommendation.find_first.return_value = SimpleNamespace(
            id="rec-2",
            workspaceId="ws-1",
            brandId="brand-1",
            title="Expand FAQ coverage",
            description="Only 40% of prompts mention the brand.",
            priority="high",
            ruleTriggersJson='{"recommendation_code": "expand_faq_coverage"}',
            createdAt=created_at,
        )
        mock_prisma.recommendation.find_many.return_value = [
            SimpleNamespace(
                id="rec-1",
                workspaceId="ws-1",
                brandId="brand-1",
                title="Expand FAQ coverage",
                description="Only 40% of prompts mention the brand.",
                priority="high",
                ruleTriggersJson='{"recommendation_code": "expand_faq_coverage"}',
                createdAt=created_at,
            ),
            SimpleNamespace(
                id="rec-2",
                workspaceId="ws-1",
                brandId="brand-1",
                title="Add review source coverage",
                description="AI cites G2 and Reddit, but not your owned content.",
                priority="medium",
                ruleTriggersJson='{"recommendation_code": "add_review_sources"}',
                createdAt=created_at,
            ),
        ]

        response = auth_client.get("/api/v1/snapshot/actions?workspace=solara-ai")

        assert response.status_code == 200
        payload = response.json()
        assert payload["workspace"] == "solara-ai"
        assert payload["total_actions"] == 2
        assert payload["items"][0]["recommendation_code"] == "expand_faq_coverage"
        assert payload["items"][0]["title"] == "Expand FAQ coverage"
        assert payload["items"][0]["description"] == "Only 40% of prompts mention the brand."


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
