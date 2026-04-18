# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownParameterType=false, reportUnknownArgumentType=false, reportMissingTypeArgument=false, reportUnusedCallResult=false

import json
import os
from typing import cast

import httpx
from dotenv import load_dotenv

_ = load_dotenv()

DATAFORSEO_AUTH = f"Basic {os.environ.get('DATAFORSEO_AUTH_HEADER', '')}"


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


async def generate_fanout_queries(prompt: str, brand: str) -> list[str]:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return []

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            instructions = (
                "You are simulating how an AI assistant researches answers. "
                "Given a user prompt, generate the 5-8 Google search queries "
                "the AI would run behind the scenes to gather information. "
                "Return ONLY valid JSON with key 'queries' containing an array of strings."
            )
            input_text = f"What search queries would an AI run to answer this prompt?\n\nPrompt: {prompt}\nBrand context: {brand}"

            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-6",
                    "max_tokens": 1024,
                    "messages": [
                        {
                            "role": "user",
                            "content": f"{instructions}\n\n{input_text}",
                        }
                    ],
                },
            )
            resp.raise_for_status()
            data = cast(dict[str, object], resp.json())
            content = data.get("content", [])
            if isinstance(content, list) and content:
                text = str(content[0].get("text", "{}"))
                json_str = _extract_json(text)
                parsed_obj = cast(object, json.loads(json_str))
                if isinstance(parsed_obj, dict):
                    queries = parsed_obj.get("queries", [])
                    if isinstance(queries, list):
                        return [str(q) for q in queries if isinstance(q, str)][:8]
    except Exception as e:
        logger.debug(f"[query_fanout] {type(e).__name__}: {e}")
    return []


async def check_rankings(queries: list[str], brand: str, location_code: int = 2840) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []

    for query in queries:
        ranking: dict[str, object] = {"query": query, "position": 0, "found": False, "top_result": ""}

        try:
            payload = [{"keyword": query, "location_code": location_code, "language_code": "en", "depth": 20}]
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(
                    "https://api.dataforseo.com/v3/serp/google/organic/live/advanced",
                    headers={"Authorization": DATAFORSEO_AUTH, "Content-Type": "application/json"},
                    json=payload,
                )
                resp.raise_for_status()
                data = cast(dict[str, object], resp.json())
                tasks = data.get("tasks", [])
                if isinstance(tasks, list) and tasks and isinstance(tasks[0], dict):
                    result = tasks[0].get("result", [])
                    if not isinstance(result, list) or not result or not isinstance(result[0], dict):
                        results.append(ranking)
                        continue
                    items = result[0].get("items", [])
                    if not isinstance(items, list):
                        results.append(ranking)
                        continue
                    brand_lower = brand.lower()
                    for item in items:
                        if not isinstance(item, dict) or item.get("type") != "organic":
                            continue
                        title = str(item.get("title", "")).lower()
                        url = str(item.get("url", "")).lower()
                        if not ranking["top_result"]:
                            ranking["top_result"] = str(item.get("title", ""))
                        if brand_lower in title or brand_lower in url:
                            ranking["position"] = item.get("rank_group", 0)
                            ranking["found"] = True
                            break
        except Exception as e:
            logger.debug(f"[query_fanout] {type(e).__name__}: {e}")

        results.append(ranking)

    return results


async def analyze_fanout(prompt: str, brand: str, location_code: int = 2840) -> dict[str, object]:
    queries = await generate_fanout_queries(prompt, brand)
    if not queries:
        return {"queries": [], "rankings": [], "coverage": 0.0}

    rankings = await check_rankings(queries, brand, location_code)
    found_count = sum(1 for r in rankings if r["found"])
    coverage = found_count / len(rankings) if rankings else 0.0

    return {
        "queries": queries,
        "rankings": rankings,
        "coverage": round(coverage, 2),
    }
