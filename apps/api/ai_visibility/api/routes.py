# pyright: reportAny=false, reportUnknownMemberType=false, reportCallInDefaultInitializer=false, reportAttributeAccessIssue=false

import os
from typing import Annotated, TypeAlias

from fastapi import Depends, FastAPI

from ai_visibility.api.auth import get_current_user_id
from ai_visibility.api.competitors_routes import router as competitors_router
from ai_visibility.api.mentions_routes import router as mentions_router
from ai_visibility.api.onboarding_routes import router as onboarding_router
from ai_visibility.api.research_routes import router as research_router
from ai_visibility.api.settings_routes import router as settings_router
from ai_visibility.api.user_routes import router as user_router
from ai_visibility.degraded import DegradedReason, DegradedState, is_degraded
from ai_visibility.metrics.snapshot import SnapshotRepository
from ai_visibility.pixel.router import router as pixel_router
from ai_visibility.prompts import DEFAULT_PROMPTS, PromptLibrary
from ai_visibility.storage.prisma_connection import get_prisma
from ai_visibility.storage.repositories.run_repo import RunRepository
from ai_visibility.storage.repositories.workspace_repo import WorkspaceRepository

ApiPayload: TypeAlias = dict[str, object]
CurrentUserId = Annotated[str, Depends(get_current_user_id)]


async def _health_payload() -> ApiPayload:
    try:
        prisma = await get_prisma()
        await prisma.aivisworkspace.count()
    except Exception as exc:
        return _degraded_response(
            DegradedState(
                reason=DegradedReason.PROVIDER_FAILURE,
                message=f"Database unavailable: {exc}",
                recoverable=True,
                context={"dependency": "postgres"},
            )
        )

    return {"status": "ok", "version": "1.0.0"}


async def _workspaces_payload() -> ApiPayload:
    try:
        prisma = await get_prisma()
        repo = WorkspaceRepository(prisma)
        workspaces = await repo.list_all()
        return {"items": workspaces}
    except Exception as exc:
        return _degraded_response(
            DegradedState(
                reason=DegradedReason.PROVIDER_FAILURE,
                message=f"Database unavailable: {exc}",
                recoverable=True,
                context={"dependency": "postgres"},
            )
        )


async def _latest_run_payload(workspace: str = "default") -> ApiPayload:
    try:
        prisma = await get_prisma()
        ws_repo = WorkspaceRepository(prisma)
        ws = await ws_repo.get_by_slug(workspace)
        if ws is None:
            return {"workspace": workspace, "run": None}

        run = await RunRepository(prisma).get_latest_by_workspace(ws["id"])
        return {"workspace": workspace, "run": run}
    except Exception as exc:
        return _degraded_response(
            DegradedState(
                reason=DegradedReason.PROVIDER_FAILURE,
                message=f"Database unavailable: {exc}",
                recoverable=True,
                context={"dependency": "postgres"},
            )
        )


async def _runs_payload(workspace: str = "default") -> ApiPayload:
    try:
        prisma = await get_prisma()
        ws_repo = WorkspaceRepository(prisma)
        ws = await ws_repo.get_by_slug(workspace)
        if ws is None:
            return {"workspace": workspace, "items": []}

        runs = await RunRepository(prisma).list_by_workspace(ws["id"])
        return {"workspace": workspace, "items": runs}
    except Exception as exc:
        return _degraded_response(
            DegradedState(
                reason=DegradedReason.PROVIDER_FAILURE,
                message=f"Database unavailable: {exc}",
                recoverable=True,
                context={"dependency": "postgres"},
            )
        )


def _prompts_payload() -> ApiPayload:
    prompt_library = PromptLibrary(prompts=DEFAULT_PROMPTS)
    return {"items": prompt_library.list_prompts()}


async def _snapshot_repository() -> SnapshotRepository:
    prisma = await get_prisma()
    return SnapshotRepository(prisma=prisma)


async def _snapshot_overview_payload(workspace: str = "default") -> ApiPayload:
    try:
        repo = await _snapshot_repository()
        snapshot = await repo.get_overview_snapshot(workspace)
        return snapshot.model_dump()
    except Exception as exc:
        return _degraded_response(
            DegradedState(
                reason=DegradedReason.PROVIDER_FAILURE,
                message=f"Database unavailable: {exc}",
                recoverable=True,
                context={"dependency": "postgres"},
            )
        )


async def _snapshot_trend_payload(workspace: str = "default") -> ApiPayload:
    try:
        repo = await _snapshot_repository()
        series = await repo.get_trend_series(workspace)
        return {"workspace": workspace, "items": [item.model_dump() for item in series]}
    except Exception as exc:
        return _degraded_response(
            DegradedState(
                reason=DegradedReason.PROVIDER_FAILURE,
                message=f"Database unavailable: {exc}",
                recoverable=True,
                context={"dependency": "postgres"},
            )
        )


async def _snapshot_findings_payload(workspace: str = "default") -> ApiPayload:
    try:
        repo = await _snapshot_repository()
        findings = repo.get_findings_summary(workspace)
        return findings.model_dump()
    except Exception as exc:
        return _degraded_response(
            DegradedState(
                reason=DegradedReason.PROVIDER_FAILURE,
                message=f"Database unavailable: {exc}",
                recoverable=True,
                context={"dependency": "postgres"},
            )
        )


async def _snapshot_actions_payload(workspace: str = "default") -> ApiPayload:
    try:
        repo = await _snapshot_repository()
        actions = await repo.get_action_queue(workspace)
        return actions.model_dump()
    except Exception as exc:
        return _degraded_response(
            DegradedState(
                reason=DegradedReason.PROVIDER_FAILURE,
                message=f"Database unavailable: {exc}",
                recoverable=True,
                context={"dependency": "postgres"},
            )
        )


async def health() -> ApiPayload:
    return await _health_payload()


async def list_workspaces(user_id: CurrentUserId) -> ApiPayload:
    # TODO Phase 3d: scope query by user_id via workspace ownership.
    _ = user_id
    return await _workspaces_payload()


async def latest_run(workspace: str = "default", *, user_id: CurrentUserId) -> ApiPayload:
    # TODO Phase 3d: scope query by user_id via workspace ownership.
    _ = user_id
    return await _latest_run_payload(workspace)


async def list_runs(workspace: str = "default", *, user_id: CurrentUserId) -> ApiPayload:
    # TODO Phase 3d: scope query by user_id via workspace ownership.
    _ = user_id
    return await _runs_payload(workspace)


async def list_prompts(user_id: CurrentUserId) -> ApiPayload:
    # TODO Phase 3d: scope query by user_id via workspace ownership.
    _ = user_id
    try:
        return _prompts_payload()
    except Exception as exc:
        return _degraded_response(
            DegradedState(
                reason=DegradedReason.PROVIDER_FAILURE,
                message=f"Prompt library unavailable: {exc}",
                recoverable=True,
            )
        )


async def snapshot_overview(workspace: str = "default", *, user_id: CurrentUserId) -> ApiPayload:
    # TODO Phase 3d: scope query by user_id via workspace ownership.
    _ = user_id
    return await _snapshot_overview_payload(workspace)


async def snapshot_trend(workspace: str = "default", *, user_id: CurrentUserId) -> ApiPayload:
    # TODO Phase 3d: scope query by user_id via workspace ownership.
    _ = user_id
    return await _snapshot_trend_payload(workspace)


async def snapshot_findings(workspace: str = "default", *, user_id: CurrentUserId) -> ApiPayload:
    # TODO Phase 3d: scope query by user_id via workspace ownership.
    _ = user_id
    return await _snapshot_findings_payload(workspace)


async def snapshot_actions(workspace: str = "default", *, user_id: CurrentUserId) -> ApiPayload:
    # TODO Phase 3d: scope query by user_id via workspace ownership.
    _ = user_id
    return await _snapshot_actions_payload(workspace)


def _degraded_response(state: DegradedState | None) -> ApiPayload:
    if state is None:
        raise ValueError("Degraded state is required")
    if not is_degraded(state):
        raise ValueError("Degraded state is required")

    return {
        "degraded": {
            "reason": state.reason.value,
            "message": state.message,
            "recoverable": state.recoverable,
        }
    }


def create_app() -> FastAPI:
    from fastapi.middleware.cors import CORSMiddleware

    from ai_visibility.observability import configure_logging
    from ai_visibility.observability.middleware import RequestContextMiddleware

    configure_logging()

    app = FastAPI(title="Citetrack AI API", version="1.0.0")
    app.add_middleware(RequestContextMiddleware)

    allowed_origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "")
    default_origins = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "https://citetrack.ai",
        "https://www.citetrack.ai",
        "https://app.citetrack.ai",
    ]
    extra_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=default_origins + extra_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_api_route("/api/v1/health", endpoint=health, methods=["GET"])
    app.add_api_route("/api/v1/workspaces", endpoint=list_workspaces, methods=["GET"])
    app.add_api_route("/api/v1/runs/latest", endpoint=latest_run, methods=["GET"])
    app.add_api_route("/api/v1/runs", endpoint=list_runs, methods=["GET"])
    app.add_api_route("/api/v1/prompts", endpoint=list_prompts, methods=["GET"])
    app.add_api_route("/api/v1/snapshot/overview", endpoint=snapshot_overview, methods=["GET"])
    app.add_api_route("/api/v1/snapshot/trend", endpoint=snapshot_trend, methods=["GET"])
    app.add_api_route("/api/v1/snapshot/findings", endpoint=snapshot_findings, methods=["GET"])
    app.add_api_route("/api/v1/snapshot/actions", endpoint=snapshot_actions, methods=["GET"])
    app.include_router(user_router, prefix="/api/v1")
    app.include_router(onboarding_router, prefix="/api/v1")
    app.include_router(competitors_router, prefix="/api/v1")
    app.include_router(research_router, prefix="/api/v1")
    app.include_router(mentions_router, prefix="/api/v1")
    app.include_router(settings_router, prefix="/api/v1")
    app.include_router(pixel_router)

    return app


app = create_app()
