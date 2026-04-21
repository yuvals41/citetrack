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

_ALLOWED_PROVIDERS: frozenset[str] = frozenset({"anthropic", "openai", "gemini", "perplexity", "grok"})
_DEFAULT_PROVIDER = "anthropic"


class PerProviderResult(BaseModel):
    provider: str
    run_id: str | None
    status: str
    results_count: int
    error_message: str | None = None


class RunScanResponse(BaseModel):
    providers: list[PerProviderResult]
    total_results: int
    succeeded: int
    failed: int


def _parse_providers(raw: str) -> list[str]:
    return [p.strip() for p in raw.split(",") if p.strip()]


@router.post(
    "/workspaces/{slug}/scan",
    response_model=RunScanResponse,
    status_code=status.HTTP_200_OK,
)
async def run_workspace_scan(
    slug: str,
    user_id: CurrentUserId,
    provider: Annotated[
        str, Query(description="Comma-separated LLM providers (e.g. 'anthropic,openai')")
    ] = _DEFAULT_PROVIDER,
) -> RunScanResponse:
    requested = _parse_providers(provider)
    if not requested:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one provider is required",
        )
    for p in requested:
        if p not in _ALLOWED_PROVIDERS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Provider {p!r} not in {sorted(_ALLOWED_PROVIDERS)}",
            )

    user_repo = UserRepository()
    if not user_repo.user_owns_workspace(user_id, slug):
        logger.warning("scan.forbidden user={} slug={}", user_id, slug)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Workspace not accessible",
        )

    logger.info("scan.start user={} slug={} providers={}", user_id, slug, requested)

    results: list[PerProviderResult] = []
    total_results = 0
    succeeded = 0
    failed = 0
    for p in requested:
        orchestrator = RunOrchestrator(workspace_slug=slug, provider=p)
        outcome = await orchestrator.scan()
        ok = outcome.status == "completed" and not outcome.failed_providers
        if ok:
            succeeded += 1
        else:
            failed += 1
        total_results += outcome.results_count
        results.append(
            PerProviderResult(
                provider=p,
                run_id=outcome.run_id,
                status=outcome.status,
                results_count=outcome.results_count,
                error_message=outcome.error_message,
            )
        )
        logger.info(
            "scan.provider_done user={} slug={} provider={} status={} results={}",
            user_id,
            slug,
            p,
            outcome.status,
            outcome.results_count,
        )

    logger.info(
        "scan.done user={} slug={} providers={} total_results={} succeeded={} failed={}",
        user_id,
        slug,
        requested,
        total_results,
        succeeded,
        failed,
    )
    return RunScanResponse(
        providers=results,
        total_results=total_results,
        succeeded=succeeded,
        failed=failed,
    )
