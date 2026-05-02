# pyright: reportArgumentType=false, reportCallIssue=false

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, cast

from typing_extensions import override

import openai

from ai_visibility.providers.gateway import ProviderError

from .base import AdapterResult, ScanAdapter

if TYPE_CHECKING:
    from ai_visibility.providers.gateway import LocationContext
    from ai_visibility.runs.scan_strategy import ProviderConfig

MODEL_NAME = "sonar-pro"
BASE_URL = "https://api.perplexity.ai"


class PerplexityAdapter(ScanAdapter):
    @override
    def execute(
        self,
        prompt_text: str,
        workspace_slug: str,
        strategy_config: ProviderConfig,
        location: LocationContext | None = None,
    ) -> AdapterResult:
        _ = workspace_slug, strategy_config
        client = openai.OpenAI(api_key=os.environ.get("PERPLEXITY_API_KEY", ""), base_url=BASE_URL)

        try:
            messages: list[dict[str, str]] = [{"role": "user", "content": prompt_text}]
            if location and location.is_set:
                user_location: dict[str, str] = {}
                if location.country:
                    user_location["country"] = location.country
                if location.region:
                    user_location["region"] = location.region
                if location.city:
                    user_location["city"] = location.city
                response = cast(Any, client.chat.completions.create)(
                    model=MODEL_NAME,
                    messages=messages,
                    stream=False,
                    web_search_options={"user_location": user_location},
                )
            else:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=cast(Any, messages),
                    stream=False,
                )
            raw_response = response.choices[0].message.content or ""
        except openai.OpenAIError as exc:
            raise ProviderError(f"Perplexity request failed: {exc}", error_code="provider_error") from exc
        except (AttributeError, IndexError, TypeError) as exc:
            raise ProviderError("Perplexity returned malformed response", error_code="provider_error") from exc

        if not raw_response.strip():
            raise ProviderError("Perplexity returned empty response", error_code="provider_error")

        citations = self._extract_citations(response)

        return AdapterResult(
            raw_response=raw_response,
            citations=citations,
            provider="perplexity",
            model_name=MODEL_NAME,
            model_version=MODEL_NAME,
            strategy_version="v1",
        )

    @staticmethod
    def _extract_citations(response: object) -> list[dict[str, object]]:
        raw_citations = getattr(response, "citations", [])
        if not isinstance(raw_citations, list):
            return []
        citation_list = cast(list[object], raw_citations)
        return [{"url": citation} for citation in citation_list if isinstance(citation, str) and citation]
