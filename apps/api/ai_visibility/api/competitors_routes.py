from __future__ import annotations

from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse, Response

from ai_visibility.api.auth import get_current_user_id
from ai_visibility.degraded import DegradedReason, DegradedState, is_degraded
from ai_visibility.models.competitor import CompetitorCreate, CompetitorListResponse, CompetitorRecord
from ai_visibility.storage.prisma_connection import get_prisma
from ai_visibility.storage.repositories.competitor_repo import CompetitorRepository
from ai_visibility.storage.repositories.workspace_repo import WorkspaceRepository

router = APIRouter(tags=["competitors"])
CurrentUserId = Annotated[str, Depends(get_current_user_id)]


@router.get("/workspaces/{workspace_slug}/competitors", response_model=CompetitorListResponse)
async def list_competitors(
    workspace_slug: str,
    user_id: CurrentUserId,
) -> CompetitorListResponse | JSONResponse:
    _ = user_id
    try:
        prisma = cast(object, await get_prisma())
        workspace = await WorkspaceRepository(prisma).get_by_slug(workspace_slug)
        if workspace is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

        items = await CompetitorRepository(prisma).list_by_workspace(workspace["id"])
        return CompetitorListResponse(workspace=workspace_slug, items=items)
    except HTTPException:
        raise
    except Exception as exc:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=CompetitorListResponse(
                workspace=workspace_slug,
                items=[],
                degraded=_degraded_payload(_database_degraded_state(exc)),
            ).model_dump(mode="json"),
        )


@router.post(
    "/workspaces/{workspace_slug}/competitors",
    response_model=CompetitorRecord,
    status_code=status.HTTP_201_CREATED,
)
async def create_competitor(
    workspace_slug: str,
    payload: CompetitorCreate,
    user_id: CurrentUserId,
) -> CompetitorRecord:
    _ = user_id
    try:
        prisma = cast(object, await get_prisma())
        workspace = await WorkspaceRepository(prisma).get_by_slug(workspace_slug)
        if workspace is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

        repo = CompetitorRepository(prisma)
        existing = await repo.get_by_domain(workspace["id"], payload.domain)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Competitor domain already exists")

        return await repo.create(workspace["id"], payload.name, payload.domain)
    except HTTPException:
        raise
    except Exception as exc:
        raise _database_http_exception(exc) from exc


@router.delete("/workspaces/{workspace_slug}/competitors/{competitor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_competitor(
    workspace_slug: str,
    competitor_id: str,
    user_id: CurrentUserId,
) -> Response:
    _ = user_id
    try:
        prisma = cast(object, await get_prisma())
        workspace = await WorkspaceRepository(prisma).get_by_slug(workspace_slug)
        if workspace is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

        repo = CompetitorRepository(prisma)
        workspace_competitors = await repo.list_by_workspace(workspace["id"])
        if not any(item.id == competitor_id for item in workspace_competitors):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competitor not found")

        deleted = await repo.delete(competitor_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competitor not found")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as exc:
        raise _database_http_exception(exc) from exc


def _database_degraded_state(exc: Exception) -> DegradedState:
    return DegradedState(
        reason=DegradedReason.PROVIDER_FAILURE,
        message=f"Database unavailable: {exc}",
        recoverable=True,
        context={"dependency": "postgres"},
    )


def _degraded_payload(state: DegradedState | None) -> dict[str, str]:
    if state is None or not is_degraded(state):
        raise ValueError("Degraded state is required")
    return {
        "reason": state.reason.value,
        "message": state.message,
    }


def _database_http_exception(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"Database unavailable: {exc}",
    )
