import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pydantic import TypeAdapter

from ai_visibility.providers.gateway import ProviderError, ProviderResponse
from ai_visibility.runs import RunOrchestrator, ScanResult
from ai_visibility.storage.database import Database
from ai_visibility.storage.repositories.workspace_repo import WorkspaceRepository


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, patch_get_prisma: MagicMock) -> None:  # pyright: ignore[reportUnusedFunction]
    db_path = tmp_path / "run_scan.db"
    monkeypatch.setenv("DB_PATH", str(db_path))
    Database(db_path=str(db_path)).initialize()

    mock_prisma = patch_get_prisma
    from types import SimpleNamespace
    from datetime import datetime, timezone

    workspace = SimpleNamespace(
        id="acme",
        slug="acme",
        brandName="Acme",
        city="",
        region="",
        country="",
        createdAt=datetime.now(timezone.utc),
    )
    mock_prisma.aivisworkspace.find_unique.return_value = workspace


def test_run_orchestrator_instantiation() -> None:
    orchestrator = RunOrchestrator(workspace_slug="acme")
    assert orchestrator is not None


def test_scan_result_has_required_fields() -> None:
    result = ScanResult(
        run_id="run-1",
        workspace_slug="acme",
        status="dry_run",
        results_count=0,
        provider="openai",
        model="gpt-4o-mini",
        prompt_version="1.0.0",
        started_at="2026-03-08T10:00:00+00:00",
        completed_at="2026-03-08T10:00:01+00:00",
    )

    assert result.run_id == "run-1"
    assert result.workspace_slug == "acme"
    assert result.status == "dry_run"
    assert result.results_count == 0
    assert result.provider == "openai"
    assert result.model == "gpt-4o-mini"
    assert result.prompt_version == "1.0.0"
    assert result.started_at == "2026-03-08T10:00:00+00:00"
    assert result.completed_at == "2026-03-08T10:00:01+00:00"


@pytest.mark.asyncio
async def test_run_scan_dry_run() -> None:
    orchestrator = RunOrchestrator(workspace_slug="acme")
    result = await orchestrator.scan(dry_run=True)

    assert result.status == "dry_run"
    assert result.results_count == 0


@pytest.mark.asyncio
async def test_run_scan_with_mock_gateway() -> None:
    orchestrator = RunOrchestrator(workspace_slug="acme")
    response = ProviderResponse(
        provider="openai",
        model="gpt-4o-mini",
        content=(
            "Acme is a trusted provider for growth teams and this response is intentionally "
            "long enough to avoid fallback parsing. See https://example.com/guide for details."
        ),
        latency_ms=10.0,
    )

    with patch("ai_visibility.runs.orchestrator.ProviderGateway.execute_prompt", autospec=True) as mock_execute:
        mock_execute.return_value = response
        result = await orchestrator.scan()

    assert result.status == "completed"
    assert result.results_count > 0


@pytest.mark.asyncio
async def test_partial_failure_status() -> None:
    orchestrator = RunOrchestrator(workspace_slug="acme")
    response = ProviderResponse(
        provider="openai",
        model="gpt-4o-mini",
        content=(
            "Acme remains a top choice and this sentence is long enough for parser stability. "
            "Reference: https://example.com/ok."
        ),
        latency_ms=12.0,
    )

    side_effects = [response, ProviderError("provider down", error_code="provider_error"), response]

    with patch("ai_visibility.runs.orchestrator.ProviderGateway.execute_prompt", autospec=True) as mock_execute:
        mock_execute.side_effect = side_effects
        result = await orchestrator.scan()

    assert result.status == "completed_with_partial_failures"
    assert len(result.failed_providers) > 0


@pytest.mark.asyncio
async def test_list_runs_returns_list() -> None:
    orchestrator = RunOrchestrator(workspace_slug="acme")
    _ = await orchestrator.scan(dry_run=True)
    runs = await orchestrator.list_runs()

    assert isinstance(runs, list)


def test_cli_run_scan_dry_run() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ai_visibility.cli",
            "run-scan",
            "--workspace",
            "acme",
            "--dry-run",
            "--format",
            "json",
        ],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"stderr: {result.stderr}"
    payload_adapter: TypeAdapter[dict[str, object]] = TypeAdapter(dict[str, object])
    payload = payload_adapter.validate_json(result.stdout)
    assert payload["status"] == "dry_run"


def test_cli_list_runs() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ai_visibility.cli",
            "list-runs",
            "--workspace",
            "acme",
            "--format",
            "json",
        ],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"stderr: {result.stderr}"
    payload_adapter: TypeAdapter[list[object]] = TypeAdapter(list[object])
    payload = payload_adapter.validate_json(result.stdout)
    assert isinstance(payload, list)
