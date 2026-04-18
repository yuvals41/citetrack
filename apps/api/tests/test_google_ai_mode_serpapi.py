from __future__ import annotations

# pyright: reportAny=false, reportExplicitAny=false, reportUnannotatedClassAttribute=false, reportPrivateLocalImportUsage=false, reportUnusedCallResult=false, reportArgumentType=false

from collections.abc import Sequence
from typing import Any

import pytest

from ai_visibility.providers.adapters.google_ai_mode_serpapi import GoogleAIModeSerpAPIAdapter
from ai_visibility.providers.gateway import LocationContext, ProviderError


class DummyResponse:
    def __init__(self, *, status_code: int, payload: Any, json_error: bool = False) -> None:
        self.status_code = status_code
        self._payload = payload
        self._json_error = json_error

    def json(self) -> Any:
        if self._json_error:
            raise ValueError("invalid json")
        return self._payload


def install_fake_async_client(
    monkeypatch: pytest.MonkeyPatch,
    responses: Sequence[DummyResponse],
    *,
    raises: Exception | None = None,
) -> list[dict[str, str]]:
    import ai_visibility.providers.adapters.google_ai_mode_serpapi as module

    queued = list(responses)
    calls: list[dict[str, str]] = []

    class FakeAsyncClient:
        def __init__(self, *, timeout: float) -> None:
            _ = timeout

        async def __aenter__(self) -> FakeAsyncClient:
            return self

        async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
            _ = exc_type
            _ = exc
            _ = tb

        async def get(self, url: str, params: dict[str, str]) -> DummyResponse:
            assert url == "https://serpapi.com/search"
            calls.append(dict(params))
            if raises is not None:
                raise raises
            if not queued:
                raise AssertionError("No queued fake responses left")
            return queued.pop(0)

    monkeypatch.setattr(module.httpx, "AsyncClient", FakeAsyncClient)
    return calls


def test_extract_brand_mentions_in_answer_text() -> None:
    adapter = GoogleAIModeSerpAPIAdapter()
    result = adapter.extract_brand_mentions(
        response_text="Maison Remodeling Group is a top recommendation.",
        references=[],
        brand="Maison Remodeling",
    )
    assert result["mentioned_in_answer"] is True
    assert result["citation_count"] == 0
    assert 1 <= int(result["position_estimate"]) <= 5


def test_extract_brand_mentions_in_references_only() -> None:
    adapter = GoogleAIModeSerpAPIAdapter()
    result = adapter.extract_brand_mentions(
        response_text="No direct mention in text.",
        references=[
            {
                "title": "Top contractors",
                "link": "https://maisonremodeling.com/services",
                "snippet": "Trusted remodeler",
                "source": "example.com",
            }
        ],
        brand="maisonremodeling",
    )
    assert result["mentioned_in_answer"] is False
    assert result["citation_count"] == 1
    assert result["position_estimate"] == 4


def test_extract_brand_mentions_not_found() -> None:
    adapter = GoogleAIModeSerpAPIAdapter()
    result = adapter.extract_brand_mentions(
        response_text="This answer discusses other providers.",
        references=[{"title": "Other provider", "link": "https://other.com", "snippet": "", "source": "other.com"}],
        brand="Maison",
    )
    assert result == {"mentioned_in_answer": False, "citation_count": 0, "position_estimate": 5}


@pytest.mark.asyncio
async def test_single_turn_success_with_citations(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERPAPI_API_KEY", "test-key")
    calls = install_fake_async_client(
        monkeypatch,
        [
            DummyResponse(
                status_code=200,
                payload={
                    "reconstructed_markdown": "Maison Remodeling is a trusted brand.",
                    "references": [
                        {
                            "title": "Maison Remodeling",
                            "link": "https://maisonremodeling.com",
                            "snippet": "Official site",
                            "source": "Google",
                        }
                    ],
                    "subsequent_request_token": "tok-1",
                },
            )
        ],
    )

    adapter = GoogleAIModeSerpAPIAdapter()
    result = await adapter.execute("best remodelers", "Maison")

    assert result.provider == "google_ai_mode_serpapi"
    assert "Maison Remodeling" in result.raw_response
    assert len(result.citations) == 1
    assert calls[0]["engine"] == "google_ai_mode"
    assert calls[0]["hl"] == "en"
    assert calls[0]["no_cache"] == "true"
    assert getattr(adapter, "_last_subsequent_request_token") == "tok-1"


@pytest.mark.asyncio
async def test_multi_turn_conversation_passes_tokens(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERPAPI_API_KEY", "test-key")
    calls = install_fake_async_client(
        monkeypatch,
        [
            DummyResponse(
                status_code=200,
                payload={
                    "reconstructed_markdown": "Turn 1 about Maison",
                    "references": [{"title": "Maison", "link": "https://maison.com", "snippet": "", "source": "x"}],
                    "subsequent_request_token": "t1",
                },
            ),
            DummyResponse(
                status_code=200,
                payload={
                    "reconstructed_markdown": "Turn 2 details",
                    "references": [],
                    "subsequent_request_token": "t2",
                },
            ),
            DummyResponse(
                status_code=200,
                payload={
                    "reconstructed_markdown": "Turn 3 details",
                    "references": [],
                    "subsequent_request_token": "t3",
                },
            ),
        ],
    )

    adapter = GoogleAIModeSerpAPIAdapter()
    turns = await adapter.execute_conversation(["q1", "q2", "q3"], "Maison")

    assert len(turns) == 3
    assert turns[0]["turn"] == 1
    assert turns[1]["turn"] == 2
    assert turns[2]["turn"] == 3
    assert calls[0].get("subsequent_request_token") is None
    assert calls[1].get("subsequent_request_token") == "t1"
    assert calls[2].get("subsequent_request_token") == "t2"
    assert getattr(adapter, "_last_subsequent_request_token") == "t3"


@pytest.mark.asyncio
async def test_missing_api_key_raises_provider_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)
    adapter = GoogleAIModeSerpAPIAdapter()
    with pytest.raises(ProviderError, match="SERPAPI_API_KEY"):
        await adapter.execute("q", "brand")


@pytest.mark.asyncio
async def test_api_error_field_raises_provider_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERPAPI_API_KEY", "test-key")
    install_fake_async_client(monkeypatch, [DummyResponse(status_code=200, payload={"error": "bad request"})])

    adapter = GoogleAIModeSerpAPIAdapter()
    with pytest.raises(ProviderError, match="bad request"):
        await adapter.execute("q", "brand")


@pytest.mark.asyncio
async def test_http_error_payload_message_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERPAPI_API_KEY", "test-key")
    install_fake_async_client(
        monkeypatch,
        [DummyResponse(status_code=500, payload={"message": "upstream failed"})],
    )

    adapter = GoogleAIModeSerpAPIAdapter()
    with pytest.raises(ProviderError, match="upstream failed"):
        await adapter.execute("q", "brand")


@pytest.mark.asyncio
async def test_rate_limit_raises_provider_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERPAPI_API_KEY", "test-key")
    install_fake_async_client(monkeypatch, [DummyResponse(status_code=429, payload={"error": "rate limited"})])

    adapter = GoogleAIModeSerpAPIAdapter()
    with pytest.raises(ProviderError, match="rate limit"):
        await adapter.execute("q", "brand")


@pytest.mark.asyncio
async def test_shopping_results_are_included_in_execute_citations(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERPAPI_API_KEY", "test-key")
    install_fake_async_client(
        monkeypatch,
        [
            DummyResponse(
                status_code=200,
                payload={
                    "reconstructed_markdown": "Answer",
                    "references": [],
                    "shopping_results": [
                        {
                            "title": "Maison Product",
                            "link": "https://shop.example.com/item",
                            "snippet": "Shopping card",
                            "source": "Shop",
                        }
                    ],
                },
            )
        ],
    )

    adapter = GoogleAIModeSerpAPIAdapter()
    result = await adapter.execute("q", "Maison")

    assert any(citation.get("type") == "shopping_result" for citation in result.citations)


@pytest.mark.asyncio
async def test_local_results_are_included_in_execute_citations(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERPAPI_API_KEY", "test-key")
    install_fake_async_client(
        monkeypatch,
        [
            DummyResponse(
                status_code=200,
                payload={
                    "reconstructed_markdown": "Answer",
                    "references": [],
                    "local_results": [
                        {
                            "title": "Maison DC",
                            "link": "https://maps.example.com/maison",
                            "snippet": "Local listing",
                            "source": "Maps",
                        }
                    ],
                },
            )
        ],
    )

    adapter = GoogleAIModeSerpAPIAdapter()
    result = await adapter.execute("q", "Maison")

    assert any(citation.get("type") == "local_result" for citation in result.citations)


@pytest.mark.asyncio
async def test_empty_response_raises_provider_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERPAPI_API_KEY", "test-key")
    install_fake_async_client(
        monkeypatch,
        [DummyResponse(status_code=200, payload={"reconstructed_markdown": "", "references": []})],
    )

    adapter = GoogleAIModeSerpAPIAdapter()
    with pytest.raises(ProviderError, match="empty response"):
        await adapter.execute("q", "brand")


@pytest.mark.asyncio
async def test_location_context_sets_gl_parameter(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERPAPI_API_KEY", "test-key")
    calls = install_fake_async_client(
        monkeypatch,
        [DummyResponse(status_code=200, payload={"reconstructed_markdown": "ok", "references": []})],
    )

    adapter = GoogleAIModeSerpAPIAdapter()
    location = LocationContext(city="San Francisco", region="CA", country="US")
    await adapter.execute("q", "brand", location=location)

    assert calls[0]["gl"] == "us"


@pytest.mark.asyncio
async def test_conversation_turn_flags_include_shopping_and_local(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERPAPI_API_KEY", "test-key")
    install_fake_async_client(
        monkeypatch,
        [
            DummyResponse(
                status_code=200,
                payload={
                    "reconstructed_markdown": "turn 1",
                    "references": [],
                    "subsequent_request_token": "a",
                    "shopping_results": [{"title": "x"}],
                },
            ),
            DummyResponse(
                status_code=200,
                payload={
                    "reconstructed_markdown": "turn 2",
                    "references": [],
                    "subsequent_request_token": "b",
                    "local_results": [{"title": "y"}],
                },
            ),
        ],
    )

    adapter = GoogleAIModeSerpAPIAdapter()
    turns = await adapter.execute_conversation(["q1", "q2"], "brand")

    assert turns[0]["has_shopping"] is True
    assert turns[0]["has_local"] is False
    assert turns[1]["has_shopping"] is False
    assert turns[1]["has_local"] is True


@pytest.mark.asyncio
async def test_conversation_uses_same_gl_and_hl_for_all_turns(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERPAPI_API_KEY", "test-key")
    calls = install_fake_async_client(
        monkeypatch,
        [
            DummyResponse(
                status_code=200,
                payload={"reconstructed_markdown": "1", "references": [], "subsequent_request_token": "x"},
            ),
            DummyResponse(
                status_code=200,
                payload={"reconstructed_markdown": "2", "references": [], "subsequent_request_token": "y"},
            ),
            DummyResponse(status_code=200, payload={"reconstructed_markdown": "3", "references": []}),
        ],
    )

    adapter = GoogleAIModeSerpAPIAdapter()
    location = LocationContext(country="US")
    await adapter.execute_conversation(["a", "b", "c"], "brand", location=location)

    assert len(calls) == 3
    assert all(call.get("hl") == "en" for call in calls)
    assert all(call.get("gl") == "us" for call in calls)


@pytest.mark.asyncio
async def test_httpx_exception_raises_provider_error(monkeypatch: pytest.MonkeyPatch) -> None:
    import ai_visibility.providers.adapters.google_ai_mode_serpapi as module

    monkeypatch.setenv("SERPAPI_API_KEY", "test-key")
    install_fake_async_client(
        monkeypatch,
        [],
        raises=module.httpx.ConnectError("connect failed"),
    )

    adapter = GoogleAIModeSerpAPIAdapter()
    with pytest.raises(ProviderError, match="request failed"):
        await adapter.execute("q", "brand")


@pytest.mark.asyncio
async def test_invalid_json_raises_provider_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERPAPI_API_KEY", "test-key")
    install_fake_async_client(
        monkeypatch,
        [DummyResponse(status_code=200, payload={}, json_error=True)],
    )

    adapter = GoogleAIModeSerpAPIAdapter()
    with pytest.raises(ProviderError, match="non-JSON"):
        await adapter.execute("q", "brand")
