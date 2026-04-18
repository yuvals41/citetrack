# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

import sys
from types import ModuleType

import pytest  # type: ignore[import-not-found]
from pydantic import ValidationError

from ai_visibility.cli import doctor
from ai_visibility.providers import LLMConfig, LocationContext, ProviderError, ProviderGateway, ProviderResponse


def test_llm_config_valid() -> None:
    config = LLMConfig(provider="openai", model="gpt-4o-mini")
    assert config.provider == "openai"
    assert config.model == "gpt-4o-mini"


def test_llm_config_invalid_provider() -> None:
    with pytest.raises(ValidationError):
        _ = LLMConfig(provider="invalid", model="gpt-4o-mini")


def test_provider_gateway_instantiation() -> None:
    gateway = ProviderGateway(config=LLMConfig(provider="openai", model="gpt-4o-mini"))
    assert gateway is not None


def test_provider_response_fields() -> None:
    response = ProviderResponse(
        provider="openai",
        model="gpt-4o-mini",
        content="ok",
        latency_ms=12.3,
        token_count=17,
    )
    assert response.provider == "openai"
    assert response.model == "gpt-4o-mini"
    assert response.content == "ok"
    assert response.latency_ms == 12.3
    assert response.token_count == 17


def test_provider_error_has_error_code() -> None:
    err = ProviderError("boom", error_code="provider_error")
    assert err.error_code == "provider_error"


def test_location_context_system_prompt() -> None:
    location = LocationContext(city="Austin", region="TX", country="US")

    assert location.is_set is True
    assert (
        location.to_system_prompt()
        == "The user is located in Austin, TX, US. Provide locally relevant recommendations, mentioning local businesses and services when applicable."
    )


def test_gateway_default_models_for_openai_and_anthropic() -> None:
    openai_gateway = ProviderGateway(config=LLMConfig(provider="openai", model=None))
    anthropic_gateway = ProviderGateway(config=LLMConfig(provider="anthropic", model=None))

    assert getattr(openai_gateway, "_resolve_model")("openai") == "gpt-5.4"
    assert getattr(anthropic_gateway, "_resolve_model")("anthropic") == "claude-sonnet-4-6"


@pytest.mark.asyncio
async def test_gateway_execute_prompt_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, object]] = []

    class FakeOrchestrator:
        def __init__(self, provider: str, override_model: str | None = None, **kwargs: object) -> None:
            _ = kwargs
            calls.append({"provider": provider, "model": override_model})

        async def generate(
            self,
            messages: list[dict[str, str]] | None = None,
            response_model: type | None = None,
            **kwargs: object,
        ) -> str:
            _ = response_model
            _ = kwargs
            prompt_text = messages[0]["content"] if messages else ""
            return f"generated:{prompt_text}"

    fake_module = ModuleType("solaraai_llm")
    setattr(fake_module, "LLMOrchestrator", FakeOrchestrator)
    monkeypatch.setitem(sys.modules, "solaraai_llm", fake_module)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    gateway = ProviderGateway(config=LLMConfig(provider="openai", model="gpt-4o-mini"))
    result = await gateway.execute_prompt("hello", variables={"x": 1}, output_schema=None)

    assert isinstance(result, ProviderResponse)
    assert result.provider == "openai"
    assert result.model == "gpt-4o-mini"
    assert "generated:hello" in result.content
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_missing_api_key_raises_provider_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    gateway = ProviderGateway(config=LLMConfig(provider="openai", model="gpt-4o-mini"))

    with pytest.raises(ProviderError) as exc_info:
        _ = await gateway.execute_prompt("hello")

    assert exc_info.value.error_code == "missing_api_key"


@pytest.mark.asyncio
async def test_fallback_chain_tries_next_provider_on_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    providers_seen: list[str] = []

    class FakeOrchestrator:
        provider: str

        def __init__(self, provider: str, override_model: str | None = None, **kwargs: object) -> None:
            _ = override_model
            _ = kwargs
            self.provider = provider

        async def generate(
            self,
            messages: list[dict[str, str]] | None = None,
            response_model: type | None = None,
            **kwargs: object,
        ) -> str:
            _ = response_model
            _ = kwargs
            _ = messages
            providers_seen.append(self.provider)
            if self.provider == "openai":
                raise RuntimeError("openai down")
            return "anthropic-success"

    fake_module = ModuleType("solaraai_llm")
    setattr(fake_module, "LLMOrchestrator", FakeOrchestrator)
    monkeypatch.setitem(sys.modules, "solaraai_llm", fake_module)
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-key")

    gateway = ProviderGateway(config=LLMConfig(provider="openai", model="gpt-4o-mini", fallback_chain=["anthropic"]))
    result = await gateway.execute_prompt("hello")

    assert result.provider == "anthropic"
    assert providers_seen == ["openai", "anthropic"]


@pytest.mark.asyncio
async def test_perplexity_provider_uses_direct_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PERPLEXITY_API_KEY", "test-key")

    async def fake_perplexity(
        self: ProviderGateway,
        prompt_text: str,
        system_message: str | None = None,
        location: LocationContext | None = None,
    ) -> ProviderResponse:
        _ = self
        _ = location
        return ProviderResponse(
            provider="perplexity",
            model="sonar-pro",
            content=f"direct:{system_message}:{prompt_text}",
            latency_ms=1.0,
        )

    monkeypatch.setattr(ProviderGateway, "_execute_perplexity_direct", fake_perplexity)

    gateway = ProviderGateway(config=LLMConfig(provider="perplexity", model=None))
    result = await gateway.execute_prompt(
        "hello",
        system_message="system",
        location=LocationContext(city="Austin", region="TX", country="US"),
    )

    assert result.provider == "perplexity"
    assert result.model == "sonar-pro"
    assert result.content == "direct:system:hello"


@pytest.mark.asyncio
async def test_openai_search_model_forwards_location(monkeypatch: pytest.MonkeyPatch) -> None:
    observed_kwargs: dict[str, object] = {}

    class FakeOrchestrator:
        def __init__(self, provider: str, override_model: str | None = None, **kwargs: object) -> None:
            _ = provider
            _ = override_model
            _ = kwargs

        async def generate(
            self,
            messages: list[dict[str, str]] | None = None,
            response_model: type | None = None,
            **kwargs: object,
        ) -> str:
            _ = response_model
            _ = messages
            observed_kwargs.update(kwargs)
            return "ok"

    fake_module = ModuleType("solaraai_llm")
    setattr(fake_module, "LLMOrchestrator", FakeOrchestrator)
    monkeypatch.setitem(sys.modules, "solaraai_llm", fake_module)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    gateway = ProviderGateway(config=LLMConfig(provider="openai", model="gpt-4o-search-preview"))
    _ = await gateway.execute_prompt(
        "hello",
        system_message="system",
        location=LocationContext(city="Austin", region="TX", country="US"),
    )

    assert observed_kwargs["web_search_options"] == {
        "user_location": {"country": "US", "region": "TX", "city": "Austin"}
    }


@pytest.mark.asyncio
async def test_openai_location_falls_back_to_system_message_when_web_search_not_supported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed_messages: list[dict[str, str]] = []

    class FakeOrchestrator:
        def __init__(self, provider: str, override_model: str | None = None, **kwargs: object) -> None:
            _ = provider
            _ = override_model
            _ = kwargs

        async def generate(
            self,
            messages: list[dict[str, str]] | None = None,
            response_model: type | None = None,
        ) -> str:
            _ = response_model
            if messages:
                observed_messages.extend(messages)
            return "ok"

    fake_module = ModuleType("solaraai_llm")
    setattr(fake_module, "LLMOrchestrator", FakeOrchestrator)
    monkeypatch.setitem(sys.modules, "solaraai_llm", fake_module)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    gateway = ProviderGateway(config=LLMConfig(provider="openai", model="gpt-4o-search-preview"))
    _ = await gateway.execute_prompt(
        "hello",
        location=LocationContext(city="Austin", region="TX", country="US"),
    )

    assert observed_messages[0]["role"] == "system"
    assert "Austin, TX, US" in observed_messages[0]["content"]
    assert observed_messages[1] == {"role": "user", "content": "hello"}


@pytest.mark.asyncio
async def test_system_message_is_prepended_to_messages(monkeypatch: pytest.MonkeyPatch) -> None:
    observed_messages: list[dict[str, str]] = []

    class FakeOrchestrator:
        def __init__(self, provider: str, override_model: str | None = None, **kwargs: object) -> None:
            _ = provider
            _ = override_model
            _ = kwargs

        async def generate(
            self,
            messages: list[dict[str, str]] | None = None,
            response_model: type | None = None,
            **kwargs: object,
        ) -> str:
            _ = response_model
            _ = kwargs
            if messages:
                observed_messages.extend(messages)
            return "ok"

    fake_module = ModuleType("solaraai_llm")
    setattr(fake_module, "LLMOrchestrator", FakeOrchestrator)
    monkeypatch.setitem(sys.modules, "solaraai_llm", fake_module)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    gateway = ProviderGateway(config=LLMConfig(provider="openai", model="gpt-5.4"))
    _ = await gateway.execute_prompt("hello", system_message="system prompt")

    assert observed_messages[0] == {"role": "system", "content": "system prompt"}
    assert observed_messages[1] == {"role": "user", "content": "hello"}


def test_doctor_reports_llm_section() -> None:
    result = doctor(format="json")
    assert result["llm_framework"] == "solaraai-llm"
    assert "providers" in result
    assert "available" in result["providers"]
