from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Annotated, cast
from typing import TypedDict
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from ai_visibility.api.auth import get_current_user_id
from ai_visibility.degraded import DegradedReason, DegradedState, is_degraded
from ai_visibility.models.onboarding import OnboardingCompleteResponse, OnboardingPayload
from ai_visibility.storage.prisma_connection import get_prisma
from ai_visibility.storage.repositories.user_repo import UserRepository
from ai_visibility.storage.repositories.workspace_repo import WorkspaceRepository
from ai_visibility.storage.types import WorkspaceRecord

router = APIRouter(tags=["onboarding"])
CurrentUserId = Annotated[str, Depends(get_current_user_id)]


class WorkspaceOnboardingMetadata(TypedDict):
    brand: dict[str, str]
    competitors: list[dict[str, str]]
    engines: list[str]


_workspace_metadata: dict[str, WorkspaceOnboardingMetadata] = {}


@router.post("/onboarding/complete", response_model=OnboardingCompleteResponse)
async def complete_onboarding(
    payload: OnboardingPayload,
    user_id: CurrentUserId,
) -> OnboardingCompleteResponse | JSONResponse:
    user_repo = UserRepository()
    workspace_slug = _slugify(payload.brand.name)
    if user_repo.user_owns_workspace(user_id, workspace_slug):
        return OnboardingCompleteResponse(workspace_slug=workspace_slug)

    try:
        prisma = cast(object, await get_prisma())
        workspace_repo = WorkspaceRepository(prisma)
        existing = await workspace_repo.get_by_slug(workspace_slug)
        if existing is not None:
            owner = user_repo.get_workspace_owner(workspace_slug)
            if owner == user_id:
                return OnboardingCompleteResponse(workspace_slug=workspace_slug)
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Workspace slug already exists")

        now = datetime.now(timezone.utc)
        workspace_record: WorkspaceRecord = {
            "id": str(uuid4()),
            "slug": workspace_slug,
            "brand_name": payload.brand.name,
            "city": "",
            "region": "",
            "country": "",
            "created_at": now.isoformat(),
        }
        created = await workspace_repo.create(workspace_record)
        user_repo.add_workspace_to_user(user_id, workspace_slug)
        _workspace_metadata[created["id"]] = {
            "brand": payload.brand.model_dump(),
            "competitors": [competitor.model_dump() for competitor in payload.competitors],
            "engines": [engine.value for engine in payload.engines],
        }
        return OnboardingCompleteResponse(workspace_slug=workspace_slug)
    except HTTPException:
        raise
    except Exception as exc:
        return JSONResponse(content=_degraded_response(_database_degraded_state(exc)))


def _slugify(value: str) -> str:
    lowered = value.strip().lower()
    replaced = re.sub(r"\s+", "-", lowered)
    cleaned = re.sub(r"[^a-z0-9-]", "", replaced)
    collapsed = re.sub(r"-+", "-", cleaned).strip("-")
    return collapsed or "workspace"


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
