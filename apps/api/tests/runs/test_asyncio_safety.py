import asyncio
import uuid
from collections.abc import Callable, Coroutine
from datetime import datetime, timezone
from typing import cast
from unittest.mock import MagicMock

import pytest

from ai_visibility.providers.gateway import ProviderResponse
from ai_visibility.runs.orchestrator import RunOrchestrator, ScanResult
from ai_visibility.storage.repositories import WorkspaceRepository
from ai_visibility.storage.types import WorkspaceRecord


async def _add_async(a: int, b: int) -> int:
    await asyncio.sleep(0)
    return a + b


async def _raise_async() -> None:
    await asyncio.sleep(0)
    raise ValueError("boom")


async def _create_workspace(mock_prisma: MagicMock, slug: str) -> WorkspaceRecord:
    workspace: WorkspaceRecord = {
        "id": str(uuid.uuid4()),
        "slug": slug,
        "brand_name": slug.title(),
        "city": "",
        "region": "",
        "country": "",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    created_at = datetime.fromisoformat(workspace["created_at"].replace("Z", "+00:00"))
    workspace_model = MagicMock(
        id=workspace["id"],
        slug=workspace["slug"],
        brandName=workspace["brand_name"],
        city=workspace["city"],
        region=workspace["region"],
        country=workspace["country"],
        createdAt=created_at,
    )
    mock_prisma.aivisworkspace.create.return_value = workspace_model  # pyright: ignore[reportAny]
    mock_prisma.aivisworkspace.find_unique.return_value = workspace_model  # pyright: ignore[reportAny]

    _ = await WorkspaceRepository(mock_prisma).create(workspace)
    return workspace


def _patch_orchestrator_get_prisma(monkeypatch: pytest.MonkeyPatch, mock_prisma: MagicMock) -> None:
    async def _fake_get_prisma() -> MagicMock:
        return mock_prisma

    monkeypatch.setattr("ai_visibility.runs.orchestrator.get_prisma", _fake_get_prisma)


def _configure_scan_prisma_models(mock_prisma: MagicMock) -> None:
    created_at = datetime.now(timezone.utc)
    metric_row = MagicMock(
        id=str(uuid.uuid4()),
        workspaceId="acme",
        brandId="acme",
        formulaVersion="v1",
        visibilityScore=0.0,
        citationCoverage=0.0,
        competitorWins=0,
        mentionCount=0,
        createdAt=created_at,
    )

    mock_prisma.aivismetricsnapshot.upsert.return_value = metric_row  # pyright: ignore[reportAny]
    mock_prisma.aivismetricsnapshot.find_first.return_value = metric_row  # pyright: ignore[reportAny]


def test_run_async_works_without_event_loop() -> None:
    orchestrator = RunOrchestrator(workspace_slug="acme")
    run_async = cast(Callable[[Coroutine[object, object, int]], int], getattr(orchestrator, "_run_async"))

    result = run_async(_add_async(2, 3))

    assert result == 5


def test_run_async_works_inside_existing_event_loop() -> None:
    orchestrator = RunOrchestrator(workspace_slug="acme")
    run_async = cast(Callable[[Coroutine[object, object, int]], int], getattr(orchestrator, "_run_async"))

    async def run_inside_loop() -> int:
        result = run_async(_add_async(4, 6))
        return int(result)

    assert asyncio.run(run_inside_loop()) == 10


def test_run_async_propagates_exceptions() -> None:
    orchestrator = RunOrchestrator(workspace_slug="acme")
    run_async = cast(Callable[[Coroutine[object, object, None]], None], getattr(orchestrator, "_run_async"))

    with pytest.raises(ValueError, match="boom"):
        _ = run_async(_raise_async())


@pytest.mark.asyncio
async def test_scan_works_from_sync_context(
    monkeypatch: pytest.MonkeyPatch,
    mock_prisma: MagicMock,
    patch_get_prisma: MagicMock,
) -> None:
    _ = patch_get_prisma
    _patch_orchestrator_get_prisma(monkeypatch, mock_prisma)
    _configure_scan_prisma_models(mock_prisma)
    _ = await _create_workspace(mock_prisma, "acme")
    mock_prisma.aivisrun.create.return_value = MagicMock()  # pyright: ignore[reportAny]
    orchestrator = RunOrchestrator(workspace_slug="acme")

    async def fake_execute(
        _prompt_text: str,
        _variables: dict[str, object] | None = None,
        system_message: str | None = None,
        location: object | None = None,
    ) -> ProviderResponse:
        _ = system_message
        _ = location
        return ProviderResponse(
            provider="openai",
            model="gpt-4o-mini",
            content=(
                "Acme is reliable and frequently cited by experts in growth strategy. "
                "See https://example.com/source for details and long-form context."
            ),
            latency_ms=8.0,
        )

    monkeypatch.setattr(orchestrator.gateway, "execute_prompt", fake_execute)
    run_async = cast(
        Callable[[Coroutine[object, object, ScanResult]], ScanResult],
        getattr(orchestrator, "_run_async"),
    )

    result = await asyncio.to_thread(run_async, orchestrator.scan())

    assert result.status in {"completed", "completed_with_partial_failures"}
    assert result.results_count >= 1


@pytest.mark.asyncio
async def test_scan_works_inside_existing_event_loop(
    monkeypatch: pytest.MonkeyPatch,
    mock_prisma: MagicMock,
    patch_get_prisma: MagicMock,
) -> None:
    _ = patch_get_prisma
    _patch_orchestrator_get_prisma(monkeypatch, mock_prisma)
    _configure_scan_prisma_models(mock_prisma)
    _ = await _create_workspace(mock_prisma, "acme")
    mock_prisma.aivisrun.create.return_value = MagicMock()  # pyright: ignore[reportAny]
    orchestrator = RunOrchestrator(workspace_slug="acme")

    async def fake_execute(
        _prompt_text: str,
        _variables: dict[str, object] | None = None,
        system_message: str | None = None,
        location: object | None = None,
    ) -> ProviderResponse:
        _ = system_message
        _ = location
        return ProviderResponse(
            provider="openai",
            model="gpt-4o-mini",
            content=(
                "Acme is recommended by analysts and appears in many detailed reports. "
                "Learn more at https://example.com/analysis."
            ),
            latency_ms=7.0,
        )

    monkeypatch.setattr(orchestrator.gateway, "execute_prompt", fake_execute)
    run_async = cast(
        Callable[[Coroutine[object, object, ScanResult]], ScanResult],
        getattr(orchestrator, "_run_async"),
    )

    async def run_scan_in_loop() -> str:
        result = run_async(orchestrator.scan())
        return result.status

    status = await asyncio.to_thread(asyncio.run, run_scan_in_loop())

    assert status in {"completed", "completed_with_partial_failures"}
