import os
import httpx
from typing import Any, cast

from loguru import logger

DATAFORSEO_AUTH = f"Basic {os.environ.get('DATAFORSEO_AUTH_HEADER', '')}"
SERP_URL = "https://api.dataforseo.com/v3/serp/google/organic/live/advanced"
TIMEOUT = 30.0


async def search_social_mentions(brand: str, platform: str, location_code: int = 2840) -> list[dict[str, object]]:
    site_filter = "youtube.com" if platform == "youtube" else "reddit.com"
    keyword = f"site:{site_filter} {brand}"

    payload = [
        {
            "keyword": keyword,
            "location_code": location_code,
            "language_code": "en",
            "depth": 20,
        }
    ]

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(
                SERP_URL,
                headers={"Authorization": DATAFORSEO_AUTH, "Content-Type": "application/json"},
                json=payload,
            )
            resp.raise_for_status()
            data = cast(dict[str, object], resp.json())
            tasks = data.get("tasks", [])
            if not tasks:
                return []
            tasks_list = cast(list[object], tasks) if isinstance(tasks, list) else []
            if not tasks_list or not isinstance(tasks_list[0], dict):
                return []
            first_task = cast(dict[str, object], tasks_list[0])
            results = first_task.get("result", [])
            if not results or not isinstance(results, list):
                return []

            first_result = results[0]
            if not isinstance(first_result, dict):
                return []
            items = first_result.get("items", [])
            mentions: list[dict[str, object]] = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                if item.get("type") != "organic":
                    continue
                mentions.append(
                    cast(
                        dict[str, object],
                        {
                            "title": str(item.get("title", "")),
                            "url": str(item.get("url", "")),
                            "description": str(item.get("description", "")),
                            "platform": platform,
                            "position": item.get("rank_group", 0),
                        },
                    )
                )
            return mentions
    except Exception as e:
        logger.debug(f"[social_visibility] Failed to search social mentions: {type(e).__name__}: {e}")
        return []


async def get_social_visibility(brand: str, location_code: int = 2840) -> dict[str, Any]:
    youtube = await search_social_mentions(brand, "youtube", location_code)
    reddit = await search_social_mentions(brand, "reddit", location_code)
    return {
        "youtube_mentions": len(youtube),
        "reddit_mentions": len(reddit),
        "youtube_results": youtube[:10],
        "reddit_results": reddit[:10],
    }
