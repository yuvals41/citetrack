"""Tests for FastAPI routes."""

from fastapi.testclient import TestClient

from ai_visibility.api import create_app


class TestHealth:
    """Test health endpoint."""

    def test_health_returns_ok(self) -> None:
        """GET /api/v1/health → 200, body has status="ok"."""
        app = create_app()
        client = TestClient(app)
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_health_has_version(self) -> None:
        """GET /api/v1/health → body has version field."""
        app = create_app()
        client = TestClient(app)
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        payload = response.json()
        assert ("version" in payload) or ("degraded" in payload)


class TestWorkspaces:
    """Test workspaces endpoint."""

    def test_workspaces_returns_list(self) -> None:
        """GET /api/v1/workspaces → 200, body has items key (list)."""
        app = create_app()
        client = TestClient(app)
        response = client.get("/api/v1/workspaces")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)


class TestRunsLatest:
    """Test latest run endpoint."""

    def test_runs_latest_empty(self) -> None:
        """GET /api/v1/runs/latest?workspace=nonexistent → 200, body has workspace and run keys."""
        app = create_app()
        client = TestClient(app)
        response = client.get("/api/v1/runs/latest?workspace=nonexistent")
        assert response.status_code == 200
        data = response.json()
        assert (("workspace" in data) and ("run" in data)) or ("degraded" in data)


class TestRunsList:
    """Test runs list endpoint."""

    def test_runs_list_empty(self) -> None:
        """GET /api/v1/runs?workspace=nonexistent → 200, body has items key (list)."""
        app = create_app()
        client = TestClient(app)
        response = client.get("/api/v1/runs?workspace=nonexistent")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)


class TestPrompts:
    """Test prompts endpoint."""

    def test_prompts_returns_list(self) -> None:
        """GET /api/v1/prompts → 200, body has items key with length > 0."""
        app = create_app()
        client = TestClient(app)
        response = client.get("/api/v1/prompts")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
        assert len(data["items"]) > 0
