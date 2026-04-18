from __future__ import annotations

# pyright: reportAny=false, reportExplicitAny=false, reportUnannotatedClassAttribute=false

from datetime import datetime
import sqlite3
from typing import Any

from ai_visibility.storage.types import RunRecord

Prisma = Any


class RunRepository:
    def __init__(self, prisma: Prisma) -> None:
        self.prisma = prisma

    async def create(self, run: RunRecord, *, conn: sqlite3.Connection | None = None) -> bool:
        payload: RunRecord = {
            "id": run["id"],
            "workspace_id": run["workspace_id"],
            "provider": run["provider"],
            "model": run["model"],
            "prompt_version": run["prompt_version"],
            "parser_version": run["parser_version"],
            "status": run["status"],
            "created_at": run["created_at"],
            "raw_response": run["raw_response"],
            "error": run["error"],
        }

        _ = conn
        workspace = await self.prisma.aivisworkspace.find_unique(where={"id": payload["workspace_id"]})
        if workspace is None:
            raise ValueError(f"Workspace not found: {payload['workspace_id']}. Cannot create run.")

        await self.prisma.aivisrun.create(
            data={
                "id": payload["id"],
                "workspaceId": payload["workspace_id"],
                "provider": payload["provider"],
                "model": payload["model"],
                "promptVersion": payload["prompt_version"],
                "parserVersion": payload["parser_version"],
                "status": _to_prisma_enum(payload["status"]),
                "createdAt": _parse_datetime(payload["created_at"]),
                "rawResponse": payload["raw_response"],
                "error": payload["error"],
            }
        )

        return True

    async def list_by_workspace(self, workspace_id: str) -> list[RunRecord]:
        rows = await self.prisma.aivisrun.find_many(
            where={"workspaceId": workspace_id},
            order=[{"createdAt": "desc"}, {"id": "desc"}],
        )

        return [_run_from_model(row) for row in rows]

    async def get_latest_by_workspace(self, workspace_id: str) -> RunRecord | None:
        row = await self.prisma.aivisrun.find_first(
            where={"workspaceId": workspace_id},
            order=[{"createdAt": "desc"}, {"id": "desc"}],
        )

        return _run_from_model(row) if row else None


def _run_from_model(row: Any) -> RunRecord:
    raw_response = row.rawResponse
    error = row.error

    return {
        "id": str(row.id),
        "workspace_id": str(row.workspaceId),
        "provider": str(row.provider),
        "model": str(row.model),
        "prompt_version": str(row.promptVersion),
        "parser_version": str(row.parserVersion),
        "status": _from_prisma_enum(row.status),
        "created_at": _to_iso(row.createdAt),
        "raw_response": None if raw_response is None else str(raw_response),
        "error": None if error is None else str(error),
    }


def _parse_datetime(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def _to_iso(value: datetime) -> str:
    return value.isoformat()


def _to_prisma_enum(value: str) -> str:
    return value.upper()


def _from_prisma_enum(value: Any) -> str:
    raw = str(value)
    if "." in raw:
        raw = raw.rsplit(".", 1)[-1]
    return raw.lower()
