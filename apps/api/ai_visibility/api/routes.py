from typing import TypeAlias

from fastapi import FastAPI

from ai_visibility.degraded import DegradedReason, DegradedState, is_degraded
from ai_visibility.metrics.snapshot import SnapshotRepository
from ai_visibility.pixel.router import router as pixel_router
from ai_visibility.prompts import DEFAULT_PROMPTS, PromptLibrary
from ai_visibility.storage.prisma_connection import get_prisma
from ai_visibility.storage.repositories.run_repo import RunRepository
from ai_visibility.storage.repositories.workspace_repo import WorkspaceRepository

ApiPayload: TypeAlias = dict[str, object]


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


async def list_workspaces() -> ApiPayload:
    return await _workspaces_payload()


async def latest_run(workspace: str = "default") -> ApiPayload:
    return await _latest_run_payload(workspace)


async def list_runs(workspace: str = "default") -> ApiPayload:
    return await _runs_payload(workspace)


async def list_prompts() -> ApiPayload:
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


async def snapshot_overview(workspace: str = "default") -> ApiPayload:
    return await _snapshot_overview_payload(workspace)


async def snapshot_trend(workspace: str = "default") -> ApiPayload:
    return await _snapshot_trend_payload(workspace)


async def snapshot_findings(workspace: str = "default") -> ApiPayload:
    return await _snapshot_findings_payload(workspace)


async def snapshot_actions(workspace: str = "default") -> ApiPayload:
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
    app = FastAPI(title="AI Visibility API", version="1.0.0")

    app.add_api_route("/api/v1/health", endpoint=health, methods=["GET"])
    app.add_api_route("/api/v1/workspaces", endpoint=list_workspaces, methods=["GET"])
    app.add_api_route("/api/v1/runs/latest", endpoint=latest_run, methods=["GET"])
    app.add_api_route("/api/v1/runs", endpoint=list_runs, methods=["GET"])
    app.add_api_route("/api/v1/prompts", endpoint=list_prompts, methods=["GET"])
    app.add_api_route("/api/v1/snapshot/overview", endpoint=snapshot_overview, methods=["GET"])
    app.add_api_route("/api/v1/snapshot/trend", endpoint=snapshot_trend, methods=["GET"])
    app.add_api_route("/api/v1/snapshot/findings", endpoint=snapshot_findings, methods=["GET"])
    app.add_api_route("/api/v1/snapshot/actions", endpoint=snapshot_actions, methods=["GET"])
    app.include_router(pixel_router)

    return app


app = create_app()
