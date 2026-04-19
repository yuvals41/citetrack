# pyright: reportMissingImports=false

from __future__ import annotations

from fastapi import APIRouter
from loguru import logger

from ai_visibility.api.auth import CurrentUserId
from ai_visibility.models.onboarding import OnboardingCompetitor
from ai_visibility.models.research import CompetitorDiscoveryRequest, CompetitorDiscoveryResponse
from ai_visibility.services.competitor_discovery import _extract_domain, discover_competitors_with_site_content

router = APIRouter(tags=["research"])


def _parse_entry(entry: str) -> OnboardingCompetitor | None:
    """Turn discovery entry strings into onboarding competitors."""
    domain = _extract_domain(entry)
    if not domain:
        return None
    name = entry.split("(")[0].strip() or domain
    try:
        return OnboardingCompetitor(name=name, domain=domain)
    except Exception:
        return None


@router.post("/research/competitors", response_model=CompetitorDiscoveryResponse)
async def research_competitors(
    request: CompetitorDiscoveryRequest,
    user_id: CurrentUserId,
) -> CompetitorDiscoveryResponse:
    _ = user_id
    try:
        raw, site_content = await discover_competitors_with_site_content(
            domain=request.domain,
            industry=request.industry,
            country_code=request.country_code,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Competitor research failed for {}", request.domain)
        return CompetitorDiscoveryResponse(
            competitors=[],
            site_content="",
            business_description="",
            degraded={"reason": f"discovery_failed: {exc}"},
        )

    parsed = [competitor for entry in raw if (competitor := _parse_entry(entry)) is not None]
    return CompetitorDiscoveryResponse(
        competitors=parsed[:5],
        site_content=site_content,
        business_description="",
    )
