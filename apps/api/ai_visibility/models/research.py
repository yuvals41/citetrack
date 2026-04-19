"""Research request and response models."""

from __future__ import annotations

from pydantic import BaseModel, Field

from ai_visibility.models.onboarding import OnboardingCompetitor


class CompetitorDiscoveryRequest(BaseModel):
    domain: str = Field(min_length=3, max_length=255)
    industry: str = Field(default="", max_length=255)
    country_code: str = Field(default="", max_length=2)


class CompetitorDiscoveryResponse(BaseModel):
    competitors: list[OnboardingCompetitor]
    site_content: str = ""
    business_description: str = ""
    degraded: dict[str, str] | None = None
