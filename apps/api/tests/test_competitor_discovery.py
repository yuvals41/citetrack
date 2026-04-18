from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from ai_visibility.ui.onboarding_state import (
    _describe_business,
    _discover_competitors_with_site_content,
    _extract_domain,
    _filter_direct_competitors,
    _find_competitors_exa,
    _find_competitors_tavily_gpt,
    _humanize_brand,
    _validate_domains,
)


class _FakeResponse:
    def __init__(self, *, status_code: int = 200, payload: dict[str, Any] | None = None, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self) -> dict[str, Any]:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def _patch_async_client(client: AsyncMock):
    context_manager = AsyncMock()
    context_manager.__aenter__.return_value = client
    context_manager.__aexit__.return_value = None
    return patch("ai_visibility.ui.onboarding_state.httpx.AsyncClient", return_value=context_manager)


def _env_map(values: dict[str, str]):
    def _getter(key: str, default: str = "") -> str:
        return values.get(key, default)

    return _getter


@pytest.mark.parametrize(
    ("entry", "expected"),
    [
        ("Name (domain.com)", "domain.com"),
        ("Name (domain.com) — description", "domain.com"),
        (
            "Checkmate (checkmateforbrands.com) — # Checkmate (Checkmate Savings, Inc.)",
            "checkmateforbrands.com",
        ),
        ("FirmPilot (firmpilot.com) — # FirmPilot (FirmPilot AI, Inc.)", "firmpilot.com"),
        ("just text", ""),
        ("", ""),
        ("A (b.com (nested))", "b.com (nested"),
        ("Name (sub.domain.com)", "sub.domain.com"),
        ("Name (site.co.uk)", "site.co.uk"),
        ("Name ( domain.com )", "domain.com"),
        ("Name ()", ""),
    ],
)
def test_extract_domain_edge_cases(entry: str, expected: str) -> None:
    assert _extract_domain(entry) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("maison-remodeling", "Maison Remodeling"),
        ("solaraai", "Solaraai"),
        ("my-company-name", "My Company Name"),
    ],
)
def test_humanize_brand(value: str, expected: str) -> None:
    assert _humanize_brand(value) == expected


@pytest.mark.asyncio
async def test_validate_domains_all_200_pass() -> None:
    client = AsyncMock()
    client.head.return_value = _FakeResponse(status_code=200)
    client.get.return_value = _FakeResponse(status_code=200)

    with _patch_async_client(client):
        result = await _validate_domains(["A (a.com)", "B (b.com)"])

    assert result == ["A (a.com)", "B (b.com)"]
    assert client.head.await_count == 2
    assert client.get.await_count == 0


@pytest.mark.asyncio
async def test_validate_domains_mixed_status_codes() -> None:
    client = AsyncMock()

    async def head_side_effect(url: str) -> _FakeResponse:
        mapping = {
            "https://ok.com": 200,
            "https://forbidden.com": 403,
            "https://server-error.com": 500,
        }
        return _FakeResponse(status_code=mapping[url])

    client.head.side_effect = head_side_effect
    client.get.return_value = _FakeResponse(status_code=500)

    entries = ["OK (ok.com)", "Forbidden (forbidden.com)", "Broken (server-error.com)"]
    with _patch_async_client(client):
        result = await _validate_domains(entries)

    assert result == ["OK (ok.com)", "Forbidden (forbidden.com)"]
    assert client.get.await_count == 1


@pytest.mark.asyncio
async def test_validate_domains_head_fails_get_succeeds() -> None:
    client = AsyncMock()
    client.head.side_effect = httpx.TimeoutException("head timeout")
    client.get.return_value = _FakeResponse(status_code=200)

    with _patch_async_client(client):
        result = await _validate_domains(["Timeout (timeout.com)"])

    assert result == ["Timeout (timeout.com)"]
    client.get.assert_awaited_once_with("https://timeout.com", timeout=5.0)


@pytest.mark.asyncio
async def test_validate_domains_both_head_and_get_fail() -> None:
    client = AsyncMock()
    client.head.side_effect = httpx.ConnectError("boom")
    client.get.side_effect = httpx.ConnectError("boom")

    with _patch_async_client(client):
        result = await _validate_domains(["Down (down.com)"])

    assert result == []


@pytest.mark.asyncio
async def test_validate_domains_entry_with_no_extractable_domain_is_skipped() -> None:
    client = AsyncMock()
    client.head.return_value = _FakeResponse(status_code=200)

    entries = ["No domain", "Valid (valid.com)"]
    with _patch_async_client(client):
        result = await _validate_domains(entries)

    assert result == ["Valid (valid.com)"]
    client.head.assert_awaited_once_with("https://valid.com")


@pytest.mark.asyncio
async def test_filter_direct_competitors_valid_json_returns_filtered_list() -> None:
    client = AsyncMock()
    client.post.return_value = _FakeResponse(
        payload={
            "content": [
                {
                    "type": "text",
                    "text": '{"competitors": ["Alpha (alpha.com) — desc", "Beta (beta.com)"]}',
                }
            ]
        }
    )

    with (
        patch("ai_visibility.ui.onboarding_state.os.getenv", return_value="anthropic-key"),
        _patch_async_client(client),
    ):
        result = await _filter_direct_competitors(
            ["Alpha (alpha.com)", "Beta (beta.com)", "Gamma (gamma.com)"],
            "Business description",
            "acme.com",
            "SaaS / Software",
        )

    assert result == ["Alpha (alpha.com)", "Beta (beta.com)"]


@pytest.mark.asyncio
async def test_filter_direct_competitors_no_api_key_falls_back() -> None:
    candidates = ["A (a.com)"]
    with patch("ai_visibility.ui.onboarding_state.os.getenv", return_value=""):
        result = await _filter_direct_competitors(candidates, "desc", "acme.com", "SaaS / Software")
    assert result == candidates


@pytest.mark.asyncio
async def test_describe_business_success_returns_claude_text_and_cleans_content() -> None:
    client = AsyncMock()
    client.post.return_value = _FakeResponse(
        payload={"content": [{"type": "text", "text": '"AI-powered marketing platform in London"\nMore text'}]}
    )

    with (
        patch(
            "ai_visibility.ui.onboarding_state.os.getenv",
            side_effect=_env_map({"ANTHROPIC_API_KEY": "anthropic-key"}),
        ),
        _patch_async_client(client),
    ):
        result = await _describe_business(
            "<h1>Acme</h1> [link](https://example.com) https://foo.bar text",
            "acme.co.uk",
            "SaaS / Software",
            "GB",
        )

    assert result == "AI-powered marketing platform in London"
    call_json = client.post.await_args.kwargs["json"]
    prompt_content = call_json["messages"][0]["content"]
    assert "<h1>" not in prompt_content
    assert "https://foo.bar" not in prompt_content
    assert "Country hint: United Kingdom" in prompt_content


@pytest.mark.asyncio
async def test_describe_business_returns_industry_when_api_key_missing() -> None:
    with patch("ai_visibility.ui.onboarding_state.os.getenv", side_effect=_env_map({})):
        result = await _describe_business("some site content", "acme.com", "SaaS / Software")
    assert result == "SaaS / Software"


@pytest.mark.asyncio
async def test_describe_business_returns_industry_when_content_empty_after_cleaning() -> None:
    with patch(
        "ai_visibility.ui.onboarding_state.os.getenv",
        side_effect=_env_map({"ANTHROPIC_API_KEY": "anthropic-key"}),
    ):
        result = await _describe_business("<div></div> https://x.com [a](https://b.com)", "acme.com", "Consulting")
    assert result == "Consulting"


@pytest.mark.asyncio
async def test_describe_business_returns_industry_on_http_failure() -> None:
    client = AsyncMock()
    client.post.side_effect = RuntimeError("anthropic down")

    with (
        patch(
            "ai_visibility.ui.onboarding_state.os.getenv",
            side_effect=_env_map({"ANTHROPIC_API_KEY": "anthropic-key"}),
        ),
        _patch_async_client(client),
    ):
        result = await _describe_business("Business text", "acme.com", "Healthcare / Medical")

    assert result == "Healthcare / Medical"


@pytest.mark.asyncio
async def test_describe_business_logs_with_describe_prefix() -> None:
    with patch("ai_visibility.ui.onboarding_state.logger.info") as info_log:
        with patch("ai_visibility.ui.onboarding_state.os.getenv", side_effect=_env_map({})):
            _ = await _describe_business("site", "acme.com", "SaaS")
    logged_messages = [call.args[0] for call in info_log.call_args_list if call.args]
    assert any("[describe]" in msg for msg in logged_messages)


@pytest.mark.asyncio
async def test_find_competitors_exa_builds_query_without_country_for_dot_com_domain() -> None:
    client = AsyncMock()
    client.post.return_value = _FakeResponse(payload={"results": []})

    with (
        patch("ai_visibility.ui.onboarding_state.os.getenv", side_effect=_env_map({"EXA_API_KEY": "exa-key"})),
        _patch_async_client(client),
    ):
        _ = await _find_competitors_exa("acme.com", "B2B accounting software", "US")

    body = client.post.await_args.kwargs["json"]
    assert body["query"] == "B2B accounting software"
    assert body["userLocation"] == "us"


@pytest.mark.asyncio
async def test_find_competitors_exa_builds_query_with_country_for_non_com_domain() -> None:
    client = AsyncMock()
    client.post.return_value = _FakeResponse(payload={"results": []})

    with (
        patch("ai_visibility.ui.onboarding_state.os.getenv", side_effect=_env_map({"EXA_API_KEY": "exa-key"})),
        _patch_async_client(client),
    ):
        _ = await _find_competitors_exa("acme.co.uk", "Home remodeling contractor", "GB")

    body = client.post.await_args.kwargs["json"]
    assert body["query"] == "Home remodeling contractor United Kingdom"


@pytest.mark.asyncio
async def test_find_competitors_exa_uses_summary_field_for_description() -> None:
    client = AsyncMock()
    client.post.return_value = _FakeResponse(
        payload={
            "results": [
                {
                    "title": "Alpha",
                    "url": "https://alpha.com",
                    "summary": "Summary text used",
                    "text": "Old text should not be used",
                }
            ]
        }
    )

    with (
        patch("ai_visibility.ui.onboarding_state.os.getenv", side_effect=_env_map({"EXA_API_KEY": "exa-key"})),
        _patch_async_client(client),
    ):
        result = await _find_competitors_exa("acme.com", "SaaS", "")

    assert result == ["Alpha (alpha.com) — Summary text used"]


@pytest.mark.asyncio
async def test_find_competitors_exa_filters_self_domain_and_blocked_sites() -> None:
    client = AsyncMock()
    client.post.return_value = _FakeResponse(
        payload={
            "results": [
                {"title": "Acme", "url": "https://acme.com", "summary": "self"},
                {"title": "Top 10", "url": "https://example.com/blog/top-10", "summary": "listicle"},
                {"title": "Reddit Thread", "url": "https://reddit.com/r/x", "summary": "forum"},
                {"title": "News", "url": "https://citynews.com/story", "summary": "news"},
                {"title": "Bravo", "url": "https://bravo.com", "summary": "real"},
            ]
        }
    )

    with (
        patch("ai_visibility.ui.onboarding_state.os.getenv", side_effect=_env_map({"EXA_API_KEY": "exa-key"})),
        _patch_async_client(client),
    ):
        result = await _find_competitors_exa("acme.com", "SaaS", "")

    assert result == ["Bravo (bravo.com) — real"]


@pytest.mark.asyncio
async def test_find_competitors_exa_deduplicates_domains_and_handles_missing_summary() -> None:
    client = AsyncMock()
    client.post.return_value = _FakeResponse(
        payload={
            "results": [
                {"title": "Alpha", "url": "https://alpha.com", "summary": "one"},
                {"title": "Alpha Duplicate", "url": "https://www.alpha.com/pricing", "summary": "two"},
                {"title": "Beta", "url": "https://beta.com"},
            ]
        }
    )

    with (
        patch("ai_visibility.ui.onboarding_state.os.getenv", side_effect=_env_map({"EXA_API_KEY": "exa-key"})),
        _patch_async_client(client),
    ):
        result = await _find_competitors_exa("acme.com", "SaaS", "")

    assert result == ["Alpha (alpha.com) — one", "Beta (beta.com)"]


@pytest.mark.asyncio
async def test_find_competitors_exa_no_api_key_returns_empty() -> None:
    with patch("ai_visibility.ui.onboarding_state.os.getenv", side_effect=_env_map({})):
        result = await _find_competitors_exa("acme.com", "SaaS", "")
    assert result == []


@pytest.mark.asyncio
async def test_find_competitors_exa_http_error_returns_empty() -> None:
    client = AsyncMock()
    client.post.side_effect = RuntimeError("exa unavailable")

    with (
        patch("ai_visibility.ui.onboarding_state.os.getenv", side_effect=_env_map({"EXA_API_KEY": "exa-key"})),
        _patch_async_client(client),
    ):
        result = await _find_competitors_exa("acme.com", "SaaS", "")

    assert result == []


@pytest.mark.asyncio
async def test_find_competitors_tavily_returns_empty_without_api_key() -> None:
    with patch("ai_visibility.ui.onboarding_state.os.getenv", side_effect=_env_map({})):
        result = await _find_competitors_tavily_gpt("acme.com", "SaaS", "US")
    assert result == []


@pytest.mark.asyncio
async def test_find_competitors_tavily_posts_with_include_answer_and_new_query_format() -> None:
    client = AsyncMock()
    client.post.return_value = _FakeResponse(payload={"results": [], "answer": ""})

    with (
        patch(
            "ai_visibility.ui.onboarding_state.os.getenv",
            side_effect=_env_map({"TAVILY_API_KEY": "tavily-key"}),
        ),
        _patch_async_client(client),
    ):
        _ = await _find_competitors_tavily_gpt("acme.com", "B2B CRM platform", "US")

    body = client.post.await_args.kwargs["json"]
    assert body["query"] == "competitors of acme.com B2B CRM platform"
    assert body["include_answer"] is True


@pytest.mark.asyncio
async def test_find_competitors_tavily_parses_answer_and_matches_result_domains() -> None:
    client = AsyncMock()
    client.post.return_value = _FakeResponse(
        payload={
            "answer": "Top competitors include Alpha Systems and Bright Labs.",
            "results": [
                {"title": "Alpha Systems | Home", "url": "https://alpha.io"},
                {"title": "Bright Labs", "url": "https://www.brightlabs.com"},
            ],
        }
    )

    with (
        patch(
            "ai_visibility.ui.onboarding_state.os.getenv",
            side_effect=_env_map({"TAVILY_API_KEY": "tavily-key"}),
        ),
        _patch_async_client(client),
    ):
        result = await _find_competitors_tavily_gpt("acme.com", "SaaS", "")

    assert result == ["Alpha Systems (alpha.io)", "Bright Labs (brightlabs.com)"]


@pytest.mark.asyncio
async def test_find_competitors_tavily_adds_remaining_domains_from_results() -> None:
    client = AsyncMock()
    client.post.return_value = _FakeResponse(
        payload={
            "answer": "",
            "results": [
                {"title": "Gamma Platform - AI", "url": "https://gamma.ai"},
                {"title": "", "url": "https://delta-tools.com"},
            ],
        }
    )

    with (
        patch(
            "ai_visibility.ui.onboarding_state.os.getenv",
            side_effect=_env_map({"TAVILY_API_KEY": "tavily-key"}),
        ),
        _patch_async_client(client),
    ):
        result = await _find_competitors_tavily_gpt("acme.com", "SaaS", "")

    assert result == ["Gamma Platform (gamma.ai)", "Delta Tools (delta-tools.com)"]


@pytest.mark.asyncio
async def test_find_competitors_tavily_filters_self_domain_listicles_and_blocked_domains() -> None:
    client = AsyncMock()
    client.post.return_value = _FakeResponse(
        payload={
            "answer": "",
            "results": [
                {"title": "Acme", "url": "https://acme.com/pricing"},
                {"title": "Top 10 tools", "url": "https://example.com/blog/top-10-tools"},
                {"title": "G2 review", "url": "https://g2.com/products/x"},
                {"title": "City Times", "url": "https://citytimes.com/news/x"},
                {"title": "Nova AI", "url": "https://nova.ai"},
            ],
        }
    )

    with (
        patch(
            "ai_visibility.ui.onboarding_state.os.getenv",
            side_effect=_env_map({"TAVILY_API_KEY": "tavily-key"}),
        ),
        _patch_async_client(client),
    ):
        result = await _find_competitors_tavily_gpt("acme.com", "SaaS", "")

    assert result == ["Nova AI (nova.ai)"]


@pytest.mark.asyncio
async def test_find_competitors_tavily_http_error_returns_empty() -> None:
    client = AsyncMock()
    client.post.side_effect = RuntimeError("tavily unavailable")

    with (
        patch(
            "ai_visibility.ui.onboarding_state.os.getenv",
            side_effect=_env_map({"TAVILY_API_KEY": "tavily-key"}),
        ),
        _patch_async_client(client),
    ):
        result = await _find_competitors_tavily_gpt("acme.com", "SaaS", "")

    assert result == []


@pytest.mark.asyncio
async def test_discover_with_site_content_invalid_input_returns_empty_immediately() -> None:
    result, site_content = await _discover_competitors_with_site_content("", "")
    assert result == []
    assert site_content == ""


@pytest.mark.asyncio
async def test_discover_with_site_content_uses_exa_contents_summary_and_skips_describe() -> None:
    client = AsyncMock()

    async def post_side_effect(url: str, **kwargs: Any) -> _FakeResponse:
        if url == "https://api.exa.ai/contents":
            return _FakeResponse(
                payload={
                    "results": [
                        {
                            "text": "x" * 300,
                            "summary": "Acme provides AI analytics software for B2B teams in New York.",
                        }
                    ]
                }
            )
        raise AssertionError(f"Unexpected URL: {url}")

    client.post.side_effect = post_side_effect

    exa_results = ["Alpha (alpha.com) — from exa", "Beta (beta.com)"]
    tavily_results = ["Alpha Inc (alpha.com)", "Gamma (gamma.com)"]
    validated = ["Alpha (alpha.com) — from exa", "Beta (beta.com)", "Gamma (gamma.com)"]
    filtered = ["Alpha (alpha.com)", "Gamma (gamma.com)"]

    with (
        patch(
            "ai_visibility.ui.onboarding_state.os.getenv",
            side_effect=_env_map({"EXA_API_KEY": "exa-key", "TAVILY_API_KEY": "tavily-key"}),
        ),
        _patch_async_client(client),
        patch(
            "ai_visibility.ui.onboarding_state._describe_business", new=AsyncMock(return_value="AI analytics platform")
        ) as describe,
        patch(
            "ai_visibility.ui.onboarding_state._find_competitors_exa", new=AsyncMock(return_value=exa_results)
        ) as exa,
        patch(
            "ai_visibility.ui.onboarding_state._find_competitors_tavily_gpt",
            new=AsyncMock(return_value=tavily_results),
        ) as tavily,
        patch("ai_visibility.ui.onboarding_state._validate_domains", new=AsyncMock(return_value=validated)) as validate,
        patch(
            "ai_visibility.ui.onboarding_state._filter_direct_competitors", new=AsyncMock(return_value=filtered)
        ) as flt,
    ):
        result, site_content = await _discover_competitors_with_site_content("acme.com", "SaaS / Software", "US")

    assert result == filtered
    assert len(site_content) == 300
    describe.assert_not_awaited()
    exa.assert_awaited_once_with("acme.com", "provides AI analytics software for B2B teams in New York.", "US")
    tavily.assert_awaited_once_with("acme.com", "provides AI analytics software for B2B teams in New York.", "US")
    validate.assert_awaited_once_with(["Alpha (alpha.com) — from exa", "Beta (beta.com)", "Gamma (gamma.com)"])
    flt.assert_awaited_once_with(
        validated,
        "x" * 300,
        "acme.com",
        "provides AI analytics software for B2B teams in New York.",
        "US",
    )

    exa_contents_call = client.post.await_args_list[0]
    assert exa_contents_call.args[0] == "https://api.exa.ai/contents"
    exa_body = exa_contents_call.kwargs["json"]
    assert exa_body["summary"]["query"].startswith("One sentence describing what this business does")


@pytest.mark.asyncio
async def test_discover_with_site_content_exa_empty_falls_back_to_tavily_extract() -> None:
    client = AsyncMock()

    async def post_side_effect(url: str, **kwargs: Any) -> _FakeResponse:
        if url == "https://api.exa.ai/contents":
            return _FakeResponse(payload={"results": [{"text": "", "summary": ""}]})
        if url == "https://api.tavily.com/extract":
            return _FakeResponse(payload={"results": [{"raw_content": "t" * 220}]})
        raise AssertionError(f"Unexpected URL: {url}")

    client.post.side_effect = post_side_effect

    with (
        patch(
            "ai_visibility.ui.onboarding_state.os.getenv",
            side_effect=_env_map({"EXA_API_KEY": "exa-key", "TAVILY_API_KEY": "tavily-key"}),
        ),
        _patch_async_client(client),
        patch(
            "ai_visibility.ui.onboarding_state._describe_business", new=AsyncMock(return_value="Claude desc")
        ) as describe,
        patch("ai_visibility.ui.onboarding_state._find_competitors_exa", new=AsyncMock(return_value=[])) as exa,
        patch("ai_visibility.ui.onboarding_state._find_competitors_tavily_gpt", new=AsyncMock(return_value=[])),
    ):
        result, site_content = await _discover_competitors_with_site_content("acme.com", "SaaS / Software", "US")

    assert result == []
    assert site_content == "t" * 220
    assert [call.args[0] for call in client.post.await_args_list] == [
        "https://api.exa.ai/contents",
        "https://api.tavily.com/extract",
    ]
    describe.assert_awaited_once_with("t" * 220, "acme.com", "SaaS / Software", "US")
    exa.assert_awaited_once_with("acme.com", "Claude desc", "US")


@pytest.mark.asyncio
async def test_discover_with_site_content_exa_failure_falls_back_to_tavily_then_describe() -> None:
    client = AsyncMock()

    async def post_side_effect(url: str, **kwargs: Any) -> _FakeResponse:
        if url == "https://api.exa.ai/contents":
            raise RuntimeError("exa down")
        if url == "https://api.tavily.com/extract":
            return _FakeResponse(payload={"results": [{"raw_content": "fallback content"}]})
        raise AssertionError(f"Unexpected URL: {url}")

    client.post.side_effect = post_side_effect

    with (
        patch(
            "ai_visibility.ui.onboarding_state.os.getenv",
            side_effect=_env_map({"EXA_API_KEY": "exa-key", "TAVILY_API_KEY": "tavily-key"}),
        ),
        _patch_async_client(client),
        patch(
            "ai_visibility.ui.onboarding_state._describe_business", new=AsyncMock(return_value="Fallback described")
        ) as describe,
        patch("ai_visibility.ui.onboarding_state._find_competitors_exa", new=AsyncMock(return_value=[])) as exa,
        patch("ai_visibility.ui.onboarding_state._find_competitors_tavily_gpt", new=AsyncMock(return_value=[])),
    ):
        result, site_content = await _discover_competitors_with_site_content("acme.com", "SaaS / Software", "US")

    assert result == []
    assert site_content == "fallback content"
    describe.assert_awaited_once_with("fallback content", "acme.com", "SaaS / Software", "US")
    exa.assert_awaited_once_with("acme.com", "Fallback described", "US")


@pytest.mark.asyncio
async def test_discover_with_site_content_strips_brand_name_from_exa_summary() -> None:
    client = AsyncMock()

    async def post_side_effect(url: str, **kwargs: Any) -> _FakeResponse:
        if url == "https://api.exa.ai/contents":
            return _FakeResponse(
                payload={
                    "results": [
                        {
                            "text": "brand site content",
                            "summary": "Acme Remodeling offers home remodeling services in Austin, Texas.",
                        }
                    ]
                }
            )
        raise AssertionError(f"Unexpected URL: {url}")

    client.post.side_effect = post_side_effect

    with (
        patch(
            "ai_visibility.ui.onboarding_state.os.getenv",
            side_effect=_env_map({"EXA_API_KEY": "exa-key"}),
        ),
        _patch_async_client(client),
        patch(
            "ai_visibility.ui.onboarding_state._describe_business", new=AsyncMock(return_value="should not be used")
        ) as describe,
        patch("ai_visibility.ui.onboarding_state._find_competitors_exa", new=AsyncMock(return_value=[])) as exa,
        patch("ai_visibility.ui.onboarding_state._find_competitors_tavily_gpt", new=AsyncMock(return_value=[])),
    ):
        result, _ = await _discover_competitors_with_site_content("acme-remodeling.com", "Home Services / Remodeling")

    assert result == []
    describe.assert_not_awaited()
    assert exa.await_args is not None
    cleaned_description = exa.await_args.args[1]
    assert "acme" not in cleaned_description.lower()
    assert "remodeling" not in cleaned_description.lower()
    assert cleaned_description == "offers home services in Austin, Texas."


@pytest.mark.asyncio
async def test_discover_with_site_content_passes_business_description_to_filter_as_industry_param() -> None:
    client = AsyncMock()

    async def post_side_effect(url: str, **kwargs: Any) -> _FakeResponse:
        if url == "https://api.exa.ai/contents":
            return _FakeResponse(payload={"results": [{"text": "", "summary": ""}]})
        if url == "https://api.tavily.com/extract":
            return _FakeResponse(payload={"results": [{"raw_content": "content" * 80}]})
        raise AssertionError(f"Unexpected URL: {url}")

    client.post.side_effect = post_side_effect

    with (
        patch(
            "ai_visibility.ui.onboarding_state.os.getenv",
            side_effect=_env_map({"EXA_API_KEY": "exa-key", "TAVILY_API_KEY": "tavily-key"}),
        ),
        _patch_async_client(client),
        patch(
            "ai_visibility.ui.onboarding_state._describe_business",
            new=AsyncMock(return_value="Custom business description"),
        ),
        patch("ai_visibility.ui.onboarding_state._find_competitors_exa", new=AsyncMock(return_value=["A (a.com)"])),
        patch("ai_visibility.ui.onboarding_state._find_competitors_tavily_gpt", new=AsyncMock(return_value=[])),
        patch("ai_visibility.ui.onboarding_state._validate_domains", new=AsyncMock(return_value=["A (a.com)"])),
        patch(
            "ai_visibility.ui.onboarding_state._filter_direct_competitors", new=AsyncMock(return_value=["A (a.com)"])
        ) as flt,
    ):
        _ = await _discover_competitors_with_site_content("acme.com", "SaaS / Software", "GB")

    assert flt.await_args is not None
    args = flt.await_args.args
    assert args[3] == "Custom business description"


@pytest.mark.asyncio
async def test_discover_with_site_content_returns_empty_when_no_candidates_after_merge() -> None:
    client = AsyncMock()

    async def post_side_effect(url: str, **kwargs: Any) -> _FakeResponse:
        if url == "https://api.exa.ai/contents":
            return _FakeResponse(
                payload={"results": [{"text": "x" * 120, "summary": "Acme provides analytics software."}]}
            )
        raise AssertionError(f"Unexpected URL: {url}")

    client.post.side_effect = post_side_effect

    with (
        patch(
            "ai_visibility.ui.onboarding_state.os.getenv",
            side_effect=_env_map({"EXA_API_KEY": "exa-key", "TAVILY_API_KEY": "tavily-key"}),
        ),
        _patch_async_client(client),
        patch("ai_visibility.ui.onboarding_state._find_competitors_exa", new=AsyncMock(return_value=[])),
        patch("ai_visibility.ui.onboarding_state._find_competitors_tavily_gpt", new=AsyncMock(return_value=[])),
    ):
        result, site_content = await _discover_competitors_with_site_content("acme.com", "SaaS")

    assert result == []
    assert site_content == "x" * 120


@pytest.mark.asyncio
async def test_discover_with_site_content_returns_empty_when_validation_fails_all() -> None:
    client = AsyncMock()

    async def post_side_effect(url: str, **kwargs: Any) -> _FakeResponse:
        if url == "https://api.exa.ai/contents":
            return _FakeResponse(
                payload={"results": [{"text": "x" * 120, "summary": "Acme provides analytics software."}]}
            )
        raise AssertionError(f"Unexpected URL: {url}")

    client.post.side_effect = post_side_effect

    with (
        patch(
            "ai_visibility.ui.onboarding_state.os.getenv",
            side_effect=_env_map({"EXA_API_KEY": "exa-key", "TAVILY_API_KEY": "tavily-key"}),
        ),
        _patch_async_client(client),
        patch("ai_visibility.ui.onboarding_state._find_competitors_exa", new=AsyncMock(return_value=["A (a.com)"])),
        patch("ai_visibility.ui.onboarding_state._find_competitors_tavily_gpt", new=AsyncMock(return_value=[])),
        patch("ai_visibility.ui.onboarding_state._validate_domains", new=AsyncMock(return_value=[])),
        patch("ai_visibility.ui.onboarding_state._filter_direct_competitors", new=AsyncMock()) as flt,
    ):
        result, _ = await _discover_competitors_with_site_content("acme.com", "SaaS")

    assert result == []
    flt.assert_not_called()


@pytest.mark.asyncio
async def test_discover_with_site_content_returns_empty_when_filter_returns_empty() -> None:
    client = AsyncMock()

    async def post_side_effect(url: str, **kwargs: Any) -> _FakeResponse:
        if url == "https://api.exa.ai/contents":
            return _FakeResponse(
                payload={"results": [{"text": "x" * 120, "summary": "Acme provides analytics software."}]}
            )
        raise AssertionError(f"Unexpected URL: {url}")

    client.post.side_effect = post_side_effect

    with (
        patch(
            "ai_visibility.ui.onboarding_state.os.getenv",
            side_effect=_env_map({"EXA_API_KEY": "exa-key", "TAVILY_API_KEY": "tavily-key"}),
        ),
        _patch_async_client(client),
        patch("ai_visibility.ui.onboarding_state._find_competitors_exa", new=AsyncMock(return_value=["A (a.com)"])),
        patch("ai_visibility.ui.onboarding_state._find_competitors_tavily_gpt", new=AsyncMock(return_value=[])),
        patch("ai_visibility.ui.onboarding_state._validate_domains", new=AsyncMock(return_value=["A (a.com)"])),
        patch("ai_visibility.ui.onboarding_state._filter_direct_competitors", new=AsyncMock(return_value=[])),
    ):
        result, _ = await _discover_competitors_with_site_content("acme.com", "SaaS")

    assert result == []


@pytest.mark.asyncio
async def test_discover_with_site_content_handles_source_exception_and_keeps_other_source_results() -> None:
    client = AsyncMock()

    async def post_side_effect(url: str, **kwargs: Any) -> _FakeResponse:
        if url == "https://api.exa.ai/contents":
            return _FakeResponse(
                payload={"results": [{"text": "x" * 120, "summary": "Acme provides analytics software."}]}
            )
        raise AssertionError(f"Unexpected URL: {url}")

    client.post.side_effect = post_side_effect

    with (
        patch(
            "ai_visibility.ui.onboarding_state.os.getenv",
            side_effect=_env_map({"EXA_API_KEY": "exa-key", "TAVILY_API_KEY": "tavily-key"}),
        ),
        _patch_async_client(client),
        patch(
            "ai_visibility.ui.onboarding_state._find_competitors_exa",
            new=AsyncMock(side_effect=RuntimeError("exa fail")),
        ),
        patch(
            "ai_visibility.ui.onboarding_state._find_competitors_tavily_gpt", new=AsyncMock(return_value=["B (b.com)"])
        ),
        patch("ai_visibility.ui.onboarding_state._validate_domains", new=AsyncMock(return_value=["B (b.com)"])),
        patch(
            "ai_visibility.ui.onboarding_state._filter_direct_competitors", new=AsyncMock(return_value=["B (b.com)"])
        ),
    ):
        result, _ = await _discover_competitors_with_site_content("acme.com", "SaaS")

    assert result == ["B (b.com)"]


@pytest.mark.asyncio
async def test_discover_with_site_content_limits_output_to_five_competitors() -> None:
    client = AsyncMock()

    async def post_side_effect(url: str, **kwargs: Any) -> _FakeResponse:
        if url == "https://api.exa.ai/contents":
            return _FakeResponse(
                payload={"results": [{"text": "x" * 200, "summary": "Acme provides analytics software."}]}
            )
        raise AssertionError(f"Unexpected URL: {url}")

    client.post.side_effect = post_side_effect

    filtered = [
        "A (a.com)",
        "B (b.com)",
        "C (c.com)",
        "D (d.com)",
        "E (e.com)",
        "F (f.com)",
    ]

    with (
        patch(
            "ai_visibility.ui.onboarding_state.os.getenv",
            side_effect=_env_map({"EXA_API_KEY": "exa-key", "TAVILY_API_KEY": "tavily-key"}),
        ),
        _patch_async_client(client),
        patch("ai_visibility.ui.onboarding_state._find_competitors_exa", new=AsyncMock(return_value=filtered)),
        patch("ai_visibility.ui.onboarding_state._find_competitors_tavily_gpt", new=AsyncMock(return_value=[])),
        patch("ai_visibility.ui.onboarding_state._validate_domains", new=AsyncMock(return_value=filtered)),
        patch("ai_visibility.ui.onboarding_state._filter_direct_competitors", new=AsyncMock(return_value=filtered)),
    ):
        result, _ = await _discover_competitors_with_site_content("acme.com", "SaaS")

    assert result == filtered[:5]


@pytest.mark.asyncio
async def test_discover_with_site_content_all_sources_fail_uses_industry_fallback_description() -> None:
    client = AsyncMock()
    client.get.side_effect = RuntimeError("direct fetch failed")

    with (
        patch("ai_visibility.ui.onboarding_state.os.getenv", side_effect=_env_map({})),
        _patch_async_client(client),
        patch("ai_visibility.ui.onboarding_state._find_competitors_exa", new=AsyncMock(return_value=[])) as exa,
        patch(
            "ai_visibility.ui.onboarding_state._find_competitors_tavily_gpt", new=AsyncMock(return_value=[])
        ) as tavily,
    ):
        result, site_content = await _discover_competitors_with_site_content("acme.com", "Consulting")

    assert result == []
    assert site_content == ""
    exa.assert_awaited_once_with("acme.com", "Consulting", "")
    tavily.assert_awaited_once_with("acme.com", "Consulting", "")
