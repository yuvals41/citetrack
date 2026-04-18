from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, cast
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from ai_visibility.api.auth import ClerkAuthContext, get_auth_context, get_current_user_id
from ai_visibility.degraded import DegradedReason, DegradedState, is_degraded
from ai_visibility.models.user import UserResponse
from ai_visibility.models.workspace import Workspace, WorkspaceCreate
from ai_visibility.storage.prisma_connection import get_prisma
from ai_visibility.storage.repositories.user_repo import UserRepository
from ai_visibility.storage.repositories.workspace_repo import WorkspaceRepository
from ai_visibility.storage.types import WorkspaceRecord

router = APIRouter(tags=["user"])
AuthContextDependency = Annotated[ClerkAuthContext, Depends(get_auth_context)]
CurrentUserId = Annotated[str, Depends(get_current_user_id)]


@router.get("/me", response_model=UserResponse)
async def get_me(auth: AuthContextDependency) -> UserResponse:
    user_repo = UserRepository()
    workspace_count = len(user_repo.list_workspaces_for_user(auth.user_id))
    return UserResponse(
        user_id=auth.user_id,
        email=None,
        first_name=None,
        last_name=None,
        workspace_count=workspace_count,
        has_completed_onboarding=workspace_count > 0,
    )


@router.get("/workspaces/mine", response_model=list[Workspace])
async def list_my_workspaces(user_id: CurrentUserId) -> list[Workspace] | JSONResponse:
    user_repo = UserRepository()
    workspace_slugs = user_repo.list_workspaces_for_user(user_id)
    if not workspace_slugs:
        return []

    try:
        prisma = cast(object, await get_prisma())
        workspace_repo = WorkspaceRepository(prisma)
        workspaces: list[Workspace] = []
        for slug in workspace_slugs:
            record = await workspace_repo.get_by_slug(slug)
            if record is None:
                continue
            workspaces.append(_workspace_from_record(record))
        return workspaces
    except Exception as exc:
        return JSONResponse(content=_degraded_response(_database_degraded_state(exc)))


@router.post("/workspaces", response_model=Workspace, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    payload: WorkspaceCreate,
    user_id: CurrentUserId,
) -> Workspace | JSONResponse:
    try:
        prisma = cast(object, await get_prisma())
        workspace_repo = WorkspaceRepository(prisma)
        existing = await workspace_repo.get_by_slug(payload.slug)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Workspace slug already exists")

        now = datetime.now(timezone.utc)
        workspace_record: WorkspaceRecord = {
            "id": str(uuid4()),
            "slug": payload.slug,
            "brand_name": payload.name,
            "city": "",
            "region": "",
            "country": "",
            "created_at": now.isoformat(),
        }
        created = await workspace_repo.create(workspace_record)
        UserRepository().add_workspace_to_user(user_id, payload.slug)
        return _workspace_from_record(created, description=payload.description)
    except HTTPException:
        raise
    except Exception as exc:
        return JSONResponse(content=_degraded_response(_database_degraded_state(exc)))


def _workspace_from_record(record: WorkspaceRecord, description: str | None = None) -> Workspace:
    created_at = _parse_iso_datetime(record["created_at"])
    return Workspace(
        id=record["id"],
        name=record["brand_name"],
        slug=record["slug"],
        description=description,
        created_at=created_at,
        updated_at=created_at,
    )


def _parse_iso_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _database_degraded_state(exc: Exception) -> DegradedState:
    return DegradedState(
        reason=DegradedReason.PROVIDER_FAILURE,
        message=f"Database unavailable: {exc}",
        recoverable=True,
        context={"dependency": "postgres"},
    )


def _degraded_response(state: DegradedState | None) -> dict[str, dict[str, object]]:
    if state is None or not is_degraded(state):
        raise ValueError("Degraded state is required")

    return {
        "degraded": {
            "reason": state.reason.value,
            "message": state.message,
            "recoverable": state.recoverable,
        }
    }
