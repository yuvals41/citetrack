from pydantic import BaseModel, Field, field_validator

SUPPORTED_PROVIDERS = {
    "openai",
    "anthropic",
    "gemini",
    "grok",
    "perplexity",
    "google_ai_overview",
    "google_ai_mode_serpapi",
}


class LLMConfig(BaseModel):
    provider: str = "openai"
    model: str | None = None
    fallback_chain: list[str] = Field(default_factory=list)
    timeout_seconds: int = 30

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, value: str) -> str:
        normalized = value.lower()
        if normalized == "xai":
            normalized = "grok"
        if normalized not in SUPPORTED_PROVIDERS:
            raise ValueError(f"Provider must be one of {sorted(SUPPORTED_PROVIDERS)}")
        return normalized

    @field_validator("fallback_chain")
    @classmethod
    def validate_fallback_chain(cls, value: list[str]) -> list[str]:
        normalized_chain: list[str] = []
        for provider in value:
            normalized = provider.lower()
            if normalized == "xai":
                normalized = "grok"
            if normalized not in SUPPORTED_PROVIDERS:
                raise ValueError(f"Fallback provider {provider!r} not in {sorted(SUPPORTED_PROVIDERS)}")
            normalized_chain.append(normalized)
        return normalized_chain
