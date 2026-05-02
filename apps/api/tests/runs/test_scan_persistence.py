import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from ai_visibility.providers.adapters import AdapterResult, StubAdapter
from ai_visibility.runs.orchestrator import RunOrchestrator
from ai_visibility.storage.repositories import ScanEvidenceRepository, WorkspaceRepository
from ai_visibility.storage.types import (
    ObservationRecord,
    PromptExecutionCitationRecord,
    PromptExecutionRecord,
    ScanExecutionRecord,
    ScanJobRecord,
    WorkspaceRecord,
)


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
    workspace_model = SimpleNamespace(
        id=workspace["id"],
        slug=workspace["slug"],
        brandName=workspace["brand_name"],
        city=workspace["city"],
        region=workspace["region"],
        country=workspace["country"],
        createdAt=created_at,
    )

    mock_prisma.workspace.create.return_value = workspace_model

    def _workspace_lookup(*, where: dict[str, str]):
        if where.get("slug") == slug or where.get("id") == workspace["id"]:
            return workspace_model
        return None

    mock_prisma.workspace.find_unique.side_effect = _workspace_lookup

    repository = WorkspaceRepository(mock_prisma)
    return await repository.create(workspace)


@pytest.mark.asyncio
async def test_scan_persists_append_only_evidence_rows(
    monkeypatch: pytest.MonkeyPatch,
    mock_prisma: MagicMock,
    patch_get_prisma: MagicMock,
) -> None:
    assert patch_get_prisma is mock_prisma
    _ = await _create_workspace(mock_prisma, "acme")

    adapter_result = AdapterResult(
        raw_response="Acme is a top option. Source: https://example.com/acme-proof",
        citations=[{"url": "https://example.com/acme-proof", "text": "Acme proof"}],
        provider="openai",
        model_name="gpt-5.4",
        model_version="gpt-5.4",
        strategy_version="v1",
    )
    orchestrator = RunOrchestrator(
        workspace_slug="acme",
        provider="openai",
        adapters={"chatgpt": StubAdapter(result=adapter_result)},
    )
    monkeypatch.setattr(
        orchestrator.prompt_library,
        "list_prompts",
        lambda: [{"id": "prompt-1", "template": "find {brand}", "version": "1.0.0"}],
    )

    first = await orchestrator.scan()
    first_counts = {
        "scan_jobs": mock_prisma.scanjob.upsert.call_count,
        "scan_executions": mock_prisma.scanexecution.upsert.call_count,
        "prompt_executions": mock_prisma.promptexecution.upsert.call_count,
        "observations": mock_prisma.observation.upsert.call_count,
        "prompt_execution_citations": mock_prisma.promptexecutioncitation.upsert.call_count,
    }

    second = await orchestrator.scan()
    second_counts = {
        "scan_jobs": mock_prisma.scanjob.upsert.call_count,
        "scan_executions": mock_prisma.scanexecution.upsert.call_count,
        "prompt_executions": mock_prisma.promptexecution.upsert.call_count,
        "observations": mock_prisma.observation.upsert.call_count,
        "prompt_execution_citations": mock_prisma.promptexecutioncitation.upsert.call_count,
    }

    assert first.status == "completed"
    assert second.status == "completed"
    assert second.run_id != first.run_id
    assert second_counts["scan_jobs"] > first_counts["scan_jobs"]
    assert second_counts["scan_executions"] > first_counts["scan_executions"]
    assert second_counts["prompt_executions"] > first_counts["prompt_executions"]
    assert second_counts["observations"] > first_counts["observations"]
    assert second_counts["prompt_execution_citations"] > first_counts["prompt_execution_citations"]

    run_create_calls = mock_prisma.run.create.await_args_list
    prompt_upsert_calls = mock_prisma.promptexecution.upsert.await_args_list

    assert all(call.kwargs["data"]["rawResponse"] for call in run_create_calls)
    assert all(call.kwargs["data"]["create"]["rawResponse"] for call in prompt_upsert_calls)


@pytest.mark.asyncio
async def test_scan_evidence_repository_writes_are_idempotent(mock_prisma: MagicMock) -> None:
    repository = ScanEvidenceRepository(mock_prisma)

    scan_job: ScanJobRecord = {
        "id": "scan-job-1",
        "workspace_slug": "acme",
        "strategy_version": "v1",
        "prompt_version": "1.0.0",
        "created_at": "2026-03-14T00:00:00+00:00",
        "idempotency_key": "scan-job-key-1",
        "status": "completed",
        "scan_mode": "scheduled",
    }
    scan_execution: ScanExecutionRecord = {
        "id": "scan-exec-1",
        "scan_job_id": "scan-job-1",
        "provider": "openai",
        "model_name": "gpt-5.4",
        "model_version": "gpt-5.4",
        "executed_at": "2026-03-14T00:00:01+00:00",
        "idempotency_key": "scan-exec-key-1",
        "status": "completed",
    }
    prompt_execution: PromptExecutionRecord = {
        "id": "prompt-exec-1",
        "scan_execution_id": "scan-exec-1",
        "prompt_id": "prompt-1",
        "prompt_text": "find acme",
        "raw_response": "Acme response",
        "executed_at": "2026-03-14T00:00:02+00:00",
        "idempotency_key": "prompt-exec-key-1",
        "parser_version": "1.0.0",
    }
    observation: ObservationRecord = {
        "id": "observation-1",
        "prompt_execution_id": "prompt-exec-1",
        "brand_mentioned": True,
        "brand_position": 1,
        "response_excerpt": "Acme appears first.",
        "idempotency_key": "observation-key-1",
        "strategy_version": "v1",
    }
    citation: PromptExecutionCitationRecord = {
        "id": "citation-1",
        "prompt_execution_id": "prompt-exec-1",
        "url": "https://example.com/proof",
        "title": "Proof",
        "cited_text": "Acme proof",
        "idempotency_key": "citation-key-1",
    }

    mock_prisma.scanjob.find_unique.side_effect = [None, MagicMock()]
    assert await repository.create_scan_job(scan_job) is True
    assert await repository.create_scan_job({**scan_job, "id": "scan-job-duplicate"}) is False

    mock_prisma.scanexecution.find_unique.side_effect = [None, MagicMock()]
    assert await repository.create_scan_execution(scan_execution) is True
    assert await repository.create_scan_execution({**scan_execution, "id": "scan-exec-duplicate"}) is False

    mock_prisma.promptexecution.find_unique.side_effect = [None, MagicMock()]
    assert await repository.create_prompt_execution(prompt_execution) is True
    assert await repository.create_prompt_execution({**prompt_execution, "id": "prompt-exec-duplicate"}) is False

    mock_prisma.observation.find_unique.side_effect = [None, MagicMock()]
    assert await repository.create_observation(observation) is True
    assert await repository.create_observation({**observation, "id": "observation-duplicate"}) is False

    mock_prisma.promptexecutioncitation.find_unique.side_effect = [None, MagicMock()]
    assert await repository.create_prompt_execution_citation(citation) is True
    assert await repository.create_prompt_execution_citation({**citation, "id": "citation-duplicate"}) is False

    assert mock_prisma.scanjob.upsert.call_count == 1
    assert mock_prisma.scanexecution.upsert.call_count == 1
    assert mock_prisma.promptexecution.upsert.call_count == 1
    assert mock_prisma.observation.upsert.call_count == 1
    assert mock_prisma.promptexecutioncitation.upsert.call_count == 1
