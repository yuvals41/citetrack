from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

import pytest
from playwright.sync_api import Error, Page, expect

BASE_URL = "http://localhost:3000"
HYDRATION_WAIT_MS = 2000
NAV_WAIT_TIMEOUT_MS = 15000


@pytest.fixture(scope="session")
def browser_context_args() -> dict[str, object]:
    return {
        "base_url": BASE_URL,
        "viewport": {"width": 1280, "height": 720},
    }


def _goto(page: Page, path: str) -> None:
    target = urljoin(f"{BASE_URL.rstrip('/')}/", path.lstrip("/"))
    _ = page.goto(target, wait_until="networkidle", timeout=NAV_WAIT_TIMEOUT_MS)
    page.wait_for_load_state("networkidle", timeout=NAV_WAIT_TIMEOUT_MS)
    page.wait_for_timeout(HYDRATION_WAIT_MS)


def _safe_click_nav_link(page: Page, label: str) -> None:
    link = page.get_by_role("link", name=label, exact=True)
    expect(link).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)
    link.click(timeout=NAV_WAIT_TIMEOUT_MS)
    page.wait_for_load_state("networkidle", timeout=NAV_WAIT_TIMEOUT_MS)
    page.wait_for_timeout(HYDRATION_WAIT_MS)


def _assert_no_render_error(page: Page) -> None:
    assert "an error occurred while rendering" not in page.content().lower()


def _go_to_onboarding_step_2(page: Page) -> None:
    _goto(page, "/onboarding")
    domain_input = page.locator("input[placeholder*='yourbrand.com']")
    expect(domain_input).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)
    domain_input.fill("example.com")
    page.get_by_role("button", name="Next", exact=True).click(timeout=NAV_WAIT_TIMEOUT_MS)
    page.wait_for_load_state("networkidle", timeout=NAV_WAIT_TIMEOUT_MS)
    page.wait_for_timeout(HYDRATION_WAIT_MS)
    expect(page.get_by_role("heading", name="Tell us about your brand")).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)


def _go_to_onboarding_step_2_with_domain(page: Page, domain: str) -> None:
    _goto(page, "/onboarding")
    domain_input = page.locator("input[placeholder*='yourbrand.com']")
    expect(domain_input).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)
    domain_input.fill(domain)
    page.get_by_role("button", name="Next", exact=True).click(timeout=NAV_WAIT_TIMEOUT_MS)
    page.wait_for_load_state("networkidle", timeout=NAV_WAIT_TIMEOUT_MS)
    page.wait_for_timeout(HYDRATION_WAIT_MS)
    expect(page.get_by_role("heading", name="Tell us about your brand")).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)


def _get_step_2_brand_name_input(page: Page):
    brand_input = page.get_by_placeholder("e.g. Solara AI")
    if brand_input.count() > 0:
        return brand_input.first

    labeled_input = page.get_by_label(re.compile("Brand Name", re.I))
    if labeled_input.count() > 0:
        return labeled_input.first

    return page.get_by_role("textbox").first


def _select_step_2_industry(page: Page) -> None:
    select_trigger = page.get_by_role("combobox").first
    expect(select_trigger).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)
    select_trigger.click(timeout=NAV_WAIT_TIMEOUT_MS)

    option = (
        page.locator("[role='option']").filter(has_text=re.compile("Marketing|Advertising|Technology|SaaS", re.I)).first
    )
    if option.count() == 0:
        option = page.locator("[role='option']").first
    expect(option).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)
    option.click(timeout=NAV_WAIT_TIMEOUT_MS)


def _advance_onboarding_step_2_to_3(page: Page) -> None:
    _go_to_onboarding_step_2(page)
    select_trigger = page.get_by_role("combobox").first
    expect(select_trigger).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)
    select_trigger.click(timeout=NAV_WAIT_TIMEOUT_MS)

    option = (
        page.locator("[role='option']").filter(has_text=re.compile("Marketing|Advertising|Technology|SaaS", re.I)).first
    )
    if option.count() == 0:
        option = page.locator("[role='option']").first
    expect(option).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)
    option.click(timeout=NAV_WAIT_TIMEOUT_MS)

    page.get_by_role("button", name="Next", exact=True).click(timeout=NAV_WAIT_TIMEOUT_MS)
    page.wait_for_load_state("networkidle", timeout=NAV_WAIT_TIMEOUT_MS)
    page.wait_for_timeout(HYDRATION_WAIT_MS)


def test_sidebar_renders_all_navigation_links(page: Page) -> None:
    _goto(page, "/")
    for label in [
        "Dashboard",
        "Setup",
        "Scans",
        "Questions",
        "AI Responses",
        "Content Analysis",
        "Action Plan",
    ]:
        expect(page.get_by_role("link", name=label, exact=True)).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)
    _assert_no_render_error(page)


def test_clicking_sidebar_links_navigates_to_expected_pages(page: Page) -> None:
    _goto(page, "/")
    nav_targets: list[tuple[str, str]] = [
        ("Dashboard", "/"),
        ("Setup", "/onboarding"),
        ("Scans", "/runs"),
        ("Questions", "/prompts"),
        ("AI Responses", "/citations"),
        ("Content Analysis", "/content-analysis"),
        ("Action Plan", "/recommendations"),
    ]
    for label, expected_path in nav_targets:
        _safe_click_nav_link(page, label)
        assert urlparse(page.url).path == expected_path
        _assert_no_render_error(page)


def test_workspace_selector_is_visible(page: Page) -> None:
    _goto(page, "/")
    expect(page.get_by_text("WORKSPACE", exact=True)).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)
    expect(page.get_by_role("combobox").first).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)
    _assert_no_render_error(page)


def test_new_workspace_button_exists(page: Page) -> None:
    _goto(page, "/")
    expect(page.get_by_role("button", name="New Workspace", exact=True)).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)
    _assert_no_render_error(page)


def test_page_header_changes_when_navigating(page: Page) -> None:
    _goto(page, "/")
    nav_and_headers: list[tuple[str, str]] = [
        ("Dashboard", "Dashboard"),
        ("Setup", "Onboarding"),
        ("Scans", "Runs"),
        ("Questions", "Prompts"),
        ("AI Responses", "AI Responses"),
        ("Content Analysis", "Content Analysis"),
        ("Action Plan", "Recommendations"),
    ]
    for nav_label, heading in nav_and_headers:
        _safe_click_nav_link(page, nav_label)
        expect(page.get_by_role("heading", name=heading, exact=True)).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)
        _assert_no_render_error(page)


def test_onboarding_loads_with_domain_input(page: Page) -> None:
    _goto(page, "/onboarding")
    expect(page.get_by_role("heading", name="What's your website?")).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)
    expect(page.locator("input[placeholder*='yourbrand.com']")).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)
    _assert_no_render_error(page)


def test_onboarding_step1_next_advances_to_step2(page: Page) -> None:
    _go_to_onboarding_step_2(page)
    expect(page.get_by_role("heading", name="Tell us about your brand")).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)
    _assert_no_render_error(page)


def test_onboarding_step2_shows_industry_dropdown(page: Page) -> None:
    _go_to_onboarding_step_2(page)
    expect(page.get_by_role("combobox").first).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)
    _assert_no_render_error(page)


def test_onboarding_step2_has_brand_name_input(page: Page) -> None:
    _go_to_onboarding_step_2_with_domain(page, "solaraai.com")
    brand_name_input = _get_step_2_brand_name_input(page)
    expect(brand_name_input).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)

    placeholder = (brand_name_input.get_attribute("placeholder") or "").lower()
    if "solara ai" not in placeholder:
        expect(brand_name_input).to_have_value(re.compile("solara", re.I), timeout=NAV_WAIT_TIMEOUT_MS)

    _assert_no_render_error(page)


def test_onboarding_step2_brand_name_is_editable(page: Page) -> None:
    _go_to_onboarding_step_2_with_domain(page, "solaraai.com")
    brand_name_input = _get_step_2_brand_name_input(page)
    expect(brand_name_input).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)

    brand_name_input.clear()
    brand_name_input.fill("My Custom Brand")
    expect(brand_name_input).to_have_value("My Custom Brand", timeout=NAV_WAIT_TIMEOUT_MS)

    _assert_no_render_error(page)


def test_onboarding_step2_brand_name_label_visible(page: Page) -> None:
    _go_to_onboarding_step_2_with_domain(page, "solaraai.com")
    expect(page.get_by_text("Brand Name", exact=True)).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)
    _assert_no_render_error(page)


def test_onboarding_prompts_use_brand_name(page: Page) -> None:
    _go_to_onboarding_step_2_with_domain(page, "solaraai.com")

    brand_name_input = _get_step_2_brand_name_input(page)
    expect(brand_name_input).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)
    brand_name_input.clear()
    brand_name_input.fill("Test Brand XYZ")
    expect(brand_name_input).to_have_value("Test Brand XYZ", timeout=NAV_WAIT_TIMEOUT_MS)

    _select_step_2_industry(page)
    page.get_by_role("button", name="Next", exact=True).click(timeout=NAV_WAIT_TIMEOUT_MS)
    page.wait_for_load_state("networkidle", timeout=NAV_WAIT_TIMEOUT_MS)
    page.wait_for_timeout(HYDRATION_WAIT_MS)
    expect(page.get_by_role("heading", name="Who are your competitors?")).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)

    page.get_by_role("button", name="Next", exact=True).click(timeout=NAV_WAIT_TIMEOUT_MS)
    page.wait_for_load_state("networkidle", timeout=NAV_WAIT_TIMEOUT_MS)
    page.wait_for_timeout(HYDRATION_WAIT_MS)

    custom_prompt = "How can Test Brand XYZ improve AI visibility?"
    prompt_input = page.locator("input[placeholder*='Add your own question']")
    expect(prompt_input).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)
    prompt_input.fill(custom_prompt)
    page.get_by_role("button", name="Add", exact=True).click(timeout=NAV_WAIT_TIMEOUT_MS)

    custom_prompt_locator = page.get_by_text(re.compile("Test Brand XYZ", re.I)).first
    expect(custom_prompt_locator).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)
    assert "solaraai" not in custom_prompt_locator.inner_text().lower()
    assert "solara ai" not in custom_prompt_locator.inner_text().lower()

    _assert_no_render_error(page)


def test_onboarding_step2_next_advances_to_step3(page: Page) -> None:
    _advance_onboarding_step_2_to_3(page)
    expect(page.get_by_role("heading", name="Who are your competitors?")).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)
    _assert_no_render_error(page)


def test_onboarding_step3_shows_competitor_discovery_state(page: Page) -> None:
    _advance_onboarding_step_2_to_3(page)

    loading_state = page.get_by_text("Finding your competitors...").count() > 0
    has_competitor_input = page.locator("input[placeholder*='competitor.com']").count() > 0
    has_competitor_cards = page.locator("div[style*='f0f9ff'], div[style*='#f0f9ff']").count() > 0

    assert loading_state or has_competitor_input or has_competitor_cards
    _assert_no_render_error(page)


def test_onboarding_step3_has_suggest_competitors_button(page: Page) -> None:
    _advance_onboarding_step_2_to_3(page)
    expect(page.get_by_role("button", name="Suggest competitors", exact=True)).to_be_visible(
        timeout=NAV_WAIT_TIMEOUT_MS
    )
    _assert_no_render_error(page)


def test_dashboard_loads_key_sections(page: Page) -> None:
    _goto(page, "/")
    expect(page.get_by_text("Visibility Score", exact=True)).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)
    expect(page.get_by_text("Scan History", exact=True)).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)
    expect(page.get_by_text("Recent Alerts", exact=True)).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)
    _assert_no_render_error(page)


def test_dashboard_run_new_check_button_exists(page: Page) -> None:
    _goto(page, "/")
    expect(page.get_by_role("button", name="Run New Check", exact=True)).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)
    _assert_no_render_error(page)


def test_dashboard_export_csv_button_exists(page: Page) -> None:
    _goto(page, "/")
    expect(page.get_by_role("button", name="Export CSV", exact=True)).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)
    _assert_no_render_error(page)


def test_dashboard_social_visibility_has_youtube_and_reddit_cards(page: Page) -> None:
    _goto(page, "/")
    expect(page.get_by_text("Social Visibility", exact=True)).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)
    expect(page.get_by_text("YouTube Mentions", exact=True)).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)
    expect(page.get_by_text("Reddit Mentions", exact=True)).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)
    _assert_no_render_error(page)


def test_content_analysis_page_loads_with_url_input(page: Page) -> None:
    _goto(page, "/content-analysis")
    expect(page.get_by_role("heading", name="Content Extractability Analyzer", exact=True)).to_be_visible(
        timeout=NAV_WAIT_TIMEOUT_MS
    )
    expect(page.locator("input[placeholder*='Enter URL']")).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)
    _assert_no_render_error(page)


def test_content_analysis_analyze_button_exists(page: Page) -> None:
    _goto(page, "/content-analysis")
    expect(page.get_by_role("button", name="Run Analysis", exact=True)).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)
    _assert_no_render_error(page)


def test_content_analysis_crawler_simulation_section_exists(page: Page) -> None:
    _goto(page, "/content-analysis")
    expect(page.get_by_text("Crawler Accessibility Simulation", exact=True)).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)
    expect(page.get_by_role("button", name=re.compile("Simulate AI Crawlers", re.I))).to_be_visible(
        timeout=NAV_WAIT_TIMEOUT_MS
    )
    _assert_no_render_error(page)


def test_ai_responses_page_loads(page: Page) -> None:
    _goto(page, "/citations")
    expect(page.get_by_role("heading", name="AI Responses", exact=True)).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)
    expect(page.get_by_text("Viewing responses from", exact=True)).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)
    _assert_no_render_error(page)


def test_ai_responses_export_button_exists(page: Page) -> None:
    _goto(page, "/citations")
    expect(page.get_by_role("button", name="Export CSV", exact=True)).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)
    _assert_no_render_error(page)


def test_ai_responses_filter_ui_elements_exist(page: Page) -> None:
    _goto(page, "/citations")
    expect(page.get_by_text("Viewing responses from", exact=True)).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)
    expect(page.get_by_role("combobox").first).to_be_visible(timeout=NAV_WAIT_TIMEOUT_MS)
    _assert_no_render_error(page)


def test_unknown_route_shows_non_crashing_response(page: Page) -> None:
    response = page.goto(
        f"{BASE_URL}/this-route-does-not-exist",
        wait_until="networkidle",
        timeout=NAV_WAIT_TIMEOUT_MS,
    )
    page.wait_for_load_state("networkidle", timeout=NAV_WAIT_TIMEOUT_MS)
    page.wait_for_timeout(HYDRATION_WAIT_MS)

    assert response is None or response.status in {200, 302, 404}
    _assert_no_render_error(page)

    current_path = urlparse(page.url).path
    assert current_path in {"/this-route-does-not-exist", "/"}
    content = page.content().lower()
    assert "not found" in content or "404" in content or "dashboard" in content or "ai visibility" in content


@pytest.mark.parametrize(
    "path", ["/", "/onboarding", "/runs", "/prompts", "/citations", "/content-analysis", "/recommendations"]
)
def test_no_javascript_errors_on_core_pages(page: Page, path: str) -> None:
    page_errors: list[str] = []
    page.on("pageerror", lambda err: page_errors.append(str(err)))

    _goto(page, path)
    _assert_no_render_error(page)

    try:
        page.wait_for_timeout(500)
    except Error:
        pass

    assert not page_errors, f"JavaScript errors on {path}: {page_errors}"
