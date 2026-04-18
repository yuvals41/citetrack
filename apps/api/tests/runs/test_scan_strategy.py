from ai_visibility.runs.scan_strategy import (
    DEFAULT_STRATEGY_V1,
    ExecutionMode,
    ProviderConfig,
    ScanMode,
    ScanStrategy,
    get_strategy_for_mode,
    validate_strategy,
)


def test_default_strategy_has_all_providers() -> None:
    providers = DEFAULT_STRATEGY_V1.providers
    assert set(providers) == {
        "chatgpt",
        "gemini",
        "anthropic",
        "perplexity",
        "grok",
        "google_ai_overview",
        "google_ai_mode_serpapi",
    }
    assert providers["chatgpt"].execution_mode == ExecutionMode.HIGH_FIDELITY
    assert providers["gemini"].execution_mode == ExecutionMode.HIGH_FIDELITY
    assert providers["anthropic"].execution_mode == ExecutionMode.WEB_SEARCH
    assert providers["perplexity"].execution_mode == ExecutionMode.DIRECT
    assert providers["grok"].execution_mode == ExecutionMode.DIRECT
    assert providers["google_ai_overview"].execution_mode == ExecutionMode.DIRECT
    assert providers["google_ai_mode_serpapi"].execution_mode == ExecutionMode.DIRECT


def test_onboarding_vs_scheduled_max_prompts() -> None:
    onboarding = get_strategy_for_mode(ScanMode.ONBOARDING)
    scheduled = get_strategy_for_mode(ScanMode.SCHEDULED)

    assert all(provider.max_prompts == 5 for provider in onboarding.providers.values())
    assert all(provider.max_prompts == 20 for provider in scheduled.providers.values())


def test_cost_ceiling_validation() -> None:
    invalid = ScanStrategy(
        strategy_version="v1",
        scan_mode=ScanMode.SCHEDULED,
        providers=DEFAULT_STRATEGY_V1.providers,
        total_cost_ceiling_usd=1.0,
    )

    errors = validate_strategy(invalid)
    assert any("exceeds 3x" in err for err in errors)


def test_disabled_provider_excluded() -> None:
    strategy = ScanStrategy(
        strategy_version="v1",
        scan_mode=ScanMode.SCHEDULED,
        providers={
            "chatgpt": ProviderConfig(
                provider="chatgpt",
                execution_mode=ExecutionMode.HIGH_FIDELITY,
                model_name="gpt-5.4",
                max_prompts=20,
                cost_ceiling_usd=2.0,
                retry_limit=2,
                enabled=True,
            ),
            "disabled": ProviderConfig(
                provider="disabled",
                execution_mode=ExecutionMode.DIRECT,
                model_name="any-model",
                max_prompts=0,
                cost_ceiling_usd=0.0,
                retry_limit=0,
                enabled=False,
            ),
        },
        total_cost_ceiling_usd=7.0,
    )

    errors = validate_strategy(strategy)
    assert all("disabled" not in error for error in errors)


def test_strategy_version_present() -> None:
    strategy = get_strategy_for_mode(ScanMode.SCHEDULED)
    assert strategy.strategy_version == "v1"
