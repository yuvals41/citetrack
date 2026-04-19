# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false

from __future__ import annotations

from typing import cast

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from loguru import logger

from ai_visibility.api.auth import CurrentUserId
from ai_visibility.models.brand_detail import BrandDetail, BrandUpsertInput
from ai_visibility.storage.prisma_connection import get_prisma
from ai_visibility.storage.repositories.brand_repo import BrandRepository
from ai_visibility.storage.repositories.user_repo import UserRepository
from ai_visibility.storage.repositories.workspace_repo import WorkspaceRepository

router = APIRouter(tags=["brands"])


def _degraded(message: str) -> dict[str, object]:
    return cast(
        dict[str, object],
        BrandDetail(
            id="",
            workspace_id="",
            name="",
            domain="",
            aliases=[],
            degraded={"reason": "database_unavailable", "message": message},
        ).model_dump(mode="json"),
    )


def _require_ownership(user_id: str, slug: str) -> None:
    repo = UserRepository()
    if not repo.user_owns_workspace(user_id, slug):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your workspace")


@router.get("/workspaces/{workspace_slug}/brand", response_model=BrandDetail)
async def get_brand(workspace_slug: str, user_id: CurrentUserId) -> BrandDetail | JSONResponse:
    _require_ownership(user_id, workspace_slug)
    try:
        prisma = cast(object, await get_prisma())
        workspace = await WorkspaceRepository(prisma).get_by_slug(workspace_slug)
        if workspace is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

        brand = await BrandRepository(prisma).get_primary_for_workspace(workspace["id"])
        if brand is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
        return brand
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("brands.get.db_error slug={}", workspace_slug)
        return JSONResponse(status_code=status.HTTP_200_OK, content=_degraded(str(exc)))


@router.put("/workspaces/{workspace_slug}/brand", response_model=BrandDetail)
async def upsert_brand(
    workspace_slug: str,
    payload: BrandUpsertInput,
    user_id: CurrentUserId,
) -> BrandDetail:
    _require_ownership(user_id, workspace_slug)
    prisma = cast(object, await get_prisma())
    workspace = await WorkspaceRepository(prisma).get_by_slug(workspace_slug)
    if workspace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

    logger.info("brands.upsert slug={} alias_count={}", workspace_slug, len(payload.aliases))
    return await BrandRepository(prisma).upsert_primary(
        workspace["id"],
        name=payload.name,
        domain=payload.domain,
        aliases=payload.aliases,
    )
