import os
import httpx
from typing import Any, cast

from loguru import logger

DATAFORSEO_AUTH = f"Basic {os.environ.get('DATAFORSEO_AUTH_HEADER', '')}"
AI_KEYWORD_URL = "https://api.dataforseo.com/v3/ai_optimization/ai_keyword_data/keywords_search_volume/live"
TIMEOUT = 30.0


async def get_ai_search_volume(keywords: list[str], location_code: int = 2840) -> list[dict[str, Any]]:
    payload = [{"keywords": keywords, "location_code": location_code}]

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(
                AI_KEYWORD_URL,
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
            if not isinstance(results, list):
                return []
            return [
                {
                    "keyword": str(row.get("keyword", "")),
                    "ai_search_volume": row.get("search_volume", 0),
                    "trend": row.get("monthly_searches", []),
                }
                for row in results
                if isinstance(row, dict)
            ]
    except Exception as e:
        logger.debug(f"[dataforseo_keywords] Failed to get AI search volume: {type(e).__name__}: {e}")
        return []
