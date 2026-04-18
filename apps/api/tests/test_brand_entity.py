# pyright: reportExplicitAny=false, reportAny=false, reportUnannotatedClassAttribute=false
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import httpx
import pytest

from ai_visibility.analysis.brand_entity import analyze_brand_entity


@dataclass
class FakeResponse:
    status_code: int = 200
    payload: dict[str, Any] | None = None
    exc: Exception | None = None

    def json(self) -> dict[str, Any]:
        return self.payload or {}

    def raise_for_status(self) -> None:
        if self.exc is not None:
            raise self.exc
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "error",
                request=httpx.Request("GET", "https://example.com"),
                response=httpx.Response(self.status_code),
            )


class FakeAsyncClient:
    def __init__(self, resolver: Callable[[str, dict[str, Any] | None], FakeResponse]) -> None:
        self._resolver = resolver

    async def __aenter__(self) -> FakeAsyncClient:
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        return None

    async def get(self, url: str, params: dict[str, Any] | None = None) -> FakeResponse:
        return self._resolver(url, params)


def _install_http_mock(
    monkeypatch: pytest.MonkeyPatch,
    resolver: Callable[[str, dict[str, Any] | None], FakeResponse],
) -> None:
    def _factory(*_args: Any, **_kwargs: Any) -> FakeAsyncClient:
        return FakeAsyncClient(resolver)

    monkeypatch.setattr(httpx, "AsyncClient", _factory)


def _kg_payload(result_score: float = 900.0, url: str = "https://acme.com") -> dict[str, Any]:
    return {
        "itemListElement": [
            {
                "resultScore": result_score,
                "result": {
                    "@id": "kg:/m/0123",
                    "name": "Acme",
                    "@type": ["Organization"],
                    "description": "Acme Description",
                    "url": url,
                    "detailedDescription": {"url": "https://en.wikipedia.org/wiki/Acme"},
                },
            }
        ]
    }


def _wikidata_search_payload(entity_id: str = "Q42") -> dict[str, Any]:
    return {
        "search": [
            {
                "id": entity_id,
                "description": "Wikidata description",
            }
        ]
    }


def _wikidata_entity_payload(entity_id: str = "Q42", sitelinks_count: int = 25) -> dict[str, Any]:
    sitelinks = {f"wiki{i}": {"site": f"wiki{i}"} for i in range(sitelinks_count)}
    if "enwiki" not in sitelinks:
        sitelinks["enwiki"] = {"site": "enwiki"}
    return {
        "entities": {
            entity_id: {
                "sitelinks": sitelinks,
            }
        }
    }


def _wikipedia_payload() -> dict[str, Any]:
    return {
        "title": "Acme",
        "description": "Wikipedia description",
        "extract": "Acme is a fictional company.",
        "wikibase_item": "Q42",
    }


def _default_resolver(url: str, params: dict[str, Any] | None = None) -> FakeResponse:
    if "kgsearch.googleapis.com" in url:
        return FakeResponse(payload=_kg_payload())
    if "wikidata.org/w/api.php" in url:
        return FakeResponse(payload=_wikidata_search_payload())
    if "Special:EntityData" in url:
        return FakeResponse(payload=_wikidata_entity_payload())
    if "wikipedia.org/api/rest_v1/page/summary" in url:
        return FakeResponse(payload=_wikipedia_payload())
    raise AssertionError(f"Unexpected URL: {url} params={params}")


async def test_full_entity_found(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    _install_http_mock(monkeypatch, _default_resolver)

    result = await analyze_brand_entity("Acme", "acme.com")

    assert result["brand"] == "Acme"
    assert result["entity_clarity_score"] == 1.0
    assert result["knowledge_graph"]["present"] is True
    assert result["knowledge_graph"]["correct_entity"] is True
    assert result["wikidata"]["present"] is True
    assert result["wikipedia"]["present"] is True
    assert result["recommendations"] == []


async def test_no_google_api_key_skips_kg(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    def resolver(url: str, params: dict[str, Any] | None = None) -> FakeResponse:
        if "kgsearch.googleapis.com" in url:
            raise AssertionError("Knowledge Graph should be skipped when API key is missing")
        return _default_resolver(url, params)

    _install_http_mock(monkeypatch, resolver)
    result = await analyze_brand_entity("Acme", "acme.com")

    assert result["knowledge_graph"]["present"] is False
    assert (
        "Create/claim your Google Business Profile and ensure consistent brand info across the web"
        in result["recommendations"]
    )


async def test_no_knowledge_graph_result(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    def resolver(url: str, params: dict[str, Any] | None = None) -> FakeResponse:
        if "kgsearch.googleapis.com" in url:
            return FakeResponse(payload={"itemListElement": []})
        return _default_resolver(url, params)

    _install_http_mock(monkeypatch, resolver)
    result = await analyze_brand_entity("Acme", "acme.com")

    assert result["knowledge_graph"]["present"] is False
    assert any("Google Business Profile" in rec for rec in result["recommendations"])


async def test_no_wikipedia_page(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    def resolver(url: str, params: dict[str, Any] | None = None) -> FakeResponse:
        if "wikipedia.org/api/rest_v1/page/summary" in url:
            return FakeResponse(status_code=404)
        return _default_resolver(url, params)

    _install_http_mock(monkeypatch, resolver)
    result = await analyze_brand_entity("Acme", "acme.com")

    assert result["wikipedia"]["present"] is False
    assert any("lacks a Wikipedia page" in rec for rec in result["recommendations"])


async def test_no_wikidata_presence(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    def resolver(url: str, params: dict[str, Any] | None = None) -> FakeResponse:
        if "wikidata.org/w/api.php" in url:
            return FakeResponse(payload={"search": []})
        return _default_resolver(url, params)

    _install_http_mock(monkeypatch, resolver)
    result = await analyze_brand_entity("Acme", "acme.com")

    assert result["wikidata"]["present"] is False
    assert any("Create a Wikidata entry" in rec for rec in result["recommendations"])


async def test_all_sources_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    def resolver(url: str, params: dict[str, Any] | None = None) -> FakeResponse:
        if "kgsearch.googleapis.com" in url:
            return FakeResponse(payload={"itemListElement": []})
        if "wikidata.org/w/api.php" in url:
            return FakeResponse(payload={"search": []})
        if "wikipedia.org/api/rest_v1/page/summary" in url:
            return FakeResponse(status_code=404)
        if "Special:EntityData" in url:
            raise AssertionError("EntityData should not be requested when search is empty")
        raise AssertionError(f"Unexpected URL: {url} params={params}")

    _install_http_mock(monkeypatch, resolver)
    result = await analyze_brand_entity("Acme", "acme.com")

    assert result["entity_clarity_score"] == 0.0
    assert len(result["recommendations"]) >= 3


async def test_disambiguation_picks_correct_entity(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    def resolver(url: str, params: dict[str, Any] | None = None) -> FakeResponse:
        if "kgsearch.googleapis.com" in url:
            payload = {
                "itemListElement": [
                    {
                        "resultScore": 900,
                        "result": {
                            "@id": "kg:/wrong",
                            "@type": ["Organization"],
                            "description": "Wrong",
                            "url": "https://other.example",
                        },
                    },
                    {
                        "resultScore": 600,
                        "result": {
                            "@id": "kg:/correct",
                            "@type": ["Organization"],
                            "description": "Correct",
                            "url": "https://acme.com/about",
                        },
                    },
                ]
            }
            return FakeResponse(payload=payload)
        return _default_resolver(url, params)

    _install_http_mock(monkeypatch, resolver)
    result = await analyze_brand_entity("Acme", "acme.com")

    assert result["knowledge_graph"]["entity_id"] == "kg:/correct"
    assert result["knowledge_graph"]["correct_entity"] is True


async def test_disambiguation_wrong_entity_recommendation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    def resolver(url: str, params: dict[str, Any] | None = None) -> FakeResponse:
        if "kgsearch.googleapis.com" in url:
            return FakeResponse(payload=_kg_payload(url="https://different-domain.com"))
        return _default_resolver(url, params)

    _install_http_mock(monkeypatch, resolver)
    result = await analyze_brand_entity("Acme", "acme.com")

    assert result["knowledge_graph"]["correct_entity"] is False
    assert any("ambiguous" in rec for rec in result["recommendations"])


async def test_low_kg_score_recommendation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    def resolver(url: str, params: dict[str, Any] | None = None) -> FakeResponse:
        if "kgsearch.googleapis.com" in url:
            return FakeResponse(payload=_kg_payload(result_score=499.0))
        return _default_resolver(url, params)

    _install_http_mock(monkeypatch, resolver)
    result = await analyze_brand_entity("Acme", "acme.com")

    assert result["knowledge_graph"]["present"] is True
    assert result["knowledge_graph"]["result_score"] == 499.0
    assert any("Strengthen your brand's online presence" in rec for rec in result["recommendations"])


async def test_kg_failure_returns_partial(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    def resolver(url: str, params: dict[str, Any] | None = None) -> FakeResponse:
        if "kgsearch.googleapis.com" in url:
            raise RuntimeError("kg down")
        return _default_resolver(url, params)

    _install_http_mock(monkeypatch, resolver)
    result = await analyze_brand_entity("Acme", "acme.com")

    assert result["knowledge_graph"]["present"] is False
    assert result["wikidata"]["present"] is True
    assert result["wikipedia"]["present"] is True


async def test_wikidata_failure_returns_partial(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    def resolver(url: str, params: dict[str, Any] | None = None) -> FakeResponse:
        if "wikidata.org/w/api.php" in url:
            raise RuntimeError("wikidata down")
        return _default_resolver(url, params)

    _install_http_mock(monkeypatch, resolver)
    result = await analyze_brand_entity("Acme", "acme.com")

    assert result["wikidata"]["present"] is False
    assert result["knowledge_graph"]["present"] is True
    assert result["wikipedia"]["present"] is True


async def test_wikipedia_failure_returns_partial(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    def resolver(url: str, params: dict[str, Any] | None = None) -> FakeResponse:
        if "wikipedia.org/api/rest_v1/page/summary" in url:
            raise RuntimeError("wikipedia down")
        return _default_resolver(url, params)

    _install_http_mock(monkeypatch, resolver)
    result = await analyze_brand_entity("Acme", "acme.com")

    assert result["wikipedia"]["present"] is False
    assert result["knowledge_graph"]["present"] is True
    assert result["wikidata"]["present"] is True


async def test_empty_brand_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    _install_http_mock(monkeypatch, _default_resolver)

    result = await analyze_brand_entity("   ", "acme.com")

    assert result["entity_clarity_score"] == 0.0
    assert result["knowledge_graph"]["present"] is False
    assert result["wikidata"]["present"] is False
    assert result["wikipedia"]["present"] is False


async def test_sitelinks_threshold_exactly_ten(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    def resolver(url: str, params: dict[str, Any] | None = None) -> FakeResponse:
        if "Special:EntityData" in url:
            return FakeResponse(payload=_wikidata_entity_payload(sitelinks_count=10))
        return _default_resolver(url, params)

    _install_http_mock(monkeypatch, resolver)
    result = await analyze_brand_entity("Acme", "acme.com")

    assert result["wikidata"]["sitelinks_count"] == 11
    assert result["entity_clarity_score"] == 0.95


async def test_sitelinks_threshold_over_ten(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    def resolver(url: str, params: dict[str, Any] | None = None) -> FakeResponse:
        if "Special:EntityData" in url:
            return FakeResponse(payload=_wikidata_entity_payload(sitelinks_count=11))
        return _default_resolver(url, params)

    _install_http_mock(monkeypatch, resolver)
    result = await analyze_brand_entity("Acme", "acme.com")

    assert result["entity_clarity_score"] == 0.95


async def test_sitelinks_threshold_over_twenty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    def resolver(url: str, params: dict[str, Any] | None = None) -> FakeResponse:
        if "Special:EntityData" in url:
            return FakeResponse(payload=_wikidata_entity_payload(sitelinks_count=21))
        return _default_resolver(url, params)

    _install_http_mock(monkeypatch, resolver)
    result = await analyze_brand_entity("Acme", "acme.com")

    assert result["entity_clarity_score"] == 1.0


async def test_domain_normalization_for_matching(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    def resolver(url: str, params: dict[str, Any] | None = None) -> FakeResponse:
        if "kgsearch.googleapis.com" in url:
            return FakeResponse(payload=_kg_payload(url="https://www.acme.com/company"))
        return _default_resolver(url, params)

    _install_http_mock(monkeypatch, resolver)
    result = await analyze_brand_entity("Acme", "https://www.acme.com")

    assert result["knowledge_graph"]["correct_entity"] is True
