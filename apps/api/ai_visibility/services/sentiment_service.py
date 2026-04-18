from __future__ import annotations

POSITIVE_WORDS = {
    "recommend",
    "best",
    "excellent",
    "top-rated",
    "highly",
    "great",
    "outstanding",
    "trusted",
}

NEGATIVE_WORDS = {
    "avoid",
    "poor",
    "worst",
    "not recommended",
    "issues",
    "problems",
    "disappointing",
    "mediocre",
}


async def compute_sentiment_from_mentions(mentions_data: list[dict[str, object]]) -> dict[str, object]:
    """Replace heuristic word counting with proper aggregation."""
    sentiment_counts: dict[str, int] = {"positive": 0, "negative": 0, "neutral": 0}
    sentiment_scores: list[float] = []

    for mention in mentions_data:
        response_text = str(mention.get("raw_response") or mention.get("text") or "")
        if not response_text:
            continue

        response_lower = response_text.lower()
        positive_count = sum(1 for word in POSITIVE_WORDS if word in response_lower)
        negative_count = sum(1 for word in NEGATIVE_WORDS if word in response_lower)

        if positive_count > negative_count:
            sentiment_counts["positive"] += 1
            sentiment_scores.append(0.8)
        elif negative_count > positive_count:
            sentiment_counts["negative"] += 1
            sentiment_scores.append(0.2)
        else:
            sentiment_counts["neutral"] += 1
            sentiment_scores.append(0.5)

    score = round(sum(sentiment_scores) / len(sentiment_scores), 2) if sentiment_scores else 0.0
    overall = "positive" if score > 0.6 else "negative" if score < 0.4 else "neutral"

    return {
        "positive": sentiment_counts["positive"],
        "negative": sentiment_counts["negative"],
        "neutral": sentiment_counts["neutral"],
        "overall": overall,
        "score": score,
    }
