# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportAny=false, reportUnusedCallResult=false, reportMissingTypeArgument=false, reportUnknownParameterType=false

import json
import os
from typing import cast

import httpx
from dotenv import load_dotenv

_ = load_dotenv()


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


async def analyze_page(url: str) -> dict[str, object]:
    tavily_key = os.getenv("TAVILY_API_KEY", "")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not tavily_key or not anthropic_key:
        return {"error": "Missing API keys", "scores": {}, "sections": []}

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            extract_resp = await client.post(
                "https://api.tavily.com/extract",
                json={"api_key": tavily_key, "urls": [url]},
            )
            results = extract_resp.json().get("results", [])
            if not results:
                return {"error": "Could not fetch page", "scores": {}, "sections": []}

            raw_content = str(results[0].get("raw_content", ""))
            if not raw_content.strip():
                return {"error": "Page has no extractable content", "scores": {}, "sections": []}

        async with httpx.AsyncClient(timeout=30.0) as client:
            instructions = (
                "You are a content extractability auditor. Analyze the website content and score "
                "how well AI assistants can extract and cite information from it. "
                "Score each dimension from 0 to 100. Return ONLY valid JSON with this structure: "
                '{"overall_score": number, "summary_block": {"score": number, "finding": string}, '
                '"section_integrity": {"score": number, "finding": string}, '
                '"modular_content": {"score": number, "finding": string}, '
                '"schema_markup": {"score": number, "finding": string}, '
                '"static_content": {"score": number, "finding": string}, '
                '"recommendations": [string]}'
            )
            input_text = f"Analyze this website content for AI extractability:\n\n{raw_content[:3000]}"

            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": anthropic_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-6",
                    "max_tokens": 8000,
                    "thinking": {"type": "adaptive"},
                    "messages": [
                        {
                            "role": "user",
                            "content": f"{instructions}\n\n{input_text}",
                        }
                    ],
                },
            )
            resp.raise_for_status()
            data = cast(dict, resp.json())
            content = data.get("content", [])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text = str(block.get("text", "{}"))
                        json_str = _extract_json(text)
                        return cast(dict, json.loads(json_str))

    except Exception as exc:
        return {"error": str(exc), "scores": {}, "sections": []}

    return {"error": "No analysis generated", "scores": {}, "sections": []}
