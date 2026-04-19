# pyright: reportMissingImports=false

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _fake_api_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EXA_API_KEY", "test-exa")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic")


@pytest.fixture
def mock_discovery():
    async def fake(domain: str, industry: str, country_code: str) -> tuple[list[str], str]:
        return (
            [
                "Alpha Systems (alpha.io) — description",
                "Bright Labs (brightlabs.com)",
            ],
            "fake site content",
        )

    with patch(
        "ai_visibility.api.research_routes.discover_competitors_with_site_content",
        new=AsyncMock(side_effect=fake),
    ):
        yield


def test_research_unauth(unauth_client: TestClient) -> None:
    response = unauth_client.post("/api/v1/research/competitors", json={"domain": "acme.com"})
    assert response.status_code in (401, 403)


def test_research_happy_path(auth_client: TestClient, mock_discovery) -> None:
    response = auth_client.post(
        "/api/v1/research/competitors",
        json={"domain": "acme.com", "industry": "SaaS"},
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["competitors"]) == 2
    assert body["competitors"][0]["name"] == "Alpha Systems"
    assert body["competitors"][0]["domain"] == "alpha.io"
    assert body["site_content"] == "fake site content"


def test_research_discovery_failure_returns_degraded(auth_client: TestClient) -> None:
    async def boom(*args: object, **kwargs: object) -> tuple[list[str], str]:
        raise RuntimeError("Exa down")

    with patch(
        "ai_visibility.api.research_routes.discover_competitors_with_site_content",
        new=AsyncMock(side_effect=boom),
    ):
        response = auth_client.post("/api/v1/research/competitors", json={"domain": "acme.com", "industry": "SaaS"})

    assert response.status_code == 200
    body = response.json()
    assert body["competitors"] == []
    assert body["degraded"] is not None
    assert "discovery_failed" in body["degraded"]["reason"]


def test_research_invalid_domain(auth_client: TestClient) -> None:
    response = auth_client.post("/api/v1/research/competitors", json={"domain": "x"})
    assert response.status_code == 422


def test_research_empty_industry_ok(auth_client: TestClient, mock_discovery) -> None:
    response = auth_client.post("/api/v1/research/competitors", json={"domain": "acme.com"})
    assert response.status_code == 200


def test_research_limits_to_five(auth_client: TestClient) -> None:
    async def many(domain: str, industry: str, country_code: str) -> tuple[list[str], str]:
        _ = (domain, industry, country_code)
        return ([f"Name {index} (n{index}.com)" for index in range(10)], "")

    with patch(
        "ai_visibility.api.research_routes.discover_competitors_with_site_content",
        new=AsyncMock(side_effect=many),
    ):
        response = auth_client.post("/api/v1/research/competitors", json={"domain": "acme.com", "industry": "SaaS"})

    assert response.status_code == 200
    assert len(response.json()["competitors"]) == 5


def test_research_missing_keys_returns_degraded(auth_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("EXA_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    response = auth_client.post("/api/v1/research/competitors", json={"domain": "acme.com"})

    assert response.status_code == 200
    body = response.json()
    assert body["competitors"] == []
    assert body["degraded"]["reason"] == "missing_api_keys"
    assert "EXA_API_KEY" in body["degraded"]["message"]
    assert "ANTHROPIC_API_KEY" in body["degraded"]["message"]


def test_research_skips_unparseable_entries(auth_client: TestClient) -> None:
    async def mixed(domain: str, industry: str, country_code: str) -> tuple[list[str], str]:
        _ = (domain, industry, country_code)
        return (["No domain here", "Valid Company (valid.com)"], "site content")

    with patch(
        "ai_visibility.api.research_routes.discover_competitors_with_site_content",
        new=AsyncMock(side_effect=mixed),
    ):
        response = auth_client.post("/api/v1/research/competitors", json={"domain": "acme.com", "industry": "SaaS"})

    assert response.status_code == 200
    body = response.json()
    assert len(body["competitors"]) == 1
    assert body["competitors"][0]["domain"] == "valid.com"
