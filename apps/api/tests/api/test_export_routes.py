from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from ai_visibility.api import export_routes

_TEST_USER_ID = "user_test_abc123"


class _FakeUserRepo:
    def __init__(self, owned: set[tuple[str, str]]) -> None:
        self._owned = owned

    def user_owns_workspace(self, user_id: str, slug: str) -> bool:
        return (user_id, slug) in self._owned


class _FakePrisma:
    def __init__(self, *, jobs=None, executions=None, prompt_execs=None, observations=None) -> None:
        self.aivisscanjob = SimpleNamespace(find_many=self._async_fixed(jobs or []))
        self.aivisscanexecution = SimpleNamespace(find_many=self._async_fixed(executions or []))
        self.aivispromptexecution = SimpleNamespace(find_many=self._async_fixed(prompt_execs or []))
        self.aivisobservation = SimpleNamespace(find_many=self._async_fixed(observations or []))

    @staticmethod
    def _async_fixed(value):
        async def _fn(**_kwargs):
            return value

        return _fn


def test_export_csv_requires_auth(unauth_client: TestClient) -> None:
    response = unauth_client.get("/api/v1/workspaces/acme/export.csv")
    assert response.status_code in {401, 403}


def test_export_csv_forbidden_when_not_owner(monkeypatch: pytest.MonkeyPatch, auth_client: TestClient) -> None:
    monkeypatch.setattr(export_routes, "UserRepository", lambda: _FakeUserRepo(set()))
    response = auth_client.get("/api/v1/workspaces/acme/export.csv")
    assert response.status_code == 403


def test_export_csv_emits_rows_for_owner(monkeypatch: pytest.MonkeyPatch, auth_client: TestClient) -> None:
    monkeypatch.setattr(export_routes, "UserRepository", lambda: _FakeUserRepo({(_TEST_USER_ID, "acme")}))

    prisma = _FakePrisma(
        jobs=[SimpleNamespace(id="job-1", createdAt=None)],
        executions=[SimpleNamespace(id="exec-1", scanJobId="job-1", provider="anthropic")],
        prompt_execs=[
            SimpleNamespace(
                id="pe-1",
                scanExecutionId="exec-1",
                promptText="What is the best Acme?",
                rawResponse="Acme is great.",
                executedAt=None,
            ),
        ],
        observations=[
            SimpleNamespace(promptExecutionId="pe-1", brandMentioned=True, brandPosition=1),
        ],
    )

    async def _fake_get_prisma():
        return prisma

    monkeypatch.setattr(export_routes, "get_prisma", _fake_get_prisma)

    response = auth_client.get("/api/v1/workspaces/acme/export.csv")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]
    body = response.text.splitlines()
    assert body[0] == "executed_at,provider,prompt,response,brand_mentioned,brand_position"
    assert "anthropic" in body[1]
    assert "Acme is great." in body[1]


def test_export_csv_empty_workspace_returns_header_only(
    monkeypatch: pytest.MonkeyPatch, auth_client: TestClient
) -> None:
    monkeypatch.setattr(export_routes, "UserRepository", lambda: _FakeUserRepo({(_TEST_USER_ID, "acme")}))
    prisma = _FakePrisma()

    async def _fake_get_prisma():
        return prisma

    monkeypatch.setattr(export_routes, "get_prisma", _fake_get_prisma)

    response = auth_client.get("/api/v1/workspaces/acme/export.csv")
    assert response.status_code == 200
    assert response.text.strip() == "executed_at,provider,prompt,response,brand_mentioned,brand_position"
