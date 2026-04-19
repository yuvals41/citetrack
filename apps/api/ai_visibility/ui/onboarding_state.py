from __future__ import annotations

from dataclasses import dataclass, field

from ai_visibility.services.competitor_discovery import (
    COUNTRIES,
    COUNTRY_CODE_TO_NAME,
    _describe_business,
    _extract_domain,
    _filter_direct_competitors,
    _find_competitors_exa,
    _find_competitors_tavily_gpt,
    _humanize_brand,
    _validate_domains,
    discover_competitors_with_site_content,
)

_discover_competitors_with_site_content = discover_competitors_with_site_content


@dataclass
class OnboardingState:
    domain: str = ""
    industry: str = ""
    custom_industry: str = ""
    city: str = ""
    region: str = ""
    city_suggestions: list[str] = field(default_factory=list)
    city_search_query: str = ""

    def _clean_domain(self) -> str:
        domain = self.domain.strip().rstrip("/")
        for prefix in ("https://", "http://"):
            if domain.lower().startswith(prefix):
                domain = domain[len(prefix) :]
        return domain.split("/")[0]

    def _effective_industry(self) -> str:
        if self.industry == "Other" and self.custom_industry.strip():
            return self.custom_industry.strip()
        return self.industry

    def select_city(self, display: str) -> None:
        parts = [part.strip() for part in display.split(",")]
        self.city = parts[0] if parts else ""
        self.region = parts[1] if len(parts) > 1 else ""
        self.city_search_query = ""
        self.city_suggestions = []
