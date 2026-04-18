import uuid
from datetime import datetime, timezone
from typing import cast, override
from unittest.mock import MagicMock

import pytest

from ai_visibility.providers.adapters import AdapterResult, ScanAdapter, StubAdapter
from ai_visibility.providers.gateway import LocationContext
from ai_visibility.runs.orchestrator import RunOrchestrator
from ai_visibility.runs.scan_strategy import ProviderConfig
from ai_visibility.storage.repositories import RunRepository, WorkspaceRepository
from ai_visibility.storage.types import WorkspaceRecord


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

    repo = WorkspaceRepository(mock_prisma)
    _ = await repo.create(workspace)
    return workspace


def _ok_result() -> AdapterResult:
    return AdapterResult(
        raw_response="Acme is trusted. https://example.com/proof",
        citations=[{"url": "https://example.com/proof"}],
        provider="openai",
        model_name="gpt-5.4",
        model_version="gpt-5.4",
        strategy_version="v1",
    )


@pytest.mark.asyncio
async def test_scan_lifecycle_status_completed_and_partial(
    monkeypatch: pytest.MonkeyPatch,
    mock_prisma: MagicMock,
    patch_get_prisma: MagicMock,
) -> None:
    _ = patch_get_prisma
    workspace = await _create_workspace(mock_prisma, "acme")
    mock_prisma.aivisrun.create.return_value = MagicMock()  # pyright: ignore[reportAny]

    complete_adapter = StubAdapter(result=_ok_result())
    complete_orchestrator = RunOrchestrator(
        workspace_slug="acme",
        provider="openai",
        adapters={"chatgpt": complete_adapter},
    )
    monkeypatch.setattr(
        complete_orchestrator.prompt_library, "list_prompts", lambda: [{"template": "{brand}", "version": "1.0.0"}]
    )
    completed = await complete_orchestrator.scan()
    assert completed.status == "completed"

    class FailOnSecondAdapter(ScanAdapter):
        calls: int

        def __init__(self) -> None:
            self.calls = 0

        @override
        def execute(
            self,
            prompt_text: str,
            workspace_slug: str,
            strategy_config: ProviderConfig,
            location: LocationContext | None = None,
        ) -> AdapterResult:
            _ = prompt_text
            _ = workspace_slug
            _ = strategy_config
            _ = location
            self.calls += 1
            if self.calls == 2:
                raise ValueError("provider down")
            return _ok_result()

    partial_orchestrator = RunOrchestrator(
        workspace_slug="acme",
        provider="openai",
        adapters={"chatgpt": FailOnSecondAdapter()},
    )
    monkeypatch.setattr(
        partial_orchestrator.prompt_library,
        "list_prompts",
        lambda: [
            {"template": "prompt 1 {brand}", "version": "1.0.0"},
            {"template": "prompt 2 {brand}", "version": "1.0.0"},
            {"template": "prompt 3 {brand}", "version": "1.0.0"},
        ],
    )
    partial = await partial_orchestrator.scan()
    assert partial.status == "completed_with_partial_failures"
    assert partial.results_count == 2

    mock_prisma.aivisrun.find_many.return_value = [  # pyright: ignore[reportAny]
        MagicMock(
            id="run-completed",
            workspaceId=workspace["id"],
            provider="openai",
            model="gpt-5.4",
            promptVersion="1.0.0",
            parserVersion="parser_v1",
            status="COMPLETED",
            createdAt=datetime.now(timezone.utc),
            rawResponse="ok",
            error=None,
        ),
        MagicMock(
            id="run-partial",
            workspaceId=workspace["id"],
            provider="openai",
            model="gpt-5.4",
            promptVersion="1.0.0",
            parserVersion="parser_v1",
            status="COMPLETED_WITH_PARTIAL_FAILURES",
            createdAt=datetime.now(timezone.utc),
            rawResponse="ok",
            error=None,
        ),
    ]
    run_repo = RunRepository(mock_prisma)
    runs = await run_repo.list_by_workspace(workspace["id"])
    assert runs[0]["status"] in {"completed", "completed_with_partial_failures"}
    assert runs[1]["status"] in {"completed", "completed_with_partial_failures"}


@pytest.mark.asyncio
async def test_scan_dispatches_adapter_with_strategy_config(
    monkeypatch: pytest.MonkeyPatch,
    mock_prisma: MagicMock,
    patch_get_prisma: MagicMock,
) -> None:
    _ = patch_get_prisma
    _ = await _create_workspace(mock_prisma, "acme")
    mock_prisma.aivisrun.create.return_value = MagicMock()  # pyright: ignore[reportAny]

    adapter = StubAdapter(result=_ok_result())
    orchestrator = RunOrchestrator(
        workspace_slug="acme",
        provider="openai",
        adapters={"chatgpt": adapter},
    )
    monkeypatch.setattr(
        orchestrator.prompt_library, "list_prompts", lambda: [{"template": "find {brand}", "version": "1.0.0"}]
    )

    result = await orchestrator.scan()

    assert result.status == "completed"
    assert len(adapter.calls) == 1
    call_args = adapter.calls[0]
    prompt_text = call_args[0]
    workspace_slug = call_args[1]
    strategy_config = call_args[2]
    assert "acme" in prompt_text.lower()
    assert workspace_slug == "acme"
    assert strategy_config.provider == "chatgpt"


@pytest.mark.asyncio
async def test_malformed_adapter_output_rejected(
    monkeypatch: pytest.MonkeyPatch,
    mock_prisma: MagicMock,
    patch_get_prisma: MagicMock,
) -> None:
    _ = patch_get_prisma
    _ = await _create_workspace(mock_prisma, "acme")
    mock_prisma.aivisrun.create.return_value = MagicMock()  # pyright: ignore[reportAny]

    class MalformedAdapter(ScanAdapter):
        @override
        def execute(
            self,
            prompt_text: str,
            workspace_slug: str,
            strategy_config: ProviderConfig,
            location: LocationContext | None = None,
        ) -> AdapterResult:
            _ = prompt_text
            _ = workspace_slug
            _ = strategy_config
            _ = location
            malformed: dict[str, object] = {
                "raw_response": "ok",
                "citations": [],
                "provider": "openai",
            }
            return cast(AdapterResult, cast(object, malformed))

    orchestrator = RunOrchestrator(
        workspace_slug="acme",
        provider="openai",
        adapters={"chatgpt": MalformedAdapter()},
    )
    monkeypatch.setattr(
        orchestrator.prompt_library, "list_prompts", lambda: [{"template": "find {brand}", "version": "1.0.0"}]
    )

    result = await orchestrator.scan()

    assert result.status == "failed"
    assert result.results_count == 0
    assert result.error_message is not None
