from __future__ import annotations

from ai_visibility.storage.prisma_connection import get_prisma


class RecommendationState:
    def __init__(self) -> None:
        self.current_workspace = ""
        self.recommendations: list[dict[str, object]] = []

    async def load_recommendations(self, workspace_slug: str) -> None:
        prisma = await get_prisma()
        rows = await prisma.query_raw("SELECT * FROM ai_vis_recommendations WHERE workspace_slug = $1", workspace_slug)
        self.current_workspace = workspace_slug
        self.recommendations = []
        if not isinstance(rows, list):
            return
        for row in rows:
            if not isinstance(row, dict):
                continue
            self.recommendations.append(
                {
                    "rule_code": str(row.get("code", "")),
                    "priority": str(row.get("impact", "")),
                    "description": str(row.get("next_step", "")),
                    "reason": str(row.get("reason", "")),
                    "confidence": row.get("confidence", 0),
                }
            )
