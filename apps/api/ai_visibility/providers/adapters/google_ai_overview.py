from __future__ import annotations

import os
import re
from typing import TYPE_CHECKING, cast, override

import requests

from ai_visibility.providers.gateway import ProviderError

from .base import AdapterResult, ScanAdapter

if TYPE_CHECKING:
    from ai_visibility.providers.gateway import LocationContext
    from ai_visibility.runs.scan_strategy import ProviderConfig

DATAFORSEO_URL = "https://api.dataforseo.com/v3/serp/google/ai_mode/live/advanced"
AUTHORIZATION_HEADER = f"Basic {os.environ.get('DATAFORSEO_AUTH_HEADER', '')}"
REQUEST_TIMEOUT_SECONDS = 45
CITATION_PATTERN = re.compile(r"\[([^\]]+)\]\((https?://[^\s)]+)\)")

COUNTRY_LOCATION_CODES = {
    "US": 2840,
    "GB": 2826,
    "CA": 2124,
    "AU": 2036,
    "DE": 2276,
    "FR": 2250,
    "IL": 2376,
    "IN": 2356,
    "BR": 2076,
    "MX": 2484,
    "ES": 2724,
    "IT": 2380,
    "NL": 2528,
    "SE": 2752,
    "JP": 2392,
    "KR": 2410,
    "ZA": 2710,
    "AE": 2784,
    "SG": 2702,
    "IE": 2372,
    "NZ": 2554,
    "PT": 2620,
    "PL": 2616,
    "AT": 2040,
    "CH": 2756,
    "BE": 2056,
    "DK": 2208,
    "FI": 2246,
    "NO": 2578,
    "CZ": 2203,
}


class GoogleAIOverviewAdapter(ScanAdapter):
    @override
    def execute(
        self,
        prompt_text: str,
        workspace_slug: str,
        strategy_config: ProviderConfig,
        location: LocationContext | None = None,
    ) -> AdapterResult:
        _ = workspace_slug
        _ = strategy_config

        location_code = 2840
        if location and location.country:
            country_upper = location.country.strip().upper()
            location_code = COUNTRY_LOCATION_CODES.get(country_upper, 2840)

        keyword = prompt_text
        if "Location context:" in keyword:
            keyword = keyword[: keyword.index("Location context:")].strip()

        payload = [
            {
                "keyword": keyword,
                "language_code": "en",
                "location_code": location_code,
            }
        ]
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
            raw_response = self._extract_response_text(response_json)
        except ProviderError:
            raise
        except (KeyError, IndexError, TypeError, ValueError, requests.RequestException) as exc:
            raise ProviderError(f"Google AI Overview request failed: {exc}", error_code="provider_error") from exc

        if not raw_response.strip():
            raise ProviderError("Google AI Overview returned an empty response", error_code="provider_error")

        citations: list[dict[str, object]] = [
            {"text": match.group(1), "url": match.group(2)} for match in CITATION_PATTERN.finditer(raw_response)
        ]

        return AdapterResult(
            raw_response=raw_response,
            citations=citations,
            provider="google_ai_overview",
            model_name="google-ai-overview",
            model_version="v1",
            strategy_version="v1",
        )

    @staticmethod
    def _extract_response_text(response_json: object) -> str:
        if not isinstance(response_json, dict):
            raise ProviderError("Google AI Overview returned malformed response", error_code="provider_error")

        tasks = response_json.get("tasks", [])
        if not isinstance(tasks, list) or not tasks:
            raise ProviderError("Google AI Overview returned no tasks", error_code="provider_error")

        first_task = tasks[0]
        if not isinstance(first_task, dict):
            raise ProviderError("Google AI Overview returned malformed task", error_code="provider_error")

        results = first_task.get("result", [])
        if not isinstance(results, list) or not results:
            raise ProviderError("Google AI Overview returned no results", error_code="provider_error")

        text_parts: list[str] = []
        for result in results:
            if not isinstance(result, dict):
                continue

            answer = result.get("answer")
            if isinstance(answer, str) and answer.strip():
                text_parts.append(answer)

            items = result.get("items")
            if isinstance(items, list):
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    markdown = item.get("markdown")
                    if isinstance(markdown, str) and markdown.strip():
                        text_parts.append(markdown)
                        continue
                    content = item.get("content") or item.get("text") or item.get("description")
                    if isinstance(content, str) and content.strip():
                        text_parts.append(content)

        if not text_parts:
            raise ProviderError("Google AI Overview returned no text content", error_code="provider_error")

        return "\n\n".join(text_parts)
