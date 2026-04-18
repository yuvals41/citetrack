import json
import os

import httpx
from dotenv import load_dotenv
from loguru import logger

_ = load_dotenv()


async def generate_recommendations(
    brand_name: str,
    visibility_score: float,
    citation_coverage: float,
    sentiment_data: dict[str, object],
    source_domains: list[str],
    competitor_scores: list[dict[str, object]],
    absent_prompts: list[str],
    mentioned_prompts: list[str],
) -> list[dict[str, str]]:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return _fallback_recommendations(visibility_score, citation_coverage, source_domains)

    context = f"""
Brand: {brand_name}
Visibility Score: {visibility_score:.0%} (% of AI responses mentioning the brand)
Citation Coverage: {citation_coverage:.0%} (% of responses linking to the website)
Sentiment: {json.dumps(sentiment_data)}
Sources AI cites: {", ".join(source_domains[:10])}
Competitors mentioned: {json.dumps(competitor_scores[:5])}
Questions where brand was NOT mentioned: {json.dumps(absent_prompts[:5])}
Questions where brand WAS mentioned: {json.dumps(mentioned_prompts[:5])}
"""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
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
                            "content": (
                                "Based on this AI visibility scan data, generate 3-5 specific, actionable "
                                "recommendations to improve this brand's visibility in AI assistant responses.\n\n"
                                f"{context}\n"
                                "For each recommendation, provide:\n"
                                "1. A specific action (what exactly to do)\n"
                                "2. Why it matters (tied to the data)\n"
                                "3. Expected impact (high/medium/low)\n\n"
                                "Return as JSON array: "
                                '[{"action": "...", "reason": "...", "impact": "high|medium|low"}]\n'
                                "Return ONLY the JSON array, no other text."
                            ),
                        }
                    ],
                },
            )
            resp.raise_for_status()
            data = resp.json()
            text = data.get("content", [{}])[0].get("text", "[]")
            if "```" in text:
                text = text.split("```", maxsplit=2)[1]
                if text.startswith("json"):
                    text = text[4:]

            recommendations = json.loads(text.strip())
            if isinstance(recommendations, list):
                return [
                    {
                        "recommendation_code": f"action_{i + 1}",
                        "reason": str(r.get("reason", "")),
                        "next_step": str(r.get("action", "")),
                        "impact": str(r.get("impact", "medium")),
                    }
                    for i, r in enumerate(recommendations)
                    if isinstance(r, dict)
                ][:5]
    except Exception as e:  # noqa: BLE001
        logger.debug(f"[actions] Failed to generate recommendations: {type(e).__name__}: {e}")

    return _fallback_recommendations(visibility_score, citation_coverage, source_domains)


def _fallback_recommendations(
    visibility_score: float,
    citation_coverage: float,
    source_domains: list[str],
) -> list[dict[str, str]]:
    recs: list[dict[str, str]] = []

    if visibility_score < 0.5:
        recs.append(
            {
                "recommendation_code": "low_visibility",
                "reason": f"Only {visibility_score:.0%} of AI responses mention your brand",
                "next_step": (
                    "Create detailed FAQ pages answering common industry questions. "
                    "AI assistants rely on structured Q&A content."
                ),
                "impact": "high",
            }
        )

    if citation_coverage < 0.1:
        recs.append(
            {
                "recommendation_code": "no_citations",
                "reason": f"Only {citation_coverage:.0%} of AI responses link to your website",
                "next_step": (
                    "Add Schema.org markup (FAQ, HowTo, Organization) to your key pages. "
                    "This helps AI cite your content directly."
                ),
                "impact": "high",
            }
        )

    if source_domains:
        missing_platforms: list[str] = []
        for platform in ["g2.com", "trustpilot.com", "reddit.com", "linkedin.com"]:
            if platform not in source_domains:
                missing_platforms.append(platform)
        if missing_platforms:
            recs.append(
                {
                    "recommendation_code": "missing_sources",
                    "reason": (f"AI cites {', '.join(source_domains[:3])} but not {', '.join(missing_platforms[:2])}"),
                    "next_step": (
                        f"Create profiles and get reviews on {missing_platforms[0]}. "
                        "AI frequently cites these platforms."
                    ),
                    "impact": "medium",
                }
            )

    if not recs:
        recs.append(
            {
                "recommendation_code": "maintain",
                "reason": "Your AI visibility is healthy",
                "next_step": (
                    "Continue monitoring and publishing content that answers common questions in your industry."
                ),
                "impact": "low",
            }
        )

    return recs
