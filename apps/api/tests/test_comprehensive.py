import os
from collections.abc import Awaitable, Callable
from typing import cast

import pytest


def _resolve_effective_industry(industry: str, custom: str) -> str:
    return custom.strip() if industry == "Other" and custom.strip() else industry


def test_strip_location_context_from_prompt():
    raw = (
        "What is the best maisonremodeling? Location context: The user is in "
        "Santa Clara, CA, US. Tailor the response to local results and nearby options when relevant."
    )
    if "Location context:" in raw:
        clean = raw[: raw.index("Location context:")].strip()
    else:
        clean = raw
    assert clean == "What is the best maisonremodeling?"
    assert "Location context" not in clean


def test_no_location_context_leaves_prompt_unchanged():
    raw = "What is the best coaching service?"
    if "Location context:" in raw:
        clean = raw[: raw.index("Location context:")].strip()
    else:
        clean = raw
    assert clean == "What is the best coaching service?"


def test_location_context_at_start_strips_everything():
    raw = "Location context: UK. What is the best brand?"
    if "Location context:" in raw:
        clean = raw[: raw.index("Location context:")].strip()
    else:
        clean = raw
    assert clean == ""


def test_mention_detected_exact_slug():
    response = "I recommend maisonremodeling for your project."
    slug = "maisonremodeling"
    assert slug in response.lower()


def test_mention_detected_with_spaces():
    response = "Based on reviews, Maison Remodeling Group offers good value."
    brand_name = "Maison Remodeling"
    assert brand_name.lower() in response.lower()


def test_mention_detected_hyphenated():
    response = "The maison-remodeling company is well reviewed."
    slug = "maison-remodeling"
    assert slug.replace("-", " ") in response.lower() or slug in response.lower()


def test_mention_not_detected_when_absent():
    response = "I recommend Norm's Kitchen Bath for remodeling in San Jose."
    slug = "maisonremodeling"
    brand_name = "Maison Remodeling"
    mentioned = slug in response.lower() or brand_name.lower() in response.lower()
    assert not mentioned


def test_mention_detection_case_insensitive():
    response = "MAISONREMODELING is a good choice."
    slug = "maisonremodeling"
    assert slug in response.lower()


def test_mention_detected_partial_brand_name():
    response = "The Missing Piece coaching offers transformative programs."
    brand_name = "The Missing Piece"
    slug = "theemissingpiece"
    mentioned = slug in response.lower() or brand_name.lower() in response.lower()
    assert mentioned


def test_mention_not_confused_with_similar_names():
    response = "Maison Design Studio offers interior design services."
    slug = "maisonremodeling"
    brand_name = "Maison Remodeling"
    mentioned = slug in response.lower() or brand_name.lower() in response.lower()
    assert not mentioned


def test_clean_domain_strips_https():
    d = "https://maisonremodeling.com"
    for prefix in ("https://", "http://"):
        if d.lower().startswith(prefix):
            d = d[len(prefix) :]
    d = d.split("/")[0]
    assert d == "maisonremodeling.com"


def test_clean_domain_strips_trailing_slash():
    d = "https://theemissingpiece.co.uk/"
    d = d.strip().rstrip("/")
    for prefix in ("https://", "http://"):
        if d.lower().startswith(prefix):
            d = d[len(prefix) :]
    d = d.split("/")[0]
    assert d == "theemissingpiece.co.uk"


def test_clean_domain_handles_bare_domain():
    d = "solaraai.com"
    for prefix in ("https://", "http://"):
        if d.lower().startswith(prefix):
            d = d[len(prefix) :]
    d = d.split("/")[0]
    assert d == "solaraai.com"


def test_clean_domain_strips_path():
    d = "https://example.com/about/team"
    d = d.strip().rstrip("/")
    for prefix in ("https://", "http://"):
        if d.lower().startswith(prefix):
            d = d[len(prefix) :]
    d = d.split("/")[0]
    assert d == "example.com"


def test_clean_domain_handles_http():
    d = "http://example.com"
    for prefix in ("https://", "http://"):
        if d.lower().startswith(prefix):
            d = d[len(prefix) :]
    d = d.split("/")[0]
    assert d == "example.com"


def test_onboarding_state_clean_domain_matches_expected_behavior():
    from ai_visibility.ui.onboarding_state import OnboardingState

    state = OnboardingState()
    state.domain = "https://example.com/about/team/"
    clean_domain = cast(object, getattr(state, "_clean_domain"))
    assert callable(clean_domain)
    assert clean_domain() == "example.com"


def test_effective_industry_returns_selected():
    industry = "SaaS / Software"
    custom = ""
    result = _resolve_effective_industry(industry, custom)
    assert result == "SaaS / Software"


def test_effective_industry_returns_custom_when_other():
    industry = "Other"
    custom = "Coaching / Personal Development"
    result = _resolve_effective_industry(industry, custom)
    assert result == "Coaching / Personal Development"


def test_effective_industry_returns_other_when_custom_empty():
    industry = "Other"
    custom = ""
    result = _resolve_effective_industry(industry, custom)
    assert result == "Other"


def test_effective_industry_trims_whitespace():
    industry = "Other"
    custom = "  coaching  "
    result = _resolve_effective_industry(industry, custom)
    assert result == "coaching"


def test_onboarding_state_effective_industry_uses_custom_for_other():
    from ai_visibility.ui.onboarding_state import OnboardingState

    state = OnboardingState()
    state.industry = "Other"
    state.custom_industry = "  coaching  "
    effective_industry = cast(object, getattr(state, "_effective_industry"))
    assert callable(effective_industry)
    assert effective_industry() == "coaching"


def test_select_city_parses_city_and_region():
    display = "Edinburgh, Scotland"
    parts = display.split(",")
    city = parts[0].strip()
    region = parts[1].strip() if len(parts) > 1 else ""
    assert city == "Edinburgh"
    assert region == "Scotland"


def test_select_city_us_format():
    display = "San Jose, California"
    parts = display.split(",")
    assert parts[0].strip() == "San Jose"
    assert parts[1].strip() == "California"


def test_select_city_no_region():
    display = "Singapore"
    parts = display.split(",")
    city = parts[0].strip()
    region = parts[1].strip() if len(parts) > 1 else ""
    assert city == "Singapore"
    assert region == ""


def test_country_code_to_name_mapping():
    from ai_visibility.ui.onboarding_state import COUNTRIES, COUNTRY_CODE_TO_NAME

    assert COUNTRY_CODE_TO_NAME["US"] == "United States"
    assert COUNTRY_CODE_TO_NAME["GB"] == "United Kingdom"
    assert COUNTRY_CODE_TO_NAME["IL"] == "Israel"
    assert len(COUNTRIES) >= 100


def test_onboarding_state_select_city_updates_state():
    from ai_visibility.ui.onboarding_state import OnboardingState

    state = OnboardingState()
    state.select_city("San Jose, California")
    assert state.city == "San Jose"
    assert state.region == "California"


def test_all_providers_have_models():
    from ai_visibility.providers.config import LLMConfig
    from ai_visibility.providers.gateway import ProviderGateway

    for provider in ["openai", "anthropic", "gemini", "perplexity", "grok"]:
        config = LLMConfig(provider=provider)
        gw = ProviderGateway(config=config)
        resolve_model = cast(Callable[[str], str], getattr(gw, "_resolve_model"))
        assert callable(resolve_model)
        model = resolve_model(provider)
        assert model != "default", f"{provider} has no model configured"
        assert len(model) > 0


def test_provider_model_names_are_current():
    from ai_visibility.providers.config import LLMConfig
    from ai_visibility.providers.gateway import ProviderGateway

    expected = {
        "openai": "gpt-5.4",
        "anthropic": "claude-sonnet-4-6",
        "gemini": "gemini-3-flash-preview",
        "perplexity": "sonar-pro",
        "grok": "grok-4-1-fast-reasoning",
    }
    for provider, expected_model in expected.items():
        config = LLMConfig(provider=provider)
        gw = ProviderGateway(config=config)
        resolve_model = cast(Callable[[str], str], getattr(gw, "_resolve_model"))
        assert callable(resolve_model)
        model = resolve_model(provider)
        assert model == expected_model, f"{provider}: expected {expected_model}, got {model}"


def test_scan_strategy_has_all_providers():
    from ai_visibility.runs.scan_strategy import DEFAULT_STRATEGY_V1

    provider_names = [p.provider for p in DEFAULT_STRATEGY_V1.providers.values()]
    for expected in ["chatgpt", "anthropic", "gemini", "perplexity", "grok"]:
        assert expected in provider_names, f"{expected} missing from scan strategy"


def test_openai_alias_maps_to_chatgpt_strategy_provider():
    from ai_visibility.runs.orchestrator import RunOrchestrator

    resolver = cast(Callable[[str], str], getattr(RunOrchestrator, "_resolve_strategy_provider"))
    assert callable(resolver)
    assert resolver("openai") == "chatgpt"


def test_location_injection_only_for_gemini_and_grok():
    from ai_visibility.providers.gateway import LocationContext
    from ai_visibility.runs.orchestrator import RunOrchestrator

    location = LocationContext(city="San Jose", region="California", country="US")
    prompt = "What is the best service?"

    injector = cast(Callable[[str, str, LocationContext], str], getattr(RunOrchestrator, "_inject_location_prompt"))
    assert callable(injector)

    openai_prompt = injector(prompt, "openai", location)
    gemini_prompt = injector(prompt, "gemini", location)
    grok_prompt = injector(prompt, "grok", location)

    assert openai_prompt == prompt
    assert gemini_prompt != prompt
    assert grok_prompt != prompt
    assert "Location context:" in gemini_prompt
    assert "Location context:" in grok_prompt


def test_all_prompts_have_brand_placeholder():
    from ai_visibility.prompts.default_set import DEFAULT_PROMPTS

    assert len(DEFAULT_PROMPTS) == 20
    for p in DEFAULT_PROMPTS:
        assert "{brand}" in p["template"], f"Prompt missing {{brand}}: {p['template']}"


def test_prompt_categories_are_valid():
    from ai_visibility.prompts.default_set import DEFAULT_PROMPTS

    valid_categories = {"buying_intent", "comparison", "recommendation", "informational"}
    for p in DEFAULT_PROMPTS:
        assert p["category"] in valid_categories, f"Invalid category: {p['category']}"


def test_prompts_render_with_brand():
    from ai_visibility.prompts.default_set import DEFAULT_PROMPTS

    for p in DEFAULT_PROMPTS:
        rendered = p["template"].replace("{brand}", "Acme Corp").replace("{competitor}", "Beta Inc")
        assert "{brand}" not in rendered
        assert "Acme Corp" in rendered


def test_extract_domain_from_entry():
    from ai_visibility.ui import onboarding_state

    extract_domain = cast(Callable[[str], str], getattr(onboarding_state, "_extract_domain"))
    assert callable(extract_domain)

    assert extract_domain("Jasper (jasper.ai)") == "jasper.ai"
    assert extract_domain("Copy.ai (copy.ai)") == "copy.ai"
    assert extract_domain("No domain here") == ""
    assert extract_domain("") == ""
    assert extract_domain("Name (domain.com) extra text") == "domain.com"


def test_extract_domain_handles_nested_parens():
    from ai_visibility.ui import onboarding_state

    extract_domain = cast(Callable[[str], str], getattr(onboarding_state, "_extract_domain"))
    assert callable(extract_domain)

    result = extract_domain("Some Company (example.com)")
    assert result == "example.com"


@pytest.mark.asyncio
@pytest.mark.slow
async def test_competitor_discovery_solaraai():
    from ai_visibility.ui import onboarding_state

    discover_competitors_with_site_content = cast(
        Callable[[str, str], Awaitable[tuple[list[str], str]]],
        getattr(onboarding_state, "_discover_competitors_with_site_content"),
    )
    assert callable(discover_competitors_with_site_content)

    if not os.getenv("OPENAI_API_KEY") or not os.getenv("TAVILY_API_KEY"):
        pytest.skip("OPENAI_API_KEY and TAVILY_API_KEY are required for competitor discovery integration test")

    competitors, site = await discover_competitors_with_site_content(
        "solaraai.com",
        "Marketing / Advertising Agency",
    )
    assert site.strip() != ""
    assert len(competitors) >= 2, f"Expected at least 2 competitors, got {len(competitors)}"
    for competitor in competitors:
        assert "(" in competitor and ")" in competitor, f"Competitor missing domain: {competitor}"


@pytest.mark.asyncio
@pytest.mark.slow
async def test_nominatim_api_works():
    import httpx

    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": "London",
                "countrycodes": "gb",
                "format": "json",
                "limit": "3",
                "accept-language": "en",
            },
            headers={"User-Agent": "ai-visibility-test/1.0"},
        )
        assert resp.status_code == 200
        payload = cast(list[dict[str, object]], resp.json())
        assert len(payload) > 0
