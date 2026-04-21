from __future__ import annotations

# pyright: reportAny=false, reportExplicitAny=false

from datetime import datetime, timezone
from typing import Any, cast
from uuid import uuid4

from ai_visibility.models.brand_detail import BrandRecord
from ai_visibility.models.competitor import normalize_domain

Prisma = Any


class BrandRepository:
    def __init__(self, prisma: Prisma) -> None:
        self.prisma: Prisma = prisma

    async def get_primary_for_workspace(self, workspace_id: str) -> BrandRecord | None:
        row = await self.prisma.aivisbrand.find_first(
            where={"workspaceId": workspace_id},
            order=[{"createdAt": "asc"}, {"id": "asc"}],
        )
        return _brand_from_model(row) if row else None

    async def list_by_workspace(self, workspace_id: str) -> list[BrandRecord]:
        rows = await self.prisma.aivisbrand.find_many(
            where={"workspaceId": workspace_id},
            order=[{"createdAt": "asc"}, {"id": "asc"}],
        )
        return [_brand_from_model(row) for row in rows]

    async def upsert_primary(
        self,
        workspace_id: str,
        *,
        name: str,
        domain: str,
        aliases: list[str] | None = None,
    ) -> BrandRecord:
        _ = aliases
        existing = await self.get_primary_for_workspace(workspace_id)
        payload = {
            "name": name.strip(),
            "domain": normalize_domain(domain),
        }

        if existing is None:
            now = datetime.now(timezone.utc)
            created = await self.prisma.aivisbrand.create(
                data={
                    "id": str(uuid4()),
                    "workspace": {"connect": {"id": workspace_id}},
                    "createdAt": now,
                    "updatedAt": now,
                    **payload,
                }
            )
            return _brand_from_model(created)

        updated = await self.prisma.aivisbrand.update(
            where={"id": existing.id},
            data=payload,
        )
        return _brand_from_model(updated)


def _brand_from_model(row: Any) -> BrandRecord:
    return BrandRecord(
        id=str(row.id),
        workspace_id=str(row.workspaceId),
        name=str(row.name),
        domain=str(row.domain),
        aliases=[],
    )
