# pyright: reportAny=false, reportExplicitAny=false, reportUnknownMemberType=false, reportUnknownVariableType=false

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, override

import anthropic

from ai_visibility.providers.gateway import ProviderError

from .base import AdapterResult, ScanAdapter

if TYPE_CHECKING:
    from ai_visibility.providers.gateway import LocationContext
    from ai_visibility.runs.scan_strategy import ProviderConfig

MODEL_NAME = "claude-sonnet-4-6"
MAX_TOKENS = 8096
WEB_SEARCH_TOOL: dict[str, str] = {"type": "web_search_20260209", "name": "web_search"}


class ClaudeWebSearchAdapter(ScanAdapter):
    @override
    def execute(
        self,
        prompt_text: str,
        workspace_slug: str,
        strategy_config: ProviderConfig,
        location: LocationContext | None = None,
    ) -> AdapterResult:
        _ = workspace_slug, strategy_config
        client = anthropic.Anthropic()

        tools: list[dict[str, object]] = [cast(dict[str, object], WEB_SEARCH_TOOL.copy())]
        if location and location.is_set:
            user_location: dict[str, str] = {}
            if location.country:
                user_location["country"] = location.country
            if location.region:
                user_location["region"] = location.region
            if location.city:
                user_location["city"] = location.city
            tools[0]["user_location"] = user_location

        try:
            response = client.messages.create(
                model=MODEL_NAME,
                max_tokens=MAX_TOKENS,
                tools=cast(Any, tools),
                messages=[{"role": "user", "content": prompt_text}],
            )
        except anthropic.APIError as exc:
            raise ProviderError(f"Claude request failed: {exc}", error_code="provider_error") from exc

        blocks = self._as_list(getattr(response, "content", []))
        raw_response = "\n\n".join(self._extract_text_blocks(blocks))
        if not raw_response.strip():
            raise ProviderError("Claude returned no text content", error_code="provider_error")

        return AdapterResult(
            raw_response=raw_response,
            citations=self._extract_citations(blocks),
            provider="anthropic",
            model_name=MODEL_NAME,
            model_version=MODEL_NAME,
            strategy_version="v1",
        )

    @staticmethod
    def _extract_text_blocks(blocks: list[object]) -> list[str]:
        text_blocks: list[str] = []
        for block in blocks:
            if getattr(block, "type", None) != "text":
                continue
            text = getattr(block, "text", None)
            if isinstance(text, str):
                text_blocks.append(text)
        return text_blocks

    @classmethod
    def _extract_citations(cls, blocks: list[object]) -> list[dict[str, object]]:
        citations: list[dict[str, object]] = []
        for block in blocks:
            if getattr(block, "type", None) != "tool_result":
                continue
            for item in cls._as_list(getattr(block, "content", [])):
                url = cls._extract_url(item)
                if isinstance(url, str) and url:
                    citations.append({"url": url})
        return citations

    @staticmethod
    def _extract_url(item: object) -> str | None:
        url = getattr(item, "url", None)
        if isinstance(url, str):
            return url
        if isinstance(item, dict):
            raw_url = cast(object | None, item.get("url"))
            if isinstance(raw_url, str):
                return raw_url
        return None

    @staticmethod
    def _as_list(value: object) -> list[object]:
        if isinstance(value, list):
            return value
        if isinstance(value, tuple):
            return [*value]
        return []
