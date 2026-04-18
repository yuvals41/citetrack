from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import httpx
import openai
import pytest

from ai_visibility.providers.adapters.perplexity import PerplexityAdapter
from ai_visibility.providers.gateway import ProviderError
from ai_visibility.runs.scan_strategy import ExecutionMode, ProviderConfig


class FakeCreateCompletion:
    result: object | None
    side_effect: Exception | None
    calls: list[dict[str, object]]

    def __init__(self, result: object | None = None, *, side_effect: Exception | None = None) -> None:
        self.result = result
        self.side_effect = side_effect
        self.calls = []

    def __call__(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        if self.side_effect is not None:
            raise self.side_effect
        return self.result


class FakePerplexityClient:
    chat: SimpleNamespace

    def __init__(self, create_completion: FakeCreateCompletion) -> None:
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=create_completion))


def build_perplexity_provider_config() -> ProviderConfig:
    return ProviderConfig(
        provider="perplexity",
        execution_mode=ExecutionMode.DIRECT,
        model_name="sonar-pro",
        max_prompts=20,
        cost_ceiling_usd=1.0,
        retry_limit=1,
        enabled=True,
    )


def build_perplexity_response(content: str, *, citations: list[str] | None = None) -> SimpleNamespace:
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
    )
    if citations is not None:
        response.citations = citations
    return response


def test_perplexity_execute_returns_adapter_result_with_citations() -> None:
    adapter = PerplexityAdapter()
    provider_config = build_perplexity_provider_config()
    create_completion = FakeCreateCompletion(
        build_perplexity_response(
            "Perplexity answer",
            citations=["https://example.com/one", "https://example.com/two"],
        )
    )
    mock_client = FakePerplexityClient(create_completion)
    factory_calls: list[dict[str, object]] = []

    def build_client(**kwargs: object) -> FakePerplexityClient:
        factory_calls.append(kwargs)
        return mock_client

    with patch.dict("os.environ", {"PERPLEXITY_API_KEY": "test-key"}, clear=False):
        with patch("ai_visibility.providers.adapters.perplexity.openai.OpenAI", side_effect=build_client):
            result = adapter.execute("Where should I advertise?", "acme", provider_config)

    assert result.raw_response == "Perplexity answer"
    assert result.citations == [
        {"url": "https://example.com/one"},
        {"url": "https://example.com/two"},
    ]
    assert result.provider == "perplexity"
    assert result.model_name == "sonar-pro"
    assert result.model_version == "sonar-pro"
    assert result.strategy_version == "v1"
    assert factory_calls == [{"api_key": "test-key", "base_url": "https://api.perplexity.ai"}]
    assert create_completion.calls == [
        {
            "model": "sonar-pro",
            "messages": [{"role": "user", "content": "Where should I advertise?"}],
            "stream": False,
        }
    ]


def test_perplexity_empty_response_raises_provider_error() -> None:
    adapter = PerplexityAdapter()
    provider_config = build_perplexity_provider_config()
    mock_client = FakePerplexityClient(FakeCreateCompletion(build_perplexity_response("   ")))

    with patch("ai_visibility.providers.adapters.perplexity.openai.OpenAI", return_value=mock_client):
        with pytest.raises(ProviderError, match="Perplexity returned empty response") as exc_info:
            _ = adapter.execute("prompt", "acme", provider_config)

    assert exc_info.value.error_code == "provider_error"


def test_perplexity_api_error_raises_provider_error() -> None:
    adapter = PerplexityAdapter()
    provider_config = build_perplexity_provider_config()
    mock_client = FakePerplexityClient(
        FakeCreateCompletion(
            side_effect=openai.APIError(
                "perplexity failed",
                request=httpx.Request("POST", "https://api.perplexity.ai/chat/completions"),
                body=None,
            )
        )
    )

    with patch("ai_visibility.providers.adapters.perplexity.openai.OpenAI", return_value=mock_client):
        with pytest.raises(ProviderError, match="Perplexity request failed") as exc_info:
            _ = adapter.execute("prompt", "acme", provider_config)

    assert exc_info.value.error_code == "provider_error"


def test_perplexity_without_citations_returns_empty_list() -> None:
    adapter = PerplexityAdapter()
    provider_config = build_perplexity_provider_config()
    mock_client = FakePerplexityClient(FakeCreateCompletion(build_perplexity_response("Answer without citations")))

    with patch("ai_visibility.providers.adapters.perplexity.openai.OpenAI", return_value=mock_client):
        result = adapter.execute("prompt", "acme", provider_config)

    assert result.raw_response == "Answer without citations"
    assert result.citations == []
