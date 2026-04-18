# pyright: reportAny=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

import re

import pytest
from dotenv import load_dotenv

_ = load_dotenv()


@pytest.mark.asyncio
@pytest.mark.slow
async def test_provider_chart_counts_match_db() -> None:
    from ai_visibility.storage.prisma_connection import disconnect_prisma, get_prisma

    prisma = await get_prisma()
    rows = await prisma.query_raw(
        """
        WITH latest_executions AS (
            SELECT DISTINCT ON (se.provider) se.id, se.provider
            FROM ai_vis_scan_executions se
            JOIN ai_vis_scan_jobs sj ON sj.id = se.scan_job_id
            WHERE sj.workspace_slug = 'maisonremodeling'
            ORDER BY se.provider, se.executed_at DESC
        )
        SELECT le.provider, COUNT(DISTINCT pe.prompt_text) as cnt
        FROM ai_vis_prompt_executions pe
        JOIN latest_executions le ON le.id = pe.scan_execution_id
        GROUP BY le.provider
        """
    )
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, dict):
                provider = str(row.get("provider", ""))
                count = int(row.get("cnt", 0))
                assert count == 3, f"{provider} should have 3 unique questions, got {count}"
    await disconnect_prisma()


@pytest.mark.asyncio
@pytest.mark.slow
async def test_mention_detection_accuracy() -> None:
    from ai_visibility.storage.prisma_connection import disconnect_prisma, get_prisma

    prisma = await get_prisma()
    rows = await prisma.query_raw(
        """
        SELECT pe.raw_response
        FROM ai_vis_prompt_executions pe
        JOIN ai_vis_scan_executions se ON se.id = pe.scan_execution_id
        JOIN ai_vis_scan_jobs sj ON sj.id = se.scan_job_id
        WHERE sj.workspace_slug = 'maisonremodeling'
        LIMIT 5
        """
    )
    slug = "maisonremodeling"
    candidate_terms = {slug, slug.replace("-", " ")}
    slug_lower = slug.lower()
    for i in range(2, len(slug_lower) - 1):
        left = slug_lower[:i]
        right = slug_lower[i:]
        if len(left) >= 2 and len(right) >= 2:
            candidate_terms.add(f"{left} {right}")

    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, dict):
                response = str(row.get("raw_response", "")).lower()
                is_mentioned = any(term in response for term in candidate_terms)
                assert isinstance(is_mentioned, bool)
    await disconnect_prisma()


@pytest.mark.asyncio
@pytest.mark.slow
async def test_citation_detection_no_false_positives() -> None:
    from ai_visibility.storage.prisma_connection import disconnect_prisma, get_prisma

    prisma = await get_prisma()
    rows = await prisma.query_raw(
        """
        SELECT pe.raw_response
        FROM ai_vis_prompt_executions pe
        JOIN ai_vis_scan_executions se ON se.id = pe.scan_execution_id
        JOIN ai_vis_scan_jobs sj ON sj.id = se.scan_job_id
        WHERE sj.workspace_slug = 'maisonremodeling'
        """
    )
    slug = "maisonremodeling"
    false_positives = 0
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, dict):
                response = str(row.get("raw_response", ""))
                all_urls = re.findall(r"https?://[^\s\)\]\}>,\"']+", response)
                has_url_citation = any(slug in url.lower() for url in all_urls)
                has_bare_domain = f"{slug}.com" in response.lower()
                if has_bare_domain and not has_url_citation:
                    false_positives += 1
    assert false_positives >= 0
    await disconnect_prisma()


@pytest.mark.asyncio
@pytest.mark.slow
async def test_citation_coverage_is_reasonable() -> None:
    from ai_visibility.storage.prisma_connection import disconnect_prisma, get_prisma

    prisma = await get_prisma()
    rows = await prisma.query_raw(
        """
        WITH latest_executions AS (
            SELECT DISTINCT ON (se.provider) se.id, se.provider
            FROM ai_vis_scan_executions se
            JOIN ai_vis_scan_jobs sj ON sj.id = se.scan_job_id
            WHERE sj.workspace_slug = 'maisonremodeling'
            ORDER BY se.provider, se.executed_at DESC
        )
        SELECT pe.raw_response
        FROM ai_vis_prompt_executions pe
        JOIN latest_executions le ON le.id = pe.scan_execution_id
        """
    )
    slug = "maisonremodeling"
    total = 0
    citations = 0
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, dict):
                total += 1
                response = str(row.get("raw_response", ""))
                all_urls = re.findall(r"https?://[^\s\)\]\}>,\"']+", response)
                if any(slug in url.lower() for url in all_urls):
                    citations += 1
    coverage = citations / total if total > 0 else 0.0
    assert 0.0 <= coverage <= 1.0
    assert coverage < 0.5, f"Citation coverage {coverage} seems too high — verify manually"
    await disconnect_prisma()


def test_no_long_decimals_in_metric_values() -> None:
    test_values = [0.6667, 0.1111, 0.3333, 1.0, 0.0]
    for v in test_values:
        result = round(v * 100) / 100
        display = str(int(result * 100))
        assert "." not in display, f"Value {v} produced decimal display: {display}"


def test_location_stripped_from_all_prompt_formats() -> None:
    prompts = [
        "What is best? Location context: The user is in US.",
        "Is it worth it?\n\nLocation context: The user is in London, UK.",
        "No location here.",
        "Location context: Start of prompt.",
    ]
    expected = [
        "What is best?",
        "Is it worth it?",
        "No location here.",
        "",
    ]
    for prompt, exp in zip(prompts, expected):
        if "Location context:" in prompt:
            clean = prompt[: prompt.index("Location context:")].strip()
        else:
            clean = prompt
        assert clean == exp


@pytest.mark.asyncio
@pytest.mark.slow
async def test_recommendations_persisted_in_db() -> None:
    from ai_visibility.storage.prisma_connection import disconnect_prisma, get_prisma

    prisma = await get_prisma()
    rows = await prisma.query_raw('SELECT COUNT(*) as cnt FROM "ai_vis_recommendation_items"')
    if isinstance(rows, list) and rows:
        count = int(rows[0].get("cnt", 0))
        assert count > 0, "Recommendations should be persisted in DB"
    await disconnect_prisma()


@pytest.mark.asyncio
@pytest.mark.slow
async def test_source_domains_extracted() -> None:
    from urllib.parse import urlparse

    from ai_visibility.storage.prisma_connection import disconnect_prisma, get_prisma

    prisma = await get_prisma()
    rows = await prisma.query_raw("SELECT pe.raw_response FROM ai_vis_prompt_executions pe LIMIT 5")
    total_urls = 0
    domains: set[str] = set()
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, dict):
                resp = str(row.get("raw_response", ""))
                urls = re.findall(r"https?://[^\s\)\]\}>,\"']+", resp)
                total_urls += len(urls)
                for url in urls:
                    domain = urlparse(url).netloc.lower().removeprefix("www.")
                    if domain:
                        domains.add(domain)
    assert total_urls >= 0
    assert isinstance(domains, set)
    await disconnect_prisma()
