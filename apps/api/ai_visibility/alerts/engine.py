from datetime import datetime, timezone


def detect_alerts(
    current_visibility: float,
    previous_visibility: float,
    current_citation_coverage: float,
    previous_citation_coverage: float,
    competitor_scores: list[dict[str, object]],
    brand_slug: str,
) -> list[dict[str, str]]:
    _ = brand_slug
    alerts: list[dict[str, str]] = []

    if previous_visibility > 0:
        drop = previous_visibility - current_visibility
        if drop > 0.1:
            alerts.append(
                {
                    "type": "visibility_drop",
                    "severity": "high",
                    "message": f"Visibility dropped {int(drop * 100)}% (from {int(previous_visibility * 100)}% to {int(current_visibility * 100)}%)",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

    if previous_citation_coverage > 0:
        cit_drop = previous_citation_coverage - current_citation_coverage
        if cit_drop > 0.1:
            alerts.append(
                {
                    "type": "citation_drop",
                    "severity": "medium",
                    "message": f"Citation coverage dropped {int(cit_drop * 100)}% (from {int(previous_citation_coverage * 100)}% to {int(current_citation_coverage * 100)}%)",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

    brand_score = 0.0
    for c in competitor_scores:
        if str(c.get("is_brand", "")) == "true":
            try:
                brand_score = float(str(c.get("score", 0)))
            except (ValueError, TypeError):
                pass

    for c in competitor_scores:
        if str(c.get("is_brand", "")) != "true":
            try:
                comp_score = float(str(c.get("score", 0)))
                if comp_score > brand_score and comp_score > 0:
                    alerts.append(
                        {
                            "type": "competitor_surge",
                            "severity": "high",
                            "message": f"{c.get('name', 'A competitor')} has higher visibility ({int(comp_score * 100)}%) than your brand ({int(brand_score * 100)}%)",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )
            except (ValueError, TypeError):
                pass

    if previous_visibility == 0 and current_visibility > 0:
        alerts.append(
            {
                "type": "first_scan",
                "severity": "info",
                "message": f"First scan complete! Your visibility score is {int(current_visibility * 100)}%",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    return alerts
