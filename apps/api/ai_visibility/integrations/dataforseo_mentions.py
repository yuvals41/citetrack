import os
import httpx
from loguru import logger
from typing import cast

DATAFORSEO_AUTH = f"Basic {os.environ.get('DATAFORSEO_AUTH_HEADER', '')}"
BASE_URL = "https://api.dataforseo.com/v3/ai_optimization/llm_mentions"
TIMEOUT = 30.0


async def search_mentions(
    keyword: str,
    domain: str | None = None,
    location_code: int = 2840,
) -> list[dict[str, object]]:
    target = [{"keyword": keyword, "search_scope": ["answer"]}]
    if domain:
        target.append({"domain": domain})
    payload: list[dict[str, object]] = [
        {"target": target, "location_code": location_code, "platform": "google", "limit": 20}
    ]
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(
            f"{BASE_URL}/search/live",
            headers={"Authorization": DATAFORSEO_AUTH, "Content-Type": "application/json"},
            json=payload,
        )
        resp.raise_for_status()
        data = cast(dict[str, object], resp.json())
        tasks = data.get("tasks", [])
        if not tasks or not isinstance(tasks, list):
            return []
        tasks_list = cast(list[object], tasks)
        first_task = tasks_list[0]
        if not isinstance(first_task, dict):
            return []
        results = first_task.get("result", [])
        if not isinstance(results, list) or not results:
            return []
        first_result = results[0]
        if not isinstance(first_result, dict):
            return []
        items = first_result.get("items", [])
        if not isinstance(items, list):
            return []
        return [cast(dict[str, object], item) for item in items if isinstance(item, dict)]


async def get_aggregated_metrics(domain: str, location_code: int = 2840) -> dict[str, object]:
    payload: list[dict[str, object]] = [
        {"target": [{"domain": domain}], "location_code": location_code, "platform": "google"}
    ]
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(
            f"{BASE_URL}/aggregated_metrics/live",
            headers={"Authorization": DATAFORSEO_AUTH, "Content-Type": "application/json"},
            json=payload,
        )
        resp.raise_for_status()
        data = cast(dict[str, object], resp.json())
        tasks = data.get("tasks", [])
        if not isinstance(tasks, list) or not tasks:
            return {}
        tasks_list = cast(list[object], tasks)
        first_task = tasks_list[0]
        if not isinstance(first_task, dict):
            return {}
        results = first_task.get("result", [])
        if not isinstance(results, list) or not results:
            return {}
        first_result = results[0]
        return cast(dict[str, object], first_result) if isinstance(first_result, dict) else {}


async def get_cross_metrics(domains: list[str], location_code: int = 2840) -> list[dict[str, object]]:
    target = [{"domain": d} for d in domains]
    payload: list[dict[str, object]] = [{"target": target, "location_code": location_code, "platform": "google"}]
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(
            f"{BASE_URL}/cross_aggregated_metrics/live",
            headers={"Authorization": DATAFORSEO_AUTH, "Content-Type": "application/json"},
            json=payload,
        )
        resp.raise_for_status()
        data = cast(dict[str, object], resp.json())
        tasks = data.get("tasks", [])
        if not isinstance(tasks, list) or not tasks:
            return []
        tasks_list = cast(list[object], tasks)
        first_task = tasks_list[0]
        if not isinstance(first_task, dict):
            return []
        results = first_task.get("result", [])
        if not isinstance(results, list):
            return []
        return [cast(dict[str, object], result) for result in results if isinstance(result, dict)]


async def get_top_domains(keyword: str, location_code: int = 2840) -> list[dict[str, object]]:
    payload: list[dict[str, object]] = [
        {
            "target": [{"keyword": keyword, "search_scope": ["answer"]}],
            "location_code": location_code,
            "platform": "google",
            "limit": 10,
        }
    ]
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(
            f"{BASE_URL}/top_domains/live",
            headers={"Authorization": DATAFORSEO_AUTH, "Content-Type": "application/json"},
            json=payload,
        )
        resp.raise_for_status()
        data = cast(dict[str, object], resp.json())
        tasks = data.get("tasks", [])
        if not isinstance(tasks, list) or not tasks:
            return []
        tasks_list = cast(list[object], tasks)
        first_task = tasks_list[0]
        if not isinstance(first_task, dict):
            return []
        results = first_task.get("result", [])
        if not isinstance(results, list):
            return []
        return [cast(dict[str, object], result) for result in results if isinstance(result, dict)]


async def get_top_pages(keyword: str, location_code: int = 2840) -> list[dict[str, object]]:
    payload: list[dict[str, object]] = [
        {
            "target": [{"keyword": keyword, "search_scope": ["answer"]}],
            "location_code": location_code,
            "platform": "google",
            "limit": 10,
        }
    ]
    logger.debug(f"[mentions] fetching top pages for keyword='{keyword}', location_code={location_code}")
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(
            f"{BASE_URL}/top_pages/live",
            headers={"Authorization": DATAFORSEO_AUTH, "Content-Type": "application/json"},
            json=payload,
        )
        resp.raise_for_status()
        data = cast(dict[str, object], resp.json())
        tasks = data.get("tasks", [])
        if not isinstance(tasks, list) or not tasks:
            logger.debug("[mentions] top pages: no tasks")
            return []
        tasks_list = cast(list[object], tasks)
        first_task = tasks_list[0]
        if not isinstance(first_task, dict):
            logger.debug("[mentions] top pages: malformed first task")
            return []
        results = first_task.get("result", [])
        if not isinstance(results, list):
            logger.debug("[mentions] top pages: no results")
            return []
        return [cast(dict[str, object], result) for result in results if isinstance(result, dict)]
