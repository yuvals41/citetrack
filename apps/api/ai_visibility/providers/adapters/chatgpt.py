from __future__ import annotations

import os
import re
from typing import TYPE_CHECKING, cast

from typing_extensions import override

import requests

from ai_visibility.providers.gateway import ProviderError

from .base import AdapterResult, ScanAdapter

if TYPE_CHECKING:
    from ai_visibility.providers.gateway import LocationContext
    from ai_visibility.runs.scan_strategy import ProviderConfig

DATAFORSEO_URL = "https://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_responses/live"
AUTHORIZATION_HEADER = f"Basic {os.environ.get('DATAFORSEO_AUTH_HEADER', '')}"
REQUEST_TIMEOUT_SECONDS = 30
MAX_OUTPUT_TOKENS = 2048
CITATION_PATTERN = re.compile(r"\[([^\]]+)\]\((https?://[^\s)]+)\)")


class ChatGPTAdapter(ScanAdapter):
    @override
    def execute(
        self,
        prompt_text: str,
        workspace_slug: str,
        strategy_config: ProviderConfig,
        location: LocationContext | None = None,
    ) -> AdapterResult:
        _ = workspace_slug
        country_code = "US"
        if location and len(location.country.strip()) == 2:
            country_code = location.country.strip().upper()
        payload = {
            "data": [
                {
                    "user_prompt": prompt_text,
                    "model_name": strategy_config.model_name,
                    "web_search": True,
                    "web_search_country_iso_code": country_code,
                    "max_output_tokens": MAX_OUTPUT_TOKENS,
                    "use_reasoning": True,
                }
            ]
        }
        headers = {
            "Authorization": AUTHORIZATION_HEADER,
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                DATAFORSEO_URL,
                json=payload,
                headers=headers,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            response_json = cast(object, response.json())
            raw_response, reasoning = self._extract_response_payload(response_json)
        except ProviderError:
            raise
        except (KeyError, IndexError, TypeError, ValueError, requests.RequestException) as exc:
            raise ProviderError(f"ChatGPT DataForSEO request failed: {exc}", error_code="provider_error") from exc

        if not raw_response.strip():
            raise ProviderError("ChatGPT DataForSEO returned an empty response", error_code="provider_error")

        citations: list[dict[str, object]] = [
            {"text": match.group(1), "url": match.group(2)} for match in CITATION_PATTERN.finditer(raw_response)
        ]

        return AdapterResult(
            raw_response=raw_response,
            citations=citations,
            provider="chatgpt",
            model_name=strategy_config.model_name,
            model_version=strategy_config.model_name,
            strategy_version="v1",
            reasoning=reasoning,
        )

    @staticmethod
    def _extract_response_payload(response_json: object) -> tuple[str, str]:
        response_map = ChatGPTAdapter._expect_mapping(response_json)
        tasks = ChatGPTAdapter._expect_list(response_map.get("tasks"), field_name="tasks")
        first_task = ChatGPTAdapter._expect_mapping(tasks[0])
        results = ChatGPTAdapter._expect_list(first_task.get("result"), field_name="result")
        first_result = ChatGPTAdapter._expect_mapping(results[0])
        items = ChatGPTAdapter._expect_list(first_result.get("items"), field_name="items")
        first_item = ChatGPTAdapter._expect_mapping(items[0])
        reasoning_text = ""
        for item in items:
            item_map = ChatGPTAdapter._expect_mapping(item)
            if item_map.get("type") == "reasoning":
                content = item_map.get("content")
                if isinstance(content, str) and content.strip():
                    reasoning_text = content.strip()
                    break
        messages = ChatGPTAdapter._expect_list(first_item.get("messages"), field_name="messages")
        if not reasoning_text:
            for message in messages:
                message_map = ChatGPTAdapter._expect_mapping(message)
                if message_map.get("type") == "reasoning":
                    content = message_map.get("content")
                    if isinstance(content, str) and content.strip():
                        reasoning_text = content.strip()
                        break
        final_message = ChatGPTAdapter._expect_mapping(messages[-1])
        return ChatGPTAdapter._expect_string(final_message.get("content"), field_name="content"), reasoning_text

    @staticmethod
    def _expect_mapping(value: object) -> dict[str, object]:
        if not isinstance(value, dict):
            raise ProviderError("ChatGPT DataForSEO returned malformed response data", error_code="provider_error")
        return {str(key): item for key, item in cast(dict[object, object], value).items()}

    @staticmethod
    def _expect_list(value: object, *, field_name: str) -> list[object]:
        if not isinstance(value, list) or not value:
            raise ProviderError(
                f"ChatGPT DataForSEO returned malformed '{field_name}' data",
                error_code="provider_error",
            )
        return cast(list[object], value)

    @staticmethod
    def _expect_string(value: object, *, field_name: str) -> str:
        if not isinstance(value, str):
            raise ProviderError(
                f"ChatGPT DataForSEO returned non-string '{field_name}' data",
                error_code="provider_error",
            )
        return value
