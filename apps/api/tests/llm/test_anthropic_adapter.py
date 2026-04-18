# pyright: reportAny=false

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import anthropic
import httpx
import pytest

from ai_visibility.providers.adapters.claude import ClaudeWebSearchAdapter
from ai_visibility.providers.gateway import ProviderError
from ai_visibility.runs.scan_strategy import ExecutionMode, ProviderConfig


def build_anthropic_provider_config() -> ProviderConfig:
    return ProviderConfig(
        provider="anthropic",
        execution_mode=ExecutionMode.WEB_SEARCH,
        model_name="claude-sonnet-4-6",
        max_prompts=20,
        cost_ceiling_usd=2.0,
        retry_limit=2,
        enabled=True,
    )


def build_anthropic_response(*blocks: object) -> SimpleNamespace:
    return SimpleNamespace(content=list(blocks))


def build_anthropic_text_block(text: str) -> SimpleNamespace:
    return SimpleNamespace(type="text", text=text)


def build_anthropic_tool_result_block(*items: object) -> SimpleNamespace:
    return SimpleNamespace(type="tool_result", content=list(items))


def test_anthropic_execute_returns_adapter_result_with_citations() -> None:
    adapter = ClaudeWebSearchAdapter()
    provider_config = build_anthropic_provider_config()
    response = build_anthropic_response(
        build_anthropic_text_block("First answer paragraph."),
        SimpleNamespace(type="tool_use", name="web_search"),
        build_anthropic_tool_result_block(
            SimpleNamespace(url="https://example.com/one"),
            {"url": "https://example.com/two"},
        ),
        build_anthropic_text_block("Second answer paragraph."),
    )
    mock_client = MagicMock()
    mock_client.messages.create.return_value = response

    with patch("ai_visibility.providers.adapters.claude.anthropic.Anthropic", return_value=mock_client) as mock_factory:
        result = adapter.execute("Where should I advertise?", "acme", provider_config)

    assert result.raw_response == "First answer paragraph.\n\nSecond answer paragraph."
    assert result.citations == [
        {"url": "https://example.com/one"},
        {"url": "https://example.com/two"},
    ]
    assert result.provider == "anthropic"
    assert result.model_name == "claude-sonnet-4-6"
    assert result.model_version == "claude-sonnet-4-6"
    assert result.strategy_version == "v1"
    mock_factory.assert_called_once_with()
    mock_client.messages.create.assert_called_once_with(
        model="claude-sonnet-4-6",
        max_tokens=8096,
        tools=[{"type": "web_search_20260209", "name": "web_search"}],
        messages=[{"role": "user", "content": "Where should I advertise?"}],
    )


def test_anthropic_no_text_content_raises_provider_error() -> None:
    adapter = ClaudeWebSearchAdapter()
    provider_config = build_anthropic_provider_config()
    response = build_anthropic_response(
        build_anthropic_tool_result_block(SimpleNamespace(url="https://example.com/one")),
        build_anthropic_text_block("   "),
    )
    mock_client = MagicMock()
    mock_client.messages.create.return_value = response

    with patch("ai_visibility.providers.adapters.claude.anthropic.Anthropic", return_value=mock_client):
        with pytest.raises(ProviderError, match="Claude returned no text content") as exc_info:
            _ = adapter.execute("prompt", "acme", provider_config)

    assert exc_info.value.error_code == "provider_error"


def test_anthropic_api_error_raises_provider_error() -> None:
    adapter = ClaudeWebSearchAdapter()
    provider_config = build_anthropic_provider_config()
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = anthropic.APIError(
        "anthropic failed",
        request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"),
        body=None,
    )

    with patch("ai_visibility.providers.adapters.claude.anthropic.Anthropic", return_value=mock_client):
        with pytest.raises(ProviderError, match="Claude request failed") as exc_info:
            _ = adapter.execute("prompt", "acme", provider_config)

    assert exc_info.value.error_code == "provider_error"


def test_anthropic_web_search_without_urls_returns_empty_citations() -> None:
    adapter = ClaudeWebSearchAdapter()
    provider_config = build_anthropic_provider_config()
    response = build_anthropic_response(
        build_anthropic_tool_result_block(
            SimpleNamespace(title="Source without url"),
            {"title": "Still no url"},
        ),
        build_anthropic_text_block("Answer without citation urls."),
    )
    mock_client = MagicMock()
    mock_client.messages.create.return_value = response

    with patch("ai_visibility.providers.adapters.claude.anthropic.Anthropic", return_value=mock_client):
        result = adapter.execute("prompt", "acme", provider_config)

    assert result.raw_response == "Answer without citation urls."
    assert result.citations == []
