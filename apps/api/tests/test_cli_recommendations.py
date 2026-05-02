from datetime import datetime, timezone
from typing import Literal, cast
from unittest.mock import MagicMock

import pytest

from ai_visibility import cli
from ai_visibility.storage.repositories import MentionRepository, RunRepository, WorkspaceRepository
from ai_visibility.storage.types import MentionRecord, RunRecord, WorkspaceRecord


async def _seed_workspace_and_run(mock_prisma: MagicMock) -> str:
    workspace_repo = WorkspaceRepository(mock_prisma)
    run_repo = RunRepository(mock_prisma)

    workspace_row = MagicMock(
        id="ws_1",
        slug="acme",
        brandName="Acme",
        city="",
        region="",
        country="",
        createdAt=datetime(2026, 3, 13, 10, 0, 0, tzinfo=timezone.utc),
    )
    mock_prisma.workspace.create.return_value = workspace_row  # pyright: ignore[reportAny]
    mock_prisma.workspace.find_unique.return_value = workspace_row  # pyright: ignore[reportAny]

    workspace: WorkspaceRecord = {
        "id": "ws_1",
        "slug": "acme",
        "brand_name": "Acme",
        "city": "",
        "region": "",
        "country": "",
        "created_at": "2026-03-13T10:00:00",
    }
    _ = await workspace_repo.create(workspace)

    run_row = MagicMock(
        id="run_1",
        workspaceId="ws_1",
        provider="openai",
        model="gpt-4.1",
        promptVersion="1.0.0",
        parserVersion="parser-v1",
        status="COMPLETED",
        createdAt=datetime(2026, 3, 13, 11, 0, 0, tzinfo=timezone.utc),
        rawResponse="raw",
        error=None,
    )
    mock_prisma.run.find_many.return_value = [run_row]  # pyright: ignore[reportAny]

    run: RunRecord = {
        "id": "run_1",
        "workspace_id": "ws_1",
        "provider": "openai",
        "model": "gpt-4.1",
        "prompt_version": "1.0.0",
        "parser_version": "parser-v1",
        "status": "completed",
        "created_at": "2026-03-13T11:00:00",
        "raw_response": "raw",
        "error": None,
    }
    _ = await run_repo.create(run)
    return run["id"]


async def _create_mentions(
    mock_prisma: MagicMock,
    run_id: str,
    mentions: list[tuple[str, Literal["found", "no_citation"]]],
) -> None:
    mention_repo = MentionRepository(mock_prisma)
    payload: list[MentionRecord] = []
    mention_rows: list[MagicMock] = []
    for index, (mention_type, citation_status) in enumerate(mentions, start=1):
        payload.append(
            {
                "id": f"mention_{index}",
                "workspace_id": "ws_1",
                "run_id": run_id,
                "brand_id": "brand_1",
                "mention_type": mention_type,
                "text": f"mention {index}",
                "citation": {
                    "url": "https://example.com" if citation_status == "found" else None,
                    "domain": "example.com" if citation_status == "found" else None,
                    "status": citation_status,
                },
            }
        )
        mention_rows.append(
            MagicMock(
                id=f"mention_{index}",
                workspaceId="ws_1",
                runId=run_id,
                brandId="brand_1",
                mentionType=mention_type,
                text=f"mention {index}",
                citationUrl="https://example.com" if citation_status == "found" else None,
                citationDomain="example.com" if citation_status == "found" else None,
                citationStatus=citation_status.upper(),
            )
        )

    mock_prisma.mention.find_many.return_value = mention_rows  # pyright: ignore[reportAny]
    await mention_repo.create_bulk(payload)


def _capture_runs(monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    captured: dict[str, object] = {}

    class FakeRecommendationsEngine:
        def generate(self, workspace_slug: str, runs: list[dict[str, object]]) -> list[object]:
            captured["workspace_slug"] = workspace_slug
            captured["runs"] = runs
            return []

    monkeypatch.setattr(cli, "RecommendationsEngine", FakeRecommendationsEngine)
    return captured


@pytest.mark.asyncio
async def test_recommend_latest_uses_explicit_mentions_for_visibility_score(
    monkeypatch: pytest.MonkeyPatch,
    mock_prisma: MagicMock,
    patch_get_prisma: MagicMock,
) -> None:
    _ = patch_get_prisma
    run_id = await _seed_workspace_and_run(mock_prisma)
    await _create_mentions(mock_prisma, run_id, [("explicit", "found"), ("absent", "no_citation")])
    captured = _capture_runs(monkeypatch)

    result = await cli.recommend_latest(workspace="acme")

    assert "degraded" not in result
    runs = cast(list[dict[str, object]], captured["runs"])
    assert float(cast(float, runs[0]["visibility_score"])) == 0.5
    assert float(cast(float, runs[0]["visibility_score"])) > 0.0


@pytest.mark.asyncio
async def test_recommend_latest_absent_mentions_produce_zero_visibility(
    monkeypatch: pytest.MonkeyPatch,
    mock_prisma: MagicMock,
    patch_get_prisma: MagicMock,
) -> None:
    _ = patch_get_prisma
    run_id = await _seed_workspace_and_run(mock_prisma)
    await _create_mentions(mock_prisma, run_id, [("absent", "no_citation"), ("absent", "no_citation")])
    captured = _capture_runs(monkeypatch)

    result = await cli.recommend_latest(workspace="acme")

    assert "degraded" not in result
    runs = cast(list[dict[str, object]], captured["runs"])
    assert float(cast(float, runs[0]["visibility_score"])) == 0.0


@pytest.mark.asyncio
async def test_recommend_latest_mixed_mentions_compute_expected_ratio(
    monkeypatch: pytest.MonkeyPatch,
    mock_prisma: MagicMock,
    patch_get_prisma: MagicMock,
) -> None:
    _ = patch_get_prisma
    run_id = await _seed_workspace_and_run(mock_prisma)
    await _create_mentions(
        mock_prisma, run_id, [("explicit", "found"), ("absent", "no_citation"), ("citation", "found")]
    )
    captured = _capture_runs(monkeypatch)

    result = await cli.recommend_latest(workspace="acme")

    assert "degraded" not in result
    runs = cast(list[dict[str, object]], captured["runs"])
    score = float(cast(float, runs[0]["visibility_score"]))
    assert abs(score - (1 / 3)) < 1e-9


@pytest.mark.asyncio
async def test_recommend_latest_handles_empty_mentions_without_crash(
    monkeypatch: pytest.MonkeyPatch,
    mock_prisma: MagicMock,
    patch_get_prisma: MagicMock,
) -> None:
    _ = patch_get_prisma
    _ = await _seed_workspace_and_run(mock_prisma)
    _ = _capture_runs(monkeypatch)

    result = await cli.recommend_latest(workspace="acme")

    assert "degraded" not in result
    payload = cast(dict[str, object], cast(object, result))
    assert payload["workspace"] == "acme"
    assert isinstance(payload["recommendations"], list)
