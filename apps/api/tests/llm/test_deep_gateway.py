import asyncio
import sys
from types import ModuleType

import pytest
from pydantic import ValidationError

from ai_visibility.providers.config import LLMConfig
from ai_visibility.providers.gateway import LocationContext, ProviderError, ProviderGateway, ProviderResponse


@pytest.mark.parametrize("provider", ["openai", "anthropic", "gemini", "grok", "perplexity"])
def test_llm_config_accepts_all_supported_providers(provider: str) -> None:
    config = LLMConfig(provider=provider, model="test-model")
    assert config.provider == provider
    assert config.model == "test-model"


def test_llm_config_invalid_provider_raises_validation_error() -> None:
    with pytest.raises(ValidationError):
        _ = LLMConfig(provider="invalid-provider")


def test_llm_config_supports_multiple_provider_names_and_aliases() -> None:
    config = LLMConfig(provider="xai", fallback_chain=["OpenAI", "ANTHROPIC", "perplexity"])
    assert config.provider == "grok"
    assert config.fallback_chain == ["openai", "anthropic", "perplexity"]


@pytest.mark.asyncio
async def test_execute_prompt_missing_api_key_raises_expected_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    gateway = ProviderGateway(config=LLMConfig(provider="openai", model="gpt-4o-mini"))

    with pytest.raises(ProviderError) as exc:
        _ = await gateway.execute_prompt("hello")

    assert exc.value.error_code == "missing_api_key"


@pytest.mark.asyncio
async def test_execute_prompt_returns_full_provider_response(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeOrchestrator:
        def __init__(self, provider: str, override_model: str | None = None) -> None:
            _ = provider
            _ = override_model

        async def generate(self, messages: list[dict[str, str]], response_model: type | None = None) -> str:
            _ = response_model
            await asyncio.sleep(0.001)
            return f"ok:{messages[0]['content']}"

    fake_module = ModuleType("solaraai_llm")
    setattr(fake_module, "LLMOrchestrator", FakeOrchestrator)
    monkeypatch.setitem(sys.modules, "solaraai_llm", fake_module)
    monkeypatch.setenv("OPENAI_API_KEY", "key")

    gateway = ProviderGateway(config=LLMConfig(provider="openai", model="gpt-4o-mini"))
    response = await gateway.execute_prompt("hello")

    assert isinstance(response, ProviderResponse)
    assert response.provider == "openai"
    assert response.model == "gpt-4o-mini"
    assert response.content == "ok:hello"
    assert isinstance(response.content, str)
    assert response.latency_ms > 0
    assert response.token_count is None


@pytest.mark.asyncio
async def test_execute_prompt_provider_failure_raises_provider_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeOrchestrator:
        def __init__(self, provider: str, override_model: str | None = None) -> None:
            _ = provider
            _ = override_model

        async def generate(self, messages: list[dict[str, str]], response_model: type | None = None) -> str:
            _ = messages
            _ = response_model
            raise RuntimeError("provider exploded")

    fake_module = ModuleType("solaraai_llm")
    setattr(fake_module, "LLMOrchestrator", FakeOrchestrator)
    monkeypatch.setitem(sys.modules, "solaraai_llm", fake_module)
    monkeypatch.setenv("OPENAI_API_KEY", "key")

    gateway = ProviderGateway(config=LLMConfig(provider="openai", model="gpt-4o-mini"))
    with pytest.raises(ProviderError) as exc:
        _ = await gateway.execute_prompt("hello")

    assert exc.value.error_code == "provider_error"


@pytest.mark.asyncio
async def test_fallback_chain_uses_secondary_provider_after_primary_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    attempted: list[str] = []

    async def fake_execute_with_provider(
        self: ProviderGateway,
        provider: str,
        prompt_text: str,
        variables: dict[str, object] | None = None,
        output_schema: type | None = None,
        system_message: str | None = None,
        location: LocationContext | None = None,
    ) -> ProviderResponse:
        _ = self
        _ = variables
        _ = output_schema
        _ = system_message
        _ = location
        attempted.append(provider)
        if provider == "openai":
            raise ProviderError("primary down", error_code="provider_error")
        return ProviderResponse(
            provider=provider,
            model="fallback-model",
            content=f"fallback:{prompt_text}",
            latency_ms=1.0,
            token_count=11,
        )

    monkeypatch.setattr(ProviderGateway, "_execute_with_provider", fake_execute_with_provider)
    gateway = ProviderGateway(config=LLMConfig(provider="openai", fallback_chain=["anthropic"]))
    response = await gateway.execute_prompt("hello")

    assert attempted == ["openai", "anthropic"]
    assert response.provider == "anthropic"
    assert response.content == "fallback:hello"


@pytest.mark.asyncio
async def test_fallback_chain_raises_when_all_providers_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    attempted: list[str] = []

    async def fake_execute_with_provider(
        self: ProviderGateway,
        provider: str,
        prompt_text: str,
        variables: dict[str, object] | None = None,
        output_schema: type | None = None,
        system_message: str | None = None,
        location: LocationContext | None = None,
    ) -> ProviderResponse:
        _ = self
        _ = prompt_text
        _ = variables
        _ = output_schema
        _ = system_message
        _ = location
        attempted.append(provider)
        raise ProviderError(f"{provider} failed", error_code="provider_error")

    monkeypatch.setattr(ProviderGateway, "_execute_with_provider", fake_execute_with_provider)
    gateway = ProviderGateway(config=LLMConfig(provider="openai", fallback_chain=["anthropic"]))

    with pytest.raises(ProviderError) as exc:
        _ = await gateway.execute_prompt("hello")

    assert attempted == ["openai", "anthropic"]
    assert "anthropic failed" in str(exc.value)


@pytest.mark.asyncio
async def test_timeout_handling_raises_timeout_error_code(monkeypatch: pytest.MonkeyPatch) -> None:
    class SlowOrchestrator:
        def __init__(self, provider: str, override_model: str | None = None) -> None:
            _ = provider
            _ = override_model

        async def generate(self, messages: list[dict[str, str]], response_model: type | None = None) -> str:
            _ = messages
            _ = response_model
            await asyncio.sleep(0.05)
            return "too late"

    fake_module = ModuleType("solaraai_llm")
    setattr(fake_module, "LLMOrchestrator", SlowOrchestrator)
    monkeypatch.setitem(sys.modules, "solaraai_llm", fake_module)
    monkeypatch.setenv("OPENAI_API_KEY", "key")

    gateway = ProviderGateway(config=LLMConfig(provider="openai", model="gpt-4o-mini", timeout_seconds=0))
    with pytest.raises(ProviderError) as exc:
        _ = await gateway.execute_prompt("hello")

    assert exc.value.error_code == "timeout"


@pytest.mark.asyncio
async def test_gemini_fallback_calls_execute_gemini_direct_when_orchestrator_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class BrokenGeminiOrchestrator:
        def __init__(self, provider: str, override_model: str | None = None) -> None:
            _ = provider
            _ = override_model

        async def generate(self, messages: list[dict[str, str]], response_model: type | None = None) -> str:
            _ = messages
            _ = response_model
            raise RuntimeError("mirascope/aiohttp crash")

    fake_module = ModuleType("solaraai_llm")
    setattr(fake_module, "LLMOrchestrator", BrokenGeminiOrchestrator)
    monkeypatch.setitem(sys.modules, "solaraai_llm", fake_module)
    monkeypatch.setenv("GEMINI_API_KEY", "key")

    called = {"value": False}

    async def fake_direct(
        self: ProviderGateway,
        prompt_text: str,
        system_message: str | None = None,
    ) -> ProviderResponse:
        _ = self
        _ = system_message
        called["value"] = True
        return ProviderResponse(
            provider="gemini",
            model="gemini-2.0-flash",
            content=f"direct:{prompt_text}",
            latency_ms=3.0,
            token_count=None,
        )

    monkeypatch.setattr(ProviderGateway, "_execute_gemini_direct", fake_direct)
    gateway = ProviderGateway(config=LLMConfig(provider="gemini", model="gemini-2.0-flash"))
    response = await gateway.execute_prompt("hello")

    assert called["value"] is True
    assert response.content == "direct:hello"


@pytest.mark.asyncio
async def test_multiple_sequential_calls_are_independent(monkeypatch: pytest.MonkeyPatch) -> None:
    counter = {"calls": 0}

    class CountingOrchestrator:
        def __init__(self, provider: str, override_model: str | None = None) -> None:
            _ = provider
            _ = override_model

        async def generate(self, messages: list[dict[str, str]], response_model: type | None = None) -> str:
            _ = response_model
            counter["calls"] += 1
            return f"call-{counter['calls']}:{messages[0]['content']}"

    fake_module = ModuleType("solaraai_llm")
    setattr(fake_module, "LLMOrchestrator", CountingOrchestrator)
    monkeypatch.setitem(sys.modules, "solaraai_llm", fake_module)
    monkeypatch.setenv("OPENAI_API_KEY", "key")

    gateway = ProviderGateway(config=LLMConfig(provider="openai", model="gpt-4o-mini"))
    first = await gateway.execute_prompt("one")
    second = await gateway.execute_prompt("two")

    assert first.content == "call-1:one"
    assert second.content == "call-2:two"


@pytest.mark.asyncio
async def test_execute_prompt_with_empty_prompt_is_handled(monkeypatch: pytest.MonkeyPatch) -> None:
    class EchoOrchestrator:
        def __init__(self, provider: str, override_model: str | None = None) -> None:
            _ = provider
            _ = override_model

        async def generate(self, messages: list[dict[str, str]], response_model: type | None = None) -> str:
            _ = response_model
            return messages[0]["content"]

    fake_module = ModuleType("solaraai_llm")
    setattr(fake_module, "LLMOrchestrator", EchoOrchestrator)
    monkeypatch.setitem(sys.modules, "solaraai_llm", fake_module)
    monkeypatch.setenv("OPENAI_API_KEY", "key")

    gateway = ProviderGateway(config=LLMConfig(provider="openai", model="gpt-4o-mini"))
    response = await gateway.execute_prompt("")

    assert isinstance(response.content, str)
    assert response.content == ""


@pytest.mark.asyncio
async def test_extract_token_count_from_usage_dict(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResult:
        usage: dict[str, int] = {"total_tokens": 77}

    class DictUsageOrchestrator:
        def __init__(self, provider: str, override_model: str | None = None) -> None:
            _ = provider
            _ = override_model

        async def generate(self, messages: list[dict[str, str]], response_model: type | None = None) -> FakeResult:
            _ = messages
            _ = response_model
            return FakeResult()

    fake_module = ModuleType("solaraai_llm")
    setattr(fake_module, "LLMOrchestrator", DictUsageOrchestrator)
    monkeypatch.setitem(sys.modules, "solaraai_llm", fake_module)
    monkeypatch.setenv("OPENAI_API_KEY", "key")

    gateway = ProviderGateway(config=LLMConfig(provider="openai", model="gpt-4o-mini"))
    response = await gateway.execute_prompt("hello")

    assert response.token_count == 77
    assert isinstance(response.content, str)


@pytest.mark.asyncio
async def test_perplexity_direct_includes_location_and_default_model(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class FakeCompletions:
        def create(self, **kwargs: object) -> object:
            captured.update(kwargs)

            class Message:
                content: str = "perplexity-ok"

            class Choice:
                message: Message = Message()

            class Usage:
                total_tokens: int = 123

            class Response:
                choices: list[Choice] = [Choice()]
                usage: Usage = Usage()

            return Response()

    class FakeOpenAI:
        def __init__(self, api_key: str, base_url: str) -> None:
            _ = api_key
            _ = base_url

            class Chat:
                completions: FakeCompletions = FakeCompletions()

            self.chat: Chat = Chat()

    fake_openai_module = ModuleType("openai")
    setattr(fake_openai_module, "OpenAI", FakeOpenAI)
    monkeypatch.setitem(sys.modules, "openai", fake_openai_module)
    monkeypatch.setenv("PERPLEXITY_API_KEY", "key")

    gateway = ProviderGateway(config=LLMConfig(provider="perplexity", model=None))
    response = await gateway.execute_prompt(
        "hello",
        system_message="system",
        location=LocationContext(city="Austin", region="TX", country="US"),
    )

    assert captured["model"] == "sonar-pro"
    assert captured["messages"] == [
        {"role": "system", "content": "system"},
        {"role": "user", "content": "hello"},
    ]
    assert captured["web_search_options"] == {"user_location": {"country": "US", "region": "TX", "city": "Austin"}}
    assert response.provider == "perplexity"
    assert response.model == "sonar-pro"
    assert response.token_count == 123
