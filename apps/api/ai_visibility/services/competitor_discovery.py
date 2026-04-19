# pyright: reportMissingImports=false

"""Competitor discovery pipeline: Exa + Tavily + Claude.

Ported from ai-visibility/ai_visibility/ui/onboarding_state.py for use in
FastAPI endpoints (no Reflex dependency).
"""

from __future__ import annotations

import asyncio
import json
import os
import re
from typing import cast
from urllib.parse import urlparse

import httpx
from loguru import logger


ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
EXA_SEARCH_URL = "https://api.exa.ai/search"
EXA_CONTENTS_URL = "https://api.exa.ai/contents"
TAVILY_SEARCH_URL = "https://api.tavily.com/search"
TAVILY_EXTRACT_URL = "https://api.tavily.com/extract"
DEFAULT_HTTP_TIMEOUT_SECONDS = 30.0
DOMAIN_VALIDATION_TIMEOUT_SECONDS = 8.0
DOMAIN_VALIDATION_GET_TIMEOUT_SECONDS = 5.0
COMPETITOR_FILTER_TIMEOUT_SECONDS = 120.0
ANTHROPIC_MODEL = "claude-sonnet-4-6"


def _extract_json(text: str) -> str:
    """Extract JSON from Claude response (may have markdown code blocks)."""
    text = text.strip()
    if "```" in text:
        parts = text.split("```")
        for part in parts[1:]:
            if part.startswith("json"):
                part = part[4:]
            part = part.strip()
            if part.startswith("{") or part.startswith("["):
                return part
    if text.startswith("{") or text.startswith("["):
        return text
    start = text.find("{")
    if start == -1:
        start = text.find("[")
    if start >= 0:
        return text[start:]
    return text


def _humanize_brand(domain_slug: str) -> str:
    """Convert domain slug to readable brand name."""
    name = domain_slug.split(".")[0]
    name = name.replace("-", " ").replace("_", " ")
    name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
    return name.title()


COUNTRIES: list[dict[str, str]] = [
    {"code": "AF", "name": "Afghanistan"},
    {"code": "AL", "name": "Albania"},
    {"code": "DZ", "name": "Algeria"},
    {"code": "AS", "name": "American Samoa"},
    {"code": "AD", "name": "Andorra"},
    {"code": "AO", "name": "Angola"},
    {"code": "AI", "name": "Anguilla"},
    {"code": "AQ", "name": "Antarctica"},
    {"code": "AG", "name": "Antigua and Barbuda"},
    {"code": "AR", "name": "Argentina"},
    {"code": "AM", "name": "Armenia"},
    {"code": "AW", "name": "Aruba"},
    {"code": "AU", "name": "Australia"},
    {"code": "AT", "name": "Austria"},
    {"code": "AZ", "name": "Azerbaijan"},
    {"code": "BS", "name": "Bahamas"},
    {"code": "BH", "name": "Bahrain"},
    {"code": "BD", "name": "Bangladesh"},
    {"code": "BB", "name": "Barbados"},
    {"code": "BY", "name": "Belarus"},
    {"code": "BE", "name": "Belgium"},
    {"code": "BZ", "name": "Belize"},
    {"code": "BJ", "name": "Benin"},
    {"code": "BM", "name": "Bermuda"},
    {"code": "BT", "name": "Bhutan"},
    {"code": "BO", "name": "Bolivia"},
    {"code": "BA", "name": "Bosnia and Herzegovina"},
    {"code": "BW", "name": "Botswana"},
    {"code": "BV", "name": "Bouvet Island"},
    {"code": "BR", "name": "Brazil"},
    {"code": "IO", "name": "British Indian Ocean Territory"},
    {"code": "BN", "name": "Brunei"},
    {"code": "BG", "name": "Bulgaria"},
    {"code": "BF", "name": "Burkina Faso"},
    {"code": "BI", "name": "Burundi"},
    {"code": "KH", "name": "Cambodia"},
    {"code": "CM", "name": "Cameroon"},
    {"code": "CA", "name": "Canada"},
    {"code": "CV", "name": "Cape Verde"},
    {"code": "KY", "name": "Cayman Islands"},
    {"code": "CF", "name": "Central African Republic"},
    {"code": "TD", "name": "Chad"},
    {"code": "CL", "name": "Chile"},
    {"code": "CN", "name": "China"},
    {"code": "CX", "name": "Christmas Island"},
    {"code": "CC", "name": "Cocos Islands"},
    {"code": "CO", "name": "Colombia"},
    {"code": "KM", "name": "Comoros"},
    {"code": "CG", "name": "Congo"},
    {"code": "CD", "name": "Congo (Democratic Republic)"},
    {"code": "CK", "name": "Cook Islands"},
    {"code": "CR", "name": "Costa Rica"},
    {"code": "HR", "name": "Croatia"},
    {"code": "CU", "name": "Cuba"},
    {"code": "CY", "name": "Cyprus"},
    {"code": "CZ", "name": "Czech Republic"},
    {"code": "DK", "name": "Denmark"},
    {"code": "DJ", "name": "Djibouti"},
    {"code": "DM", "name": "Dominica"},
    {"code": "DO", "name": "Dominican Republic"},
    {"code": "EC", "name": "Ecuador"},
    {"code": "EG", "name": "Egypt"},
    {"code": "SV", "name": "El Salvador"},
    {"code": "GQ", "name": "Equatorial Guinea"},
    {"code": "ER", "name": "Eritrea"},
    {"code": "EE", "name": "Estonia"},
    {"code": "ET", "name": "Ethiopia"},
    {"code": "FK", "name": "Falkland Islands"},
    {"code": "FO", "name": "Faroe Islands"},
    {"code": "FJ", "name": "Fiji"},
    {"code": "FI", "name": "Finland"},
    {"code": "FR", "name": "France"},
    {"code": "GF", "name": "French Guiana"},
    {"code": "PF", "name": "French Polynesia"},
    {"code": "TF", "name": "French Southern Territories"},
    {"code": "GA", "name": "Gabon"},
    {"code": "GM", "name": "Gambia"},
    {"code": "GE", "name": "Georgia"},
    {"code": "DE", "name": "Germany"},
    {"code": "GH", "name": "Ghana"},
    {"code": "GI", "name": "Gibraltar"},
    {"code": "GR", "name": "Greece"},
    {"code": "GL", "name": "Greenland"},
    {"code": "GD", "name": "Grenada"},
    {"code": "GP", "name": "Guadeloupe"},
    {"code": "GU", "name": "Guam"},
    {"code": "GT", "name": "Guatemala"},
    {"code": "GG", "name": "Guernsey"},
    {"code": "GN", "name": "Guinea"},
    {"code": "GW", "name": "Guinea-Bissau"},
    {"code": "GY", "name": "Guyana"},
    {"code": "HT", "name": "Haiti"},
    {"code": "HM", "name": "Heard Island and McDonald Islands"},
    {"code": "HN", "name": "Honduras"},
    {"code": "HK", "name": "Hong Kong"},
    {"code": "HU", "name": "Hungary"},
    {"code": "IS", "name": "Iceland"},
    {"code": "IN", "name": "India"},
    {"code": "ID", "name": "Indonesia"},
    {"code": "IR", "name": "Iran"},
    {"code": "IQ", "name": "Iraq"},
    {"code": "IE", "name": "Ireland"},
    {"code": "IM", "name": "Isle of Man"},
    {"code": "IL", "name": "Israel"},
    {"code": "IT", "name": "Italy"},
    {"code": "CI", "name": "Ivory Coast"},
    {"code": "JM", "name": "Jamaica"},
    {"code": "JP", "name": "Japan"},
    {"code": "JE", "name": "Jersey"},
    {"code": "JO", "name": "Jordan"},
    {"code": "KZ", "name": "Kazakhstan"},
    {"code": "KE", "name": "Kenya"},
    {"code": "KI", "name": "Kiribati"},
    {"code": "KP", "name": "Korea (North)"},
    {"code": "KR", "name": "Korea (South)"},
    {"code": "KW", "name": "Kuwait"},
    {"code": "KG", "name": "Kyrgyzstan"},
    {"code": "LA", "name": "Laos"},
    {"code": "LV", "name": "Latvia"},
    {"code": "LB", "name": "Lebanon"},
    {"code": "LS", "name": "Lesotho"},
    {"code": "LR", "name": "Liberia"},
    {"code": "LY", "name": "Libya"},
    {"code": "LI", "name": "Liechtenstein"},
    {"code": "LT", "name": "Lithuania"},
    {"code": "LU", "name": "Luxembourg"},
    {"code": "MO", "name": "Macao"},
    {"code": "MK", "name": "Macedonia"},
    {"code": "MG", "name": "Madagascar"},
    {"code": "MW", "name": "Malawi"},
    {"code": "MY", "name": "Malaysia"},
    {"code": "MV", "name": "Maldives"},
    {"code": "ML", "name": "Mali"},
    {"code": "MT", "name": "Malta"},
    {"code": "MH", "name": "Marshall Islands"},
    {"code": "MQ", "name": "Martinique"},
    {"code": "MR", "name": "Mauritania"},
    {"code": "MU", "name": "Mauritius"},
    {"code": "YT", "name": "Mayotte"},
    {"code": "MX", "name": "Mexico"},
    {"code": "FM", "name": "Micronesia"},
    {"code": "MD", "name": "Moldova"},
    {"code": "MC", "name": "Monaco"},
    {"code": "MN", "name": "Mongolia"},
    {"code": "ME", "name": "Montenegro"},
    {"code": "MA", "name": "Morocco"},
    {"code": "MZ", "name": "Mozambique"},
    {"code": "MM", "name": "Myanmar"},
    {"code": "NA", "name": "Namibia"},
    {"code": "NR", "name": "Nauru"},
    {"code": "NP", "name": "Nepal"},
    {"code": "NL", "name": "Netherlands"},
    {"code": "AN", "name": "Netherlands Antilles"},
    {"code": "NC", "name": "New Caledonia"},
    {"code": "NZ", "name": "New Zealand"},
    {"code": "NI", "name": "Nicaragua"},
    {"code": "NE", "name": "Niger"},
    {"code": "NG", "name": "Nigeria"},
    {"code": "NU", "name": "Niue"},
    {"code": "NF", "name": "Norfolk Island"},
    {"code": "MP", "name": "Northern Mariana Islands"},
    {"code": "NO", "name": "Norway"},
    {"code": "OM", "name": "Oman"},
    {"code": "PK", "name": "Pakistan"},
    {"code": "PW", "name": "Palau"},
    {"code": "PS", "name": "Palestine"},
    {"code": "PA", "name": "Panama"},
    {"code": "PG", "name": "Papua New Guinea"},
    {"code": "PY", "name": "Paraguay"},
    {"code": "PE", "name": "Peru"},
    {"code": "PH", "name": "Philippines"},
    {"code": "PN", "name": "Pitcairn Islands"},
    {"code": "PL", "name": "Poland"},
    {"code": "PT", "name": "Portugal"},
    {"code": "PR", "name": "Puerto Rico"},
    {"code": "QA", "name": "Qatar"},
    {"code": "RE", "name": "Reunion"},
    {"code": "RO", "name": "Romania"},
    {"code": "RU", "name": "Russia"},
    {"code": "RW", "name": "Rwanda"},
    {"code": "BL", "name": "Saint Barthelemy"},
    {"code": "SH", "name": "Saint Helena"},
    {"code": "KN", "name": "Saint Kitts and Nevis"},
    {"code": "LC", "name": "Saint Lucia"},
    {"code": "MF", "name": "Saint Martin"},
    {"code": "PM", "name": "Saint Pierre and Miquelon"},
    {"code": "VC", "name": "Saint Vincent and the Grenadines"},
    {"code": "WS", "name": "Samoa"},
    {"code": "SM", "name": "San Marino"},
    {"code": "ST", "name": "Sao Tome and Principe"},
    {"code": "SA", "name": "Saudi Arabia"},
    {"code": "SN", "name": "Senegal"},
    {"code": "RS", "name": "Serbia"},
    {"code": "SC", "name": "Seychelles"},
    {"code": "SL", "name": "Sierra Leone"},
    {"code": "SG", "name": "Singapore"},
    {"code": "SK", "name": "Slovakia"},
    {"code": "SI", "name": "Slovenia"},
    {"code": "SB", "name": "Solomon Islands"},
    {"code": "SO", "name": "Somalia"},
    {"code": "ZA", "name": "South Africa"},
    {"code": "GS", "name": "South Georgia and the South Sandwich Islands"},
    {"code": "SS", "name": "South Sudan"},
    {"code": "ES", "name": "Spain"},
    {"code": "LK", "name": "Sri Lanka"},
    {"code": "SD", "name": "Sudan"},
    {"code": "SR", "name": "Suriname"},
    {"code": "SJ", "name": "Svalbard and Jan Mayen"},
    {"code": "SZ", "name": "Swaziland"},
    {"code": "SE", "name": "Sweden"},
    {"code": "CH", "name": "Switzerland"},
    {"code": "SY", "name": "Syria"},
    {"code": "TW", "name": "Taiwan"},
    {"code": "TJ", "name": "Tajikistan"},
    {"code": "TZ", "name": "Tanzania"},
    {"code": "TH", "name": "Thailand"},
    {"code": "TL", "name": "Timor-Leste"},
    {"code": "TG", "name": "Togo"},
    {"code": "TK", "name": "Tokelau"},
    {"code": "TO", "name": "Tonga"},
    {"code": "TT", "name": "Trinidad and Tobago"},
    {"code": "TN", "name": "Tunisia"},
    {"code": "TR", "name": "Turkey"},
    {"code": "TM", "name": "Turkmenistan"},
    {"code": "TC", "name": "Turks and Caicos Islands"},
    {"code": "TV", "name": "Tuvalu"},
    {"code": "UG", "name": "Uganda"},
    {"code": "UA", "name": "Ukraine"},
    {"code": "AE", "name": "United Arab Emirates"},
    {"code": "GB", "name": "United Kingdom"},
    {"code": "US", "name": "United States"},
    {"code": "UM", "name": "United States Minor Outlying Islands"},
    {"code": "UY", "name": "Uruguay"},
    {"code": "UZ", "name": "Uzbekistan"},
    {"code": "VU", "name": "Vanuatu"},
    {"code": "VA", "name": "Vatican City"},
    {"code": "VE", "name": "Venezuela"},
    {"code": "VN", "name": "Vietnam"},
    {"code": "VG", "name": "Virgin Islands (British)"},
    {"code": "VI", "name": "Virgin Islands (U.S.)"},
    {"code": "WF", "name": "Wallis and Futuna"},
    {"code": "EH", "name": "Western Sahara"},
    {"code": "YE", "name": "Yemen"},
    {"code": "ZM", "name": "Zambia"},
    {"code": "ZW", "name": "Zimbabwe"},
]

COUNTRY_CODE_TO_NAME: dict[str, str] = {country["code"]: country["name"] for country in COUNTRIES}
COUNTRY_NAME_TO_CODE: dict[str, str] = {country["name"].lower(): country["code"] for country in COUNTRIES}
COUNTRY_NAME_TO_CODE.update(
    {
        "uk": "GB",
        "u.k.": "GB",
        "great britain": "GB",
        "england": "GB",
        "usa": "US",
        "u.s.": "US",
        "u.s.a.": "US",
    }
)


def _extract_domain(entry: str) -> str:
    start = entry.find("(")
    end = entry.find(")", start) if start != -1 else -1
    if start != -1 and end != -1 and end > start:
        return entry[start + 1 : end].strip()
    return ""


async def _validate_domains(entries: list[str]) -> list[str]:
    logger.info(f"[validate] checking {len(entries)} domains")
    validated: list[str] = []
    async with httpx.AsyncClient(timeout=DOMAIN_VALIDATION_TIMEOUT_SECONDS, follow_redirects=True) as client:
        for entry in entries:
            domain = _extract_domain(entry)
            if not domain:
                logger.debug(f"[validate] no domain extracted from: {entry[:60]}")
                continue
            try:
                response = await client.head(f"https://{domain}")
                logger.debug(f"[validate] {domain} HEAD → {response.status_code}")
                if response.status_code < 500:
                    validated.append(entry)
                    continue
            except Exception as exc:  # noqa: BLE001
                logger.debug(f"[validate] {domain} HEAD failed: {type(exc).__name__}")
            try:
                response = await client.get(f"https://{domain}", timeout=DOMAIN_VALIDATION_GET_TIMEOUT_SECONDS)
                logger.debug(f"[validate] {domain} GET → {response.status_code}")
                if response.status_code < 500:
                    validated.append(entry)
            except Exception as exc:  # noqa: BLE001
                logger.debug(f"[validate] {domain} GET failed: {type(exc).__name__}")
    logger.info(f"[validate] {len(validated)}/{len(entries)} passed")
    return validated


async def _filter_direct_competitors(
    candidates: list[str],
    business_description: str,
    domain: str,
    industry: str,
    country_code: str = "",
) -> list[str]:
    logger.info(f"[filter] filtering {len(candidates)} candidates for {domain}")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not anthropic_key or not candidates:
        logger.warning("[filter] no API key or empty candidates, returning as-is")
        return candidates

    try:
        async with httpx.AsyncClient(timeout=COMPETITOR_FILTER_TIMEOUT_SECONDS) as client:
            instructions = (
                "You are a competitor analysis expert. Given a business and a list of candidate competitors, "
                "determine which candidates are TRUE direct competitors — companies that a customer would "
                "realistically choose between.\n\n"
                "To decide, reason through these questions for each candidate:\n"
                "1. Do they offer the same type of product or service?\n"
                "2. Do they serve the same target customer?\n"
                "3. Are they a similar scale? (A 2-person startup and a 500-person enterprise are not peers.)\n"
                "4. If the business is local, are candidates in the same area?\n"
                "5. Is the candidate an actual business, or a directory/marketplace/review site/listicle?\n\n"
                "Remove anything that is NOT a direct competitor: directories, marketplaces, review aggregators, "
                "listicle articles, companies in a different industry, or companies that are dramatically "
                "larger or smaller than the business.\n\n"
                "The candidate descriptions may include employee counts and revenue — use this to assess scale.\n\n"
                'Return ONLY valid JSON: {"competitors": ["Name (domain.com)", ...]}\n'
                "Strip any description text after the domain. Return an empty list if none qualify."
            )
            country_name = COUNTRY_CODE_TO_NAME.get(country_code.upper(), "") if country_code else ""
            location_ctx = f"\nLocation: {country_name}\n" if country_name else "\n"
            input_text = (
                f"Business: {domain} ({industry})\n"
                f"Description: {business_description[:300]}"
                f"{location_ctx}\n"
                f"Candidate competitors:\n"
                + "\n".join(f"- {candidate}" for candidate in candidates)
                + "\n\nWhich of these are true direct competitors? Prefer companies in the same country."
            )

            response = await client.post(
                ANTHROPIC_MESSAGES_URL,
                headers={
                    "x-api-key": anthropic_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": ANTHROPIC_MODEL,
                    "max_tokens": 8000,
                    "thinking": {"type": "adaptive"},
                    "messages": [{"role": "user", "content": f"{instructions}\n\n{input_text}"}],
                },
            )
            _ = response.raise_for_status()
            data = cast(dict[str, object], response.json())

            content = data.get("content", [])
            text = ""
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text = str(block.get("text", "{}"))
                        break
            json_str = _extract_json(text) if text else "{}"
            parsed = cast(dict[str, object], json.loads(json_str))
            filtered = parsed.get("competitors", [])
            logger.info(
                f"[filter] Claude returned {len(filtered) if isinstance(filtered, list) else 'non-list'}: {filtered}"
            )
            if isinstance(filtered, list):
                cleaned: list[str] = []
                for competitor in filtered:
                    if not isinstance(competitor, str):
                        continue
                    if " — " in competitor:
                        competitor = competitor[: competitor.index(" — ")]
                    cleaned.append(competitor.strip())
                logger.info(f"[filter] final {len(cleaned)}: {cleaned}")
                return cleaned
            return candidates
    except Exception as exc:  # noqa: BLE001
        logger.error(f"[filter] failed: {type(exc).__name__}: {exc}")
        return candidates


async def _describe_business(site_content: str, domain: str, industry: str, country_code: str = "") -> str:
    logger.info(f"[describe] generating business description for {domain}")
    cleaned = re.sub(r"<[^>]+>", " ", site_content or "")
    cleaned = re.sub(r"!?\[[^\]]*\]\([^)]*\)", " ", cleaned)
    cleaned = re.sub(r"https?://\S+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    content_snippet = cleaned[:1500]

    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not anthropic_key:
        logger.warning("[describe] missing ANTHROPIC_API_KEY, fallback to industry")
        return industry
    if not content_snippet:
        logger.warning("[describe] empty site content after cleaning, fallback to industry")
        return industry

    country_name = COUNTRY_CODE_TO_NAME.get(country_code.upper(), "") if country_code else ""
    country_line = f"Country hint: {country_name}\n" if country_name else ""

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_HTTP_TIMEOUT_SECONDS) as client:
            prompt = (
                "Based on this website content, write a single sentence describing what this business does, "
                "including its location if detectable. Be specific about the product/service type. "
                "Example: 'AI-powered social media marketing platform that creates and schedules content' "
                "or 'home remodeling contractor serving Santa Clara and Bay Area California' "
                "or 'lifestyle coaching and personal development services in London UK'. "
                "Do NOT include the company name."
            )
            response = await client.post(
                ANTHROPIC_MESSAGES_URL,
                headers={
                    "x-api-key": anthropic_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": ANTHROPIC_MODEL,
                    "max_tokens": 256,
                    "messages": [
                        {
                            "role": "user",
                            "content": (
                                f"{prompt}\n\n"
                                f"Domain: {domain}\n"
                                f"Industry from user: {industry}\n"
                                f"{country_line}"
                                f"Website content:\n{content_snippet}"
                            ),
                        }
                    ],
                },
            )
            _ = response.raise_for_status()
            data = cast(dict[str, object], response.json())
            content = data.get("content", [])
            description = ""
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        description = str(block.get("text", "")).strip()
                        break
            if description:
                description = description.split("\n", 1)[0].strip().strip('"')
                logger.info(f"[describe] generated description: {description[:160]}")
                return description
            logger.warning("[describe] empty Claude response, fallback to industry")
            return industry
    except Exception as exc:  # noqa: BLE001
        logger.error(f"[describe] failed: {type(exc).__name__}: {exc}")
        return industry


async def _find_competitors_exa(domain: str, business_description: str, country_code: str = "") -> list[str]:
    logger.info(f"[exa] searching competitors for {domain}")
    exa_key = os.getenv("EXA_API_KEY", "")
    if not exa_key:
        logger.warning("[exa] no API key")
        return []

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            country_name = COUNTRY_CODE_TO_NAME.get(country_code.upper(), "") if country_code else ""
            cc_lower = country_code.lower() if country_code else None

            query = f"{business_description}".strip()
            normalized_domain = domain.lower()
            if country_name and not normalized_domain.endswith(".com"):
                query = f"{query} {country_name}"
            logger.debug(f"[exa] query: {query}")

            response = await client.post(
                EXA_SEARCH_URL,
                headers={"x-api-key": exa_key, "Content-Type": "application/json"},
                json={
                    key: value
                    for key, value in {
                        "query": query,
                        "numResults": 10,
                        "category": "company",
                        "type": "auto",
                        "contents": {
                            "summary": {"query": "What does this company do?"},
                            "text": {"maxCharacters": 200},
                        },
                        "userLocation": cc_lower,
                    }.items()
                    if value is not None
                },
            )
            _ = response.raise_for_status()
            payload = cast(dict[str, object], response.json())
            results_raw = payload.get("results", [])
            results = (
                [result for result in results_raw if isinstance(result, dict)] if isinstance(results_raw, list) else []
            )
            logger.info(f"[exa] total raw results: {len(results)}")

            competitors: list[str] = []
            seen_domains: set[str] = set()
            domain_base = domain.split(".")[0].lower().replace("-", "").replace("www", "")

            for result in results:
                title = str(result.get("title", "")).strip()
                url = str(result.get("url", "")).strip()
                normalized_url = url.lower().replace("www.", "")

                if domain_base and domain_base in normalized_url:
                    logger.debug(f"[exa] skipping {url}: self-domain")
                    continue

                parsed_check = urlparse(url if url.startswith(("http://", "https://")) else f"https://{url}")
                path = parsed_check.path.rstrip("/").lower()
                if len(path) > 1 and any(
                    pattern in path
                    for pattern in [
                        "/blog",
                        "/article",
                        "/news",
                        "/best-",
                        "/top-",
                        "/alternatives",
                        "/compare",
                        "/vs-",
                        "/review",
                        "/list",
                    ]
                ):
                    logger.debug(f"[exa] skipping {url}: listicle/directory path")
                    continue

                title_lower = title.lower()
                if any(
                    pattern in title_lower
                    for pattern in ["top 1", "top 2", "top 3", "top 5", "best ", "vs ", " alternatives", " comparison"]
                ):
                    logger.debug(f"[exa] skipping {title}: listicle title")
                    continue

                parsed = urlparse(url if url.startswith(("http://", "https://")) else f"https://{url}")
                comp_domain = parsed.netloc.lower().removeprefix("www.")
                news_patterns = (
                    "post.com",
                    "times.com",
                    "herald.com",
                    "tribune.com",
                    "gazette.com",
                    "journal.com",
                    "news.com",
                )
                is_news = any(comp_domain.endswith(pattern) for pattern in news_patterns)
                if is_news:
                    logger.debug(f"[exa] skipping {comp_domain}: news site")
                    continue
                if comp_domain in (
                    "reddit.com",
                    "f6s.com",
                    "g2.com",
                    "capterra.com",
                    "crunchbase.com",
                    "linkedin.com",
                    "facebook.com",
                    "twitter.com",
                    "x.com",
                    "instagram.com",
                    "youtube.com",
                    "tiktok.com",
                    "medium.com",
                    "wikipedia.org",
                    "github.com",
                    "producthunt.com",
                    "trustpilot.com",
                    "yelp.com",
                    "bbb.org",
                    "glassdoor.com",
                    "indeed.com",
                    "angel.co",
                    "wellfound.com",
                ):
                    logger.debug(f"[exa] skipping {comp_domain}: directory/platform")
                    continue

                if not title or not comp_domain:
                    continue

                title_words = [word.lower().replace(".", "") for word in re.split(r"[\s\-_:]+", title) if len(word) > 3]
                domain_flat = comp_domain.lower().replace("-", "").replace(".", "")
                has_overlap = any(word in domain_flat for word in title_words if len(word) > 3)
                if not has_overlap:
                    logger.debug(f"[exa] domain mismatch: '{title}' vs '{comp_domain}', looking up real domain")
                    try:
                        lookup_response = await client.post(
                            EXA_SEARCH_URL,
                            headers={"x-api-key": exa_key, "Content-Type": "application/json"},
                            json={
                                "query": title,
                                "numResults": 1,
                                "category": "company",
                                "type": "auto",
                                "contents": {"text": {"maxCharacters": 50}},
                            },
                        )
                        lookup_data = cast(dict[str, object], lookup_response.json())
                        lookup_results = lookup_data.get("results", [])
                        if isinstance(lookup_results, list) and lookup_results:
                            first = lookup_results[0]
                            if isinstance(first, dict):
                                lookup_url = str(first.get("url", ""))
                                lookup_parsed = urlparse(
                                    lookup_url
                                    if lookup_url.startswith(("http://", "https://"))
                                    else f"https://{lookup_url}"
                                )
                                real_domain = lookup_parsed.netloc.lower().removeprefix("www.")
                                if real_domain and real_domain != domain.lower():
                                    logger.debug(f"[exa] resolved '{title}' → {real_domain} (was {comp_domain})")
                                    comp_domain = real_domain
                    except Exception as exc:  # noqa: BLE001
                        logger.debug(f"[exa] domain lookup failed for '{title}': {type(exc).__name__}: {exc}")

                if comp_domain not in seen_domains:
                    seen_domains.add(comp_domain)
                    summary = str(result.get("summary", ""))[:150].strip()
                    if summary:
                        competitors.append(f"{title} ({comp_domain}) — {summary}")
                    else:
                        competitors.append(f"{title} ({comp_domain})")
                    logger.debug(f"[exa] added: {comp_domain}")

            logger.info(f"[exa] final count: {len(competitors)}")
            return competitors[:8]
    except Exception as exc:  # noqa: BLE001
        logger.error(f"[exa] failed: {type(exc).__name__}: {exc}")
        return []


async def _find_competitors_tavily_gpt(domain: str, business_description: str, country_code: str = "") -> list[str]:
    logger.info(f"[tavily] searching competitors for {domain}")
    tavily_key = os.getenv("TAVILY_API_KEY", "")
    if not tavily_key:
        logger.warning("[tavily] missing TAVILY_API_KEY")
        return []

    def _is_blocked_domain(comp_domain: str) -> bool:
        if not comp_domain:
            return True
        blocked = {
            "reddit.com",
            "f6s.com",
            "g2.com",
            "capterra.com",
            "crunchbase.com",
            "linkedin.com",
            "facebook.com",
            "twitter.com",
            "x.com",
            "instagram.com",
            "youtube.com",
            "tiktok.com",
            "medium.com",
            "wikipedia.org",
            "github.com",
            "producthunt.com",
            "trustpilot.com",
            "yelp.com",
            "bbb.org",
            "glassdoor.com",
            "indeed.com",
            "angel.co",
            "wellfound.com",
        }
        if comp_domain in blocked:
            return True
        return any(
            comp_domain.endswith(suffix)
            for suffix in (
                "post.com",
                "times.com",
                "herald.com",
                "tribune.com",
                "gazette.com",
                "journal.com",
                "news.com",
            )
        )

    def _name_to_key(name: str) -> str:
        return re.sub(r"[^a-z0-9]", "", name.lower())

    try:
        if country_code:
            logger.debug(f"[tavily] location hint: {country_code.lower()}")
        query = f"competitors of {domain} {business_description}".strip()
        logger.debug(f"[tavily] query: {query[:180]}")
        async with httpx.AsyncClient(timeout=DEFAULT_HTTP_TIMEOUT_SECONDS) as client:
            response = await client.post(
                TAVILY_SEARCH_URL,
                json={
                    "api_key": tavily_key,
                    "query": query,
                    "include_answer": True,
                    "search_depth": "advanced",
                    "max_results": 8,
                },
            )
            _ = response.raise_for_status()
            data = cast(dict[str, object], response.json())

        results_raw = data.get("results", [])
        results = (
            [result for result in results_raw if isinstance(result, dict)] if isinstance(results_raw, list) else []
        )
        answer = str(data.get("answer", "")).strip()
        logger.info(f"[tavily] raw results: {len(results)}, answer length: {len(answer)}")

        domain_base = domain.split(".")[0].lower().replace("-", "").replace("www", "")
        seen_domains: set[str] = set()
        competitors: list[str] = []

        result_domains: list[tuple[str, str]] = []
        for result in results:
            url = str(result.get("url", "")).strip()
            title = str(result.get("title", "")).strip()
            parsed = urlparse(url if url.startswith(("http://", "https://")) else f"https://{url}")
            comp_domain = parsed.netloc.lower().removeprefix("www.")
            if not comp_domain:
                continue
            normalized_url = url.lower().replace("www.", "")
            if domain_base and domain_base in normalized_url:
                logger.debug(f"[tavily] skip {comp_domain}: self-domain")
                continue

            path = parsed.path.rstrip("/").lower()
            if len(path) > 1 and any(
                pattern in path
                for pattern in [
                    "/blog",
                    "/article",
                    "/news",
                    "/best-",
                    "/top-",
                    "/alternatives",
                    "/compare",
                    "/vs-",
                    "/review",
                    "/list",
                ]
            ):
                logger.debug(f"[tavily] skip {comp_domain}: listicle/directory path")
                continue

            title_lower = title.lower()
            if any(
                pattern in title_lower
                for pattern in ["top 1", "top 2", "top 3", "top 5", "best ", "vs ", " alternatives", " comparison"]
            ):
                logger.debug(f"[tavily] skip {title}: listicle title")
                continue
            if _is_blocked_domain(comp_domain):
                logger.debug(f"[tavily] skip {comp_domain}: blocked domain")
                continue
            result_domains.append((comp_domain, title))

        if answer:
            normalized = re.sub(r"(?i)\b(include|includes|including|such as|like)\b", ",", answer)
            normalized = re.sub(r"(?i)\band\b", ",", normalized)
            chunks = [chunk.strip(" .;:-") for chunk in normalized.split(",") if chunk.strip()]
            candidate_names: list[str] = []
            for chunk in chunks:
                matches = re.findall(r"\b[A-Z][A-Za-z0-9&'\.-]*(?:\s+[A-Z][A-Za-z0-9&'\.-]*)+\b", chunk)
                for match in matches:
                    name = re.sub(r"\s+", " ", match).strip()
                    if len(name.split()) < 2:
                        continue
                    if _name_to_key(name) == _name_to_key(domain_base):
                        continue
                    if name not in candidate_names:
                        candidate_names.append(name)

            logger.info(f"[tavily] parsed {len(candidate_names)} candidate names from answer")
            for name in candidate_names:
                name_key = _name_to_key(name)
                matched_domain = ""
                for comp_domain, title in result_domains:
                    title_key = _name_to_key(title)
                    domain_key = _name_to_key(comp_domain.split(".")[0])
                    if (
                        (name_key and name_key in title_key)
                        or (name_key and domain_key in name_key)
                        or (name_key and name_key in domain_key)
                    ):
                        matched_domain = comp_domain
                        break
                if matched_domain and matched_domain not in seen_domains:
                    seen_domains.add(matched_domain)
                    competitors.append(f"{name} ({matched_domain})")
                    logger.debug(f"[tavily] added from answer: {name} ({matched_domain})")

        for comp_domain, title in result_domains:
            if comp_domain in seen_domains:
                continue
            display_name = title.split("|")[0].split("-")[0].strip() if title else _humanize_brand(comp_domain)
            if not display_name:
                display_name = _humanize_brand(comp_domain)
            seen_domains.add(comp_domain)
            competitors.append(f"{display_name} ({comp_domain})")
            logger.debug(f"[tavily] added from results: {comp_domain}")

        logger.info(f"[tavily] final count: {len(competitors)}")
        return competitors[:8]
    except Exception as exc:  # noqa: BLE001
        logger.error(f"[tavily] failed: {type(exc).__name__}: {exc}")
        return []


async def discover_competitors_with_site_content(
    domain: str,
    industry: str,
    country_code: str = "",
) -> tuple[list[str], str]:
    exa_key = os.getenv("EXA_API_KEY", "")
    tavily_key = os.getenv("TAVILY_API_KEY", "")
    if not domain:
        return [], ""

    site_content = ""
    business_description = ""

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_HTTP_TIMEOUT_SECONDS) as client:
            if exa_key:
                try:
                    exa_response = await client.post(
                        EXA_CONTENTS_URL,
                        headers={"x-api-key": exa_key, "Content-Type": "application/json"},
                        json={
                            "urls": [f"https://{domain}"],
                            "text": {"maxCharacters": 3000},
                            "summary": {
                                "query": (
                                    "One sentence describing what this business does, its products/services, and "
                                    "location if detectable. Do not include the company name."
                                ),
                            },
                        },
                    )
                    exa_data = cast(dict[str, object], exa_response.json())
                    exa_results = exa_data.get("results", [])
                    if isinstance(exa_results, list) and exa_results:
                        first = exa_results[0]
                        if isinstance(first, dict):
                            site_content = str(first.get("text", "") or "")
                            exa_summary = str(first.get("summary", "") or "")
                            if exa_summary:
                                brand_words = domain.split(".")[0].lower().split("-")
                                desc = exa_summary
                                for word in brand_words:
                                    if len(word) > 2:
                                        desc = re.sub(rf"(?i)\b{re.escape(word)}\b", "", desc)
                                desc = re.sub(r"\s+", " ", desc).strip().lstrip(".,;:- ")
                                if len(desc) > 20:
                                    business_description = desc
                                logger.info(f"[discover] exa summary: {exa_summary[:150]}")
                                logger.info(f"[discover] cleaned description: {business_description[:150]}")
                    logger.info(f"[discover] exa content: {len(site_content)} chars")
                except Exception as exc:  # noqa: BLE001
                    logger.debug(f"[discover] exa contents failed: {type(exc).__name__}: {exc}")

            if (not site_content or len(site_content) < 50) and tavily_key:
                logger.info("[discover] falling back to Tavily extract")
                try:
                    extract_response = await client.post(
                        TAVILY_EXTRACT_URL,
                        json={"api_key": tavily_key, "urls": [f"https://{domain}"], "extract_depth": "advanced"},
                    )
                    extract_payload = cast(dict[str, object], extract_response.json())
                    extract_results = extract_payload.get("results", [])
                    if isinstance(extract_results, list) and extract_results:
                        first = extract_results[0]
                        if isinstance(first, dict):
                            site_content = str(first.get("raw_content", ""))[:3000]
                            logger.info(f"[discover] tavily fallback content: {len(site_content)} chars")
                except Exception as exc:  # noqa: BLE001
                    logger.debug(f"[discover] tavily extract failed: {type(exc).__name__}: {exc}")

            if not site_content or len(site_content) < 50:
                try:
                    direct_response = await client.get(
                        f"https://{domain}",
                        headers={"User-Agent": "Mozilla/5.0"},
                        follow_redirects=True,
                        timeout=10.0,
                    )
                    if direct_response.status_code == 200:
                        text = re.sub(r"<[^>]+>", " ", direct_response.text)
                        text = re.sub(r"\s+", " ", text).strip()
                        if len(text) > len(site_content):
                            site_content = text[:3000]
                except Exception as exc:  # noqa: BLE001
                    logger.debug(f"[discover] direct fetch failed: {type(exc).__name__}: {exc}")

            if not business_description:
                business_description = await _describe_business(site_content, domain, industry, country_code)

            logger.info(f"[discover] final description: {business_description[:200]}")

        exa_results, tavily_results = await asyncio.gather(
            _find_competitors_exa(domain, business_description, country_code),
            _find_competitors_tavily_gpt(domain, business_description, country_code),
            return_exceptions=True,
        )
        exa_list = exa_results if isinstance(exa_results, list) else []
        tavily_list = tavily_results if isinstance(tavily_results, list) else []
        logger.info(f"[discover] exa returned {len(exa_list)}: {[candidate.split(' — ')[0] for candidate in exa_list]}")
        logger.info(f"[discover] tavily returned {len(tavily_list)}: {tavily_list}")

        seen_domains: set[str] = set()
        merged: list[str] = []
        for entry in exa_list + tavily_list:
            extracted = _extract_domain(entry)
            if extracted and extracted not in seen_domains:
                seen_domains.add(extracted)
                merged.append(entry)
        logger.info(f"[discover] merged {len(merged)} unique candidates")

        if not merged:
            logger.warning(f"[discover] no candidates found for {domain}")
            return [], site_content

        validated = await _validate_domains(merged)
        if not validated:
            logger.warning("[discover] all domains failed validation")
            return [], site_content

        filtered = await _filter_direct_competitors(
            validated,
            site_content,
            domain,
            business_description,
            country_code,
        )
        if filtered:
            logger.info(f"[discover] success: {len(filtered)} competitors: {filtered}")
            return filtered[:5], site_content

        logger.warning("[discover] Claude filter removed all candidates")
        return [], site_content
    except Exception as exc:  # noqa: BLE001
        logger.error(f"[discover] failed: {type(exc).__name__}: {exc}")
        return [], site_content


async def discover_competitors(domain: str, industry: str = "", country_code: str = "") -> list[str]:
    competitors, _ = await discover_competitors_with_site_content(domain, industry, country_code)
    return competitors
