from __future__ import annotations

# pyright: reportIncompatibleMethodOverride=false, reportImplicitOverride=false, reportAny=false, reportExplicitAny=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false, reportOperatorIssue=false, reportArgumentType=false

import logging
import os
from typing import TYPE_CHECKING, Any

import httpx

from ai_visibility.providers.gateway import ProviderError

from .base import AdapterResult, ScanAdapter

if TYPE_CHECKING:
    from ai_visibility.providers.gateway import LocationContext

SERPAPI_URL = "https://serpapi.com/search"
REQUEST_TIMEOUT_SECONDS = 45.0
LOG_PREFIX = "[serpapi-ai-mode]"

logger = logging.getLogger(__name__)


class GoogleAIModeSerpAPIAdapter(ScanAdapter):
    def __init__(self) -> None:
        self._last_subsequent_request_token: str | None = None

    async def execute(
        self,
        prompt: str,
        brand: str,
        location: LocationContext | None = None,
    ) -> AdapterResult:
        response_json = await self._request(query=prompt, location=location, subsequent_request_token=None)
        parsed = self._parse_response(response_json)
        self._last_subsequent_request_token = parsed["subsequent_request_token"]

        brand_info = self.extract_brand_mentions(parsed["response_text"], parsed["references"], brand)
        citations = list(parsed["references"])
        citations.extend(parsed["shopping_results"])
        citations.extend(parsed["local_results"])

        if not parsed["response_text"].strip():
            raise ProviderError("Google AI Mode SerpAPI returned an empty response", error_code="provider_error")

        return AdapterResult(
            raw_response=parsed["response_text"],
            citations=citations,
            provider="google_ai_mode_serpapi",
            model_name="google-ai-mode",
            model_version="serpapi-v1",
            strategy_version="v1",
            reasoning=(
                f"mentioned_in_answer={brand_info['mentioned_in_answer']}; "
                f"citation_count={brand_info['citation_count']}; "
                f"position_estimate={brand_info['position_estimate']}"
            ),
        )

    async def execute_conversation(
        self,
        questions: list[str],
        brand: str,
        location: LocationContext | None = None,
    ) -> list[dict[str, object]]:
        turn_results: list[dict[str, object]] = []
        subsequent_request_token: str | None = None

        for idx, question in enumerate(questions, start=1):
            response_json = await self._request(
                query=question,
                location=location,
                subsequent_request_token=subsequent_request_token,
            )
            parsed = self._parse_response(response_json)
            subsequent_request_token = parsed["subsequent_request_token"]
            self._last_subsequent_request_token = subsequent_request_token

            brand_info = self.extract_brand_mentions(parsed["response_text"], parsed["references"], brand)

            turn_results.append(
                {
                    "turn": idx,
                    "query": question,
                    "response_text": parsed["response_text"],
                    "references": parsed["references"],
                    "brand_mentioned": bool(brand_info["mentioned_in_answer"] or brand_info["citation_count"] > 0),
                    "citation_count": int(brand_info["citation_count"]),
                    "has_shopping": bool(parsed["shopping_results"]),
                    "has_local": bool(parsed["local_results"]),
                }
            )

        return turn_results

    def extract_brand_mentions(
        self, response_text: str, references: list[dict[str, object]], brand: str
    ) -> dict[str, object]:
        brand_term = brand.strip().lower()
        mentioned_in_answer = bool(brand_term and brand_term in response_text.lower())

        citation_count = 0
        if brand_term:
            for reference in references:
                searchable = " ".join(
                    str(reference.get(key, "")) for key in ("title", "link", "snippet", "source")
                ).lower()
                if brand_term in searchable:
                    citation_count += 1

        position_estimate = 5
        if mentioned_in_answer:
            mention_index = response_text.lower().find(brand_term)
            if mention_index <= 0:
                position_estimate = 1
            else:
                normalized = mention_index / max(len(response_text), 1)
                position_estimate = max(1, min(5, int(normalized * 5) + 1))
        elif citation_count > 0:
            position_estimate = 4

        return {
            "mentioned_in_answer": mentioned_in_answer,
            "citation_count": citation_count,
            "position_estimate": position_estimate,
        }

    async def _request(
        self,
        query: str,
        location: LocationContext | None,
        subsequent_request_token: str | None,
    ) -> dict[str, Any]:
        api_key = os.getenv("SERPAPI_API_KEY", "").strip()
        if not api_key:
            raise ProviderError("SERPAPI_API_KEY is not set", error_code="missing_api_key")

        params: dict[str, str] = {
            "q": query,
            "api_key": api_key,
            "engine": "google_ai_mode",
            "hl": "en",
            "no_cache": "true",
        }

        country = (location.country if location else "").strip().lower()
        if len(country) == 2:
            params["gl"] = country

        if subsequent_request_token:
            params["subsequent_request_token"] = subsequent_request_token

        logger.info("%s request q=%s gl=%s", LOG_PREFIX, query, params.get("gl", ""))

        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
                response = await client.get(SERPAPI_URL, params=params)
        except httpx.HTTPError as exc:
            raise ProviderError(f"SerpAPI request failed: {exc}", error_code="provider_error") from exc

        if response.status_code == 429:
            logger.warning("%s rate limited by SerpAPI", LOG_PREFIX)
            raise ProviderError("SerpAPI rate limit exceeded", error_code="provider_error")

        try:
            response_json = response.json()
        except ValueError as exc:
            raise ProviderError("SerpAPI returned non-JSON response", error_code="provider_error") from exc

        if response.status_code >= 400:
            error_message = "unknown error"
            if isinstance(response_json, dict):
                error_message = str(response_json.get("error") or response_json.get("message") or error_message)
            raise ProviderError(f"SerpAPI request failed: {error_message}", error_code="provider_error")

        if not isinstance(response_json, dict):
            raise ProviderError("SerpAPI returned malformed response", error_code="provider_error")

        if "error" in response_json:
            raise ProviderError(f"SerpAPI API error: {response_json['error']}", error_code="provider_error")

        return response_json

    @staticmethod
    def _parse_response(response_json: dict[str, Any]) -> dict[str, Any]:
        response_text = str(response_json.get("reconstructed_markdown") or "").strip()

        references_raw = response_json.get("references")
        references: list[dict[str, object]] = []
        if isinstance(references_raw, list):
            for item in references_raw:
                if not isinstance(item, dict):
                    continue
                references.append(
                    {
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                        "source": item.get("source", ""),
                    }
                )

        shopping_results = GoogleAIModeSerpAPIAdapter._normalize_result_items(
            response_json.get("shopping_results"), item_type="shopping_result"
        )
        local_results = GoogleAIModeSerpAPIAdapter._normalize_result_items(
            response_json.get("local_results"), item_type="local_result"
        )

        return {
            "response_text": response_text,
            "references": references,
            "subsequent_request_token": response_json.get("subsequent_request_token"),
            "shopping_results": shopping_results,
            "local_results": local_results,
        }

    @staticmethod
    def _normalize_result_items(raw_items: Any, *, item_type: str) -> list[dict[str, object]]:
        normalized: list[dict[str, object]] = []
        if not isinstance(raw_items, list):
            return normalized

        for item in raw_items:
            if not isinstance(item, dict):
                continue
            normalized.append(
                {
                    "type": item_type,
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "source": item.get("source", ""),
                }
            )
        return normalized
