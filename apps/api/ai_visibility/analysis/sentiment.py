import json
import os
from typing import Any, cast

import httpx
from dotenv import load_dotenv
from loguru import logger

load_dotenv()


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


async def analyze_sentiment(brand_name: str, response_text: str) -> dict[str, Any]:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key or not response_text.strip():
        return {"sentiment": "neutral", "score": 0.5, "reason": ""}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            instructions = (
                "Analyze how this AI response describes the brand. "
                "Is the description positive, neutral, or negative? "
                "Score from 0.0 (very negative) to 1.0 (very positive). "
                "Return ONLY valid JSON with keys: sentiment (string: positive/neutral/negative), score (number), reason (string)."
            )
            input_text = f"Brand: {brand_name}\n\nAI Response:\n{response_text[:1000]}"

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
            data = cast(dict[str, Any], resp.json())
            content = data.get("content", [])
            if isinstance(content, list) and content:
                text = str(content[0].get("text", "{}"))
                json_str = _extract_json(text)
                return cast(dict[str, Any], json.loads(json_str))
    except Exception as e:
        logger.debug(f"[sentiment] {type(e).__name__}: {e}")
    return {"sentiment": "neutral", "score": 0.5, "reason": ""}
