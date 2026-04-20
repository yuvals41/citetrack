from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Annotated, cast
from typing import TypedDict
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from loguru import logger

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
    base_slug = _slugify(payload.brand.name)
    logger.info(
        "onboarding.start brand={!r} slug={} competitors={} engines={}",
        payload.brand.name,
        base_slug,
        len(payload.competitors),
        [e.value for e in payload.engines],
    )

    if user_repo.user_owns_workspace(user_id, base_slug):
        logger.info("onboarding.idempotent slug={} — already owned by user", base_slug)
        return OnboardingCompleteResponse(workspace_slug=base_slug)

    try:
        prisma = cast(object, await get_prisma())
        workspace_repo = WorkspaceRepository(prisma)
        workspace_slug = await _resolve_available_slug(
            base_slug=base_slug,
            user_id=user_id,
            user_repo=user_repo,
            workspace_repo=workspace_repo,
        )
        if workspace_slug != base_slug:
            logger.info(
                "onboarding.slug_disambiguated base={} resolved={}",
                base_slug,
                workspace_slug,
            )
        if user_repo.user_owns_workspace(user_id, workspace_slug):
            return OnboardingCompleteResponse(workspace_slug=workspace_slug)

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
        logger.info(
            "onboarding.complete workspace_id={} slug={}",
            created["id"],
            workspace_slug,
        )
        return OnboardingCompleteResponse(workspace_slug=workspace_slug)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("onboarding.db_error slug={}", workspace_slug)
        return JSONResponse(content=_degraded_response(_database_degraded_state(exc)))


def _slugify(value: str) -> str:
    lowered = value.strip().lower()
    replaced = re.sub(r"\s+", "-", lowered)
    cleaned = re.sub(r"[^a-z0-9-]", "", replaced)
    collapsed = re.sub(r"-+", "-", cleaned).strip("-")
    return collapsed or "workspace"


MAX_SLUG_ATTEMPTS = 100


async def _resolve_available_slug(
    *,
    base_slug: str,
    user_id: str,
    user_repo: UserRepository,
    workspace_repo: WorkspaceRepository,
) -> str:
    for attempt in range(MAX_SLUG_ATTEMPTS):
        candidate = base_slug if attempt == 0 else f"{base_slug}-{attempt + 1}"
        existing = await workspace_repo.get_by_slug(candidate)
        if existing is None:
            return candidate
        if user_repo.get_workspace_owner(candidate) == user_id:
            return candidate
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=f"Could not find an available slug for '{base_slug}' after {MAX_SLUG_ATTEMPTS} attempts",
    )


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
