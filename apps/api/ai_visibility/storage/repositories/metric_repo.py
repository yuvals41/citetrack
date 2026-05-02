from __future__ import annotations

# pyright: reportAny=false, reportExplicitAny=false, reportUnannotatedClassAttribute=false

from datetime import datetime
import sqlite3
from typing import Any

from ai_visibility.storage.types import MetricSnapshotRecord

Prisma = Any


class MetricRepository:
    def __init__(self, prisma: Prisma) -> None:
        self.prisma = prisma

    async def upsert_snapshot(
        self,
        snapshot: MetricSnapshotRecord,
        *,
        conn: sqlite3.Connection | None = None,
    ) -> MetricSnapshotRecord:
        citation_coverage = float(snapshot["citation_coverage"]) if "citation_coverage" in snapshot else 0.0
        competitor_wins = int(snapshot["competitor_wins"]) if "competitor_wins" in snapshot else 0
        payload: MetricSnapshotRecord = {
            "id": snapshot["id"],
            "workspace_id": snapshot["workspace_id"],
            "brand_id": snapshot["brand_id"],
            "formula_version": snapshot["formula_version"],
            "visibility_score": snapshot["visibility_score"],
            "citation_coverage": citation_coverage,
            "competitor_wins": competitor_wins,
            "mention_count": snapshot["mention_count"],
            "created_at": snapshot["created_at"],
        }

        _ = conn
        result = await self.prisma.metricsnapshot.upsert(
            where={"id": payload["id"]},
            data={
                "create": {
                    "id": payload["id"],
                    "workspaceId": payload["workspace_id"],
                    "brandId": payload["brand_id"],
                    "formulaVersion": payload["formula_version"],
                    "visibilityScore": float(payload["visibility_score"]),
                    "citationCoverage": citation_coverage,
                    "competitorWins": competitor_wins,
                    "mentionCount": int(payload["mention_count"]),
                    "createdAt": _parse_datetime(payload["created_at"]),
                },
                "update": {
                    "workspaceId": payload["workspace_id"],
                    "brandId": payload["brand_id"],
                    "formulaVersion": payload["formula_version"],
                    "visibilityScore": float(payload["visibility_score"]),
                    "citationCoverage": citation_coverage,
                    "competitorWins": competitor_wins,
                    "mentionCount": int(payload["mention_count"]),
                    "createdAt": _parse_datetime(payload["created_at"]),
                },
            },
        )

        return _metric_from_model(result)

    async def get_latest_by_workspace(self, workspace_id: str) -> MetricSnapshotRecord | None:
        row = await self.prisma.metricsnapshot.find_first(
            where={"workspaceId": workspace_id},
            order=[{"createdAt": "desc"}, {"id": "desc"}],
        )

        return _metric_from_model(row) if row else None

    async def get_previous_by_workspace(self, workspace_id: str) -> MetricSnapshotRecord | None:
        row = await self.prisma.metricsnapshot.find_first(
            where={"workspaceId": workspace_id},
            order=[{"createdAt": "desc"}, {"id": "desc"}],
            skip=1,
        )

        return _metric_from_model(row) if row else None

    async def list_by_workspace(self, workspace_id: str) -> list[MetricSnapshotRecord]:
        rows = await self.prisma.metricsnapshot.find_many(
            where={"workspaceId": workspace_id},
            order=[{"createdAt": "asc"}, {"id": "asc"}],
        )

        return [_metric_from_model(row) for row in rows]


def _metric_from_model(row: Any) -> MetricSnapshotRecord:
    return {
        "id": str(row.id),
        "workspace_id": str(row.workspaceId),
        "brand_id": str(row.brandId),
        "formula_version": str(row.formulaVersion),
        "visibility_score": float(row.visibilityScore),
        "citation_coverage": float(row.citationCoverage),
        "competitor_wins": int(row.competitorWins),
        "mention_count": int(row.mentionCount),
        "created_at": _to_iso(row.createdAt),
    }


def _parse_datetime(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def _to_iso(value: datetime) -> str:
    return value.isoformat()
