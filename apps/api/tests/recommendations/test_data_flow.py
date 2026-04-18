from __future__ import annotations
# pyright: reportAny=false, reportArgumentType=false

import asyncio
from typing import cast
from unittest.mock import AsyncMock, patch

from ai_visibility.models import RunResult
from ai_visibility.prompts import DEFAULT_PROMPTS
from ai_visibility.recommendations.engine import PROMPT_CATEGORY_GAP, RecommendationsEngine
from ai_visibility.ui.pages.recommendations import RecommendationState


def test_recommendation_state_maps_db_rows_to_view_state() -> None:
    mock_prisma = AsyncMock()
    mock_prisma.query_raw.return_value = [
        {
            "code": "LOW_VISIBILITY",
            "reason": "Brand rarely appears",
            "impact": "high",
            "next_step": "Expand comparison content",
            "confidence": 0.91,
        }
    ]

    with patch("ai_visibility.ui.pages.recommendations.get_prisma", new=AsyncMock(return_value=mock_prisma)):
        state = RecommendationState()
        asyncio.run(state.load_recommendations("acme"))

    assert state.current_workspace == "acme"
    assert len(state.recommendations) == 1
    assert state.recommendations[0]["rule_code"] == "LOW_VISIBILITY"
    assert state.recommendations[0]["priority"] == "high"
    assert state.recommendations[0]["description"] == "Expand comparison content"
    assert state.recommendations[0]["reason"] == "Brand rarely appears"


def test_prompt_category_gap_uses_default_prompt_categories() -> None:
    required_categories = {prompt["category"] for prompt in DEFAULT_PROMPTS}
    assert required_categories == {"buying_intent", "comparison", "recommendation", "informational"}

    runs = [
        {
            "visibility_score": 0.9,
            "citation_coverage": 0.9,
            "competitor_wins": 0,
            "missing_citations": 0,
            "prompt_category": sorted(required_categories),
        }
    ]

    recommendations = RecommendationsEngine().generate("acme", cast(list[RunResult], runs))
    assert all(item.rule_code != PROMPT_CATEGORY_GAP for item in recommendations)
