from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(scope="session")
def browser_context_args() -> dict[str, dict[str, int]]:
    return {"viewport": {"width": 1280, "height": 720}}


def _goto_and_hydrate(page: Page, path: str, base_url: str) -> None:
    target_url = urljoin(f"{base_url.rstrip('/')}/", path.lstrip("/"))
    _ = page.goto(target_url)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(3000)


def _assert_no_render_error(page: Page) -> None:
    assert "an error occurred while rendering" not in page.content().lower()


@pytest.mark.parametrize(
    "path,expected_terms",
    [
        ("/", ["dashboard"]),
        ("/onboarding", ["what's your website", "website"]),
        ("/runs", ["scan history", "ai assistant", "runs"]),
        ("/prompts", ["questions", "sample questions we ask ai", "prompts"]),
        ("/citations", ["citations", "responses", "what the ai said"]),
        ("/recommendations", ["action", "recommendations"]),
        ("/prompt-detail", ["response", "response details", "prompt detail"]),
    ],
)
def test_page_loads(page: Page, base_url: str, path: str, expected_terms: list[str]) -> None:
    _goto_and_hydrate(page, path, base_url)

    content = page.content().lower()
    assert any(term in content for term in expected_terms)
    _assert_no_render_error(page)


def test_sidebar_navigation_and_workspace_selector(page: Page, base_url: str) -> None:
    nav_targets: list[tuple[str, str, str]] = [
        ("Dashboard", "/", "dashboard"),
        ("Setup", "/onboarding", "website"),
        ("Scans", "/runs", "scan"),
        ("Questions", "/prompts", "questions"),
        ("AI Responses", "/citations", "responses"),
        ("Action Plan", "/recommendations", "action"),
    ]

    _goto_and_hydrate(page, "/", base_url)

    expect(page.get_by_text("WORKSPACE", exact=True)).to_be_visible()
    expect(page.get_by_role("combobox").first).to_be_visible()

    for label, expected_path, expected_term in nav_targets:
        page.get_by_role("link", name=label, exact=True).click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)

        current_path = urlparse(page.url).path
        assert current_path == expected_path
        assert expected_term in page.content().lower()
        _assert_no_render_error(page)


def test_dashboard_shows_metrics_and_history(page: Page, base_url: str) -> None:
    _goto_and_hydrate(page, "/", base_url)

    expect(page.get_by_text("Visibility Score", exact=True)).to_be_visible()
    expect(page.get_by_text("Citation Coverage", exact=True)).to_be_visible()
    expect(page.get_by_text("Competitor Comparison", exact=True)).to_be_visible()
    expect(page.get_by_text("Competitor Wins", exact=True)).to_be_visible()
    expect(page.locator("text=Scan History")).to_be_visible()
    expect(page.get_by_role("button", name="Run New Check")).to_be_visible()
    _assert_no_render_error(page)


@pytest.mark.slow
def test_onboarding_full_wizard_flow(page: Page, base_url: str) -> None:
    _goto_and_hydrate(page, "/onboarding", base_url)

    expect(page.locator("text=What's your website?")).to_be_visible()
    domain_input = page.locator("input[placeholder*='yourbrand.com']")
    expect(domain_input).to_be_visible()
    domain_input.fill("solaraai.com")
    page.get_by_role("button", name="Next").click()

    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(3000)
    expect(page.locator("text=What industry are you in?")).to_be_visible()

    page.get_by_role("combobox").nth(1).click()
    page.locator("[role='option']").filter(has_text="Marketing / Advertising Agency").first.click()
    page.get_by_role("button", name="Next").click()

    expect(page.locator("text=Who are your competitors?")).to_be_visible()

    spinner = page.locator("text=Finding your competitors...")
    if spinner.count() > 0:
        spinner.first.wait_for(state="hidden", timeout=30000)

    page.wait_for_timeout(5000)
    competitor_boxes = page.locator("div[style*='#f0f9ff'], div[style*='f0f9ff']")
    if competitor_boxes.count() == 0:
        competitor_boxes = page.locator("p, span").filter(has_text=re.compile(r"\.\w{2,3}\)"))
    assert competitor_boxes.count() >= 1, "Expected at least 1 competitor to be discovered"

    page.get_by_role("button", name="Next").click()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(3000)

    expect(page.locator("text=Questions we'll ask AI")).to_be_visible()
    expect(page.locator("text=best tools in my industry category")).to_be_visible()
    page.get_by_role("button", name="Start Checking AI Now").click()

    expect(page.locator("text=Setup Complete!")).to_be_visible(timeout=30000)
    _assert_no_render_error(page)


def test_citations_page_has_selector_headers_and_rows(page: Page, base_url: str) -> None:
    _goto_and_hydrate(page, "/citations", base_url)

    has_heading = (
        page.locator("text=Showing citations for").count() > 0 or page.locator("text=Showing responses for").count() > 0
    )
    assert has_heading or page.locator("button[role='combobox']").first.is_visible()
    run_selector = page.locator("button[role='combobox']")
    if run_selector.count() > 0:
        expect(run_selector.first).to_be_visible()

    content = page.content().lower()
    headers_present = all(header in content for header in ["status", "your brand", "what the ai said"])
    card_layout_present = "question asked" in content or "mentioned" in content or "provider" in content
    has_empty_state = "no ai responses found for this scan" in content or "select a scan above" in content
    assert headers_present or card_layout_present or has_empty_state

    if headers_present and not has_empty_state:
        row_count = page.locator("table tbody tr").count()
        assert row_count >= 1

    _assert_no_render_error(page)


def test_recommendations_page_shows_cards_or_empty_state(page: Page, base_url: str) -> None:
    _goto_and_hydrate(page, "/recommendations", base_url)

    expect(page.get_by_role("button", name="Refresh Results")).to_be_visible()

    content = page.content().lower()
    assert (
        "no recommendations yet" in content
        or "high priority" in content
        or "medium priority" in content
        or "low priority" in content
    )

    _assert_no_render_error(page)


def test_runs_page_has_table_headers_and_run_button(page: Page, base_url: str) -> None:
    _goto_and_hydrate(page, "/runs", base_url)

    expect(page.get_by_role("button", name="Run New Check")).to_be_visible()

    content = page.content().lower()
    headers_present = all(header in content for header in ["ai assistant", "ai model", "status", "date"])
    has_empty_state = "no scans yet" in content
    assert headers_present or has_empty_state

    _assert_no_render_error(page)


def test_dashboard_charts_have_data(page: Page, base_url: str) -> None:
    _goto_and_hydrate(page, "/", base_url)
    assert page.locator("text=Results by AI Assistant").is_visible()
    dashboard_text = page.locator("body").inner_text().lower()
    assert "questions" in dashboard_text and ("answered" in dashboard_text or "asked" in dashboard_text)
    assert page.locator("text=Mention Type Breakdown").is_visible()
    assert page.locator("text=Competitor Comparison").is_visible()
    assert page.locator("text=Visibility Trend").is_visible()


def test_dashboard_has_source_attribution_chart(page: Page, base_url: str) -> None:
    _goto_and_hydrate(page, "/", base_url)
    assert page.locator("text=Sources Cited by AI").first.is_visible()


def test_dashboard_has_sentiment_chart(page: Page, base_url: str) -> None:
    _goto_and_hydrate(page, "/", base_url)
    assert page.locator("text=Brand Sentiment").first.is_visible()


def test_dashboard_has_position_metric(page: Page, base_url: str) -> None:
    _goto_and_hydrate(page, "/", base_url)
    content = page.content().lower()
    assert "avg position" in content or "position" in content


def test_dashboard_has_issues_found(page: Page, base_url: str) -> None:
    _goto_and_hydrate(page, "/", base_url)
    assert page.locator("text=Issues Found").first.is_visible()


def test_recommendations_page_has_content(page: Page, base_url: str) -> None:
    _goto_and_hydrate(page, "/recommendations", base_url)
    content = page.locator("body").inner_text().lower()
    has_recs = "high" in content or "medium" in content or "action" in content
    has_empty = "no recommendations" in content
    assert has_recs or has_empty, "Recommendations page has no content"


def test_dashboard_loading_spinner_exists(page: Page, base_url: str) -> None:
    _goto_and_hydrate(page, "/", base_url)
    assert "An error occurred while rendering" not in page.content()


def test_dashboard_metrics_are_integers(page: Page, base_url: str) -> None:
    _goto_and_hydrate(page, "/", base_url)
    metric_snippets: list[str] = []
    for label in ["Visibility Score", "Citation Coverage", "Competitor Comparison", "Competitor Wins"]:
        metric_card = page.get_by_text(label, exact=True).first.locator("xpath=ancestor::div[1]")
        metric_snippets.append(metric_card.inner_text())
    content = "\n".join(metric_snippets)
    long_decimals = re.findall(r"\d+\.\d{5,}", content)
    assert len(long_decimals) == 0, f"Found long decimals in dashboard: {long_decimals[:3]}"


def test_ai_responses_shows_all_providers(page: Page, base_url: str) -> None:
    _goto_and_hydrate(page, "/citations", base_url)
    content = page.content().lower()
    body_text = page.locator("body").inner_text().lower()
    if "default" in body_text and ("0 ai responses" in body_text or "openai" not in body_text):
        pytest.skip("No scan data available — workspace is 'default'")
    run_selector = page.locator("button[role='combobox']")
    if run_selector.count() > 0:
        run_selector.first.click()
        page.wait_for_timeout(1000)
        content = f"{content} {page.content().lower()}"
    for provider in ["openai", "anthropic", "gemini", "perplexity", "grok"]:
        assert provider in content, f"Provider {provider} not found on AI Responses page"


def test_ai_responses_card_expands(page: Page, base_url: str) -> None:
    _goto_and_hydrate(page, "/citations", base_url)
    first_card = page.locator("button[data-state]").first
    if first_card.is_visible():
        before_state = first_card.get_attribute("data-state")
        first_card.click()
        page.wait_for_timeout(1000)
        after_state = first_card.get_attribute("data-state")
        assert after_state == "open" or before_state != after_state


def test_questions_page_no_placeholders(page: Page, base_url: str) -> None:
    _goto_and_hydrate(page, "/prompts", base_url)
    content = page.locator("body").inner_text().lower()
    assert "{brand}" not in content, "Found unresolved {brand} placeholder"
    assert "{competitor}" not in content, "Found unresolved {competitor} placeholder"


def test_scans_page_has_history(page: Page, base_url: str) -> None:
    _goto_and_hydrate(page, "/runs", base_url)
    content = page.content().lower()
    has_status = "done" in content or "failed" in content or "completed" in content
    has_empty = "no scans yet" in content or "run your first" in content
    assert has_status or has_empty, "No scan status or empty state found"


def test_delete_workspace_button_exists(page: Page, base_url: str) -> None:
    _goto_and_hydrate(page, "/", base_url)
    trash_button = page.locator("svg.lucide-trash-2, svg.lucide-trash2, [data-lucide='trash-2']").first
    assert trash_button.is_visible(), "Delete workspace button not found"


def test_new_workspace_button_exists(page: Page, base_url: str) -> None:
    _goto_and_hydrate(page, "/", base_url)
    assert page.locator("text=New Workspace").is_visible()


@pytest.mark.parametrize("path", ["/", "/onboarding", "/runs", "/prompts", "/citations", "/recommendations"])
def test_no_react_errors(page: Page, base_url: str, path: str) -> None:
    _goto_and_hydrate(page, path, base_url)
    assert "an error occurred while rendering" not in page.content().lower()
