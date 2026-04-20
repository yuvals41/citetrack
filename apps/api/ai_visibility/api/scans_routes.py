from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from pydantic import BaseModel

from ai_visibility.api.auth import get_current_user_id
from ai_visibility.runs.orchestrator import RunOrchestrator
from ai_visibility.storage.repositories.user_repo import UserRepository

router = APIRouter(tags=["scans"])
CurrentUserId = Annotated[str, Depends(get_current_user_id)]

_ALLOWED_PROVIDERS: frozenset[str] = frozenset({"anthropic", "openai"})
_DEFAULT_PROVIDER = "anthropic"


class RunScanResponse(BaseModel):
    run_id: str | None
    status: str
    results_count: int
    provider: str
    failed_providers: list[str] = []
    error_message: str | None = None


@router.post(
    "/workspaces/{slug}/scan",
    response_model=RunScanResponse,
    status_code=status.HTTP_200_OK,
)
async def run_workspace_scan(
    slug: str,
    user_id: CurrentUserId,
    provider: Annotated[str, Query(description="LLM provider to scan with")] = _DEFAULT_PROVIDER,
) -> RunScanResponse:
    if provider not in _ALLOWED_PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provider must be one of {sorted(_ALLOWED_PROVIDERS)}",
        )

    user_repo = UserRepository()
    if not user_repo.user_owns_workspace(user_id, slug):
        logger.warning("scan.forbidden user={} slug={}", user_id, slug)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Workspace not accessible",
        )

    logger.info("scan.start user={} slug={} provider={}", user_id, slug, provider)
    orchestrator = RunOrchestrator(workspace_slug=slug, provider=provider)
    result = await orchestrator.scan()
    logger.info(
        "scan.done user={} slug={} provider={} status={} results={} failed={}",
        user_id,
        slug,
        provider,
        result.status,
        result.results_count,
        result.failed_providers,
    )

    return RunScanResponse(
        run_id=result.run_id,
        status=result.status,
        results_count=result.results_count,
        provider=provider,
        failed_providers=list(result.failed_providers or []),
        error_message=result.error_message,
    )
