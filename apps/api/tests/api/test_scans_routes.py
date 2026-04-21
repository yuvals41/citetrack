from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from ai_visibility.api import scans_routes


class _FakeUserRepo:
    def __init__(self, owned: set[tuple[str, str]]) -> None:
        self._owned = owned

    def user_owns_workspace(self, user_id: str, slug: str) -> bool:
        return (user_id, slug) in self._owned


class _RunOrchestratorFactory:
    def __init__(self, scan_result) -> None:
        self._scan_result = scan_result
        self.init_calls: list[dict[str, str]] = []
        self.scan_calls: int = 0

    def __call__(self, *, workspace_slug: str, provider: str):
        self.init_calls.append({"workspace_slug": workspace_slug, "provider": provider})
        factory = self

        class _Stub:
            async def scan(self):
                factory.scan_calls += 1
                return factory._scan_result

        return _Stub()


def test_run_scan_requires_auth(unauth_client: TestClient) -> None:
    response = unauth_client.post("/api/v1/workspaces/acme/scan")
    assert response.status_code in {401, 403}


def test_run_scan_rejects_unknown_provider(monkeypatch: pytest.MonkeyPatch, auth_client: TestClient) -> None:
    response = auth_client.post("/api/v1/workspaces/acme/scan?provider=bogus-provider")
    assert response.status_code == 400
    assert "provider" in response.json()["detail"].lower()


def test_run_scan_forbidden_if_user_does_not_own_workspace(
    monkeypatch: pytest.MonkeyPatch, auth_client: TestClient
) -> None:
    fake_user_repo = _FakeUserRepo(owned=set())
    monkeypatch.setattr(scans_routes, "UserRepository", lambda: fake_user_repo)

    response = auth_client.post("/api/v1/workspaces/acme/scan")
    assert response.status_code == 403


_TEST_USER_ID = "user_test_abc123"


def test_run_scan_owner_triggers_orchestrator(monkeypatch: pytest.MonkeyPatch, auth_client: TestClient) -> None:
    fake_user_repo = _FakeUserRepo(owned={(_TEST_USER_ID, "acme")})
    monkeypatch.setattr(scans_routes, "UserRepository", lambda: fake_user_repo)

    factory = _RunOrchestratorFactory(
        scan_result=SimpleNamespace(
            run_id="run-1",
            status="completed",
            results_count=5,
            failed_providers=[],
            error_message=None,
        )
    )
    monkeypatch.setattr(scans_routes, "RunOrchestrator", factory)

    response = auth_client.post("/api/v1/workspaces/acme/scan")
    assert response.status_code == 200
    body = response.json()
    assert body["succeeded"] == 1
    assert body["failed"] == 0
    assert body["total_results"] == 5
    assert len(body["providers"]) == 1
    assert body["providers"][0] == {
        "provider": "anthropic",
        "run_id": "run-1",
        "status": "completed",
        "results_count": 5,
        "error_message": None,
    }
    assert factory.init_calls == [{"workspace_slug": "acme", "provider": "anthropic"}]
    assert factory.scan_calls == 1


def test_run_scan_accepts_openai_provider(monkeypatch: pytest.MonkeyPatch, auth_client: TestClient) -> None:
    fake_user_repo = _FakeUserRepo(owned={(_TEST_USER_ID, "acme")})
    monkeypatch.setattr(scans_routes, "UserRepository", lambda: fake_user_repo)

    factory = _RunOrchestratorFactory(
        scan_result=SimpleNamespace(
            run_id="run-2",
            status="completed",
            results_count=3,
            failed_providers=[],
            error_message=None,
        )
    )
    monkeypatch.setattr(scans_routes, "RunOrchestrator", factory)

    response = auth_client.post("/api/v1/workspaces/acme/scan?provider=openai")
    assert response.status_code == 200
    assert factory.init_calls == [{"workspace_slug": "acme", "provider": "openai"}]
    assert response.json()["providers"][0]["provider"] == "openai"


def test_run_scan_fans_out_across_providers(monkeypatch: pytest.MonkeyPatch, auth_client: TestClient) -> None:
    fake_user_repo = _FakeUserRepo(owned={(_TEST_USER_ID, "acme")})
    monkeypatch.setattr(scans_routes, "UserRepository", lambda: fake_user_repo)

    call_log: list[str] = []

    class _Factory:
        def __init__(self, *, workspace_slug: str, provider: str) -> None:
            call_log.append(provider)
            self._provider = provider

        async def scan(self):
            return SimpleNamespace(
                run_id=f"run-{self._provider}",
                status="completed",
                results_count=3,
                failed_providers=[],
                error_message=None,
            )

    monkeypatch.setattr(scans_routes, "RunOrchestrator", _Factory)

    response = auth_client.post("/api/v1/workspaces/acme/scan?provider=anthropic,openai,gemini")
    assert response.status_code == 200
    body = response.json()
    assert [p["provider"] for p in body["providers"]] == ["anthropic", "openai", "gemini"]
    assert body["total_results"] == 9
    assert body["succeeded"] == 3
    assert body["failed"] == 0
    assert call_log == ["anthropic", "openai", "gemini"]


def test_run_scan_counts_failed_providers(monkeypatch: pytest.MonkeyPatch, auth_client: TestClient) -> None:
    fake_user_repo = _FakeUserRepo(owned={(_TEST_USER_ID, "acme")})
    monkeypatch.setattr(scans_routes, "UserRepository", lambda: fake_user_repo)

    class _Factory:
        def __init__(self, *, workspace_slug: str, provider: str) -> None:
            self._provider = provider

        async def scan(self):
            if self._provider == "openai":
                return SimpleNamespace(
                    run_id=None,
                    status="failed",
                    results_count=0,
                    failed_providers=["openai"],
                    error_message="Missing API key: OPENAI_API_KEY",
                )
            return SimpleNamespace(
                run_id=f"run-{self._provider}",
                status="completed",
                results_count=3,
                failed_providers=[],
                error_message=None,
            )

    monkeypatch.setattr(scans_routes, "RunOrchestrator", _Factory)

    response = auth_client.post("/api/v1/workspaces/acme/scan?provider=anthropic,openai")
    assert response.status_code == 200
    body = response.json()
    assert body["succeeded"] == 1
    assert body["failed"] == 1
    failed = next(p for p in body["providers"] if p["provider"] == "openai")
    assert failed["status"] == "failed"
    assert "Missing API key" in (failed["error_message"] or "")
