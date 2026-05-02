# pyright: reportMissingImports=false, reportMissingTypeStubs=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

import asyncio
import os
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

from pydantic import BaseModel

from .config import LLMConfig

if TYPE_CHECKING:
    from ai_visibility.runs.scan_strategy import ProviderConfig


class ProviderResponse(BaseModel):
    provider: str
    model: str
    content: str
    latency_ms: float
    token_count: int | None = None


class ProviderError(Exception):
    error_code: str

    def __init__(self, message: str, error_code: str):
        super().__init__(message)
        self.error_code = error_code


@dataclass
class LocationContext:
    city: str = ""
    region: str = ""
    country: str = ""

    @property
    def is_set(self) -> bool:
        return bool(self.city or self.region or self.country)

    def to_system_prompt(self) -> str:
        parts = [part for part in [self.city, self.region, self.country] if part]
        location_str = ", ".join(parts)
        return (
            f"The user is located in {location_str}. Provide locally relevant recommendations, "
            "mentioning local businesses and services when applicable."
        )

    def to_prompt_suffix(self) -> str:
        parts = [part for part in [self.city, self.region, self.country] if part]
        location_str = ", ".join(parts)
        return (
            f"\n\nLocation context: The user is in {location_str}. "
            "Tailor the response to local results and nearby options when relevant."
        )


class ProviderGateway:
    config: LLMConfig
    _google_ai_mode_serpapi_adapter: Any | None

    def __init__(self, config: LLMConfig | None = None):
        resolved_config = config or LLMConfig()
        env_provider = os.getenv("LLM_PROVIDER", "").strip().lower()
        if env_provider:
            resolved_config = resolved_config.model_copy(update={"provider": env_provider})
        self.config = resolved_config
        self._google_ai_mode_serpapi_adapter = None
        try:
            from ai_visibility.providers.adapters.google_ai_mode_serpapi import GoogleAIModeSerpAPIAdapter

            self._google_ai_mode_serpapi_adapter = GoogleAIModeSerpAPIAdapter()
        except Exception:
            self._google_ai_mode_serpapi_adapter = None

    def _check_api_key(self, provider: str) -> None:
        key_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "grok": "XAI_API_KEY",
            "perplexity": "PERPLEXITY_API_KEY",
            "google_ai_mode_serpapi": "SERPAPI_API_KEY",
        }
        env_var = key_map.get(provider)
        if env_var and not os.getenv(env_var):
            # Gemini also accepts GOOGLE_API_KEY
            if provider == "gemini" and os.getenv("GOOGLE_API_KEY"):
                return
            raise ProviderError(f"Missing API key: {env_var} not set", error_code="missing_api_key")

    @staticmethod
    def _extract_content(result: object) -> str:
        if isinstance(result, BaseModel):
            return result.model_dump_json()
        if isinstance(result, dict):
            return str(result)
        return str(result)

    @staticmethod
    def _extract_token_count(result: object) -> int | None:
        usage: object | None = getattr(result, "usage", None)
        if usage is None:
            return None
        total_tokens = getattr(usage, "total_tokens", None)
        if isinstance(total_tokens, int):
            return total_tokens
        if isinstance(usage, dict):
            token_value = usage.get("total_tokens")
            if isinstance(token_value, int):
                return token_value
        return None

    def _resolve_model(self, provider: str) -> str:
        if self.config.model:
            return self.config.model

        defaults = {
            "openai": "gpt-5.4",
            "anthropic": "claude-sonnet-4-6",
            "perplexity": "sonar-pro",
            "gemini": "gemini-3-flash-preview",
            "grok": "grok-4-1-fast-reasoning",
            "google_ai_overview": "google-ai-overview",
            "google_ai_mode_serpapi": "google-ai-mode-serpapi",
        }
        return defaults.get(provider, "default")

    @staticmethod
    def _apply_location_to_messages(
        messages: list[dict[str, str]],
        location: LocationContext | None,
    ) -> list[dict[str, str]]:
        if location is None or not location.is_set:
            return messages

        location_message = location.to_system_prompt()
        if not messages:
            return [{"role": "system", "content": location_message}]

        first_message = messages[0]
        if first_message.get("role") == "system":
            merged_system_message = {
                "role": "system",
                "content": f"{first_message.get('content', '')}\n\n{location_message}",
            }
            return [merged_system_message, *messages[1:]]

        return [{"role": "system", "content": location_message}, *messages]

    async def _execute_gemini_direct(
        self,
        prompt_text: str,
        system_message: str | None = None,
    ) -> ProviderResponse:
        """Fallback: call Gemini via google-genai SDK directly (bypasses mirascope aiohttp bug)."""
        start = time.monotonic()
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
        try:
            from google import genai  # type: ignore[import-not-found]

            client = genai.Client(api_key=api_key)
            model_name = self._resolve_model("gemini")
            rendered_prompt = prompt_text
            if system_message:
                rendered_prompt = f"{system_message}\n\n{prompt_text}"
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=model_name,
                contents=rendered_prompt,
            )
            latency_ms = (time.monotonic() - start) * 1000
            content = response.text or ""
            return ProviderResponse(
                provider="gemini",
                model=model_name,
                content=content,
                latency_ms=latency_ms,
                token_count=None,
            )
        except Exception as exc:
            raise ProviderError(str(exc), error_code="provider_error") from exc

    async def _execute_perplexity_direct(
        self,
        prompt_text: str,
        system_message: str | None = None,
        location: LocationContext | None = None,
    ) -> ProviderResponse:
        start = time.monotonic()
        api_key = os.getenv("PERPLEXITY_API_KEY", "")
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")

            messages: list[dict[str, str]] = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt_text})

            model_name = self._resolve_model("perplexity")
            kwargs: dict[str, Any] = {
                "model": model_name,
                "messages": messages,
            }

            if location and location.is_set:
                user_loc: dict[str, str] = {}
                if location.country:
                    user_loc["country"] = location.country
                if location.region:
                    user_loc["region"] = location.region
                if location.city:
                    user_loc["city"] = location.city
                kwargs["web_search_options"] = {"user_location": user_loc}

            create_completion = cast(Any, client.chat.completions.create)
            if "web_search_options" in kwargs:
                response = await asyncio.to_thread(
                    create_completion,
                    model=model_name,
                    messages=messages,
                    web_search_options=kwargs["web_search_options"],
                )
            else:
                response = await asyncio.to_thread(create_completion, model=model_name, messages=messages)
            latency_ms = (time.monotonic() - start) * 1000
            content = response.choices[0].message.content or ""
            return ProviderResponse(
                provider="perplexity",
                model=model_name,
                content=content,
                latency_ms=latency_ms,
                token_count=getattr(response.usage, "total_tokens", None) if response.usage else None,
            )
        except Exception as exc:
            raise ProviderError(str(exc), error_code="provider_error") from exc

    async def _execute_with_provider(
        self,
        provider: str,
        prompt_text: str,
        variables: dict[str, object] | None = None,
        output_schema: type[BaseModel] | None = None,
        system_message: str | None = None,
        location: LocationContext | None = None,
    ) -> ProviderResponse:
        _ = variables
        self._check_api_key(provider)
        start = time.monotonic()
        if provider == "perplexity":
            return await self._execute_perplexity_direct(
                prompt_text=prompt_text,
                system_message=system_message,
                location=location,
            )
        if provider == "google_ai_mode_serpapi":
            if self._google_ai_mode_serpapi_adapter is None:
                raise ProviderError(
                    "google_ai_mode_serpapi adapter is unavailable",
                    error_code="provider_error",
                )
            adapter_result = await self._google_ai_mode_serpapi_adapter.execute(
                prompt_text,
                "",
                location,
            )
            return ProviderResponse(
                provider="google_ai_mode_serpapi",
                model=self._resolve_model("google_ai_mode_serpapi"),
                content=adapter_result.raw_response,
                latency_ms=(time.monotonic() - start) * 1000,
                token_count=None,
            )

        from solaraai_llm import LLMOrchestrator  # type: ignore[import-not-found]

        model_name = self._resolve_model(provider)
        orchestrator = LLMOrchestrator(provider=provider, override_model=model_name)
        messages: list[dict[str, str]] = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt_text})

        web_search_options: dict[str, dict[str, str]] | None = None
        if provider in {"openai", "anthropic"} and location and location.is_set:
            user_loc: dict[str, str] = {}
            if location.country:
                user_loc["country"] = location.country
            if location.region:
                user_loc["region"] = location.region
            if location.city:
                user_loc["city"] = location.city
            web_search_options = {"user_location": user_loc}

        try:
            # LLMOrchestrator.generate() is async
            generate_call = cast(Any, orchestrator.generate)
            generate_kwargs: dict[str, object] = {
                "messages": messages,
                "response_model": output_schema,
            }
            if web_search_options is not None:
                generate_kwargs["web_search_options"] = web_search_options

            generate_request: Any
            try:
                generate_request = generate_call(**generate_kwargs)
            except TypeError as exc:
                error_message = str(exc)
                if "web_search_options" not in error_message:
                    raise
                fallback_messages = self._apply_location_to_messages(messages, location)
                generate_request = generate_call(
                    messages=fallback_messages,
                    response_model=output_schema,
                )
            result = await asyncio.wait_for(
                generate_request,
                timeout=self.config.timeout_seconds,
            )
            latency_ms = (time.monotonic() - start) * 1000
            return ProviderResponse(
                provider=provider,
                model=model_name,
                content=self._extract_content(result),
                latency_ms=latency_ms,
                token_count=self._extract_token_count(result),
            )
        except ProviderError:
            raise
        except asyncio.TimeoutError as exc:
            raise ProviderError(str(exc) or "Provider timeout", error_code="timeout") from exc
        except Exception as exc:
            # Gemini fallback: if mirascope/aiohttp crashes, use google-genai directly
            if provider == "gemini":
                return await self._execute_gemini_direct(prompt_text, system_message=system_message)
            raise ProviderError(str(exc), error_code="provider_error") from exc

    async def execute_prompt(
        self,
        prompt_text: str,
        variables: dict[str, object] | None = None,
        output_schema: type[BaseModel] | None = None,
        system_message: str | None = None,
        location: LocationContext | None = None,
    ) -> ProviderResponse:
        providers = [self.config.provider, *self.config.fallback_chain]
        last_error: ProviderError | None = None

        for provider in providers:
            try:
                return await self._execute_with_provider(
                    provider=provider,
                    prompt_text=prompt_text,
                    variables=variables,
                    output_schema=output_schema,
                    system_message=system_message,
                    location=location,
                )
            except ProviderError as exc:
                last_error = exc

        if last_error is None:
            raise ProviderError("No provider configured", error_code="provider_error")
        raise last_error
