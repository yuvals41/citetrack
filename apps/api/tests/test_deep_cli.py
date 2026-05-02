from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from ai_visibility import cli
from ai_visibility.storage.repositories import WorkspaceRepository


def _patch_cli_get_prisma(monkeypatch: pytest.MonkeyPatch, mock_prisma: MagicMock) -> None:
    async def _fake_get_prisma() -> MagicMock:
        return mock_prisma

    monkeypatch.setattr(cli, "get_prisma", _fake_get_prisma)


def _workspace_model(
    *,
    workspace_id: str,
    slug: str,
    brand_name: str,
    city: str = "",
    region: str = "",
    country: str = "",
) -> SimpleNamespace:
    return SimpleNamespace(
        id=workspace_id,
        slug=slug,
        brandName=brand_name,
        city=city,
        region=region,
        country=country,
        createdAt=datetime.now(timezone.utc),
    )


def _run_model(*, run_id: str, workspace_id: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=run_id,
        workspaceId=workspace_id,
        provider="openai",
        model="gpt-4",
        promptVersion="v1",
        parserVersion="parser_v1",
        status="COMPLETED",
        createdAt=datetime.now(timezone.utc),
        rawResponse="sample",
        error=None,
    )


def test_doctor_returns_expected_shape() -> None:
    result = cli.doctor(format="json")

    assert isinstance(result, dict)
    assert {"status", "llm_framework", "db_path", "log_level", "providers"}.issubset(result.keys())
    assert isinstance(result["providers"], dict)


def test_list_prompts_returns_prompt_collections() -> None:
    result = cli.list_prompts()

    assert isinstance(result, dict)
    assert result["status"] == "success"
    assert isinstance(result["categories"], list)
    assert isinstance(result["prompt_sets"], dict)
    assert result["total_count"] > 0


@pytest.mark.asyncio
async def test_list_workspaces_returns_workspace_list(
    monkeypatch: pytest.MonkeyPatch,
    mock_prisma: MagicMock,
    patch_get_prisma: MagicMock,
) -> None:
    _ = patch_get_prisma
    _patch_cli_get_prisma(monkeypatch, mock_prisma)
    mock_prisma.workspace.find_many.return_value = [
        _workspace_model(workspace_id="ws-acme", slug="acme", brand_name="Acme Corp"),
        _workspace_model(workspace_id="ws-beta", slug="beta-brand", brand_name="Beta Brand"),
    ]

    result = await cli.list_workspaces()
    assert isinstance(result, dict)
    assert result["status"] == "success"
    assert isinstance(result["workspaces"], list)
    assert result["total_count"] >= 2


@pytest.mark.asyncio
async def test_seed_demo_creates_workspace_records_in_db(
    monkeypatch: pytest.MonkeyPatch,
    mock_prisma: MagicMock,
    patch_get_prisma: MagicMock,
) -> None:
    _ = patch_get_prisma
    _patch_cli_get_prisma(monkeypatch, mock_prisma)

    acme = _workspace_model(workspace_id="ws-acme", slug="acme", brand_name="Acme Corp")
    beta = _workspace_model(workspace_id="ws-beta", slug="beta-brand", brand_name="Beta Brand")

    def find_unique_side_effect(*, where: dict[str, str]) -> SimpleNamespace | None:
        if where.get("slug") == "acme":
            return acme
        if where.get("slug") == "beta-brand":
            return beta
        if where.get("id") == "ws-acme":
            return acme
        if where.get("id") == "ws-beta":
            return beta
        return None

    mock_prisma.workspace.find_unique.side_effect = find_unique_side_effect
    mock_prisma.run.find_many.return_value = [_run_model(run_id="run-1", workspace_id="ws-acme")]

    result = await cli.seed_demo()

    repo = WorkspaceRepository(mock_prisma)
    acme_record = await repo.get_by_slug("acme")
    beta_record = await repo.get_by_slug("beta-brand")

    assert isinstance(result, dict)
    assert result["status"] == "success"
    assert acme_record is not None
    assert beta_record is not None


@pytest.mark.asyncio
async def test_recommend_latest_returns_recommendations_list(
    monkeypatch: pytest.MonkeyPatch,
    mock_prisma: MagicMock,
    patch_get_prisma: MagicMock,
) -> None:
    _ = patch_get_prisma
    _patch_cli_get_prisma(monkeypatch, mock_prisma)
    mock_prisma.workspace.find_unique.return_value = _workspace_model(
        workspace_id="ws-acme",
        slug="acme",
        brand_name="Acme Corp",
    )
    mock_prisma.run.find_many.return_value = [_run_model(run_id="run-1", workspace_id="ws-acme")]
    mock_prisma.mention.find_many.return_value = []

    result = await cli.recommend_latest(workspace="acme")
    assert isinstance(result, dict)
    assert "degraded" not in result
    assert result["workspace"] == "acme"
    assert isinstance(result["recommendations"], list)
    assert isinstance(result["explanations_enabled"], bool)


@pytest.mark.asyncio
async def test_recommend_latest_handles_missing_workspace_gracefully(
    monkeypatch: pytest.MonkeyPatch,
    mock_prisma: MagicMock,
    patch_get_prisma: MagicMock,
) -> None:
    _ = patch_get_prisma
    _patch_cli_get_prisma(monkeypatch, mock_prisma)
    mock_prisma.workspace.find_unique.return_value = None
    mock_prisma.workspace.find_many.return_value = [
        _workspace_model(workspace_id="ws-existing", slug="existing", brand_name="Existing"),
    ]

    result = await cli.recommend_latest(workspace="missing-workspace")
    assert isinstance(result, dict)
    assert "degraded" in result
    assert result["degraded"]["reason"] == "workspace_not_found"


@pytest.mark.asyncio
async def test_summarize_latest_handles_missing_workspace_gracefully(
    monkeypatch: pytest.MonkeyPatch,
    mock_prisma: MagicMock,
    patch_get_prisma: MagicMock,
) -> None:
    _ = patch_get_prisma
    _patch_cli_get_prisma(monkeypatch, mock_prisma)
    mock_prisma.workspace.find_unique.return_value = None
    mock_prisma.workspace.find_many.return_value = [
        _workspace_model(workspace_id="ws-existing", slug="existing", brand_name="Existing"),
    ]

    result = await cli.summarize_latest(workspace="missing-workspace")
    assert isinstance(result, dict)
    assert "degraded" in result
    assert result["degraded"]["reason"] == "workspace_not_found"


@pytest.mark.asyncio
async def test_run_scan_returns_degraded_state_when_provider_fails(
    monkeypatch: pytest.MonkeyPatch,
    mock_prisma: MagicMock,
    patch_get_prisma: MagicMock,
) -> None:
    _ = patch_get_prisma
    _patch_cli_get_prisma(monkeypatch, mock_prisma)
    mock_prisma.workspace.find_unique.return_value = _workspace_model(
        workspace_id="ws-acme",
        slug="acme",
        brand_name="Acme Corp",
    )

    class FakeResult:
        run_id: str = "run-1"
        workspace_slug: str = "acme"
        status: str = "failed"
        results_count: int = 0
        provider: str = "openai"
        started_at: str = "2026-03-13T00:00:00+00:00"
        failed_providers: list[str] = ["openai"]
        error_message: str = "Missing API key: OPENAI_API_KEY not set"

    class FakeOrchestrator:
        def __init__(self, workspace_slug: str, provider: str = "openai") -> None:
            _ = workspace_slug
            _ = provider

        async def scan(self, dry_run: bool = False) -> FakeResult:
            _ = dry_run
            return FakeResult()

    monkeypatch.setattr(cli, "RunOrchestrator", FakeOrchestrator)

    result = await cli.run_scan(workspace="acme", provider="openai")
    assert isinstance(result, dict)
    assert "degraded" in result
    assert result["degraded"]["reason"] == "missing_api_key"


@pytest.mark.asyncio
async def test_recommend_latest_returns_degraded_state_when_storage_errors(
    monkeypatch: pytest.MonkeyPatch,
    mock_prisma: MagicMock,
    patch_get_prisma: MagicMock,
) -> None:
    _ = patch_get_prisma
    _patch_cli_get_prisma(monkeypatch, mock_prisma)
    mock_prisma.workspace.find_unique.return_value = _workspace_model(
        workspace_id="ws-acme",
        slug="acme",
        brand_name="Acme Corp",
    )

    async def fail_list_by_workspace(self: object, workspace_id: str) -> list[dict[str, object]]:
        _ = self
        _ = workspace_id
        raise RuntimeError("disk io error")

    monkeypatch.setattr("ai_visibility.cli.RunRepository.list_by_workspace", fail_list_by_workspace)

    result = await cli.recommend_latest(workspace="acme")
    assert isinstance(result, dict)
    assert "degraded" in result
    assert result["degraded"]["reason"] == "provider_failure"


@pytest.mark.asyncio
async def test_command_functions_return_dict_not_string(
    monkeypatch: pytest.MonkeyPatch,
    mock_prisma: MagicMock,
    patch_get_prisma: MagicMock,
) -> None:
    _ = patch_get_prisma
    _patch_cli_get_prisma(monkeypatch, mock_prisma)
    mock_prisma.workspace.find_many.return_value = [
        _workspace_model(workspace_id="ws-acme", slug="acme", brand_name="Acme Corp"),
    ]
    mock_prisma.workspace.find_unique.return_value = _workspace_model(
        workspace_id="ws-acme",
        slug="acme",
        brand_name="Acme Corp",
    )
    mock_prisma.run.find_many.return_value = []

    outputs = [
        cli.doctor(),
        cli.list_prompts(),
        await cli.list_workspaces(),
        await cli.seed_demo(),
        await cli.recommend_latest(workspace="acme"),
    ]

    assert all(isinstance(output, dict) for output in outputs)
    assert all(not isinstance(output, str) for output in outputs)


@pytest.mark.asyncio
async def test_create_workspace_stores_location_fields(
    monkeypatch: pytest.MonkeyPatch,
    mock_prisma: MagicMock,
    patch_get_prisma: MagicMock,
) -> None:
    _ = patch_get_prisma
    _patch_cli_get_prisma(monkeypatch, mock_prisma)

    created_workspace = _workspace_model(
        workspace_id="ws-acme-loc",
        slug="acme-loc",
        brand_name="Acme",
        city="San Francisco",
        region="CA",
        country="US",
    )
    mock_prisma.workspace.find_unique.side_effect = [None, created_workspace]
    mock_prisma.workspace.create.return_value = created_workspace

    result = await cli.create_workspace(
        brand_name="Acme",
        slug="acme-loc",
        city="San Francisco",
        region="CA",
        country="US",
    )

    repo = WorkspaceRepository(mock_prisma)
    workspace = await repo.get_by_slug("acme-loc")
    assert result["status"] == "created"
    assert workspace is not None
    assert workspace["city"] == "San Francisco"
    assert workspace["region"] == "CA"
    assert workspace["country"] == "US"


@pytest.mark.asyncio
async def test_create_workspace_cli_accepts_location_flags(
    monkeypatch: pytest.MonkeyPatch,
    mock_prisma: MagicMock,
    patch_get_prisma: MagicMock,
) -> None:
    _ = patch_get_prisma
    _patch_cli_get_prisma(monkeypatch, mock_prisma)

    created_workspace = _workspace_model(
        workspace_id="ws-acme-cli-loc",
        slug="acme-cli-loc",
        brand_name="Acme CLI",
        city="Austin",
        region="TX",
        country="US",
    )
    mock_prisma.workspace.find_unique.side_effect = [None, created_workspace]
    mock_prisma.workspace.create.return_value = created_workspace

    payload = await cli.create_workspace(
        brand_name="Acme CLI",
        slug="acme-cli-loc",
        city="Austin",
        region="TX",
        country="US",
    )

    assert payload["status"] == "created"

    repo = WorkspaceRepository(mock_prisma)
    workspace = await repo.get_by_slug("acme-cli-loc")
    assert workspace is not None
    assert workspace["city"] == "Austin"
    assert workspace["region"] == "TX"
    assert workspace["country"] == "US"
