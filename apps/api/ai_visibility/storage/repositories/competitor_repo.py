from __future__ import annotations

# pyright: reportAny=false, reportExplicitAny=false

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from ai_visibility.models.competitor import CompetitorRecord, normalize_domain

Prisma = Any


class CompetitorRepository:
    def __init__(self, prisma: Prisma) -> None:
        self.prisma: Prisma = prisma

    async def list_by_workspace(self, workspace_id: str) -> list[CompetitorRecord]:
        rows = await self.prisma.aiviscompetitor.find_many(
            where={"workspaceId": workspace_id},
            order=[{"createdAt": "asc"}, {"id": "asc"}],
        )
        return [_competitor_from_model(row) for row in rows]

    async def create(self, workspace_id: str, name: str, domain: str) -> CompetitorRecord:
        now = datetime.now(timezone.utc)
        created = await self.prisma.aiviscompetitor.create(
            data={
                "id": str(uuid4()),
                "workspace": {"connect": {"id": workspace_id}},
                "name": name.strip(),
                "domain": normalize_domain(domain),
                "createdAt": now,
                "updatedAt": now,
            }
        )
        return _competitor_from_model(created)

    async def delete(self, competitor_id: str) -> bool:
        existing = await self.prisma.aiviscompetitor.find_unique(where={"id": competitor_id})
        if existing is None:
            return False
        await self.prisma.aiviscompetitor.delete(where={"id": competitor_id})
        return True

    async def get_by_domain(self, workspace_id: str, domain: str) -> CompetitorRecord | None:
        row = await self.prisma.aiviscompetitor.find_first(
            where={
                "workspaceId": workspace_id,
                "domain": normalize_domain(domain),
            }
        )
        return _competitor_from_model(row) if row else None


def _competitor_from_model(row: Any) -> CompetitorRecord:
    created_at = row.createdAt
    return CompetitorRecord(
        id=str(row.id),
        workspace_id=str(row.workspaceId),
        name=str(row.name),
        domain=str(row.domain),
        created_at=created_at if isinstance(created_at, datetime) else None,
    )
