from __future__ import annotations

from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ai_visibility.pixel import events as events_module
from ai_visibility.pixel import router as router_module
from ai_visibility.pixel.events import PixelEvent
from ai_visibility.pixel.events import get_pixel_stats
from ai_visibility.pixel.events import store_pixel_event
from ai_visibility.pixel.snippet import generate_pixel_snippet


def _pixel_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router_module.router)
    return app


def _valid_payload() -> dict[str, Any]:
    return {
        "workspace_id": "ws-1",
        "source": "chatgpt",
        "referrer": "https://chatgpt.com/share/1",
        "page_url": "https://example.com/pricing",
        "timestamp": "2026-03-22T10:00:00Z",
        "session_id": "sid-123",
        "event_type": "visit",
    }


def test_generate_pixel_snippet_contains_workspace_id() -> None:
    snippet = generate_pixel_snippet("workspace-123")
    assert "workspace-123" in snippet


def test_generate_pixel_snippet_contains_endpoint() -> None:
    snippet = generate_pixel_snippet("workspace-123", "https://api.example.com")
    assert "/api/v1/pixel/event" in snippet
    assert "https://api.example.com" in snippet


def test_generate_pixel_snippet_contains_referrer_patterns() -> None:
    snippet = generate_pixel_snippet("workspace-123")
    for pattern in [
        "chatgpt.com",
        "chat.openai.com",
        "perplexity.ai",
        "claude.ai",
        "gemini.google.com",
        "bard.google.com",
        "grok.x.ai",
        "x.com/i/grok",
        "bing.com/chat",
        "copilot.microsoft.com",
        "utm_source",
        "utm_medium",
    ]:
        assert pattern in snippet


def test_generate_pixel_snippet_has_conversion_function() -> None:
    snippet = generate_pixel_snippet("workspace-123")
    assert "window.aiVisTrackConversion" in snippet
    assert "conversion_value" in snippet
    assert "conversion_currency" in snippet


def test_generate_pixel_snippet_is_script_tag_and_under_2kb() -> None:
    snippet = generate_pixel_snippet("workspace-123")
    assert snippet.startswith("<script>")
    assert snippet.endswith("</script>")
    assert len(snippet.encode("utf-8")) < 2048


def test_parse_pixel_event_payload_valid() -> None:
    event = router_module._parse_pixel_event_payload(_valid_payload())
    assert event.workspace_id == "ws-1"
    assert event.source == "chatgpt"
    assert event.event_type == "visit"


def test_parse_pixel_event_payload_missing_fields() -> None:
    with pytest.raises(ValueError, match="missing fields"):
        router_module._parse_pixel_event_payload({"workspace_id": "ws-1"})


def test_parse_pixel_event_payload_unknown_source() -> None:
    payload = _valid_payload()
    payload["source"] = "unknown"
    with pytest.raises(ValueError, match="unsupported source"):
        router_module._parse_pixel_event_payload(payload)


def test_parse_pixel_event_payload_invalid_conversion_value() -> None:
    payload = _valid_payload()
    payload["event_type"] = "conversion"
    payload["conversion_value"] = "abc"
    with pytest.raises(ValueError, match="conversion_value"):
        router_module._parse_pixel_event_payload(payload)


def test_parse_pixel_event_payload_normalizes_currency() -> None:
    payload = _valid_payload()
    payload["event_type"] = "conversion"
    payload["conversion_value"] = 15
    payload["conversion_currency"] = "usd"
    event = router_module._parse_pixel_event_payload(payload)
    assert event.conversion_value == 15.0
    assert event.conversion_currency == "USD"


@pytest.mark.asyncio
async def test_store_pixel_event_executes_create_and_insert(monkeypatch: pytest.MonkeyPatch) -> None:
    class _PrismaStub:
        def __init__(self) -> None:
            self.calls: list[tuple[str, tuple[Any, ...]]] = []

        async def execute_raw(self, query: str, *args: Any) -> int:
            self.calls.append((query, args))
            return 1

    prisma = _PrismaStub()

    async def _fake_get_prisma() -> _PrismaStub:
        return prisma

    monkeypatch.setattr(events_module, "get_prisma", _fake_get_prisma)

    await store_pixel_event(
        PixelEvent(
            workspace_id="ws-1",
            source="chatgpt",
            referrer="https://chatgpt.com",
            page_url="https://example.com",
            timestamp="2026-03-22T10:00:00Z",
            session_id="sid-1",
            event_type="visit",
        )
    )

    assert any("CREATE TABLE IF NOT EXISTS ai_vis_pixel_events" in call[0] for call in prisma.calls)
    assert any("INSERT INTO ai_vis_pixel_events" in call[0] for call in prisma.calls)


@pytest.mark.asyncio
async def test_store_pixel_event_rejects_invalid_source() -> None:
    with pytest.raises(ValueError, match="Unsupported source"):
        await store_pixel_event(
            PixelEvent(
                workspace_id="ws-1",
                source="bad",
                referrer="",
                page_url="",
                timestamp="2026-03-22T10:00:00Z",
                session_id="sid",
                event_type="visit",
            )
        )


@pytest.mark.asyncio
async def test_get_pixel_stats_aggregates_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    class _PrismaStub:
        async def execute_raw(self, _query: str, *_args: Any) -> int:
            return 1

        async def query_raw(self, query: str, *_args: Any) -> list[dict[str, Any]]:
            if "total_visits" in query:
                return [{"total_visits": "10", "total_conversions": "2", "total_revenue": "99.5"}]
            if "event_type = 'visit'" in query and "GROUP BY source" in query:
                return [{"source": "chatgpt", "count": "7"}, {"source": "perplexity", "count": "3"}]
            if "event_type = 'conversion'" in query:
                return [{"source": "chatgpt", "count": "2"}]
            return [{"date": "2026-03-21", "source": "chatgpt", "count": "4"}]

    async def _fake_get_prisma() -> _PrismaStub:
        return _PrismaStub()

    monkeypatch.setattr(events_module, "get_prisma", _fake_get_prisma)

    stats = await get_pixel_stats("ws-1", days=14)
    assert stats["total_visits"] == 10
    assert stats["total_conversions"] == 2
    assert stats["total_revenue"] == 99.5
    assert stats["visits_by_source"]["chatgpt"] == 7
    assert stats["conversions_by_source"]["chatgpt"] == 2
    assert stats["daily_visits"][0]["date"] == "2026-03-21"


def test_event_endpoint_returns_204_and_cors(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[PixelEvent] = []

    def _fake_store(event: PixelEvent) -> None:
        captured.append(event)

    def _fake_create_task(_coro: Any) -> object:
        return object()

    monkeypatch.setattr(router_module, "store_pixel_event", _fake_store)
    monkeypatch.setattr(router_module.asyncio, "create_task", _fake_create_task)

    client = TestClient(_pixel_app())
    response = client.post("/api/v1/pixel/event", json=_valid_payload())
    assert response.status_code == 204
    assert response.headers.get("access-control-allow-origin") == "*"
    assert len(captured) == 1


def test_event_endpoint_ignores_invalid_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    called = {"count": 0}

    def _fake_create_task(_coro: Any) -> object:
        called["count"] += 1
        return object()

    monkeypatch.setattr(router_module.asyncio, "create_task", _fake_create_task)

    client = TestClient(_pixel_app())
    response = client.post("/api/v1/pixel/event", json={"workspace_id": "ws-1"})
    assert response.status_code == 204
    assert response.headers.get("access-control-allow-origin") == "*"
    assert called["count"] == 0


def test_snippet_endpoint_returns_javascript_content_type() -> None:
    client = TestClient(_pixel_app())
    response = client.get("/api/v1/pixel/snippet/ws-abc")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/javascript")
    assert "<script>" in response.text
    assert "ws-abc" in response.text


def test_stats_endpoint_returns_mocked_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_stats(workspace_id: str, days: int = 30) -> dict[str, Any]:
        assert workspace_id == "ws-abc"
        assert days == 7
        return {
            "total_visits": 5,
            "total_conversions": 1,
            "total_revenue": 25.0,
            "visits_by_source": {"chatgpt": 5},
            "conversions_by_source": {"chatgpt": 1},
            "daily_visits": [{"date": "2026-03-22", "source": "chatgpt", "count": 5}],
        }

    monkeypatch.setattr(router_module, "get_pixel_stats", _fake_stats)

    client = TestClient(_pixel_app())
    response = client.get("/api/v1/pixel/stats/ws-abc?days=7")
    assert response.status_code == 200
    assert response.json()["total_visits"] == 5
    assert response.json()["daily_visits"][0]["source"] == "chatgpt"
