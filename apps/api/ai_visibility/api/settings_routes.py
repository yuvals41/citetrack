# pyright: reportMissingImports=false

from __future__ import annotations

from datetime import datetime
from typing import cast

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from loguru import logger

from ai_visibility.api.auth import CurrentUserId
from ai_visibility.models.settings import (
    ScanSchedule,
    WorkspaceSettings,
    WorkspaceSettingsUpdate,
)
from ai_visibility.storage.prisma_connection import get_prisma
from ai_visibility.storage.repositories.user_repo import UserRepository
from ai_visibility.storage.repositories.workspace_repo import WorkspaceRepository

router = APIRouter(tags=["settings"])


def _coerce_created_at(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value.strip():
        normalized = value.strip().replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            return None
    return None


def _degraded(reason: str, message: str) -> dict[str, object]:
    return {
        "workspace_slug": "",
        "name": "",
        "scan_schedule": ScanSchedule.DAILY.value,
        "created_at": None,
        "degraded": {"reason": reason, "message": message},
    }


def _require_ownership(user_id: str, slug: str) -> None:
    repo = UserRepository()
    if not repo.user_owns_workspace(user_id, slug):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your workspace")


@router.get("/workspaces/{workspace_slug}/settings")
async def get_settings(workspace_slug: str, user_id: CurrentUserId) -> JSONResponse:
    _require_ownership(user_id, workspace_slug)
    try:
        prisma = cast(object, await get_prisma())
        repo = WorkspaceRepository(prisma)
        workspace = await repo.get_by_slug(workspace_slug)
        if workspace is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
        schedule = await repo.get_scan_schedule(workspace["id"])
        response = WorkspaceSettings(
            workspace_slug=workspace["slug"],
            name=workspace["brand_name"],
            scan_schedule=ScanSchedule(schedule),
            created_at=_coerce_created_at(workspace.get("created_at")),
        )
        return JSONResponse(content=response.model_dump(mode="json"))
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("settings.get.db_error slug={}", workspace_slug)
        return JSONResponse(content=_degraded("database_unavailable", str(exc)))


@router.put("/workspaces/{workspace_slug}/settings", response_model=WorkspaceSettings)
async def update_settings(
    workspace_slug: str,
    payload: WorkspaceSettingsUpdate,
    user_id: CurrentUserId,
) -> WorkspaceSettings:
    _require_ownership(user_id, workspace_slug)
    logger.info(
        "settings.update slug={} name_changed={} schedule_changed={}",
        workspace_slug,
        payload.name is not None,
        payload.scan_schedule is not None,
    )
    prisma = cast(object, await get_prisma())
    repo = WorkspaceRepository(prisma)
    updated = await repo.update_by_slug(
        workspace_slug,
        brand_name=payload.name,
        scan_schedule=payload.scan_schedule.value if payload.scan_schedule else None,
    )
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    schedule = await repo.get_scan_schedule(updated["id"])
    return WorkspaceSettings(
        workspace_slug=updated["slug"],
        name=updated["brand_name"],
        scan_schedule=ScanSchedule(schedule),
        created_at=_coerce_created_at(updated.get("created_at")),
    )
