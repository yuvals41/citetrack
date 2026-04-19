from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from ai_visibility.api import create_app
from ai_visibility.api.auth import get_current_user_id
from ai_visibility.services import content_analysis as service


def _transport(handler: Callable[[httpx.Request], httpx.Response]) -> Callable[..., httpx.AsyncClient]:
    def factory(*args: object, **kwargs: object) -> httpx.AsyncClient:
        timeout = kwargs.get("timeout", 20.0)
        headers = kwargs.get("headers")
        return httpx.AsyncClient(transport=httpx.MockTransport(handler), timeout=timeout, headers=headers)

    return factory


@pytest.fixture
def content_analysis_auth_client(patch_get_prisma) -> TestClient:
    _ = patch_get_prisma
    app = create_app()
    app.dependency_overrides[get_current_user_id] = lambda: "user_test"
    client = TestClient(app)
    try:
        yield client
    finally:
        app.dependency_overrides.clear()


def test_extractability_valid_url_returns_score(
    content_analysis_auth_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        html = """
        <html><body>
          <h1>Citetrack</h1>
          <p>Track AI visibility with clear summaries and buyer-ready evidence.</p>
          <h2>Features</h2><ul><li>Analytics</li></ul>
          <h3>Details</h3>
          <script type="application/ld+json">{"@type":"Organization"}</script>
        </body></html>
        """
        return httpx.Response(200, text=html)

    monkeypatch.setattr(service, "_make_client", _transport(handler))

    response = content_analysis_auth_client.post(
        "/api/v1/analyzers/extractability",
        json={"url": "https://example.com/page"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["overall_score"] > 0
    assert payload["summary_block"]["score"] >= 60


def test_extractability_invalid_url_returns_422(content_analysis_auth_client: TestClient) -> None:
    response = content_analysis_auth_client.post(
        "/api/v1/analyzers/extractability",
        json={"url": "not-a-url"},
    )
    assert response.status_code == 422


def test_crawler_sim_returns_six_bots(
    content_analysis_auth_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt" and request.method == "HEAD":
            return httpx.Response(200, text="")
        if request.url.path == "/robots.txt" and request.method == "GET":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        return httpx.Response(200, text="ok")

    monkeypatch.setattr(service, "_make_client", _transport(handler))

    response = content_analysis_auth_client.post(
        "/api/v1/analyzers/crawler-sim",
        json={"url": "https://example.com/page"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["results"]) == 6
    assert {item["bot"] for item in payload["results"]} == {
        "GPTBot",
        "ClaudeBot",
        "PerplexityBot",
        "Google-Extended",
        "Googlebot",
        "Bingbot",
    }


def test_query_fanout_without_keys_returns_degraded(
    content_analysis_auth_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    response = content_analysis_auth_client.post(
        "/api/v1/analyzers/query-fanout",
        json={"prompt": "best ai visibility tools", "brand_domain": "citetrack.ai"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["degraded"]["reason"] == "missing_api_keys"


def test_query_fanout_with_mocked_keys_returns_success_shape(
    content_analysis_auth_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")

    def handler(request: httpx.Request) -> httpx.Response:
        if str(request.url) == service.ANTHROPIC_MESSAGES_URL:
            body = {"content": [{"type": "text", "text": '{"queries": ["citetrack reviews", "citetrack pricing"]}'}]}
            return httpx.Response(200, json=body)
        if str(request.url) == service.TAVILY_SEARCH_URL:
            payload = json.loads(request.content.decode())
            query = payload["query"]
            if query == "citetrack reviews":
                return httpx.Response(200, json={"results": [{"url": "https://citetrack.ai/reviews"}]})
            return httpx.Response(200, json={"results": [{"url": "https://other.com/article"}]})
        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    monkeypatch.setattr(service, "_make_client", _transport(handler))

    response = content_analysis_auth_client.post(
        "/api/v1/analyzers/query-fanout",
        json={"prompt": "best ai visibility tools", "brand_domain": "citetrack.ai"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["fanout_prompt"] == "best ai visibility tools"
    assert len(payload["results"]) == 2
    assert payload["results"][0]["ranked"] is True
    assert payload["coverage"] == 0.5


def test_entity_analysis_without_keys_still_checks_wikipedia(
    content_analysis_auth_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATAFORSEO_AUTH_HEADER", raising=False)

    def handler(request: httpx.Request) -> httpx.Response:
        if str(request.url) == "https://en.wikipedia.org/wiki/Citetrack":
            return httpx.Response(200, text="wiki")
        if request.url.host == "www.wikidata.org":
            return httpx.Response(200, json={"search": [{"id": "Q123"}]})
        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    monkeypatch.setattr(service, "_make_client", _transport(handler))

    response = content_analysis_auth_client.post("/api/v1/analyzers/entity", json={"brand_name": "Citetrack"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["knowledge_graph"]["present"] is False
    assert payload["wikipedia"]["present"] is True
    assert payload["wikidata"]["present"] is True


def test_shopping_analysis_without_any_keys_returns_degraded(
    content_analysis_auth_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    response = content_analysis_auth_client.post("/api/v1/analyzers/shopping", json={"brand_name": "Citetrack"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["visibility_score"] == 0
    assert payload["degraded"]["reason"] == "missing_api_keys"


def test_extractability_requires_auth(unauth_client: TestClient) -> None:
    response = unauth_client.post("/api/v1/analyzers/extractability", json={"url": "https://example.com"})
    assert response.status_code in (401, 403)
