import uuid
from datetime import datetime, timezone
from typing import override
from unittest.mock import MagicMock

import pytest

from ai_visibility.providers.adapters import AdapterResult, StubAdapter
from ai_visibility.runs.orchestrator import RunOrchestrator
from ai_visibility.storage.repositories import RunRepository, WorkspaceRepository
from ai_visibility.storage.types import WorkspaceRecord


async def _create_workspace(mock_prisma: MagicMock, slug: str) -> WorkspaceRecord:
    created_at = datetime.now(timezone.utc)
    workspace: WorkspaceRecord = {
        "id": str(uuid.uuid4()),
        "slug": slug,
        "brand_name": f"{slug.title()} Brand",
        "city": "",
        "region": "",
        "country": "",
        "created_at": created_at.isoformat(),
    }

    workspace_row = MagicMock(
        id=workspace["id"],
        slug=workspace["slug"],
        brandName=workspace["brand_name"],
        city=workspace["city"],
        region=workspace["region"],
        country=workspace["country"],
        createdAt=created_at,
    )
    mock_prisma.aivisworkspace.create.return_value = workspace_row  # pyright: ignore[reportAny]
    mock_prisma.aivisworkspace.find_unique.return_value = workspace_row  # pyright: ignore[reportAny]

    _ = await WorkspaceRepository(mock_prisma).create(workspace)
    return workspace


def _adapter_result() -> AdapterResult:
    return AdapterResult(
        raw_response="Acme appears with source https://example.com/docs",
        citations=[{"url": "https://example.com/docs"}],
        provider="openai",
        model_name="gpt-5.4",
        model_version="gpt-5.4",
        strategy_version="v1",
    )


@pytest.mark.asyncio
async def test_scan_persists_run_and_list_runs(
    monkeypatch: pytest.MonkeyPatch,
    mock_prisma: MagicMock,
    patch_get_prisma: MagicMock,
) -> None:
    _ = patch_get_prisma
    workspace = await _create_workspace(mock_prisma, "acme")

    mock_prisma.aivisrun.create.return_value = MagicMock()  # pyright: ignore[reportAny]

    orchestrator = RunOrchestrator(
        workspace_slug="acme",
        provider="openai",
        adapters={"chatgpt": StubAdapter(result=_adapter_result())},
    )
    monkeypatch.setattr(
        orchestrator.prompt_library, "list_prompts", lambda: [{"template": "{brand}", "version": "1.0.0"}]
    )

    result = await orchestrator.scan()

    assert result.status == "completed"

    mock_run_row = MagicMock(
        id=result.run_id,
        workspaceId=workspace["id"],
        provider="openai",
        model="gpt-5.4",
        promptVersion="1.0.0",
        parserVersion="parser_v1",
        status="COMPLETED",
        createdAt=datetime.now(timezone.utc),
        rawResponse="Acme appears with source https://example.com/docs",
        error=None,
    )
    mock_prisma.aivisrun.find_many.return_value = [mock_run_row]  # pyright: ignore[reportAny]

    run_repo = RunRepository(mock_prisma)
    runs = await run_repo.list_by_workspace(workspace["id"])
    assert len(runs) == 1
    assert runs[0]["id"] == result.run_id
    assert runs[0]["status"] == "completed"

    listed = await orchestrator.list_runs()
    assert len(listed) == 1
    assert listed[0]["id"] == result.run_id


@pytest.mark.asyncio
async def test_scan_uses_first_three_prompts(
    monkeypatch: pytest.MonkeyPatch,
    mock_prisma: MagicMock,
    patch_get_prisma: MagicMock,
) -> None:
    _ = patch_get_prisma
    _ = await _create_workspace(mock_prisma, "acme")
    adapter = StubAdapter(result=_adapter_result())
    orchestrator = RunOrchestrator(
        workspace_slug="acme",
        provider="openai",
        adapters={"chatgpt": adapter},
    )
    monkeypatch.setattr(
        orchestrator.prompt_library,
        "list_prompts",
        lambda: [
            {"template": "prompt 1 {brand}", "version": "1.0.0"},
            {"template": "prompt 2 {brand}", "version": "1.0.0"},
            {"template": "prompt 3 {brand}", "version": "1.0.0"},
            {"template": "prompt 4 {brand}", "version": "1.0.0"},
        ],
    )

    result = await orchestrator.scan()

    assert result.results_count == 3
    assert len(adapter.calls) == 3


@pytest.mark.asyncio
async def test_scan_failed_when_every_prompt_fails(
    monkeypatch: pytest.MonkeyPatch,
    mock_prisma: MagicMock,
    patch_get_prisma: MagicMock,
) -> None:
    _ = patch_get_prisma
    _ = await _create_workspace(mock_prisma, "acme")

    class FailingAdapter(StubAdapter):
        @override
        def execute(self, prompt_text: str, workspace_slug: str, strategy_config: object) -> AdapterResult:
            _ = prompt_text
            _ = workspace_slug
            _ = strategy_config
            raise ValueError("adapter failed")

    orchestrator = RunOrchestrator(
        workspace_slug="acme",
        provider="openai",
        adapters={"chatgpt": FailingAdapter()},
    )
    monkeypatch.setattr(
        orchestrator.prompt_library, "list_prompts", lambda: [{"template": "{brand}", "version": "1.0.0"}]
    )

    result = await orchestrator.scan()

    assert result.status == "failed"
    assert result.results_count == 0
    assert result.error_message is not None
