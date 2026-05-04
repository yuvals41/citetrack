from __future__ import annotations

# pyright: reportAny=false, reportExplicitAny=false

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from ai_visibility.storage.types import RecommendationRecord

Prisma = Any
_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


class RecommendationRepository:
    def __init__(self, prisma: Prisma) -> None:
        self.prisma: Prisma = prisma

    async def persist_batch(
        self,
        workspace_id: str,
        brand_id: str,
        recommendations: list[dict[str, str]],
    ) -> int:
        if not recommendations:
            return 0

        created_at = datetime.now(timezone.utc)
        inserted = 0
        for recommendation in recommendations:
            title = str(recommendation.get("title", "")).strip()
            description = str(recommendation.get("description", "")).strip()
            priority = _normalize_priority(recommendation.get("priority"))
            if not title or not description:
                continue

            await self.prisma.recommendation.create(
                data={
                    "id": str(uuid4()),
                    "workspaceId": workspace_id,
                    "brandId": brand_id,
                    "title": title,
                    "description": description,
                    "priority": priority,
                    "ruleTriggersJson": recommendation.get("rule_triggers_json"),
                    "createdAt": created_at,
                }
            )
            inserted += 1

        return inserted

    async def get_latest_for_workspace(
        self,
        workspace_id: str,
        limit: int = 10,
    ) -> list[dict[str, object]]:
        latest = await self.prisma.recommendation.find_first(
            where={"workspaceId": workspace_id},
            order=[{"createdAt": "desc"}, {"id": "desc"}],
        )
        if latest is None:
            return []

        rows = await self.prisma.recommendation.find_many(
            where={"workspaceId": workspace_id, "createdAt": latest.createdAt},
        )
        records = [_recommendation_from_model(row) for row in rows]
        records.sort(key=lambda record: (_PRIORITY_ORDER.get(str(record["priority"]), 99), str(record["title"])))
        return records[:limit]


def _recommendation_from_model(row: Any) -> dict[str, object]:
    rule_triggers_json = None if row.ruleTriggersJson is None else str(row.ruleTriggersJson)
    recommendation_code = _recommendation_code_from_rule_triggers(rule_triggers_json) or str(row.id)
    record: RecommendationRecord = {
        "id": str(row.id),
        "workspace_id": str(row.workspaceId),
        "brand_id": str(row.brandId),
        "title": str(row.title),
        "description": str(row.description),
        "priority": _normalize_priority(row.priority),
        "rule_triggers_json": rule_triggers_json,
        "created_at": _to_iso(row.createdAt),
    }
    return {
        **record,
        "action_id": recommendation_code,
        "recommendation_code": recommendation_code,
    }


def _recommendation_code_from_rule_triggers(raw: str | None) -> str | None:
    if raw is None:
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None

    if not isinstance(parsed, dict):
        return None
    code = parsed.get("recommendation_code") or parsed.get("code")
    if not isinstance(code, str):
        return None
    normalized = code.strip()
    return normalized or None


def _normalize_priority(value: object) -> str:
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in _PRIORITY_ORDER:
            return normalized
    return "medium"


def _to_iso(value: datetime) -> str:
    return value.isoformat()
