from __future__ import annotations

# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnusedCallResult=false

import re
from datetime import datetime, timezone
from typing import Annotated, cast
from typing import TypedDict
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from loguru import logger

from ai_visibility.api.auth import get_current_user_id
from ai_visibility.contracts.scan_contracts import LifecycleStatus
from ai_visibility.degraded import DegradedReason, DegradedState, is_degraded
from ai_visibility.models.onboarding import OnboardingCompleteResponse, OnboardingPayload
from ai_visibility.runs.execution_core import resolve_provider_key
from ai_visibility.runs.orchestrator import RunOrchestrator
from ai_visibility.runs.scan_strategy import ScanMode, get_strategy_for_mode
from ai_visibility.storage.prisma_connection import get_prisma
from ai_visibility.storage.repositories.brand_repo import BrandRepository
from ai_visibility.storage.repositories.competitor_repo import CompetitorRepository
from ai_visibility.storage.repositories.run_repo import RunRepository
from ai_visibility.storage.repositories.user_repo import UserRepository
from ai_visibility.storage.repositories.workspace_repo import WorkspaceRepository
from ai_visibility.storage.types import WorkspaceRecord

router = APIRouter(tags=["onboarding"])
CurrentUserId = Annotated[str, Depends(get_current_user_id)]

_FIRST_SCAN_PROVIDER = "anthropic"
_FAILED_FIRST_SCAN_ERROR_MAX_LEN = 500


class WorkspaceOnboardingMetadata(TypedDict):
    brand: dict[str, str]
    competitors: list[dict[str, str]]
    engines: list[str]


_workspace_metadata: dict[str, WorkspaceOnboardingMetadata] = {}


async def _fire_first_scan(workspace_slug: str, provider: str) -> None:
    # RunOrchestrator.scan() already persists failed rows for pipeline-level failures.
    # This recovery path is for exceptions raised before that persistence happens
    # (for example workspace lookup / setup failures) so onboarding doesn't leave a
    # workspace stuck in an indistinguishable "no runs" state.
    try:
        orchestrator = RunOrchestrator(workspace_slug=workspace_slug, provider=provider)
        result = await orchestrator.scan()
        logger.info(
            "onboarding.first_scan.done slug={} provider={} status={} results={}",
            workspace_slug,
            provider,
            result.status,
            result.results_count,
        )
    except Exception as exc:
        logger.exception(
            "onboarding.first_scan.failed slug={} provider={} error_class={} error_message={}",
            workspace_slug,
            provider,
            type(exc).__name__,
            str(exc),
        )
        await _persist_failed_first_scan(workspace_slug, provider, error_message=str(exc))


async def _persist_failed_first_scan(workspace_slug: str, provider: str, error_message: str) -> None:
    try:
        prisma = cast(object, await get_prisma())
        workspace_repo = WorkspaceRepository(prisma)
        workspace = await workspace_repo.get_by_slug(workspace_slug)
        if workspace is None:
            logger.warning(
                "onboarding.first_scan.failure_not_persisted slug={} provider={} reason=workspace_not_found",
                workspace_slug,
                provider,
            )
            return

        now = datetime.now(timezone.utc).isoformat()
        model_name = _first_scan_model_name(provider)
        truncated_error = error_message[:_FAILED_FIRST_SCAN_ERROR_MAX_LEN]
        _ = await RunRepository(prisma).create(
            {
                "id": str(uuid4()),
                "workspace_id": workspace["id"],
                "provider": provider,
                "model": model_name,
                "prompt_version": "1.0.0",
                "parser_version": "parser_v1",
                "status": LifecycleStatus.FAILED.value,
                "created_at": now,
                "raw_response": None,
                "error": truncated_error,
            }
        )
        logger.info(
            "onboarding.first_scan.failure_persisted slug={} provider={} status={} model={}",
            workspace_slug,
            provider,
            LifecycleStatus.FAILED.value,
            model_name,
        )
    except Exception as persistence_exc:
        logger.exception(
            "onboarding.first_scan.failure_persist_failed slug={} provider={} error_class={} error_message={}",
            workspace_slug,
            provider,
            type(persistence_exc).__name__,
            str(persistence_exc),
        )


def _first_scan_model_name(provider: str) -> str:
    provider_key = resolve_provider_key(provider)
    provider_config = get_strategy_for_mode(ScanMode.SCHEDULED).providers.get(provider_key)
    if provider_config is None:
        return provider
    return provider_config.model_name


@router.post("/onboarding/complete", response_model=OnboardingCompleteResponse)
async def complete_onboarding(
    payload: OnboardingPayload,
    user_id: CurrentUserId,
    background_tasks: BackgroundTasks,
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
    workspace_slug = base_slug

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

        _ = await BrandRepository(prisma).upsert_primary(
            created["id"],
            name=payload.brand.name,
            domain=payload.brand.domain,
            aliases=[],
        )

        competitor_repo = CompetitorRepository(prisma)
        for competitor in payload.competitors:
            try:
                _ = await competitor_repo.create(
                    created["id"],
                    competitor.name,
                    competitor.domain,
                )
            except Exception:
                logger.exception(
                    "onboarding.competitor_create_failed slug={} name={}",
                    workspace_slug,
                    competitor.name,
                )

        _workspace_metadata[created["id"]] = {
            "brand": payload.brand.model_dump(),
            "competitors": [competitor.model_dump() for competitor in payload.competitors],
            "engines": [engine.value for engine in payload.engines],
        }
        logger.info(
            "onboarding.complete workspace_id={} slug={} competitors={}",
            created["id"],
            workspace_slug,
            len(payload.competitors),
        )
        background_tasks.add_task(_fire_first_scan, workspace_slug, _FIRST_SCAN_PROVIDER)
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
