from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ExecutionMode(str, Enum):
    HIGH_FIDELITY = "high_fidelity"
    WEB_SEARCH = "web_search"
    DIRECT = "direct"


class ScanMode(str, Enum):
    ONBOARDING = "onboarding"
    SCHEDULED = "scheduled"


@dataclass(slots=True)
class ProviderConfig:
    provider: str
    execution_mode: ExecutionMode
    model_name: str
    max_prompts: int
    cost_ceiling_usd: float
    retry_limit: int
    enabled: bool


@dataclass(slots=True)
class ScanStrategy:
    strategy_version: str
    scan_mode: ScanMode
    providers: dict[str, ProviderConfig]
    total_cost_ceiling_usd: float


DEFAULT_STRATEGY_V1 = ScanStrategy(
    strategy_version="v1",
    scan_mode=ScanMode.SCHEDULED,
    providers={
        "chatgpt": ProviderConfig(
            provider="chatgpt",
            execution_mode=ExecutionMode.HIGH_FIDELITY,
            model_name="gpt-5.4",
            max_prompts=20,
            cost_ceiling_usd=2.00,
            retry_limit=2,
            enabled=True,
        ),
        "gemini": ProviderConfig(
            provider="gemini",
            execution_mode=ExecutionMode.HIGH_FIDELITY,
            model_name="gemini-3-flash-preview",
            max_prompts=20,
            cost_ceiling_usd=2.00,
            retry_limit=2,
            enabled=True,
        ),
        "anthropic": ProviderConfig(
            provider="anthropic",
            execution_mode=ExecutionMode.WEB_SEARCH,
            model_name="claude-sonnet-4-6",
            max_prompts=20,
            cost_ceiling_usd=2.00,
            retry_limit=2,
            enabled=True,
        ),
        "perplexity": ProviderConfig(
            provider="perplexity",
            execution_mode=ExecutionMode.DIRECT,
            model_name="sonar-pro",
            max_prompts=20,
            cost_ceiling_usd=1.00,
            retry_limit=1,
            enabled=True,
        ),
        "grok": ProviderConfig(
            provider="grok",
            execution_mode=ExecutionMode.DIRECT,
            model_name="grok-4-1-fast-reasoning",
            max_prompts=20,
            cost_ceiling_usd=2.00,
            retry_limit=2,
            enabled=True,
        ),
        "google_ai_overview": ProviderConfig(
            provider="google_ai_overview",
            execution_mode=ExecutionMode.DIRECT,
            model_name="google-ai-overview",
            max_prompts=20,
            cost_ceiling_usd=1.00,
            retry_limit=1,
            enabled=True,
        ),
        "google_ai_mode_serpapi": ProviderConfig(
            provider="google_ai_mode_serpapi",
            execution_mode=ExecutionMode.DIRECT,
            model_name="google-ai-mode-serpapi",
            max_prompts=20,
            cost_ceiling_usd=1.00,
            retry_limit=1,
            enabled=True,
        ),
    },
    total_cost_ceiling_usd=10.00,
)


def validate_strategy(strategy: ScanStrategy) -> list[str]:
    errors: list[str] = []

    if not strategy.strategy_version.strip():
        errors.append("strategy_version must not be empty")

    if strategy.total_cost_ceiling_usd <= 0:
        errors.append("total_cost_ceiling_usd must be positive")

    enabled_cost_total = 0.0
    for key, provider in strategy.providers.items():
        if not provider.enabled:
            continue

        if provider.max_prompts <= 0:
            errors.append(f"provider '{key}' must have max_prompts > 0")
        if provider.cost_ceiling_usd < 0:
            errors.append(f"provider '{key}' must have cost_ceiling_usd >= 0")
        enabled_cost_total += provider.cost_ceiling_usd

    if enabled_cost_total > strategy.total_cost_ceiling_usd * 3:
        errors.append("sum of enabled provider cost ceilings exceeds 3x total_cost_ceiling_usd")

    return errors


def get_strategy_for_mode(scan_mode: ScanMode, strategy_version: str = "v1") -> ScanStrategy:
    if strategy_version != "v1":
        raise ValueError(f"Unsupported scan strategy version: {strategy_version}")

    max_prompts = 5 if scan_mode == ScanMode.ONBOARDING else 20
    providers = {
        key: ProviderConfig(
            provider=config.provider,
            execution_mode=config.execution_mode,
            model_name=config.model_name,
            max_prompts=max_prompts,
            cost_ceiling_usd=config.cost_ceiling_usd,
            retry_limit=config.retry_limit,
            enabled=config.enabled,
        )
        for key, config in DEFAULT_STRATEGY_V1.providers.items()
        if config.enabled
    }

    return ScanStrategy(
        strategy_version=DEFAULT_STRATEGY_V1.strategy_version,
        scan_mode=scan_mode,
        providers=providers,
        total_cost_ceiling_usd=DEFAULT_STRATEGY_V1.total_cost_ceiling_usd,
    )
