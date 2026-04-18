from __future__ import annotations

from datetime import datetime
from typing import Any
from typing import cast

from ai_visibility.storage.types import WorkspaceRecord

Prisma = Any
ScanSchedule = str
DEFAULT_SCAN_SCHEDULE: ScanSchedule = "daily"
VALID_SCAN_SCHEDULES: set[str] = {"daily", "weekly", "off"}


class WorkspaceRepository:
    def __init__(self, prisma: Prisma) -> None:
        self.prisma = prisma

    async def create(self, workspace: WorkspaceRecord) -> WorkspaceRecord:
        await self._ensure_schedule_table()
        schedule = _normalize_scan_schedule(workspace.get("scan_schedule"))
        payload: WorkspaceRecord = {
            "id": workspace["id"],
            "slug": workspace["slug"],
            "brand_name": workspace["brand_name"],
            "city": workspace.get("city", ""),
            "region": workspace.get("region", ""),
            "country": workspace.get("country", ""),
            "created_at": workspace["created_at"],
        }

        created = await self.prisma.aivisworkspace.create(
            data={
                "id": payload["id"],
                "slug": payload["slug"],
                "brandName": payload["brand_name"],
                "city": payload["city"],
                "region": payload["region"],
                "country": payload["country"],
                "createdAt": _parse_datetime(payload["created_at"]),
            }
        )
        await self.set_scan_schedule(payload["id"], schedule)

        return _workspace_from_model(created, schedule)

    async def get_by_slug(self, slug: str) -> WorkspaceRecord | None:
        await self._ensure_schedule_table()
        row = await self.prisma.aivisworkspace.find_unique(where={"slug": slug})
        schedule = await self.get_scan_schedule(str(row.id)) if row else DEFAULT_SCAN_SCHEDULE

        return _workspace_from_model(row, schedule) if row else None

    async def list_all(self) -> list[WorkspaceRecord]:
        await self._ensure_schedule_table()
        rows = await self.prisma.aivisworkspace.find_many(
            order=[{"createdAt": "asc"}, {"id": "asc"}],
        )
        schedule_map = await self._get_schedule_map()

        return [_workspace_from_model(row, schedule_map.get(str(row.id), DEFAULT_SCAN_SCHEDULE)) for row in rows]

    async def get_scan_schedule(self, workspace_id: str) -> ScanSchedule:
        await self._ensure_schedule_table()
        rows = await self.prisma.query_raw(
            'SELECT "scan_schedule" FROM "ai_vis_workspace_schedules" WHERE "workspace_id" = $1 LIMIT 1',
            workspace_id,
        )
        if isinstance(rows, list) and rows and isinstance(rows[0], dict):
            return _normalize_scan_schedule(rows[0].get("scan_schedule"))
        return DEFAULT_SCAN_SCHEDULE

    async def set_scan_schedule(self, workspace_id: str, schedule: ScanSchedule) -> None:
        await self._ensure_schedule_table()
        normalized = _normalize_scan_schedule(schedule)
        _ = await self.prisma.execute_raw(
            'INSERT INTO "ai_vis_workspace_schedules" ("workspace_id", "scan_schedule") VALUES ($1, $2) '
            'ON CONFLICT ("workspace_id") DO UPDATE SET "scan_schedule" = EXCLUDED."scan_schedule", "updated_at" = NOW()',
            workspace_id,
            normalized,
        )

    async def _get_schedule_map(self) -> dict[str, ScanSchedule]:
        rows = await self.prisma.query_raw(
            'SELECT "workspace_id", "scan_schedule" FROM "ai_vis_workspace_schedules"',
        )
        schedule_map: dict[str, ScanSchedule] = {}
        if not isinstance(rows, list):
            return schedule_map
        for row in rows:
            if not isinstance(row, dict):
                continue
            workspace_id = str(row.get("workspace_id") or "")
            if not workspace_id:
                continue
            schedule_map[workspace_id] = _normalize_scan_schedule(row.get("scan_schedule"))
        return schedule_map

    async def _ensure_schedule_table(self) -> None:
        _ = await self.prisma.execute_raw(
            'CREATE TABLE IF NOT EXISTS "ai_vis_workspace_schedules" ('
            '"workspace_id" TEXT PRIMARY KEY REFERENCES "ai_vis_workspaces"("id") ON DELETE CASCADE, '
            "\"scan_schedule\" TEXT NOT NULL CHECK (\"scan_schedule\" IN ('daily', 'weekly', 'off')), "
            '"updated_at" TIMESTAMP NOT NULL DEFAULT NOW())'
        )
        _ = await self.prisma.execute_raw(
            'CREATE INDEX IF NOT EXISTS "idx_ai_vis_workspace_schedules_schedule" '
            'ON "ai_vis_workspace_schedules" ("scan_schedule")'
        )


def _workspace_from_model(row: Any, scan_schedule: ScanSchedule = DEFAULT_SCAN_SCHEDULE) -> WorkspaceRecord:
    payload = {
        "id": str(row.id),
        "slug": str(row.slug),
        "brand_name": str(row.brandName),
        "city": str(row.city),
        "region": str(row.region),
        "country": str(row.country),
        "created_at": _to_iso(row.createdAt),
        "scan_schedule": scan_schedule,
    }
    return cast(WorkspaceRecord, cast(object, payload))


def _parse_datetime(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def _to_iso(value: datetime) -> str:
    return value.isoformat()


def _normalize_scan_schedule(value: object) -> ScanSchedule:
    if isinstance(value, str) and value in VALID_SCAN_SCHEDULES:
        return value  # type: ignore[return-value]
    return DEFAULT_SCAN_SCHEDULE
