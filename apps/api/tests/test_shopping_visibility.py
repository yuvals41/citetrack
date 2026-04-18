from __future__ import annotations

from typing import Any

import pytest

import ai_visibility.analysis.shopping_visibility as shopping_visibility


def _serp_payload(items: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "tasks": [
            {
                "result": [
                    {
                        "items": items,
                    }
                ]
            }
        ]
    }


def test_build_queries_uses_defaults_when_none() -> None:
    queries = shopping_visibility._build_queries("Acme", None)
    assert queries == [
        "Acme products",
        "best alternatives to Acme",
        "buy Acme",
    ]


def test_build_queries_filters_empty_values() -> None:
    queries = shopping_visibility._build_queries("Acme", ["", " laptop ", "   "])
    assert queries == ["laptop"]


@pytest.mark.asyncio
async def test_brand_found_in_all_channels(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_post(url: str, payload: list[dict[str, Any]]) -> dict[str, Any]:
        _ = payload
        if url == shopping_visibility.GOOGLE_ORGANIC_URL:
            return _serp_payload(
                [
                    {
                        "type": "knowledge_graph_shopping_item",
                        "title": "Acme Blender",
                        "price": "$49.99",
                        "source": "Acme Store",
                        "rank_group": 2,
                    }
                ]
            )
        if url == shopping_visibility.GOOGLE_AI_MODE_URL:
            return _serp_payload(
                [
                    {
                        "type": "shopping_carousel",
                        "title": "Acme Blender Pro",
                        "description": "Acme is one of the top options.",
                        "price": "$49.99",
                    }
                ]
            )
        return _serp_payload(
            [
                {
                    "type": "llm_answer",
                    "text": "The best blenders include Acme Blender Pro and other premium options.",
                }
            ]
        )

    monkeypatch.setattr(shopping_visibility, "_post_dataforseo", _fake_post)
    result = await shopping_visibility.check_shopping_visibility("Acme", ["blender"])

    assert result["google_shopping"]["brand_products_found"] == 1
    assert result["ai_mode_shopping"]["brand_in_ai_text"] is True
    assert result["chatgpt_shopping"]["brand_mentioned"] is True
    assert result["visibility_score"] == 1.0


@pytest.mark.asyncio
async def test_no_shopping_presence_returns_zero_score(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_post(url: str, payload: list[dict[str, Any]]) -> dict[str, Any]:
        _ = (url, payload)
        return _serp_payload(
            [
                {
                    "type": "organic",
                    "title": "Generic products",
                    "description": "No matching brand appears here.",
                }
            ]
        )

    monkeypatch.setattr(shopping_visibility, "_post_dataforseo", _fake_post)
    result = await shopping_visibility.check_shopping_visibility("Acme", ["blender"])

    assert result["google_shopping"]["brand_products_found"] == 0
    assert result["ai_mode_shopping"]["brand_in_ai_text"] is False
    assert result["chatgpt_shopping"]["brand_mentioned"] is False
    assert result["visibility_score"] == 0.0
    assert len(result["recommendations"]) >= 1


@pytest.mark.asyncio
async def test_partial_results_when_google_shopping_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_post(url: str, payload: list[dict[str, Any]]) -> dict[str, Any]:
        _ = payload
        if url == shopping_visibility.GOOGLE_ORGANIC_URL:
            raise RuntimeError("google shopping unavailable")
        if url == shopping_visibility.GOOGLE_AI_MODE_URL:
            return _serp_payload([{"type": "shopping_block", "description": "Acme is featured."}])
        return _serp_payload([{"type": "llm_answer", "text": "Acme is recommended."}])

    monkeypatch.setattr(shopping_visibility, "_post_dataforseo", _fake_post)
    result = await shopping_visibility.check_shopping_visibility("Acme", ["blender"])

    assert result["google_shopping"]["brand_products_found"] == 0
    assert result["ai_mode_shopping"]["brand_in_ai_text"] is True
    assert result["chatgpt_shopping"]["brand_mentioned"] is True
    assert result["visibility_score"] == 0.6


@pytest.mark.asyncio
async def test_partial_results_when_ai_mode_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_post(url: str, payload: list[dict[str, Any]]) -> dict[str, Any]:
        _ = payload
        if url == shopping_visibility.GOOGLE_ORGANIC_URL:
            return _serp_payload(
                [
                    {
                        "type": "knowledge_graph_shopping_item",
                        "title": "Acme Coffee Maker",
                        "rank_group": 3,
                        "source": "Acme",
                    }
                ]
            )
        if url == shopping_visibility.GOOGLE_AI_MODE_URL:
            raise RuntimeError("no subscription")
        return _serp_payload([{"type": "llm_answer", "text": "Acme Coffee Maker is excellent."}])

    monkeypatch.setattr(shopping_visibility, "_post_dataforseo", _fake_post)
    result = await shopping_visibility.check_shopping_visibility("Acme", ["coffee maker"])

    assert result["google_shopping"]["brand_products_found"] == 1
    assert result["ai_mode_shopping"]["brand_in_ai_text"] is False
    assert result["chatgpt_shopping"]["brand_mentioned"] is True
    assert result["visibility_score"] == 0.75


@pytest.mark.asyncio
async def test_partial_results_when_chatgpt_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_post(url: str, payload: list[dict[str, Any]]) -> dict[str, Any]:
        _ = payload
        if url == shopping_visibility.GOOGLE_ORGANIC_URL:
            return _serp_payload(
                [
                    {
                        "type": "knowledge_graph_shopping_item",
                        "title": "Acme Camera",
                        "rank_group": 1,
                        "source": "Acme",
                    }
                ]
            )
        if url == shopping_visibility.GOOGLE_AI_MODE_URL:
            return _serp_payload([{"type": "shopping_list", "description": "Acme camera is highlighted."}])
        raise RuntimeError("chatgpt endpoint failed")

    monkeypatch.setattr(shopping_visibility, "_post_dataforseo", _fake_post)
    result = await shopping_visibility.check_shopping_visibility("Acme", ["camera"])

    assert result["google_shopping"]["brand_products_found"] == 1
    assert result["ai_mode_shopping"]["brand_in_ai_text"] is True
    assert result["chatgpt_shopping"]["brand_mentioned"] is False
    assert result["visibility_score"] == 0.75


@pytest.mark.asyncio
async def test_default_query_generation_used_when_none(monkeypatch: pytest.MonkeyPatch) -> None:
    seen_queries: list[str] = []

    async def _fake_post(url: str, payload: list[dict[str, Any]]) -> dict[str, Any]:
        keyword = str(payload[0].get("keyword", ""))
        seen_queries.append(f"{url}|{keyword}")
        return _serp_payload([])

    monkeypatch.setattr(shopping_visibility, "_post_dataforseo", _fake_post)
    await shopping_visibility.check_shopping_visibility("Acme", None)

    google_keywords = [
        value.split("|", 1)[1] for value in seen_queries if value.startswith(shopping_visibility.GOOGLE_ORGANIC_URL)
    ]
    assert google_keywords == [
        "Acme products",
        "best alternatives to Acme",
        "buy Acme",
    ]

    ai_keywords = [
        value.split("|", 1)[1] for value in seen_queries if value.startswith(shopping_visibility.GOOGLE_AI_MODE_URL)
    ]
    assert ai_keywords == ["best Acme alternatives"]

    chatgpt_keywords = [
        value.split("|", 1)[1] for value in seen_queries if value.startswith(shopping_visibility.CHATGPT_SHOPPING_URL)
    ]
    assert chatgpt_keywords == ["What are the best Acme products to buy?"]


@pytest.mark.asyncio
async def test_custom_queries_are_used_for_ai_mode_and_chatgpt(monkeypatch: pytest.MonkeyPatch) -> None:
    seen_queries: list[str] = []

    async def _fake_post(url: str, payload: list[dict[str, Any]]) -> dict[str, Any]:
        seen_queries.append(f"{url}|{payload[0].get('keyword', '')}")
        return _serp_payload([])

    monkeypatch.setattr(shopping_visibility, "_post_dataforseo", _fake_post)
    await shopping_visibility.check_shopping_visibility("Acme", ["espresso machine", "coffee grinder"])

    ai_keywords = [
        value.split("|", 1)[1] for value in seen_queries if value.startswith(shopping_visibility.GOOGLE_AI_MODE_URL)
    ]
    assert ai_keywords == ["espresso machine", "coffee grinder"]

    chatgpt_keywords = [
        value.split("|", 1)[1] for value in seen_queries if value.startswith(shopping_visibility.CHATGPT_SHOPPING_URL)
    ]
    assert chatgpt_keywords == ["What are the best espresso machine to buy?"]


def test_compute_visibility_score_without_top_rank_bonus() -> None:
    score = shopping_visibility._compute_visibility_score(
        google_shopping={
            "brand_products_found": 1,
            "products": [{"rank": 8}],
        },
        ai_mode_shopping={"brand_in_ai_text": True},
        chatgpt_shopping={"brand_mentioned": True},
    )
    assert score == 0.9


def test_compute_visibility_score_single_channel_only() -> None:
    score = shopping_visibility._compute_visibility_score(
        google_shopping={
            "brand_products_found": 1,
            "products": [{"rank": 2}],
        },
        ai_mode_shopping={"brand_in_ai_text": False},
        chatgpt_shopping={"brand_mentioned": False},
    )
    assert score == 0.4


def test_extract_chatgpt_text_uses_task_level_fallback() -> None:
    payload = {
        "tasks": [
            {
                "result": [{"items": []}],
                "result_text": "Acme appears in this fallback text.",
            }
        ]
    }
    text = shopping_visibility._extract_chatgpt_text(payload)
    assert text == "Acme appears in this fallback text."


@pytest.mark.asyncio
async def test_gather_return_exceptions_still_returns_partial_result(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _raise_google(brand_name: str, queries: list[str]) -> dict[str, Any]:
        _ = (brand_name, queries)
        raise RuntimeError("google task exploded")

    async def _ok_ai(brand_name: str, queries: list[str]) -> dict[str, Any]:
        _ = (brand_name, queries)
        return {
            "brand_in_ai_text": True,
            "shopping_items_total": 2,
            "brand_shopping_items": 1,
        }

    async def _ok_chatgpt(brand_name: str, queries: list[str]) -> dict[str, Any]:
        _ = (brand_name, queries)
        return {
            "brand_mentioned": True,
            "mention_position": 5,
            "response_snippet": "Acme appears in this answer.",
        }

    monkeypatch.setattr(shopping_visibility, "_fetch_google_shopping", _raise_google)
    monkeypatch.setattr(shopping_visibility, "_fetch_ai_mode_shopping", _ok_ai)
    monkeypatch.setattr(shopping_visibility, "_fetch_chatgpt_shopping", _ok_chatgpt)

    result = await shopping_visibility.check_shopping_visibility("Acme", ["headphones"])

    assert result["google_shopping"]["brand_products_found"] == 0
    assert result["ai_mode_shopping"]["brand_in_ai_text"] is True
    assert result["chatgpt_shopping"]["brand_mentioned"] is True
    assert result["visibility_score"] == 0.6
