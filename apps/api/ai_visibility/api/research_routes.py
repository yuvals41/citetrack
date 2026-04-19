# pyright: reportMissingImports=false

from __future__ import annotations

import os

from fastapi import APIRouter
from loguru import logger

from ai_visibility.api.auth import CurrentUserId
from ai_visibility.models.onboarding import OnboardingCompetitor
from ai_visibility.models.research import CompetitorDiscoveryRequest, CompetitorDiscoveryResponse
from ai_visibility.services.competitor_discovery import _extract_domain, discover_competitors_with_site_content

router = APIRouter(tags=["research"])


def _parse_entry(entry: str) -> OnboardingCompetitor | None:
    domain = _extract_domain(entry)
    if not domain:
        return None
    name = entry.split("(")[0].strip() or domain
    try:
        return OnboardingCompetitor(name=name, domain=domain)
    except Exception:
        return None


def _check_required_api_keys() -> dict[str, str] | None:
    has_search_provider = bool(os.getenv("EXA_API_KEY") or os.getenv("TAVILY_API_KEY"))
    has_llm_filter = bool(os.getenv("ANTHROPIC_API_KEY"))
    if has_search_provider and has_llm_filter:
        return None
    missing = []
    if not has_search_provider:
        missing.append("EXA_API_KEY or TAVILY_API_KEY")
    if not has_llm_filter:
        missing.append("ANTHROPIC_API_KEY")
    return {
        "reason": "missing_api_keys",
        "message": (
            f"Research is disabled until you set {' and '.join(missing)} in apps/api/.env. "
            "EXA/TAVILY finds candidate companies, ANTHROPIC's Claude filters them to real competitors. "
            "Get keys at https://exa.ai, https://tavily.com, https://console.anthropic.com."
        ),
    }


@router.post("/research/competitors", response_model=CompetitorDiscoveryResponse)
async def research_competitors(
    request: CompetitorDiscoveryRequest,
    user_id: CurrentUserId,
) -> CompetitorDiscoveryResponse:
    _ = user_id
    logger.info(
        "research.start domain={} industry={!r} country={!r}",
        request.domain,
        request.industry or None,
        request.country_code or None,
    )

    if (missing := _check_required_api_keys()) is not None:
        logger.warning(
            "research.skipped reason={} domain={}",
            missing["reason"],
            request.domain,
        )
        return CompetitorDiscoveryResponse(
            competitors=[],
            site_content="",
            business_description="",
            degraded=missing,
        )

    try:
        raw, site_content = await discover_competitors_with_site_content(
            domain=request.domain,
            industry=request.industry,
            country_code=request.country_code,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("research.failed domain={} error={}", request.domain, exc)
        return CompetitorDiscoveryResponse(
            competitors=[],
            site_content="",
            business_description="",
            degraded={"reason": "discovery_failed", "message": str(exc)},
        )

    parsed = [competitor for entry in raw if (competitor := _parse_entry(entry)) is not None]
    kept = parsed[:5]
    logger.info(
        "research.complete domain={} candidates={} kept={} site_content_chars={}",
        request.domain,
        len(raw),
        len(kept),
        len(site_content),
    )
    return CompetitorDiscoveryResponse(
        competitors=kept,
        site_content=site_content,
        business_description="",
    )
