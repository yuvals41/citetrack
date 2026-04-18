import asyncio
import os
from typing import Any, cast

import httpx
from loguru import logger

DATAFORSEO_AUTH = f"Basic {os.environ.get('DATAFORSEO_AUTH_HEADER', '')}"
GOOGLE_ORGANIC_URL = "https://api.dataforseo.com/v3/serp/google/organic/live/advanced"
GOOGLE_AI_MODE_URL = "https://api.dataforseo.com/v3/serp/google/ai_mode/live/advanced"
CHATGPT_SHOPPING_URL = "https://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/live/advanced"
TIMEOUT = 30.0


def _build_queries(brand_name: str, product_queries: list[str] | None) -> list[str]:
    if product_queries is not None:
        cleaned = [query.strip() for query in product_queries if query.strip()]
        if cleaned:
            return cleaned
    return [
        f"{brand_name} products",
        f"best alternatives to {brand_name}",
        f"buy {brand_name}",
    ]


def _extract_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    tasks = payload.get("tasks", [])
    if not isinstance(tasks, list) or not tasks:
        return []

    first_task = tasks[0]
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

    return [cast(dict[str, Any], item) for item in items if isinstance(item, dict)]


def _extract_chatgpt_text(payload: dict[str, Any]) -> str:
    items = _extract_items(payload)
    for item in items:
        for field in ("text", "description", "content", "snippet", "title"):
            value = item.get(field)
            if isinstance(value, str) and value.strip():
                return value

    tasks = payload.get("tasks", [])
    if isinstance(tasks, list) and tasks and isinstance(tasks[0], dict):
        first_task = cast(dict[str, Any], tasks[0])
        for field in ("result_text", "response", "ai_text"):
            value = first_task.get(field)
            if isinstance(value, str) and value.strip():
                return value
    return ""


def _parse_rank(item: dict[str, Any]) -> int:
    for key in ("rank_group", "rank_absolute", "rank"):
        value = item.get(key)
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
    return 0


def _parse_price(item: dict[str, Any]) -> str:
    for key in ("price", "current_price", "price_from", "displayed_price"):
        value = item.get(key)
        if value is None:
            continue
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def _item_text(item: dict[str, Any]) -> str:
    parts: list[str] = []
    for field in ("title", "description", "snippet", "text", "source", "seller", "merchant"):
        value = item.get(field)
        if isinstance(value, str):
            parts.append(value)
    return " ".join(parts).lower()


async def _post_dataforseo(url: str, payload: list[dict[str, Any]]) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.post(
            url,
            headers={"Authorization": DATAFORSEO_AUTH, "Content-Type": "application/json"},
            json=payload,
        )
        response.raise_for_status()
        return cast(dict[str, Any], response.json())


async def _fetch_google_shopping(brand_name: str, queries: list[str]) -> dict[str, Any]:
    products: list[dict[str, Any]] = []
    brand = brand_name.lower()

    for query in queries:
        payload = [
            {
                "keyword": query,
                "location_code": 2840,
                "language_code": "en",
                "depth": 20,
            }
        ]
        try:
            result = await _post_dataforseo(GOOGLE_ORGANIC_URL, payload)
        except Exception as exc:
            logger.debug(f"[shopping] Google Shopping request failed for '{query}': {type(exc).__name__}: {exc}")
            continue

        for item in _extract_items(result):
            if item.get("type") != "knowledge_graph_shopping_item":
                continue

            title = str(item.get("title") or item.get("name") or "")
            seller = str(item.get("source") or item.get("seller") or item.get("merchant") or "")
            rank = _parse_rank(item)
            price = _parse_price(item)
            combined = f"{title} {seller}".lower()
            brand_match = brand in combined

            products.append(
                {
                    "title": title,
                    "price": price,
                    "rank": rank,
                    "seller": seller,
                    "brand_match": brand_match,
                }
            )

    brand_products = [product for product in products if bool(product.get("brand_match"))]
    return {
        "brand_products_found": len(brand_products),
        "products": [
            {
                "title": str(product.get("title", "")),
                "price": str(product.get("price", "")),
                "rank": int(product.get("rank", 0) or 0),
                "seller": str(product.get("seller", "")),
            }
            for product in brand_products
        ],
    }


async def _fetch_ai_mode_shopping(brand_name: str, queries: list[str]) -> dict[str, Any]:
    ai_queries = queries if queries else [f"best {brand_name} alternatives"]
    brand = brand_name.lower()
    brand_in_ai_text = False
    shopping_items_total = 0
    brand_shopping_items = 0

    for query in ai_queries:
        payload = [
            {
                "keyword": query,
                "location_code": 2840,
                "language_code": "en",
                "depth": 20,
            }
        ]
        try:
            result = await _post_dataforseo(GOOGLE_AI_MODE_URL, payload)
        except Exception as exc:
            logger.debug(f"[shopping] AI Mode request failed for '{query}': {type(exc).__name__}: {exc}")
            continue

        items = _extract_items(result)
        for item in items:
            text = _item_text(item)
            if brand in text:
                brand_in_ai_text = True

            item_type = str(item.get("type", "")).lower()
            has_shopping_signal = "shopping" in item_type or any(
                key in item for key in ("price", "seller", "merchant", "product_id")
            )
            if has_shopping_signal:
                shopping_items_total += 1
                if brand in text:
                    brand_shopping_items += 1

    return {
        "brand_in_ai_text": brand_in_ai_text,
        "shopping_items_total": shopping_items_total,
        "brand_shopping_items": brand_shopping_items,
    }


async def _fetch_chatgpt_shopping(brand_name: str, queries: list[str]) -> dict[str, Any]:
    first_query = queries[0] if queries else f"{brand_name} products"
    prompt = f"What are the best {first_query} to buy?"
    payload = [{"keyword": prompt, "language_code": "en"}]

    try:
        result = await _post_dataforseo(CHATGPT_SHOPPING_URL, payload)
    except Exception as exc:
        logger.debug(f"[shopping] ChatGPT shopping request failed: {type(exc).__name__}: {exc}")
        return {
            "brand_mentioned": False,
            "mention_position": None,
            "response_snippet": "",
        }

    response_text = _extract_chatgpt_text(result)
    normalized_response = response_text.lower()
    normalized_brand = brand_name.lower()
    index = normalized_response.find(normalized_brand)
    mention_position = index + 1 if index >= 0 else None

    return {
        "brand_mentioned": index >= 0,
        "mention_position": mention_position,
        "response_snippet": response_text[:200],
    }


def _compute_visibility_score(
    google_shopping: dict[str, Any],
    ai_mode_shopping: dict[str, Any],
    chatgpt_shopping: dict[str, Any],
) -> float:
    score = 0.0

    google_has_brand = int(google_shopping.get("brand_products_found", 0)) > 0
    ai_has_brand = bool(ai_mode_shopping.get("brand_in_ai_text", False))
    chatgpt_has_brand = bool(chatgpt_shopping.get("brand_mentioned", False))

    if google_has_brand:
        score += 0.30
    if ai_has_brand:
        score += 0.25
    if chatgpt_has_brand:
        score += 0.25

    products = cast(list[dict[str, Any]], google_shopping.get("products", []))
    top_rank_found = any(int(product.get("rank", 0) or 0) in range(1, 6) for product in products)
    if top_rank_found:
        score += 0.10

    channel_mentions = sum([google_has_brand, ai_has_brand, chatgpt_has_brand])
    if channel_mentions >= 2:
        score += 0.10

    return max(0.0, min(1.0, round(score, 2)))


def _build_recommendations(
    brand_name: str,
    google_shopping: dict[str, Any],
    ai_mode_shopping: dict[str, Any],
    chatgpt_shopping: dict[str, Any],
    score: float,
) -> list[str]:
    recommendations: list[str] = []

    if int(google_shopping.get("brand_products_found", 0)) == 0:
        recommendations.append(
            f"Add stronger product schema and merchant feed coverage so {brand_name} appears in Google Shopping cards."
        )
    else:
        products = cast(list[dict[str, Any]], google_shopping.get("products", []))
        best_rank = min([int(product.get("rank", 99) or 99) for product in products], default=99)
        if best_rank > 5:
            recommendations.append(
                "Improve product page quality, price competitiveness, and merchant trust signals to reach top-5 shopping placement."
            )

    if not bool(ai_mode_shopping.get("brand_in_ai_text", False)):
        recommendations.append(
            f"Publish comparison content (e.g., 'best alternatives to {brand_name}') with clear product specs AI can quote."
        )

    if not bool(chatgpt_shopping.get("brand_mentioned", False)):
        recommendations.append(
            "Create buyer-guide and review-friendly pages that include explicit purchase intent phrases and product differentiators."
        )

    if score >= 0.8:
        recommendations.append(
            "Visibility is strong across channels; focus on defending rankings with fresh reviews and pricing updates."
        )

    if not recommendations:
        recommendations.append(
            "Maintain current shopping visibility and monitor weekly for ranking or mention declines."
        )

    return recommendations


async def check_shopping_visibility(brand_name: str, product_queries: list[str] | None = None) -> dict[str, Any]:
    queries = _build_queries(brand_name, product_queries)
    logger.debug(f"[shopping] Checking shopping visibility for brand='{brand_name}' with {len(queries)} queries")

    channel_results = await asyncio.gather(
        _fetch_google_shopping(brand_name, queries),
        _fetch_ai_mode_shopping(
            brand_name, queries if product_queries is not None else [f"best {brand_name} alternatives"]
        ),
        _fetch_chatgpt_shopping(brand_name, queries),
        return_exceptions=True,
    )

    google_shopping_default: dict[str, Any] = {"brand_products_found": 0, "products": []}
    ai_mode_default: dict[str, Any] = {
        "brand_in_ai_text": False,
        "shopping_items_total": 0,
        "brand_shopping_items": 0,
    }
    chatgpt_default: dict[str, Any] = {
        "brand_mentioned": False,
        "mention_position": None,
        "response_snippet": "",
    }

    google_result_raw, ai_mode_raw, chatgpt_raw = channel_results

    google_shopping = google_shopping_default
    if isinstance(google_result_raw, Exception):
        logger.debug(f"[shopping] Google Shopping failed: {type(google_result_raw).__name__}: {google_result_raw}")
    elif isinstance(google_result_raw, dict):
        google_shopping = google_result_raw

    ai_mode_shopping = ai_mode_default
    if isinstance(ai_mode_raw, Exception):
        logger.debug(f"[shopping] AI Mode failed: {type(ai_mode_raw).__name__}: {ai_mode_raw}")
    elif isinstance(ai_mode_raw, dict):
        ai_mode_shopping = ai_mode_raw

    chatgpt_shopping = chatgpt_default
    if isinstance(chatgpt_raw, Exception):
        logger.debug(f"[shopping] ChatGPT shopping failed: {type(chatgpt_raw).__name__}: {chatgpt_raw}")
    elif isinstance(chatgpt_raw, dict):
        chatgpt_shopping = chatgpt_raw

    score = _compute_visibility_score(google_shopping, ai_mode_shopping, chatgpt_shopping)
    recommendations = _build_recommendations(
        brand_name=brand_name,
        google_shopping=google_shopping,
        ai_mode_shopping=ai_mode_shopping,
        chatgpt_shopping=chatgpt_shopping,
        score=score,
    )

    result: dict[str, Any] = {
        "brand": brand_name,
        "google_shopping": google_shopping,
        "ai_mode_shopping": ai_mode_shopping,
        "chatgpt_shopping": chatgpt_shopping,
        "visibility_score": score,
        "recommendations": recommendations,
    }
    logger.debug(f"[shopping] Completed shopping visibility for brand='{brand_name}' score={score}")
    return result
