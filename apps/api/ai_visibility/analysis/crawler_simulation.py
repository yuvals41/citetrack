import httpx
from typing import TypedDict
import re
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from loguru import logger

AI_BOTS = {
    "GPTBot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; GPTBot/1.2; +https://openai.com/gptbot",
    "ClaudeBot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; ClaudeBot/1.0; +https://www.anthropic.com/claude-bot",
    "PerplexityBot": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; PerplexityBot/1.0; +https://perplexity.ai/bot",
    "Google-Extended": "Mozilla/5.0 (compatible; Google-Extended)",
    "Googlebot": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
}


class CrawlerResult(TypedDict):
    bot: str
    user_agent: str
    robots_allowed: bool
    http_status: int
    accessible: bool
    content_length: int
    issue: str
    js_rendering: dict[str, object]


async def _check_js_rendering(url: str) -> dict[str, object]:
    signals: list[str] = []
    text_length = 0

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url)
            html = resp.text or ""
    except Exception as e:  # noqa: BLE001
        logger.debug(f"[crawler] JS rendering check failed: {type(e).__name__}: {e}")
        return {"js_required": False, "signals": ["fetch_failed"], "text_length": 0}

    noscript_matches = re.findall(r"<noscript[^>]*>(.*?)</noscript>", html, flags=re.IGNORECASE | re.DOTALL)
    for match in noscript_matches:
        no_tag_text = re.sub(r"<[^>]+>", " ", match)
        meaningful = " ".join(no_tag_text.split())
        if len(meaningful) >= 20:
            signals.append("noscript_content")
            break

    lower_html = html.lower()
    has_script_tags = "<script" in lower_html
    has_spa_root = bool(re.search(r'id=["\'](?:root|app|__next)["\']', lower_html))
    has_ajax_fragment_meta = bool(re.search(r'<meta[^>]*name=["\']fragment["\'][^>]*content=["\']!["\']', lower_html))

    stripped = re.sub(r"<script[\\s\\S]*?</script>", " ", html, flags=re.IGNORECASE)
    stripped = re.sub(r"<style[\\s\\S]*?</style>", " ", stripped, flags=re.IGNORECASE)
    stripped = re.sub(r"<[^>]+>", " ", stripped)
    text_length = len(" ".join(stripped.split()))

    if text_length < 100 and has_script_tags:
        signals.append("minimal_text_with_scripts")
    if has_spa_root:
        signals.append("spa_root_div")
    if has_ajax_fragment_meta:
        signals.append("ajax_fragment_meta")

    js_required = len(signals) > 0
    logger.debug(
        f"[crawler] JS rendering check for {url}: js_required={js_required}, signals={signals}, text_length={text_length}"
    )
    return {
        "js_required": js_required,
        "signals": signals,
        "text_length": text_length,
    }


async def simulate_crawlers(url: str) -> list[CrawlerResult]:
    if not url.startswith("http"):
        url = f"https://{url}"
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    robots_url = f"{base_url}/robots.txt"

    results: list[CrawlerResult] = []

    robots_content = ""
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(robots_url)
            if resp.status_code == 200:
                robots_content = resp.text
    except Exception as e:
        logger.debug(f"[crawler_simulation] {type(e).__name__}: {e}")

    js_rendering_result = await _check_js_rendering(url)

    for bot_name, user_agent in AI_BOTS.items():
        result: CrawlerResult = {
            "bot": bot_name,
            "user_agent": user_agent,
            "robots_allowed": True,
            "http_status": 0,
            "accessible": False,
            "content_length": 0,
            "issue": "",
            "js_rendering": js_rendering_result,
        }

        if robots_content:
            rp = RobotFileParser()
            rp.parse(robots_content.splitlines())
            allowed = rp.can_fetch(user_agent, url)
            result["robots_allowed"] = allowed
            if not allowed:
                result["issue"] = f"Blocked by robots.txt for {bot_name}"
                results.append(result)
                continue

        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                resp = await client.get(url, headers={"User-Agent": user_agent})
                result["http_status"] = resp.status_code
                result["content_length"] = len(resp.text)

                if resp.status_code == 200:
                    result["accessible"] = True
                    if len(resp.text) < 500:
                        result["issue"] = "Page returned very little content (possible JS-only rendering)"
                elif resp.status_code == 403:
                    result["issue"] = f"Access forbidden (HTTP 403) for {bot_name}"
                elif resp.status_code == 429:
                    result["issue"] = f"Rate limited (HTTP 429) for {bot_name}"
                else:
                    result["issue"] = f"HTTP {resp.status_code} response"
        except Exception as exc:
            result["issue"] = f"Connection failed: {type(exc).__name__}"

        results.append(result)

    return results
