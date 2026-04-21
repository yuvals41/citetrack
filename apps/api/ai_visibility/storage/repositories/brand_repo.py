from __future__ import annotations

# pyright: reportAny=false, reportExplicitAny=false

from datetime import datetime, timezone
from typing import Any, cast
from uuid import uuid4

from ai_visibility.models.brand_detail import BrandRecord
from ai_visibility.models.competitor import normalize_domain
from ai_visibility.storage.repositories.brand_alias_repo import BrandAliasRepository

Prisma = Any


class BrandRepository:
    def __init__(self, prisma: Prisma, alias_repo: BrandAliasRepository | None = None) -> None:
        self.prisma: Prisma = prisma
        self._alias_repo: BrandAliasRepository = alias_repo or BrandAliasRepository()

    async def get_primary_for_workspace(self, workspace_id: str) -> BrandRecord | None:
        row = await self.prisma.aivisbrand.find_first(
            where={"workspaceId": workspace_id},
            order=[{"createdAt": "asc"}, {"id": "asc"}],
        )
        if not row:
            return None
        aliases = self._alias_repo.get_aliases(str(row.workspaceId))
        return _brand_from_model(row, aliases=aliases)

    async def list_by_workspace(self, workspace_id: str) -> list[BrandRecord]:
        rows = await self.prisma.aivisbrand.find_many(
            where={"workspaceId": workspace_id},
            order=[{"createdAt": "asc"}, {"id": "asc"}],
        )
        aliases = self._alias_repo.get_aliases(workspace_id)
        return [_brand_from_model(row, aliases=aliases) for row in rows]

    async def upsert_primary(
        self,
        workspace_id: str,
        *,
        name: str,
        domain: str,
        aliases: list[str] | None = None,
    ) -> BrandRecord:
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
            stored_aliases = self._alias_repo.set_aliases(workspace_id, aliases or [])
            return _brand_from_model(created, aliases=stored_aliases)

        updated = await self.prisma.aivisbrand.update(
            where={"id": existing.id},
            data=payload,
        )
        stored_aliases = self._alias_repo.set_aliases(workspace_id, aliases or [])
        return _brand_from_model(updated, aliases=stored_aliases)


def _brand_from_model(row: Any, *, aliases: list[str] | None = None) -> BrandRecord:
    return BrandRecord(
        id=str(row.id),
        workspace_id=str(row.workspaceId),
        name=str(row.name),
        domain=str(row.domain),
        aliases=list(aliases or []),
    )
