"""Tests for authenticated AI response routes."""

# pyright: reportMissingImports=false, reportAny=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownParameterType=false, reportMissingParameterType=false, reportUnknownVariableType=false, reportUntypedFunctionDecorator=false, reportUnusedParameter=false

from __future__ import annotations

from datetime import UTC, datetime
from typing import cast

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def patch_mentions_dependencies(monkeypatch: pytest.MonkeyPatch, mock_prisma):
    from ai_visibility.api import mentions_routes
    from ai_visibility.storage.repositories.workspace_repo import WorkspaceRepository

    async def _fake_get_prisma():
        return mock_prisma

    async def _fake_get_by_slug(self, slug: str):  # noqa: ANN001
        if slug == "default":
            return {
                "id": "ws-default",
                "slug": "default",
                "brand_name": "Default Brand",
                "city": "",
                "region": "",
                "country": "",
                "created_at": datetime.now(UTC).isoformat(),
                "scan_schedule": "daily",
            }
        return None

    class _AlwaysOwnsUserRepo:
        def user_owns_workspace(self, user_id: str, slug: str) -> bool:  # noqa: ARG002
            return True

    monkeypatch.setattr(mentions_routes, "get_prisma", _fake_get_prisma)
    monkeypatch.setattr(mentions_routes, "UserRepository", lambda: _AlwaysOwnsUserRepo())
    monkeypatch.setattr(WorkspaceRepository, "get_by_slug", _fake_get_by_slug)
    return mock_prisma


@pytest.fixture
def mentions_auth_client(patch_mentions_dependencies, auth_client: TestClient) -> TestClient:
    _ = patch_mentions_dependencies
    return auth_client


@pytest.fixture
def mentions_unauth_client(patch_mentions_dependencies, unauth_client: TestClient) -> TestClient:
    _ = patch_mentions_dependencies
    return unauth_client


def _prompt_row(
    *,
    execution_id: str,
    run_id: str,
    provider: str = "openai",
    model: str = "gpt-4o-mini",
    prompt_text: str = "What do you know about Citetrack?",
    response_text: str = "Citetrack helps teams monitor AI visibility.",
    created_at: datetime | None = None,
) -> dict[str, object]:
    return {
        "id": execution_id,
        "run_id": run_id,
        "provider": provider,
        "model": model,
        "prompt_text": prompt_text,
        "response_text": response_text,
        "created_at": created_at or datetime(2026, 1, 1, tzinfo=UTC),
    }


def _citation_row(execution_id: str, url: str) -> dict[str, object]:
    return {"prompt_execution_id": execution_id, "url": url}


def _observation_row(
    execution_id: str,
    *,
    brand_mentioned: bool,
    brand_position: int | None,
) -> dict[str, object]:
    return {
        "prompt_execution_id": execution_id,
        "brand_mentioned": brand_mentioned,
        "brand_position": brand_position,
    }


def _set_query_raw(
    mock_prisma, *, total: int, prompt_rows: list[dict[str, object]], citation_rows=None, observation_rows=None
):
    citation_rows = citation_rows or []
    observation_rows = observation_rows or []

    async def _query_raw(query: str, *params: object):
        normalized = " ".join(query.split())
        if "SELECT COUNT(*) AS total" in normalized:
            return [{"total": total}]
        if "FROM ai_vis_prompt_executions pe" in normalized and "LIMIT" in normalized:
            if "AND se.id = $2" in normalized:
                filtered_run_id = cast(str, params[1])
                return [row for row in prompt_rows if row["run_id"] == filtered_run_id]
            return prompt_rows
        if "FROM ai_vis_prompt_execution_citations" in normalized:
            ids = set(cast(list[str], params[0]))
            return [row for row in citation_rows if cast(str, row["prompt_execution_id"]) in ids]
        if "FROM ai_vis_observations" in normalized:
            ids = set(cast(list[str], params[0]))
            return [row for row in observation_rows if cast(str, row["prompt_execution_id"]) in ids]
        return []

    mock_prisma.query_raw.side_effect = _query_raw


def test_responses_unauth_returns_401(mentions_unauth_client: TestClient) -> None:
    response = mentions_unauth_client.get("/api/v1/workspaces/default/responses")

    assert response.status_code in {401, 403}


def test_responses_empty_workspace_returns_empty_list(
    mentions_auth_client: TestClient,
    patch_mentions_dependencies,
) -> None:
    mock_prisma = patch_mentions_dependencies
    _set_query_raw(mock_prisma, total=0, prompt_rows=[])

    response = mentions_auth_client.get("/api/v1/workspaces/default/responses")

    assert response.status_code == 200
    assert response.json() == {
        "workspace": "default",
        "total": 0,
        "items": [],
        "degraded": None,
    }


def test_responses_seeded_data_returns_expected_shape(
    mentions_auth_client: TestClient,
    patch_mentions_dependencies,
) -> None:
    mock_prisma = patch_mentions_dependencies
    _set_query_raw(
        mock_prisma,
        total=2,
        prompt_rows=[
            _prompt_row(execution_id="pe-1", run_id="run-1"),
            _prompt_row(
                execution_id="pe-2",
                run_id="run-2",
                provider="anthropic",
                model="claude-sonnet-4",
                response_text="Citetrack was not mentioned in this response.",
            ),
        ],
        citation_rows=[_citation_row("pe-1", "https://docs.citetrack.ai/guide")],
        observation_rows=[
            _observation_row("pe-1", brand_mentioned=True, brand_position=2),
            _observation_row("pe-2", brand_mentioned=False, brand_position=None),
        ],
    )

    response = mentions_auth_client.get("/api/v1/workspaces/default/responses")

    assert response.status_code == 200
    payload = response.json()
    assert payload["workspace"] == "default"
    assert payload["total"] == 2
    assert len(payload["items"]) == 2
    assert payload["items"][0]["mention_type"] == "cited"
    assert payload["items"][0]["citations"] == [
        {"url": "https://docs.citetrack.ai/guide", "domain": "docs.citetrack.ai"}
    ]
    assert payload["items"][0]["position"] == 2
    assert payload["items"][1]["mention_type"] == "not_mentioned"
    assert payload["items"][1]["sentiment"] is None


def test_responses_run_id_filter_narrows_results(
    mentions_auth_client: TestClient,
    patch_mentions_dependencies,
) -> None:
    mock_prisma = patch_mentions_dependencies
    rows = [
        _prompt_row(execution_id="pe-1", run_id="run-1"),
        _prompt_row(execution_id="pe-2", run_id="run-2"),
    ]
    _set_query_raw(
        mock_prisma,
        total=1,
        prompt_rows=rows,
        observation_rows=[_observation_row("pe-2", brand_mentioned=True, brand_position=1)],
    )

    response = mentions_auth_client.get("/api/v1/workspaces/default/responses?run_id=run-2")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert [item["run_id"] for item in payload["items"]] == ["run-2"]


def test_responses_db_error_returns_degraded(
    mentions_auth_client: TestClient,
    patch_mentions_dependencies,
) -> None:
    mock_prisma = patch_mentions_dependencies

    async def _boom(*args: object, **kwargs: object):
        raise RuntimeError("database offline")

    mock_prisma.query_raw.side_effect = _boom

    response = mentions_auth_client.get("/api/v1/workspaces/default/responses")

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"] == []
    assert payload["total"] == 0
    assert payload["degraded"] == {
        "reason": "provider_failure",
        "message": "AI responses are temporarily unavailable: database offline",
    }


def test_responses_excerpt_truncates_to_200_chars(
    mentions_auth_client: TestClient,
    patch_mentions_dependencies,
) -> None:
    mock_prisma = patch_mentions_dependencies
    long_response = "x" * 250
    _set_query_raw(
        mock_prisma,
        total=1,
        prompt_rows=[_prompt_row(execution_id="pe-1", run_id="run-1", response_text=long_response)],
        observation_rows=[_observation_row("pe-1", brand_mentioned=True, brand_position=4)],
    )

    response = mentions_auth_client.get("/api/v1/workspaces/default/responses")

    assert response.status_code == 200
    excerpt = response.json()["items"][0]["excerpt"]
    assert excerpt == "x" * 200
    assert len(excerpt) == 200
