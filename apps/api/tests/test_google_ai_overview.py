from __future__ import annotations

import os
import re
from typing import Callable, cast

import pytest

from ai_visibility.providers.adapters.google_ai_overview import COUNTRY_LOCATION_CODES, GoogleAIOverviewAdapter
from ai_visibility.providers.config import LLMConfig, SUPPORTED_PROVIDERS
from ai_visibility.providers.gateway import ProviderError, ProviderGateway
from ai_visibility.runs.scan_strategy import ExecutionMode, ProviderConfig


def extract_response_text(response_json: object) -> str:
    extractor = cast(Callable[[object], str], getattr(GoogleAIOverviewAdapter, "_extract_response_text"))
    return extractor(response_json)


def build_google_ai_overview_provider_config() -> ProviderConfig:
    return ProviderConfig(
        provider="google_ai_overview",
        execution_mode=ExecutionMode.DIRECT,
        model_name="google-ai-overview",
        max_prompts=20,
        cost_ceiling_usd=1.0,
        retry_limit=1,
        enabled=True,
    )


def test_parser_extracts_markdown_from_ai_overview() -> None:
    mock_response = {
        "tasks": [
            {
                "result": [
                    {
                        "items": [
                            {
                                "type": "ai_overview",
                                "markdown": "## Best Services\nMaison Remodeling Group is top rated.",
                            }
                        ]
                    }
                ]
            }
        ]
    }
    result = extract_response_text(mock_response)
    assert "Maison Remodeling" in result


def test_parser_extracts_answer_field() -> None:
    mock_response = {"tasks": [{"result": [{"answer": "The best remodeling company is Maison."}]}]}
    result = extract_response_text(mock_response)
    assert "Maison" in result


def test_parser_falls_back_to_content_field() -> None:
    mock_response = {"tasks": [{"result": [{"items": [{"type": "text", "content": "Some content here."}]}]}]}
    result = extract_response_text(mock_response)
    assert "Some content" in result


def test_parser_raises_on_empty_response() -> None:
    mock_response: dict[str, object] = {"tasks": [{"result": [{"items": []}]}]}
    with pytest.raises(ProviderError):
        _ = extract_response_text(cast(object, mock_response))


def test_parser_raises_on_no_tasks() -> None:
    with pytest.raises(ProviderError):
        _ = extract_response_text({"tasks": []})


def test_parser_raises_on_malformed_response() -> None:
    with pytest.raises(ProviderError):
        _ = extract_response_text("not a dict")


def test_parser_combines_multiple_items() -> None:
    mock_response = {
        "tasks": [
            {
                "result": [
                    {
                        "items": [
                            {"type": "ai_overview", "markdown": "Part 1"},
                            {"type": "ai_overview", "markdown": "Part 2"},
                        ]
                    }
                ]
            }
        ]
    }
    result = extract_response_text(mock_response)
    assert "Part 1" in result
    assert "Part 2" in result


def test_parser_prefers_markdown_over_content() -> None:
    mock_response = {
        "tasks": [
            {
                "result": [
                    {
                        "items": [
                            {
                                "type": "ai_overview",
                                "markdown": "Markdown text",
                                "content": "Content text",
                            }
                        ]
                    }
                ]
            }
        ]
    }
    result = extract_response_text(mock_response)
    assert "Markdown text" in result


def test_us_location_code() -> None:
    assert COUNTRY_LOCATION_CODES["US"] == 2840


def test_uk_location_code() -> None:
    assert COUNTRY_LOCATION_CODES["GB"] == 2826


def test_common_countries_have_codes() -> None:
    for country in ["US", "GB", "CA", "AU", "DE", "FR", "IL", "IN", "JP"]:
        assert country in COUNTRY_LOCATION_CODES, f"Missing location code for {country}"


def test_strips_location_context_from_keyword() -> None:
    prompt = "What is the best maisonremodeling? Location context: The user is in Santa Clara, CA, US."
    if "Location context:" in prompt:
        clean = prompt[: prompt.index("Location context:")].strip()
    else:
        clean = prompt
    assert clean == "What is the best maisonremodeling?"
    assert "Location context" not in clean


def test_extracts_markdown_citations() -> None:
    citation_pattern = re.compile(r"\[([^\]]+)\]\((https?://[^\s)]+)\)")
    text = "Visit [Maison Remodeling](https://maisonremodeling.com) for details."
    matches = citation_pattern.findall(text)
    assert len(matches) == 1
    assert matches[0][0] == "Maison Remodeling"
    assert matches[0][1] == "https://maisonremodeling.com"


def test_no_citations_returns_empty() -> None:
    citation_pattern = re.compile(r"\[([^\]]+)\]\((https?://[^\s)]+)\)")
    text = "No links in this response."
    matches = citation_pattern.findall(text)
    assert len(matches) == 0


@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.skipif(not os.environ.get("RUN_SLOW_API_TESTS"), reason="Set RUN_SLOW_API_TESTS=1 to run live API tests")
async def test_google_ai_overview_real_api_call() -> None:
    adapter = GoogleAIOverviewAdapter()
    result = adapter.execute(
        "What is the best home remodeling company?",
        "test",
        build_google_ai_overview_provider_config(),
    )
    assert result.provider == "google_ai_overview"
    assert len(result.raw_response) > 100
    assert result.model_name == "google-ai-overview"


@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.skipif(not os.environ.get("RUN_SLOW_API_TESTS"), reason="Set RUN_SLOW_API_TESTS=1 to run live API tests")
async def test_google_ai_overview_mentions_known_brand() -> None:
    adapter = GoogleAIOverviewAdapter()
    result = adapter.execute(
        "What is maisonremodeling?",
        "maisonremodeling",
        build_google_ai_overview_provider_config(),
    )
    assert "maison" in result.raw_response.lower()


def test_google_ai_overview_in_supported_providers() -> None:
    assert "google_ai_overview" in SUPPORTED_PROVIDERS


def test_google_ai_overview_in_gateway_defaults() -> None:
    config = LLMConfig(provider="google_ai_overview")
    gateway = ProviderGateway(config=config)
    resolve_model = cast(Callable[[str], str], getattr(gateway, "_resolve_model"))
    model = resolve_model("google_ai_overview")
    assert model == "google-ai-overview"
