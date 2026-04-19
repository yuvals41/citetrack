# pyright: reportMissingImports=false

from __future__ import annotations

# pyright: reportPrivateUsage=false, reportAny=false, reportExplicitAny=false, reportUnannotatedClassAttribute=false

from typing import Any
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from ai_visibility.providers.adapters import AdapterResult, StubAdapter
from ai_visibility.runs.orchestrator import RunOrchestrator
from ai_visibility.services.competitor_discovery import discover_competitors_with_site_content


class _FakeResponse:
    def __init__(self, *, status_code: int = 200, payload: dict[str, Any] | None = None, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self) -> dict[str, Any]:
        return self._payload


def _patch_async_client(client: AsyncMock):
    context_manager = AsyncMock()
    context_manager.__aenter__.return_value = client
    context_manager.__aexit__.return_value = None
    return patch("ai_visibility.services.competitor_discovery.httpx.AsyncClient", return_value=context_manager)


def _env_map(values: dict[str, str]):
    def _getter(key: str, default: str = "") -> str:
        return values.get(key, default)

    return _getter


def _ok_result() -> AdapterResult:
    return AdapterResult(
        raw_response="Acme is trusted. https://example.com/proof",
        citations=[{"url": "https://example.com/proof"}],
        provider="openai",
        model_name="gpt-5.4",
        model_version="gpt-5.4",
        strategy_version="v1",
    )


@pytest.mark.asyncio
async def test_orchestrator_uses_workspace_brand_name(
    monkeypatch: pytest.MonkeyPatch,
    mock_prisma: AsyncMock,
    patch_get_prisma: AsyncMock,
) -> None:
    _ = patch_get_prisma
    mock_prisma.aivisworkspace.find_unique.return_value = object()
    orch = RunOrchestrator(
        workspace_slug="solara-ai",
        provider="openai",
        adapters={"chatgpt": StubAdapter(result=_ok_result())},
    )
    monkeypatch.setattr(orch.prompt_library, "list_prompts", lambda: [{"template": "find {brand}", "version": "1.0.0"}])

    with patch(
        "ai_visibility.runs.orchestrator.WorkspaceRepository.get_by_slug",
        new=AsyncMock(
            return_value={
                "id": "ws1",
                "brand_name": "Solara AI",
                "slug": "solara-ai",
                "city": "",
                "region": "",
                "country": "",
            }
        ),
    ):
        _ = await orch.scan()

    assert orch.brand_names == ["Solara AI"]


@pytest.mark.asyncio
async def test_orchestrator_falls_back_to_slug_when_no_brand_name(
    monkeypatch: pytest.MonkeyPatch,
    mock_prisma: AsyncMock,
    patch_get_prisma: AsyncMock,
) -> None:
    _ = patch_get_prisma
    mock_prisma.aivisworkspace.find_unique.return_value = object()
    orch = RunOrchestrator(
        workspace_slug="solara-ai",
        provider="openai",
        adapters={"chatgpt": StubAdapter(result=_ok_result())},
    )
    monkeypatch.setattr(orch.prompt_library, "list_prompts", lambda: [{"template": "find {brand}", "version": "1.0.0"}])

    with patch(
        "ai_visibility.runs.orchestrator.WorkspaceRepository.get_by_slug",
        new=AsyncMock(
            return_value={
                "id": "ws1",
                "brand_name": "",
                "slug": "solara-ai",
                "city": "",
                "region": "",
                "country": "",
            }
        ),
    ):
        _ = await orch.scan()

    assert orch.brand_names == ["solara-ai"]


@pytest.mark.asyncio
async def test_orchestrator_uses_explicit_brand_names_over_workspace(
    monkeypatch: pytest.MonkeyPatch,
    mock_prisma: AsyncMock,
    patch_get_prisma: AsyncMock,
) -> None:
    _ = patch_get_prisma
    mock_prisma.aivisworkspace.find_unique.return_value = object()
    orch = RunOrchestrator(
        workspace_slug="solara-ai",
        provider="openai",
        brand_names=["My Brand"],
        adapters={"chatgpt": StubAdapter(result=_ok_result())},
    )
    monkeypatch.setattr(orch.prompt_library, "list_prompts", lambda: [{"template": "find {brand}", "version": "1.0.0"}])

    with patch(
        "ai_visibility.runs.orchestrator.WorkspaceRepository.get_by_slug",
        new=AsyncMock(
            return_value={
                "id": "ws1",
                "brand_name": "Solara AI",
                "slug": "solara-ai",
                "city": "",
                "region": "",
                "country": "",
            }
        ),
    ):
        _ = await orch.scan()

    assert orch.brand_names == ["My Brand"]


@pytest.mark.asyncio
async def test_exa_contents_provides_summary_and_text() -> None:
    client = AsyncMock()

    async def post_side_effect(url: str, **kwargs: Any) -> _FakeResponse:
        _ = kwargs
        if url == "https://api.exa.ai/contents":
            return _FakeResponse(
                payload={
                    "results": [
                        {
                            "text": "site content from exa",
                            "summary": "An AI marketing platform for agencies and SMB teams.",
                        }
                    ]
                }
            )
        raise AssertionError(f"Unexpected URL: {url}")

    client.post.side_effect = post_side_effect

    with (
        patch(
            "ai_visibility.services.competitor_discovery.os.getenv",
            side_effect=_env_map({"EXA_API_KEY": "exa-key", "TAVILY_API_KEY": "tavily-key"}),
        ),
        _patch_async_client(client),
        patch(
            "ai_visibility.services.competitor_discovery._describe_business",
            new=AsyncMock(return_value="should not be used"),
        ) as describe,
        patch(
            "ai_visibility.services.competitor_discovery._find_competitors_exa", new=AsyncMock(return_value=[])
        ) as find_exa,
        patch(
            "ai_visibility.services.competitor_discovery._find_competitors_tavily_gpt", new=AsyncMock(return_value=[])
        ) as find_tavily,
        patch(
            "ai_visibility.services.competitor_discovery._validate_domains", new=AsyncMock(return_value=[])
        ) as validate,
        patch(
            "ai_visibility.services.competitor_discovery._filter_direct_competitors", new=AsyncMock(return_value=[])
        ) as filter_competitors,
    ):
        result, site_content = await discover_competitors_with_site_content("solaraai.com", "SaaS / Software", "US")

    assert result == []
    assert site_content == "site content from exa"
    describe.assert_not_awaited()
    find_exa.assert_awaited_once_with("solaraai.com", "An AI marketing platform for agencies and SMB teams.", "US")
    find_tavily.assert_awaited_once_with("solaraai.com", "An AI marketing platform for agencies and SMB teams.", "US")
    validate.assert_not_awaited()
    filter_competitors.assert_not_awaited()


@pytest.mark.asyncio
async def test_exa_contents_empty_falls_back_to_tavily() -> None:
    client = AsyncMock()

    async def post_side_effect(url: str, **kwargs: Any) -> _FakeResponse:
        _ = kwargs
        if url == "https://api.exa.ai/contents":
            return _FakeResponse(payload={"results": []})
        if url == "https://api.tavily.com/extract":
            return _FakeResponse(payload={"results": [{"raw_content": "t" * 220}]})
        raise AssertionError(f"Unexpected URL: {url}")

    client.post.side_effect = post_side_effect

    with (
        patch(
            "ai_visibility.services.competitor_discovery.os.getenv",
            side_effect=_env_map({"EXA_API_KEY": "exa-key", "TAVILY_API_KEY": "tavily-key"}),
        ),
        _patch_async_client(client),
        patch(
            "ai_visibility.services.competitor_discovery._describe_business",
            new=AsyncMock(return_value="described from tavily"),
        ) as describe,
        patch("ai_visibility.services.competitor_discovery._find_competitors_exa", new=AsyncMock(return_value=[])),
        patch(
            "ai_visibility.services.competitor_discovery._find_competitors_tavily_gpt", new=AsyncMock(return_value=[])
        ),
        patch("ai_visibility.services.competitor_discovery._validate_domains", new=AsyncMock(return_value=[])),
        patch("ai_visibility.services.competitor_discovery._filter_direct_competitors", new=AsyncMock(return_value=[])),
    ):
        result, site_content = await discover_competitors_with_site_content("solaraai.com", "SaaS / Software", "US")

    assert result == []
    assert site_content == "t" * 220
    assert [call.args[0] for call in client.post.await_args_list] == [
        "https://api.exa.ai/contents",
        "https://api.tavily.com/extract",
    ]
    describe.assert_awaited_once_with("t" * 220, "solaraai.com", "SaaS / Software", "US")


@pytest.mark.asyncio
async def test_exa_contents_error_falls_back_to_tavily() -> None:
    client = AsyncMock()

    async def post_side_effect(url: str, **kwargs: Any) -> _FakeResponse:
        _ = kwargs
        if url == "https://api.exa.ai/contents":
            raise httpx.HTTPError("exa failed")
        if url == "https://api.tavily.com/extract":
            return _FakeResponse(payload={"results": [{"raw_content": "tavily fallback"}]})
        raise AssertionError(f"Unexpected URL: {url}")

    client.post.side_effect = post_side_effect

    with (
        patch(
            "ai_visibility.services.competitor_discovery.os.getenv",
            side_effect=_env_map({"EXA_API_KEY": "exa-key", "TAVILY_API_KEY": "tavily-key"}),
        ),
        _patch_async_client(client),
        patch(
            "ai_visibility.services.competitor_discovery._describe_business", new=AsyncMock(return_value="desc")
        ) as describe,
        patch("ai_visibility.services.competitor_discovery._find_competitors_exa", new=AsyncMock(return_value=[])),
        patch(
            "ai_visibility.services.competitor_discovery._find_competitors_tavily_gpt", new=AsyncMock(return_value=[])
        ),
        patch("ai_visibility.services.competitor_discovery._validate_domains", new=AsyncMock(return_value=[])),
        patch("ai_visibility.services.competitor_discovery._filter_direct_competitors", new=AsyncMock(return_value=[])),
    ):
        result, site_content = await discover_competitors_with_site_content("solaraai.com", "SaaS / Software", "US")

    assert result == []
    assert site_content == "tavily fallback"
    describe.assert_awaited_once_with("tavily fallback", "solaraai.com", "SaaS / Software", "US")


@pytest.mark.asyncio
async def test_all_extraction_fails_uses_direct_http() -> None:
    client = AsyncMock()

    async def post_side_effect(url: str, **kwargs: Any) -> _FakeResponse:
        _ = kwargs
        if url in {"https://api.exa.ai/contents", "https://api.tavily.com/extract"}:
            raise httpx.HTTPError("provider failed")
        raise AssertionError(f"Unexpected URL: {url}")

    client.post.side_effect = post_side_effect
    client.get.return_value = _FakeResponse(
        status_code=200,
        text="<html><body>Solara AI helps teams automate social media workflows at scale.</body></html>",
    )

    with (
        patch(
            "ai_visibility.services.competitor_discovery.os.getenv",
            side_effect=_env_map({"EXA_API_KEY": "exa-key", "TAVILY_API_KEY": "tavily-key"}),
        ),
        _patch_async_client(client),
        patch(
            "ai_visibility.services.competitor_discovery._describe_business", new=AsyncMock(return_value="desc")
        ) as describe,
        patch("ai_visibility.services.competitor_discovery._find_competitors_exa", new=AsyncMock(return_value=[])),
        patch(
            "ai_visibility.services.competitor_discovery._find_competitors_tavily_gpt", new=AsyncMock(return_value=[])
        ),
        patch("ai_visibility.services.competitor_discovery._validate_domains", new=AsyncMock(return_value=[])),
        patch("ai_visibility.services.competitor_discovery._filter_direct_competitors", new=AsyncMock(return_value=[])),
    ):
        result, site_content = await discover_competitors_with_site_content("solaraai.com", "SaaS / Software", "US")

    assert result == []
    assert "Solara AI helps teams automate social media workflows at scale." in site_content
    describe.assert_awaited_once_with(site_content, "solaraai.com", "SaaS / Software", "US")
    client.get.assert_awaited_once_with(
        "https://solaraai.com",
        headers={"User-Agent": "Mozilla/5.0"},
        follow_redirects=True,
        timeout=10.0,
    )


@pytest.mark.asyncio
async def test_brand_name_stripped_from_exa_summary() -> None:
    client = AsyncMock()

    async def post_side_effect(url: str, **kwargs: Any) -> _FakeResponse:
        _ = kwargs
        if url == "https://api.exa.ai/contents":
            return _FakeResponse(
                payload={
                    "results": [
                        {
                            "text": "site content",
                            "summary": "Solaraai provides marketing automation for growth teams.",
                        }
                    ]
                }
            )
        raise AssertionError(f"Unexpected URL: {url}")

    client.post.side_effect = post_side_effect

    with (
        patch(
            "ai_visibility.services.competitor_discovery.os.getenv", side_effect=_env_map({"EXA_API_KEY": "exa-key"})
        ),
        _patch_async_client(client),
        patch(
            "ai_visibility.services.competitor_discovery._describe_business",
            new=AsyncMock(return_value="should not run"),
        ) as describe,
        patch(
            "ai_visibility.services.competitor_discovery._find_competitors_exa", new=AsyncMock(return_value=[])
        ) as find_exa,
        patch(
            "ai_visibility.services.competitor_discovery._find_competitors_tavily_gpt", new=AsyncMock(return_value=[])
        ),
        patch("ai_visibility.services.competitor_discovery._validate_domains", new=AsyncMock(return_value=[])),
        patch("ai_visibility.services.competitor_discovery._filter_direct_competitors", new=AsyncMock(return_value=[])),
    ):
        result, _ = await discover_competitors_with_site_content("solaraai.com", "SaaS / Software")

    assert result == []
    describe.assert_not_awaited()
    assert find_exa.await_args is not None
    cleaned_description = find_exa.await_args.args[1]
    assert "solara" not in cleaned_description.lower()
    assert "solaraai" not in cleaned_description.lower()
