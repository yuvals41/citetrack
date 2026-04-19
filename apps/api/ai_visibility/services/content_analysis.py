from __future__ import annotations

import asyncio
import json
import os
import re
from typing import Any, cast
from urllib.parse import quote, urljoin, urlparse

import httpx
from loguru import logger

from ai_visibility.models.content_analysis import (
    AIShoppingResult,
    AnalyzerDimension,
    BotAccessResult,
    ChatGPTShoppingResult,
    CrawlerSimResult,
    EntityResult,
    ExtractabilityResult,
    GoogleShoppingResult,
    PresenceResult,
    QueryFanoutItem,
    QueryFanoutResult,
    ShoppingResult,
)

ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
TAVILY_SEARCH_URL = "https://api.tavily.com/search"
DATAFORSEO_ORGANIC_URL = "https://api.dataforseo.com/v3/serp/google/organic/live/advanced"
DEFAULT_TIMEOUT = 20.0
ANTHROPIC_MODEL = "claude-sonnet-4-6"

BOT_USER_AGENTS: dict[str, str] = {
    "GPTBot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; GPTBot/1.2; +https://openai.com/gptbot",
    "ClaudeBot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; ClaudeBot/1.0; +https://www.anthropic.com/claude-bot",
    "PerplexityBot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; PerplexityBot/1.0; +https://perplexity.ai/bot",
    "Google-Extended": "Mozilla/5.0 (compatible; Google-Extended)",
    "Googlebot": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "Bingbot": "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
}

WEIGHTS = {
    "summary_block": 0.25,
    "section_integrity": 0.2,
    "modular_content": 0.2,
    "schema_markup": 0.15,
    "static_content": 0.2,
}


def _make_client(*, timeout: float = DEFAULT_TIMEOUT, headers: dict[str, str] | None = None) -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=headers)


def _degraded(reason: str, message: str) -> dict[str, str]:
    return {"reason": reason, "message": message}


def _safe_slug(value: str) -> str:
    slug = re.sub(r"\s+", "_", value.strip())
    slug = re.sub(r"[^A-Za-z0-9_\-]", "", slug)
    return slug or value.strip().replace(" ", "_")


def _extract_json(text: str) -> str:
    stripped = text.strip()
    if "```" in stripped:
        for part in stripped.split("```")[1:]:
            clean = part[4:] if part.startswith("json") else part
            clean = clean.strip()
            if clean.startswith("{") or clean.startswith("["):
                return clean
    if stripped.startswith("{") or stripped.startswith("["):
        return stripped
    start = stripped.find("[")
    if start == -1:
        start = stripped.find("{")
    return stripped[start:] if start >= 0 else stripped


def _strip_tags(html: str) -> str:
    without_scripts = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.IGNORECASE)
    without_styles = re.sub(r"<style[\s\S]*?</style>", " ", without_scripts, flags=re.IGNORECASE)
    without_noscript = re.sub(r"<noscript[\s\S]*?</noscript>", " ", without_styles, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", without_noscript)
    return re.sub(r"\s+", " ", text).strip()


def _script_bytes(html: str) -> int:
    scripts = re.findall(r"<script[\s\S]*?</script>", html, flags=re.IGNORECASE)
    return sum(len(script) for script in scripts)


def _extract_headings(html: str, tag: str) -> list[str]:
    pattern = rf"<{tag}[^>]*>(.*?)</{tag}>"
    matches = re.findall(pattern, html, flags=re.IGNORECASE | re.DOTALL)
    return [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", match)).strip() for match in matches if match.strip()]


def _has_modular_content(html: str) -> tuple[int, str]:
    features = {
        "lists": len(re.findall(r"<(ul|ol)\b", html, flags=re.IGNORECASE)),
        "tables": len(re.findall(r"<table\b", html, flags=re.IGNORECASE)),
        "definitions": len(re.findall(r"<dl\b", html, flags=re.IGNORECASE)),
    }
    total = sum(features.values())
    if total == 0:
        return 15, "No lists, tables, or definition lists were found."
    if total == 1:
        return 60, "Some modular content exists, but the page could expose more scannable blocks."
    return min(100, 75 + min(total, 5) * 5), "The page exposes structured lists or tables AI systems can quote cleanly."


def _summary_block_dimension(html: str) -> AnalyzerDimension:
    h1_matches = _extract_headings(html, "h1")
    paragraphs = re.findall(r"<(p|div)[^>]*>(.*?)</\1>", html, flags=re.IGNORECASE | re.DOTALL)
    first_supporting_text = ""
    for _tag, raw in paragraphs[:6]:
        clean = re.sub(r"<[^>]+>", " ", raw)
        clean = re.sub(r"\s+", " ", clean).strip()
        if len(clean) >= 50:
            first_supporting_text = clean
            break
    if h1_matches and first_supporting_text:
        return AnalyzerDimension(
            score=95,
            finding="Clear H1 with supporting summary copy appears near the top of the page.",
        )
    if h1_matches:
        return AnalyzerDimension(
            score=60,
            finding="The page has an H1, but it lacks strong supporting summary text above the fold.",
        )
    return AnalyzerDimension(score=10, finding="No clear H1 hero block was found for AI systems to anchor on.")


def _section_integrity_dimension(html: str) -> AnalyzerDimension:
    h2_matches = _extract_headings(html, "h2")
    h3_matches = _extract_headings(html, "h3")
    if h2_matches and h3_matches:
        return AnalyzerDimension(
            score=95,
            finding="The page uses a healthy H2/H3 hierarchy that breaks content into coherent sections.",
        )
    if len(h2_matches) >= 2:
        return AnalyzerDimension(
            score=75,
            finding="The page has section headings, but adding nested H3 structure would improve extractability.",
        )
    if h2_matches:
        return AnalyzerDimension(
            score=50,
            finding="Only one strong section heading was found; AI systems may see the page as one block.",
        )
    return AnalyzerDimension(score=15, finding="The page lacks a clear H2/H3 section hierarchy.")


def _schema_markup_dimension(html: str) -> AnalyzerDimension:
    matches = re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>([\s\S]*?)</script>',
        html,
        flags=re.IGNORECASE,
    )
    if not matches:
        return AnalyzerDimension(score=5, finding="No JSON-LD schema markup was detected.")
    valid_blocks = 0
    for block in matches:
        try:
            json.loads(block.strip())
            valid_blocks += 1
        except json.JSONDecodeError:
            continue
    if valid_blocks:
        return AnalyzerDimension(
            score=100,
            finding=f"Found {valid_blocks} valid JSON-LD schema block(s).",
        )
    return AnalyzerDimension(score=40, finding="Schema blocks exist, but they appear malformed.")


def _static_content_dimension(html: str) -> AnalyzerDimension:
    visible_text = _strip_tags(html)
    visible_len = len(visible_text)
    script_len = _script_bytes(html)
    noscript_len = len(" ".join(re.findall(r"<noscript[^>]*>(.*?)</noscript>", html, flags=re.IGNORECASE | re.DOTALL)))
    ratio = visible_len / max(script_len, 1)
    if visible_len >= 800 and ratio >= 1.5 and noscript_len < 100:
        return AnalyzerDimension(
            score=95,
            finding="Most meaningful content is present in static HTML without heavy JavaScript dependence.",
        )
    if visible_len >= 400 and ratio >= 0.6:
        return AnalyzerDimension(
            score=70,
            finding="The page exposes usable text in static HTML, but scripts still dominate the payload.",
        )
    if noscript_len > 150:
        return AnalyzerDimension(
            score=35,
            finding="Meaningful content appears tucked into noscript or relies heavily on JavaScript rendering.",
        )
    return AnalyzerDimension(
        score=20,
        finding="Very little visible HTML text was found compared with script weight, suggesting JS-heavy rendering.",
    )


def _recommendations_from_dimensions(dimensions: dict[str, AnalyzerDimension]) -> list[str]:
    recommendations: list[str] = []
    if dimensions["summary_block"].score < 70:
        recommendations.append("Add a clear hero summary: one H1 plus a concise supporting paragraph near the top.")
    if dimensions["section_integrity"].score < 70:
        recommendations.append(
            "Break the page into descriptive H2/H3 sections so AI systems can segment answers cleanly."
        )
    if dimensions["modular_content"].score < 70:
        recommendations.append("Convert dense prose into lists, comparison tables, or definition blocks.")
    if dimensions["schema_markup"].score < 70:
        recommendations.append("Add valid JSON-LD schema markup for the page's main entity and content type.")
    if dimensions["static_content"].score < 70:
        recommendations.append(
            "Ensure key copy ships in server-rendered HTML instead of relying on client-side rendering."
        )
    return recommendations[:4]


async def analyze_extractability(url: str) -> ExtractabilityResult:
    async with _make_client() as client:
        response = await client.get(url)
        response.raise_for_status()
        html = response.text

    modular_score, modular_finding = _has_modular_content(html)
    dimensions = {
        "summary_block": _summary_block_dimension(html),
        "section_integrity": _section_integrity_dimension(html),
        "modular_content": AnalyzerDimension(score=modular_score, finding=modular_finding),
        "schema_markup": _schema_markup_dimension(html),
        "static_content": _static_content_dimension(html),
    }
    overall_score = round(
        sum(dimensions[name].score * weight for name, weight in WEIGHTS.items()),
        1,
    )
    recommendations = _recommendations_from_dimensions(dimensions)
    return ExtractabilityResult(
        url=url,
        overall_score=overall_score,
        summary_block=dimensions["summary_block"],
        section_integrity=dimensions["section_integrity"],
        modular_content=dimensions["modular_content"],
        schema_markup=dimensions["schema_markup"],
        static_content=dimensions["static_content"],
        recommendations=recommendations,
    )


def _robots_base_url(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def _parse_robots_disallow_all(robots_text: str, bot_name: str) -> bool:
    current_agents: list[str] = []
    blocked = False
    for raw_line in robots_text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = [part.strip() for part in line.split(":", 1)]
        lowered_key = key.lower()
        if lowered_key == "user-agent":
            current_agents = [agent.strip().lower() for agent in value.split()] or ["*"]
            continue
        if lowered_key == "disallow" and value == "/":
            normalized_agents = {agent.lower() for agent in current_agents}
            if bot_name.lower() in normalized_agents or "*" in normalized_agents:
                blocked = True
    return blocked


async def simulate_crawler_access(url: str) -> CrawlerSimResult:
    robots_url = urljoin(f"{_robots_base_url(url)}/", "robots.txt")
    results: list[BotAccessResult] = []
    async with _make_client(timeout=15.0) as client:
        for bot_name, user_agent in BOT_USER_AGENTS.items():
            headers = {"User-Agent": user_agent}
            status_code = 0
            reason = ""
            accessible = False
            robots_text = ""
            try:
                page_response = await client.head(url, headers=headers)
                status_code = page_response.status_code
                robots_head = await client.head(robots_url, headers=headers)
                if robots_head.status_code < 400:
                    robots_get = await client.get(robots_url, headers=headers)
                    if robots_get.status_code == 200:
                        robots_text = robots_get.text
                blocked = _parse_robots_disallow_all(robots_text, bot_name)
                if blocked:
                    reason = "Blocked by robots.txt"
                elif 200 <= status_code < 400:
                    accessible = True
                    reason = "Accessible"
                else:
                    reason = f"Target returned HTTP {status_code}"
            except Exception as exc:  # noqa: BLE001
                reason = f"Request failed: {type(exc).__name__}"
                logger.debug("crawler_sim.failed bot={} url={} error={}", bot_name, url, exc)
            results.append(
                BotAccessResult(
                    bot=bot_name,
                    accessible=accessible,
                    status_code=status_code,
                    reason=reason,
                )
            )
    return CrawlerSimResult(url=url, results=results)


async def _anthropic_text(prompt: str) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return ""
    async with _make_client(timeout=25.0) as client:
        response = await client.post(
            ANTHROPIC_MESSAGES_URL,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": ANTHROPIC_MODEL,
                "max_tokens": 800,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        response.raise_for_status()
        payload = cast(dict[str, object], response.json())
    content = payload.get("content", [])
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                return str(block.get("text", ""))
    return ""


async def _tavily_search(query: str) -> list[dict[str, Any]]:
    tavily_key = os.getenv("TAVILY_API_KEY", "").strip()
    if not tavily_key:
        return []
    async with _make_client(timeout=20.0) as client:
        response = await client.post(
            TAVILY_SEARCH_URL,
            json={
                "api_key": tavily_key,
                "query": query,
                "max_results": 5,
                "search_depth": "basic",
                "include_answer": True,
            },
        )
        response.raise_for_status()
        payload = cast(dict[str, Any], response.json())
    results = payload.get("results", [])
    return [item for item in results if isinstance(item, dict)] if isinstance(results, list) else []


def _normalize_domain(domain: str) -> str:
    candidate = domain.strip().lower()
    if not candidate:
        return ""
    if "://" not in candidate:
        candidate = f"https://{candidate}"
    parsed = urlparse(candidate)
    host = parsed.netloc or parsed.path
    host = host.split("/")[0]
    return host[4:] if host.startswith("www.") else host


def _result_domain(result: dict[str, Any]) -> str:
    value = str(result.get("url") or result.get("link") or "")
    return _normalize_domain(value)


async def generate_query_fanout(prompt: str, brand_domain: str) -> QueryFanoutResult:
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY", "").strip())
    has_tavily = bool(os.getenv("TAVILY_API_KEY", "").strip())
    if not has_anthropic or not has_tavily:
        return QueryFanoutResult(
            fanout_prompt=prompt,
            results=[],
            coverage=0,
            degraded=_degraded(
                "missing_api_keys",
                "Query fan-out needs ANTHROPIC_API_KEY and TAVILY_API_KEY to expand and verify sub-queries.",
            ),
        )

    prompt_text = (
        "Generate 5 to 8 short search sub-queries an AI assistant would use behind the scenes. "
        'Return only JSON like {"queries": ["..."]}.\n\n'
        f"User prompt: {prompt}\nBrand domain: {brand_domain}"
    )
    raw_text = await _anthropic_text(prompt_text)
    queries_payload = cast(dict[str, object], json.loads(_extract_json(raw_text) or "{}"))
    raw_queries = queries_payload.get("queries", [])
    query_items = raw_queries if isinstance(raw_queries, list) else []
    queries = [str(item).strip() for item in query_items if isinstance(item, str) and str(item).strip()][:8]
    normalized_brand_domain = _normalize_domain(brand_domain)
    results: list[QueryFanoutItem] = []
    for sub_query in queries:
        organic_results = await _tavily_search(sub_query)
        ranked = False
        position: int | None = None
        for index, item in enumerate(organic_results[:5], start=1):
            if _result_domain(item) == normalized_brand_domain:
                ranked = True
                position = index
                break
        results.append(QueryFanoutItem(sub_query=sub_query, ranked=ranked, position=position))

    coverage = round(sum(1 for item in results if item.ranked) / len(results), 4) if results else 0.0
    return QueryFanoutResult(fanout_prompt=prompt, results=results, coverage=coverage)


async def _knowledge_graph_presence(brand_name: str) -> PresenceResult:
    auth_header = os.getenv("DATAFORSEO_AUTH_HEADER", "").strip()
    if not auth_header:
        return PresenceResult(present=False, url=None)
    async with _make_client(timeout=25.0) as client:
        response = await client.post(
            DATAFORSEO_ORGANIC_URL,
            headers={"Authorization": f"Basic {auth_header}", "Content-Type": "application/json"},
            json=[{"keyword": brand_name, "location_code": 2840, "language_code": "en", "depth": 10}],
        )
        response.raise_for_status()
        payload = cast(dict[str, Any], response.json())
    tasks = payload.get("tasks", [])
    if not isinstance(tasks, list) or not tasks or not isinstance(tasks[0], dict):
        return PresenceResult(present=False, url=None)
    task_result = cast(dict[str, Any], tasks[0]).get("result", [])
    if not isinstance(task_result, list) or not task_result or not isinstance(task_result[0], dict):
        return PresenceResult(present=False, url=None)
    items = task_result[0].get("items", [])
    if not isinstance(items, list):
        return PresenceResult(present=False, url=None)
    for item in items:
        if not isinstance(item, dict):
            continue
        if "knowledge_graph" in str(item.get("type", "")).lower():
            url = str(item.get("url") or item.get("source") or "") or None
            return PresenceResult(present=True, url=url)
    return PresenceResult(present=False, url=None)


async def _wikipedia_presence(brand_name: str) -> PresenceResult:
    slug = quote(_safe_slug(brand_name), safe="_")
    url = f"https://en.wikipedia.org/wiki/{slug}"
    async with _make_client() as client:
        response = await client.get(url)
    return PresenceResult(present=response.status_code == 200, url=url)


async def _wikidata_presence(brand_name: str) -> PresenceResult:
    async with _make_client() as client:
        response = await client.get(
            "https://www.wikidata.org/w/api.php",
            params={
                "action": "wbsearchentities",
                "search": brand_name,
                "language": "en",
                "format": "json",
                "limit": 1,
            },
        )
        response.raise_for_status()
        payload = cast(dict[str, Any], response.json())
    results = payload.get("search", [])
    if not isinstance(results, list) or not results or not isinstance(results[0], dict):
        return PresenceResult(present=False, url=None)
    entity_id = str(results[0].get("id") or "")
    return PresenceResult(
        present=bool(entity_id),
        url=f"https://www.wikidata.org/wiki/{entity_id}" if entity_id else None,
    )


def _entity_recommendations(kg: PresenceResult, wikipedia: PresenceResult, wikidata: PresenceResult) -> list[str]:
    recommendations: list[str] = []
    if not kg.present:
        recommendations.append(
            "Strengthen your brand entity with consistent organization schema and third-party citations."
        )
    if not wikipedia.present:
        recommendations.append(
            "Build notability signals that can support a future Wikipedia page or references in existing pages."
        )
    if not wikidata.present:
        recommendations.append(
            "Create or improve a Wikidata record so AI systems can connect your brand to a canonical entity."
        )
    if not recommendations:
        recommendations.append(
            "Keep brand naming, descriptions, and schema consistent across your website and listings."
        )
    return recommendations


async def _analyze_brand_entity_impl(brand_name: str) -> EntityResult:
    kg, wikipedia, wikidata = await asyncio.gather(
        _knowledge_graph_presence(brand_name),
        _wikipedia_presence(brand_name),
        _wikidata_presence(brand_name),
    )
    score = round((0.4 if kg.present else 0) + (0.3 if wikipedia.present else 0) + (0.3 if wikidata.present else 0), 4)
    return EntityResult(
        brand_name=brand_name,
        entity_clarity_score=score,
        knowledge_graph=kg,
        wikipedia=wikipedia,
        wikidata=wikidata,
        recommendations=_entity_recommendations(kg, wikipedia, wikidata),
    )


async def analyze_brand_entity(brand_name: str) -> EntityResult:
    return await _analyze_brand_entity_impl(brand_name)


async def _shopping_google_presence(brand_name: str) -> tuple[bool, bool]:
    if not os.getenv("TAVILY_API_KEY", "").strip():
        return False, False
    query = f'site:shopping.google.com "{brand_name}"'
    results = await _tavily_search(query)
    brand_lower = brand_name.lower()
    found = any(brand_lower in json.dumps(item).lower() for item in results)
    ai_text = any(brand_lower in str(item.get("content") or item.get("title") or "").lower() for item in results)
    return found, ai_text


async def _shopping_chatgpt_presence(brand_name: str) -> bool:
    if not os.getenv("ANTHROPIC_API_KEY", "").strip():
        return False
    text = await _anthropic_text(
        f"In one short paragraph, answer a shopping-style question for the brand {brand_name}. Mention the brand only if it is a sensible shopping result."
    )
    return brand_name.lower() in text.lower()


def _shopping_recommendations(google_found: bool, ai_found: bool, chatgpt_found: bool) -> list[str]:
    recommendations: list[str] = []
    if not google_found:
        recommendations.append(
            "Publish merchant/product pages that Google Shopping and aggregators can index directly."
        )
    if not ai_found:
        recommendations.append(
            "Add explicit product and pricing copy so AI shopping systems can identify your catalog."
        )
    if not chatgpt_found:
        recommendations.append(
            "Increase product review and third-party mention coverage so assistants can reference the brand with confidence."
        )
    if not recommendations:
        recommendations.append(
            "Maintain fresh product availability, price, and review data across your catalog and merchant feeds."
        )
    return recommendations


async def analyze_shopping_visibility(brand_name: str) -> ShoppingResult:
    has_tavily = bool(os.getenv("TAVILY_API_KEY", "").strip())
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY", "").strip())
    if not has_tavily and not has_anthropic:
        return ShoppingResult(
            brand_name=brand_name,
            visibility_score=0,
            google_shopping=GoogleShoppingResult(brand_products_found=False),
            ai_mode_shopping=AIShoppingResult(brand_in_ai_text=False),
            chatgpt_shopping=ChatGPTShoppingResult(brand_mentioned=False),
            recommendations=["Add TAVILY_API_KEY or ANTHROPIC_API_KEY to enable shopping visibility checks."],
            degraded=_degraded(
                "missing_api_keys",
                "Shopping visibility needs TAVILY_API_KEY and/or ANTHROPIC_API_KEY for best-effort checks.",
            ),
        )

    google_found, ai_found = await _shopping_google_presence(brand_name)
    chatgpt_found = await _shopping_chatgpt_presence(brand_name)
    score = round((0.4 if google_found else 0) + (0.3 if ai_found else 0) + (0.3 if chatgpt_found else 0), 4)
    return ShoppingResult(
        brand_name=brand_name,
        visibility_score=score,
        google_shopping=GoogleShoppingResult(brand_products_found=google_found),
        ai_mode_shopping=AIShoppingResult(brand_in_ai_text=ai_found),
        chatgpt_shopping=ChatGPTShoppingResult(brand_mentioned=chatgpt_found),
        recommendations=_shopping_recommendations(google_found, ai_found, chatgpt_found),
    )
