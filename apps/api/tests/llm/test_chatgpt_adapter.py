from __future__ import annotations

from unittest.mock import patch
from typing import override

import pytest
import requests

from ai_visibility.providers.adapters.chatgpt import AUTHORIZATION_HEADER, ChatGPTAdapter
from ai_visibility.providers.gateway import ProviderError
from ai_visibility.runs.scan_strategy import ExecutionMode, ProviderConfig


class FakeResponse:
    payload: dict[str, object]
    http_error: Exception | None

    def __init__(self, payload: dict[str, object] | None = None, *, http_error: Exception | None = None) -> None:
        self.payload = payload or {}
        self.http_error = http_error

    def raise_for_status(self) -> None:
        if self.http_error is not None:
            raise self.http_error

    def json(self) -> dict[str, object]:
        return self.payload


class MalformedJsonResponse(FakeResponse):
    @override
    def json(self) -> dict[str, object]:
        raise ValueError("bad json")


def build_chatgpt_provider_config() -> ProviderConfig:
    return ProviderConfig(
        provider="chatgpt",
        execution_mode=ExecutionMode.HIGH_FIDELITY,
        model_name="gpt-5.4",
        max_prompts=20,
        cost_ceiling_usd=2.0,
        retry_limit=2,
        enabled=True,
    )


def build_chatgpt_response(content: str) -> dict[str, object]:
    return {
        "tasks": [
            {
                "result": [
                    {
                        "items": [
                            {
                                "messages": [
                                    {"content": "ignored"},
                                    {"content": content},
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }


def test_chatgpt_execute_returns_adapter_result_with_citations() -> None:
    adapter = ChatGPTAdapter()
    provider_config = build_chatgpt_provider_config()
    response_text = "Answer with [Source One](https://example.com/one) and [Source Two](https://example.com/two)."
    response_payload = build_chatgpt_response(response_text)

    with patch(
        "ai_visibility.providers.adapters.chatgpt.requests.post",
        return_value=FakeResponse(response_payload),
    ) as mock_post:
        result = adapter.execute("Where should I advertise?", "acme", provider_config)

    assert result.raw_response == response_text
    assert result.citations == [
        {"text": "Source One", "url": "https://example.com/one"},
        {"text": "Source Two", "url": "https://example.com/two"},
    ]
    assert result.provider == "chatgpt"
    assert result.model_name == "gpt-5.4"
    assert result.model_version == "gpt-5.4"
    assert result.strategy_version == "v1"
    mock_post.assert_called_once_with(
        "https://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_responses/live",
        json={
            "data": [
                {
                    "user_prompt": "Where should I advertise?",
                    "model_name": "gpt-5.4",
                    "web_search": True,
                    "web_search_country_iso_code": "US",
                    "max_output_tokens": 2048,
                    "use_reasoning": True,
                }
            ]
        },
        headers={
            "Authorization": AUTHORIZATION_HEADER,
            "Content-Type": "application/json",
        },
        timeout=30,
    )


def test_chatgpt_empty_response_raises_provider_error() -> None:
    adapter = ChatGPTAdapter()
    provider_config = build_chatgpt_provider_config()

    with patch(
        "ai_visibility.providers.adapters.chatgpt.requests.post",
        return_value=FakeResponse(build_chatgpt_response("   ")),
    ):
        with pytest.raises(ProviderError, match="empty response") as exc_info:
            _ = adapter.execute("prompt", "acme", provider_config)

    assert exc_info.value.error_code == "provider_error"


def test_chatgpt_http_error_raises_provider_error() -> None:
    adapter = ChatGPTAdapter()
    provider_config = build_chatgpt_provider_config()
    http_error = requests.HTTPError("500 Server Error")

    with patch(
        "ai_visibility.providers.adapters.chatgpt.requests.post",
        return_value=FakeResponse(http_error=http_error),
    ):
        with pytest.raises(ProviderError, match="request failed") as exc_info:
            _ = adapter.execute("prompt", "acme", provider_config)

    assert exc_info.value.error_code == "provider_error"


def test_chatgpt_malformed_json_raises_provider_error() -> None:
    adapter = ChatGPTAdapter()
    provider_config = build_chatgpt_provider_config()

    with patch(
        "ai_visibility.providers.adapters.chatgpt.requests.post",
        return_value=MalformedJsonResponse(),
    ):
        with pytest.raises(ProviderError, match="request failed") as exc_info:
            _ = adapter.execute("prompt", "acme", provider_config)

    assert exc_info.value.error_code == "provider_error"
