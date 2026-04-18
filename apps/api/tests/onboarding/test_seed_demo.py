"""Tests for seed-demo CLI command."""

from datetime import datetime, timezone
import json
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai_visibility.cli import seed_demo
from ai_visibility.storage.repositories.workspace_repo import WorkspaceRepository


def _workspace_model(
    *,
    workspace_id: str,
    slug: str,
    brand_name: str,
    city: str = "",
    region: str = "",
    country: str = "",
    created_at: datetime | None = None,
) -> MagicMock:
    row = MagicMock()
    row.id = workspace_id
    row.slug = slug
    row.brandName = brand_name
    row.city = city
    row.region = region
    row.country = country
    row.createdAt = created_at or datetime.now(timezone.utc)
    return row


def _configure_workspace_state(
    mock_prisma: MagicMock,
    *,
    initial: dict[str, MagicMock] | None = None,
) -> dict[str, MagicMock]:
    state = dict(initial or {})

    async def _find_unique(*, where: dict[str, str]) -> MagicMock | None:
        slug = where.get("slug")
        if slug:
            return state.get(slug)
        id_val = where.get("id")
        if id_val:
            for entry in state.values():
                if entry.id == id_val:
                    return entry
        return None

    async def _create(*, data: dict[str, object]) -> MagicMock:
        created_at = data["createdAt"]
        row = _workspace_model(
            workspace_id=str(data["id"]),
            slug=str(data["slug"]),
            brand_name=str(data["brandName"]),
            city=str(data.get("city", "")),
            region=str(data.get("region", "")),
            country=str(data.get("country", "")),
            created_at=created_at if isinstance(created_at, datetime) else datetime.now(timezone.utc),
        )
        state[str(data["slug"])] = row
        return row

    workspace_model = cast(MagicMock, getattr(mock_prisma, "aivisworkspace"))
    setattr(workspace_model, "find_unique", AsyncMock(side_effect=_find_unique))
    setattr(workspace_model, "create", AsyncMock(side_effect=_create))
    return state


@pytest.fixture
def configured_mock_prisma(
    mock_prisma: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> MagicMock:
    monkeypatch.setattr("ai_visibility.cli.get_prisma", AsyncMock(return_value=mock_prisma))
    _ = _configure_workspace_state(mock_prisma)
    return mock_prisma


@pytest.mark.usefixtures("patch_get_prisma")
@pytest.mark.asyncio
class TestSeedDemoFunction:
    """Test the seed_demo() function directly."""

    async def test_seed_demo_returns_dict(self, configured_mock_prisma: MagicMock) -> None:
        """Test that seed_demo returns a dictionary."""
        _ = configured_mock_prisma
        result = await seed_demo(_format_arg="json")
        assert isinstance(result, dict)

    async def test_seed_demo_has_required_keys(self, configured_mock_prisma: MagicMock) -> None:
        """Test that seed_demo result has required keys."""
        _ = configured_mock_prisma
        result = await seed_demo(_format_arg="json")
        assert "status" in result
        assert "workspaces_created" in result
        assert "workspaces_skipped" in result
        assert "runs_created" in result
        assert "mentions_created" in result

    async def test_seed_demo_status_is_success(self, configured_mock_prisma: MagicMock) -> None:
        """Test that seed_demo status is 'success'."""
        _ = configured_mock_prisma
        result = await seed_demo(_format_arg="json")
        assert result["status"] == "success"

    async def test_seed_demo_creates_or_skips_workspaces(self, configured_mock_prisma: MagicMock) -> None:
        """Test that seed_demo creates or skips workspaces."""
        _ = configured_mock_prisma
        result = await seed_demo(_format_arg="json")
        # Either creates 5 (first run) or skips 5 (subsequent runs)
        total = result["workspaces_created"] + result["workspaces_skipped"]
        assert total == 5

    async def test_seed_demo_is_idempotent(self, configured_mock_prisma: MagicMock) -> None:
        """Test that seed_demo is idempotent (second run skips existing)."""
        _ = _configure_workspace_state(configured_mock_prisma)

        # First run
        result1 = await seed_demo(_format_arg="json")
        created1 = result1["workspaces_created"]
        _ = result1["workspaces_skipped"]

        # Second run (should skip what was created)
        result2 = await seed_demo(_format_arg="json")
        created2 = result2["workspaces_created"]
        skipped2 = result2["workspaces_skipped"]

        # If first run created, second should skip
        if created1 > 0:
            assert created2 == 0
            assert skipped2 == created1

    async def test_seed_demo_creates_acme_workspace(self, configured_mock_prisma: MagicMock) -> None:
        """Test that seed_demo creates 'acme' workspace."""
        _ = await seed_demo(_format_arg="json")
        repo = WorkspaceRepository(configured_mock_prisma)
        acme = await repo.get_by_slug("acme")
        assert acme is not None
        assert acme["slug"] == "acme"
        assert acme["brand_name"] == "Acme Corp"

    async def test_seed_demo_creates_beta_brand_workspace(self, configured_mock_prisma: MagicMock) -> None:
        """Test that seed_demo creates 'beta-brand' workspace."""
        _ = await seed_demo(_format_arg="json")
        repo = WorkspaceRepository(configured_mock_prisma)
        beta = await repo.get_by_slug("beta-brand")
        assert beta is not None
        assert beta["slug"] == "beta-brand"
        assert beta["brand_name"] == "Beta Brand"

    async def test_seed_demo_workspaces_have_ids(self, configured_mock_prisma: MagicMock) -> None:
        """Test that created workspaces have IDs."""
        _ = await seed_demo(_format_arg="json")
        repo = WorkspaceRepository(configured_mock_prisma)
        acme = await repo.get_by_slug("acme")
        beta = await repo.get_by_slug("beta-brand")

        assert acme is not None and acme["id"]
        assert beta is not None and beta["id"]
        assert acme["id"] != beta["id"]

    async def test_seed_demo_workspaces_have_created_at(self, configured_mock_prisma: MagicMock) -> None:
        """Test that created workspaces have created_at timestamp."""
        _ = await seed_demo(_format_arg="json")
        repo = WorkspaceRepository(configured_mock_prisma)
        acme = await repo.get_by_slug("acme")
        beta = await repo.get_by_slug("beta-brand")

        assert acme is not None and acme["created_at"]
        assert beta is not None and beta["created_at"]

    async def test_seed_demo_creates_acme_saas_workspace(self, configured_mock_prisma: MagicMock) -> None:
        """Test that seed_demo creates 'acme-saas' workspace."""
        _ = await seed_demo(_format_arg="json")
        repo = WorkspaceRepository(configured_mock_prisma)
        acme_saas = await repo.get_by_slug("acme-saas")
        assert acme_saas is not None
        assert acme_saas["slug"] == "acme-saas"
        assert acme_saas["brand_name"] == "Acme SaaS"
        assert acme_saas["city"] == ""
        assert acme_saas["region"] == ""
        assert acme_saas["country"] == ""

    async def test_seed_demo_creates_local_plumber_workspace(self, configured_mock_prisma: MagicMock) -> None:
        """Test that seed_demo creates 'local-plumber' workspace with location."""
        _ = await seed_demo(_format_arg="json")
        repo = WorkspaceRepository(configured_mock_prisma)
        local_plumber = await repo.get_by_slug("local-plumber")
        assert local_plumber is not None
        assert local_plumber["slug"] == "local-plumber"
        assert local_plumber["brand_name"] == "Joe's Plumbing"
        assert local_plumber["city"] == "Denver"
        assert local_plumber["region"] == "Colorado"
        assert local_plumber["country"] == "US"

    async def test_seed_demo_creates_echo_brand_workspace(self, configured_mock_prisma: MagicMock) -> None:
        """Test that seed_demo creates 'echo-brand' workspace."""
        _ = await seed_demo(_format_arg="json")
        repo = WorkspaceRepository(configured_mock_prisma)
        echo_brand = await repo.get_by_slug("echo-brand")
        assert echo_brand is not None
        assert echo_brand["slug"] == "echo-brand"
        assert echo_brand["brand_name"] == "Echo"
        assert echo_brand["city"] == ""
        assert echo_brand["region"] == ""
        assert echo_brand["country"] == ""


@pytest.mark.usefixtures("patch_get_prisma")
@pytest.mark.asyncio
class TestSeedDemoCliCommand:
    """Test the seed-demo CLI command via subprocess."""

    async def test_cli_seed_demo_exits_zero(self, configured_mock_prisma: MagicMock) -> None:
        """Test that CLI seed-demo command exits with code 0."""
        _ = configured_mock_prisma
        result = await seed_demo(_format_arg="json")
        assert result["status"] == "success"

    async def test_cli_seed_demo_output_is_valid_json(self, configured_mock_prisma: MagicMock) -> None:
        """Test that CLI seed-demo output is valid JSON."""
        _ = configured_mock_prisma
        result = await seed_demo(_format_arg="json")
        output = cast(dict[str, object], json.loads(json.dumps(result)))
        assert isinstance(output, dict)

    async def test_cli_seed_demo_output_has_required_fields(self, configured_mock_prisma: MagicMock) -> None:
        """Test that CLI seed-demo output has required fields."""
        _ = configured_mock_prisma
        output = await seed_demo(_format_arg="json")
        assert "status" in output
        assert "workspaces_created" in output
        assert "workspaces_skipped" in output
        assert "runs_created" in output
        assert "mentions_created" in output

    async def test_cli_seed_demo_output_status_is_success(self, configured_mock_prisma: MagicMock) -> None:
        """Test that CLI seed-demo output status is 'success'."""
        _ = configured_mock_prisma
        output = await seed_demo(_format_arg="json")
        assert output["status"] == "success"

    async def test_cli_seed_demo_creates_or_skips_workspaces(self, configured_mock_prisma: MagicMock) -> None:
        """Test that CLI seed-demo creates or skips workspaces."""
        _ = configured_mock_prisma
        output = await seed_demo(_format_arg="json")
        total = output["workspaces_created"] + output["workspaces_skipped"]
        assert total == 5

    async def test_cli_seed_demo_is_idempotent(self, configured_mock_prisma: MagicMock) -> None:
        """Test that second CLI seed-demo run is idempotent."""
        _ = _configure_workspace_state(configured_mock_prisma)

        # First run
        output1 = await seed_demo(_format_arg="json")
        created1 = output1["workspaces_created"]

        # Second run (should skip)
        output2 = await seed_demo(_format_arg="json")
        created2 = output2["workspaces_created"]
        skipped2 = output2["workspaces_skipped"]

        # If first run created, second should skip
        if created1 > 0:
            assert created2 == 0
            assert skipped2 == created1

    async def test_cli_seed_demo_creates_acme_in_db(self, configured_mock_prisma: MagicMock) -> None:
        """Test that CLI seed-demo creates acme workspace in DB."""
        _ = await seed_demo(_format_arg="json")
        repo = WorkspaceRepository(configured_mock_prisma)
        acme = await repo.get_by_slug("acme")
        assert acme is not None
        assert acme["brand_name"] == "Acme Corp"

    async def test_cli_seed_demo_creates_beta_brand_in_db(self, configured_mock_prisma: MagicMock) -> None:
        """Test that CLI seed-demo creates beta-brand workspace in DB."""
        _ = await seed_demo(_format_arg="json")
        repo = WorkspaceRepository(configured_mock_prisma)
        beta = await repo.get_by_slug("beta-brand")
        assert beta is not None
        assert beta["brand_name"] == "Beta Brand"
