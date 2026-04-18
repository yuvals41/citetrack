import sqlite3
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Literal, cast

import pytest

from ai_visibility.storage.repositories.mention_repo import MentionRepository
from ai_visibility.storage.repositories.metric_repo import MetricRepository
from ai_visibility.storage.repositories.run_repo import RunRepository
from ai_visibility.storage.repositories.workspace_repo import WorkspaceRepository
from ai_visibility.storage.types import MentionRecord, MetricSnapshotRecord, RunRecord, WorkspaceRecord


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _workspace_row(workspace: WorkspaceRecord) -> SimpleNamespace:
    return SimpleNamespace(
        id=workspace["id"],
        slug=workspace["slug"],
        brandName=workspace["brand_name"],
        city=workspace.get("city", ""),
        region=workspace.get("region", ""),
        country=workspace.get("country", ""),
        createdAt=_parse_iso(workspace["created_at"]),
    )


def _run_row(run: RunRecord) -> SimpleNamespace:
    return SimpleNamespace(
        id=run["id"],
        workspaceId=run["workspace_id"],
        provider=run["provider"],
        model=run["model"],
        promptVersion=run["prompt_version"],
        parserVersion=run["parser_version"],
        status=run["status"].upper(),
        createdAt=_parse_iso(run["created_at"]),
        rawResponse=run["raw_response"],
        error=run["error"],
    )


def _mention_row(mention: MentionRecord) -> SimpleNamespace:
    return SimpleNamespace(
        id=mention["id"],
        workspaceId=mention["workspace_id"],
        runId=mention["run_id"],
        brandId=mention["brand_id"],
        mentionType=mention["mention_type"],
        text=mention["text"],
        citationUrl=mention["citation"].get("url"),
        citationDomain=mention["citation"].get("domain"),
        citationStatus=str(mention["citation"]["status"]).upper(),
    )


def _metric_row(snapshot: MetricSnapshotRecord) -> SimpleNamespace:
    return SimpleNamespace(
        id=snapshot["id"],
        workspaceId=snapshot["workspace_id"],
        brandId=snapshot["brand_id"],
        formulaVersion=snapshot["formula_version"],
        visibilityScore=float(snapshot["visibility_score"]),
        citationCoverage=float(snapshot["citation_coverage"]),
        competitorWins=int(snapshot["competitor_wins"]),
        mentionCount=int(snapshot["mention_count"]),
        createdAt=_parse_iso(snapshot["created_at"]),
    )


@pytest.fixture
def seeded_repositories(mock_prisma):
    workspaces: dict[str, WorkspaceRecord] = {}
    schedules: dict[str, str] = {}
    runs: dict[str, RunRecord] = {}
    mentions: dict[str, MentionRecord] = {}
    snapshots: dict[str, MetricSnapshotRecord] = {}

    async def workspace_create(*, data):
        existing_slug = {workspace["slug"] for workspace in workspaces.values()}
        if data["id"] in workspaces or data["slug"] in existing_slug:
            raise sqlite3.IntegrityError("workspace already exists")
        workspaces[data["id"]] = {
            "id": data["id"],
            "slug": data["slug"],
            "brand_name": data["brandName"],
            "city": data.get("city", ""),
            "region": data.get("region", ""),
            "country": data.get("country", ""),
            "created_at": data["createdAt"].isoformat(),
            "scan_schedule": "daily",
        }
        return _workspace_row(cast(WorkspaceRecord, workspaces[data["id"]]))

    async def workspace_find_unique(*, where):
        if "slug" in where:
            for workspace in workspaces.values():
                if workspace["slug"] == where["slug"]:
                    return _workspace_row(cast(WorkspaceRecord, workspace))
            return None
        workspace_id = where.get("id")
        workspace = workspaces.get(workspace_id)
        return _workspace_row(cast(WorkspaceRecord, workspace)) if workspace else None

    async def workspace_find_many(*, order):
        _ = order
        ordered = sorted(workspaces.values(), key=lambda workspace: (workspace["created_at"], workspace["id"]))
        return [_workspace_row(cast(WorkspaceRecord, workspace)) for workspace in ordered]

    async def run_create(*, data):
        if data["id"] in runs:
            raise sqlite3.IntegrityError("run already exists")
        runs[data["id"]] = {
            "id": data["id"],
            "workspace_id": data["workspaceId"],
            "provider": data["provider"],
            "model": data["model"],
            "prompt_version": data["promptVersion"],
            "parser_version": data["parserVersion"],
            "status": str(data["status"]).lower(),
            "created_at": data["createdAt"].isoformat(),
            "raw_response": data["rawResponse"],
            "error": data["error"],
        }
        return _run_row(cast(RunRecord, runs[data["id"]]))

    async def run_find_many(*, where, order):
        _ = order
        workspace_runs = [run for run in runs.values() if run["workspace_id"] == where["workspaceId"]]
        workspace_runs.sort(key=lambda run: (run["created_at"], run["id"]), reverse=True)
        return [_run_row(cast(RunRecord, run)) for run in workspace_runs]

    async def run_find_first(*, where, order):
        listed = await run_find_many(where=where, order=order)
        return listed[0] if listed else None

    async def mention_create(*, data):
        mentions[data["id"]] = cast(
            MentionRecord,
            cast(
                object,
                {
                    "id": data["id"],
                    "workspace_id": data["workspaceId"],
                    "run_id": data["runId"],
                    "brand_id": data["brandId"],
                    "mention_type": data["mentionType"],
                    "text": data["text"],
                    "citation": {
                        "url": data["citationUrl"],
                        "domain": data["citationDomain"],
                        "status": str(data["citationStatus"]).lower(),
                    },
                },
            ),
        )
        return _mention_row(cast(MentionRecord, mentions[data["id"]]))

    async def mention_find_many(*, where, order):
        _ = order
        run_mentions = [mention for mention in mentions.values() if mention["run_id"] == where["runId"]]
        run_mentions.sort(key=lambda mention: mention["id"])
        return [_mention_row(cast(MentionRecord, mention)) for mention in run_mentions]

    async def metric_upsert(*, where, data):
        snapshot_id = where["id"]
        payload = data["update"] if snapshot_id in snapshots else data["create"]
        snapshots[snapshot_id] = {
            "id": snapshot_id,
            "workspace_id": payload["workspaceId"],
            "brand_id": payload["brandId"],
            "formula_version": payload["formulaVersion"],
            "visibility_score": float(payload["visibilityScore"]),
            "citation_coverage": float(payload["citationCoverage"]),
            "competitor_wins": int(payload["competitorWins"]),
            "mention_count": int(payload["mentionCount"]),
            "created_at": payload["createdAt"].isoformat(),
        }
        return _metric_row(cast(MetricSnapshotRecord, snapshots[snapshot_id]))

    async def metric_find_first(*, where, order, skip=0):
        _ = order
        workspace_snapshots = [
            snapshot for snapshot in snapshots.values() if snapshot["workspace_id"] == where["workspaceId"]
        ]
        workspace_snapshots.sort(key=lambda snapshot: (snapshot["created_at"], snapshot["id"]), reverse=True)
        if skip >= len(workspace_snapshots):
            return None
        return _metric_row(cast(MetricSnapshotRecord, workspace_snapshots[skip]))

    async def execute_raw(query, *args):
        if 'INSERT INTO "ai_vis_workspace_schedules"' in query:
            workspace_id, schedule = cast(tuple[str, str], args)
            schedules[workspace_id] = schedule
        return None

    async def query_raw(query, *args):
        if 'SELECT "scan_schedule" FROM "ai_vis_workspace_schedules"' in query:
            workspace_id = cast(str, args[0])
            if workspace_id in schedules:
                return [{"scan_schedule": schedules[workspace_id]}]
            return []
        if 'SELECT "workspace_id", "scan_schedule" FROM "ai_vis_workspace_schedules"' in query:
            return [
                {"workspace_id": workspace_id, "scan_schedule": schedule}
                for workspace_id, schedule in schedules.items()
            ]
        return []

    mock_prisma.aivisworkspace.create.side_effect = workspace_create
    mock_prisma.aivisworkspace.find_unique.side_effect = workspace_find_unique
    mock_prisma.aivisworkspace.find_many.side_effect = workspace_find_many

    mock_prisma.aivisrun.create.side_effect = run_create
    mock_prisma.aivisrun.find_many.side_effect = run_find_many
    mock_prisma.aivisrun.find_first.side_effect = run_find_first

    mock_prisma.aivismention.create.side_effect = mention_create
    mock_prisma.aivismention.find_many.side_effect = mention_find_many

    mock_prisma.aivismetricsnapshot.upsert.side_effect = metric_upsert
    mock_prisma.aivismetricsnapshot.find_first.side_effect = metric_find_first

    mock_prisma.execute_raw.side_effect = execute_raw
    mock_prisma.query_raw.side_effect = query_raw

    return {
        "workspace_repo": WorkspaceRepository(mock_prisma),
        "run_repo": RunRepository(mock_prisma),
        "mention_repo": MentionRepository(mock_prisma),
        "metric_repo": MetricRepository(mock_prisma),
        "mentions": mentions,
    }


def make_workspace(*, workspace_id: str, slug: str, created_at: str, brand_name: str = "Acme") -> WorkspaceRecord:
    return {
        "id": workspace_id,
        "slug": slug,
        "brand_name": brand_name,
        "city": "",
        "region": "",
        "country": "",
        "created_at": created_at,
        "scan_schedule": "daily",
    }


def make_run(
    *,
    run_id: str,
    workspace_id: str,
    created_at: str,
    status: str = "completed",
    provider: str = "openai",
    model: str = "gpt-4.1",
    prompt_version: str = "1.0.0",
    parser_version: str = "1.0.0",
    raw_response: str | None = "raw",
    error: str | None = None,
) -> RunRecord:
    return {
        "id": run_id,
        "workspace_id": workspace_id,
        "provider": provider,
        "model": model,
        "prompt_version": prompt_version,
        "parser_version": parser_version,
        "status": status,
        "created_at": created_at,
        "raw_response": raw_response,
        "error": error,
    }


def make_mention(
    *,
    mention_id: str,
    workspace_id: str,
    run_id: str,
    mention_type: str,
    text: str,
    citation_status: Literal["found", "no_citation"],
    citation_url: str | None = None,
    citation_domain: str | None = None,
    brand_id: str = "brand_1",
) -> MentionRecord:
    return {
        "id": mention_id,
        "workspace_id": workspace_id,
        "run_id": run_id,
        "brand_id": brand_id,
        "mention_type": mention_type,
        "text": text,
        "citation": {
            "url": citation_url,
            "domain": citation_domain,
            "status": citation_status,
        },
    }


@pytest.mark.asyncio
async def test_workspace_create_returns_all_fields(tmp_path: Path, seeded_repositories) -> None:
    _ = tmp_path
    repo = seeded_repositories["workspace_repo"]
    workspace = make_workspace(
        workspace_id="ws_1", slug="solara", created_at="2026-03-10T10:00:00", brand_name="Solara"
    )

    created = await repo.create(workspace)

    assert created == workspace
    assert await repo.get_by_slug("solara") == workspace


@pytest.mark.asyncio
async def test_workspace_create_duplicate_slug_raises_integrity_error(tmp_path: Path, seeded_repositories) -> None:
    _ = tmp_path
    repo = seeded_repositories["workspace_repo"]
    first = make_workspace(workspace_id="ws_1", slug="solara", created_at="2026-03-10T10:00:00")
    second = make_workspace(workspace_id="ws_2", slug="solara", created_at="2026-03-10T11:00:00")
    _ = await repo.create(first)

    with pytest.raises(sqlite3.IntegrityError):
        _ = await repo.create(second)


@pytest.mark.asyncio
async def test_workspace_get_by_slug_nonexistent_returns_none(tmp_path: Path, seeded_repositories) -> None:
    _ = tmp_path
    repo = seeded_repositories["workspace_repo"]
    assert await repo.get_by_slug("does-not-exist") is None


@pytest.mark.asyncio
async def test_workspace_list_all_empty_returns_empty_list(tmp_path: Path, seeded_repositories) -> None:
    _ = tmp_path
    repo = seeded_repositories["workspace_repo"]
    assert await repo.list_all() == []


@pytest.mark.asyncio
async def test_workspace_list_all_orders_by_created_at_ascending(tmp_path: Path, seeded_repositories) -> None:
    _ = tmp_path
    repo = seeded_repositories["workspace_repo"]
    newest = make_workspace(workspace_id="ws_new", slug="new", created_at="2026-03-10T12:00:00")
    oldest = make_workspace(workspace_id="ws_old", slug="old", created_at="2026-03-10T09:00:00")
    middle = make_workspace(workspace_id="ws_mid", slug="mid", created_at="2026-03-10T11:00:00")

    _ = await repo.create(newest)
    _ = await repo.create(oldest)
    _ = await repo.create(middle)

    workspaces = await repo.list_all()
    assert [workspace["id"] for workspace in workspaces] == ["ws_old", "ws_mid", "ws_new"]


@pytest.mark.asyncio
async def test_workspace_create_multiple_and_list_all_contains_all(tmp_path: Path, seeded_repositories) -> None:
    _ = tmp_path
    repo = seeded_repositories["workspace_repo"]
    expected = [
        make_workspace(workspace_id="ws_1", slug="acme", created_at="2026-03-10T10:00:00"),
        make_workspace(workspace_id="ws_2", slug="globex", created_at="2026-03-10T11:00:00", brand_name="Globex"),
        make_workspace(workspace_id="ws_3", slug="initech", created_at="2026-03-10T12:00:00", brand_name="Initech"),
    ]
    for workspace in expected:
        _ = await repo.create(workspace)

    assert await repo.list_all() == expected


@pytest.mark.asyncio
async def test_run_create_returns_true(tmp_path: Path, seeded_repositories) -> None:
    _ = tmp_path
    workspace_repo = seeded_repositories["workspace_repo"]
    run_repo = seeded_repositories["run_repo"]
    _ = await workspace_repo.create(make_workspace(workspace_id="ws_1", slug="acme", created_at="2026-03-10T10:00:00"))

    created = await run_repo.create(make_run(run_id="run_1", workspace_id="ws_1", created_at="2026-03-10T11:00:00"))
    assert created is True


@pytest.mark.asyncio
async def test_run_create_duplicate_id_raises_integrity_error(tmp_path: Path, seeded_repositories) -> None:
    _ = tmp_path
    workspace_repo = seeded_repositories["workspace_repo"]
    run_repo = seeded_repositories["run_repo"]
    _ = await workspace_repo.create(make_workspace(workspace_id="ws_1", slug="acme", created_at="2026-03-10T10:00:00"))

    first = await run_repo.create(make_run(run_id="run_1", workspace_id="ws_1", created_at="2026-03-10T11:00:00"))
    assert first is True

    with pytest.raises(sqlite3.IntegrityError):
        _ = await run_repo.create(
            make_run(run_id="run_1", workspace_id="ws_1", created_at="2026-03-10T12:00:00", provider="anthropic")
        )
    assert len(await run_repo.list_by_workspace("ws_1")) == 1


@pytest.mark.asyncio
async def test_run_list_by_workspace_wrong_workspace_returns_empty_list(tmp_path: Path, seeded_repositories) -> None:
    _ = tmp_path
    workspace_repo = seeded_repositories["workspace_repo"]
    run_repo = seeded_repositories["run_repo"]
    _ = await workspace_repo.create(make_workspace(workspace_id="ws_1", slug="acme", created_at="2026-03-10T10:00:00"))
    _ = await run_repo.create(make_run(run_id="run_1", workspace_id="ws_1", created_at="2026-03-10T11:00:00"))

    assert await run_repo.list_by_workspace("ws_unknown") == []


@pytest.mark.asyncio
async def test_run_list_by_workspace_orders_by_created_at_desc(tmp_path: Path, seeded_repositories) -> None:
    _ = tmp_path
    workspace_repo = seeded_repositories["workspace_repo"]
    run_repo = seeded_repositories["run_repo"]
    _ = await workspace_repo.create(make_workspace(workspace_id="ws_1", slug="acme", created_at="2026-03-10T10:00:00"))
    _ = await run_repo.create(make_run(run_id="run_old", workspace_id="ws_1", created_at="2026-03-10T10:00:00"))
    _ = await run_repo.create(make_run(run_id="run_new", workspace_id="ws_1", created_at="2026-03-10T12:00:00"))
    _ = await run_repo.create(make_run(run_id="run_mid", workspace_id="ws_1", created_at="2026-03-10T11:00:00"))

    runs = await run_repo.list_by_workspace("ws_1")
    assert [run["id"] for run in runs] == ["run_new", "run_mid", "run_old"]


@pytest.mark.asyncio
async def test_run_get_latest_with_no_runs_returns_none(tmp_path: Path, seeded_repositories) -> None:
    _ = tmp_path
    workspace_repo = seeded_repositories["workspace_repo"]
    run_repo = seeded_repositories["run_repo"]
    _ = await workspace_repo.create(make_workspace(workspace_id="ws_1", slug="acme", created_at="2026-03-10T10:00:00"))

    assert await run_repo.get_latest_by_workspace("ws_1") is None


@pytest.mark.asyncio
async def test_run_get_latest_returns_most_recent(tmp_path: Path, seeded_repositories) -> None:
    _ = tmp_path
    workspace_repo = seeded_repositories["workspace_repo"]
    run_repo = seeded_repositories["run_repo"]
    _ = await workspace_repo.create(make_workspace(workspace_id="ws_1", slug="acme", created_at="2026-03-10T10:00:00"))
    old = make_run(run_id="run_old", workspace_id="ws_1", created_at="2026-03-10T10:00:00")
    latest = make_run(run_id="run_latest", workspace_id="ws_1", created_at="2026-03-10T13:00:00")
    _ = await run_repo.create(old)
    _ = await run_repo.create(latest)

    assert await run_repo.get_latest_by_workspace("ws_1") == latest


@pytest.mark.asyncio
async def test_run_create_with_nonexistent_workspace_raises_error(tmp_path: Path, seeded_repositories) -> None:
    _ = tmp_path
    run_repo = seeded_repositories["run_repo"]

    with pytest.raises(ValueError):
        _ = await run_repo.create(make_run(run_id="run_1", workspace_id="missing_ws", created_at="2026-03-10T11:00:00"))


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["completed", "failed", "completed_with_partial_failures"])
async def test_run_create_supports_all_status_values(tmp_path: Path, seeded_repositories, status: str) -> None:
    _ = tmp_path
    workspace_repo = seeded_repositories["workspace_repo"]
    run_repo = seeded_repositories["run_repo"]
    _ = await workspace_repo.create(make_workspace(workspace_id="ws_1", slug="acme", created_at="2026-03-10T10:00:00"))
    run = make_run(
        run_id=f"run_{status}",
        workspace_id="ws_1",
        created_at="2026-03-10T11:00:00",
        status=status,
        error="boom" if status == "failed" else None,
    )

    assert await run_repo.create(run) is True
    latest = await run_repo.get_latest_by_workspace("ws_1")
    assert latest is not None
    assert latest["status"] == status


@pytest.mark.asyncio
async def test_mention_create_bulk_empty_list_no_crash(tmp_path: Path, seeded_repositories) -> None:
    _ = tmp_path
    repo = seeded_repositories["mention_repo"]

    await repo.create_bulk([])
    assert await repo.list_by_run("run_1") == []


@pytest.mark.asyncio
async def test_mention_create_bulk_with_citations_and_no_citation(tmp_path: Path, seeded_repositories) -> None:
    _ = tmp_path
    workspace_repo = seeded_repositories["workspace_repo"]
    run_repo = seeded_repositories["run_repo"]
    mention_repo = seeded_repositories["mention_repo"]
    _ = await workspace_repo.create(make_workspace(workspace_id="ws_1", slug="acme", created_at="2026-03-10T10:00:00"))
    _ = await run_repo.create(make_run(run_id="run_1", workspace_id="ws_1", created_at="2026-03-10T11:00:00"))
    mentions = [
        make_mention(
            mention_id="m1",
            workspace_id="ws_1",
            run_id="run_1",
            mention_type="explicit",
            text="Acme is best",
            citation_status="found",
            citation_url="https://example.com/a",
            citation_domain="example.com",
        ),
        make_mention(
            mention_id="m2",
            workspace_id="ws_1",
            run_id="run_1",
            mention_type="citation",
            text="Mention without url",
            citation_status="no_citation",
        ),
    ]

    await mention_repo.create_bulk(mentions)
    assert await mention_repo.list_by_run("run_1") == mentions


@pytest.mark.asyncio
async def test_mention_list_by_run_nonexistent_returns_empty(tmp_path: Path, seeded_repositories) -> None:
    _ = tmp_path
    workspace_repo = seeded_repositories["workspace_repo"]
    run_repo = seeded_repositories["run_repo"]
    mention_repo = seeded_repositories["mention_repo"]
    _ = await workspace_repo.create(make_workspace(workspace_id="ws_1", slug="acme", created_at="2026-03-10T10:00:00"))
    _ = await run_repo.create(make_run(run_id="run_1", workspace_id="ws_1", created_at="2026-03-10T11:00:00"))

    assert await mention_repo.list_by_run("run_missing") == []


@pytest.mark.asyncio
async def test_mention_citation_join_returns_correct_fields(tmp_path: Path, seeded_repositories) -> None:
    _ = tmp_path
    workspace_repo = seeded_repositories["workspace_repo"]
    run_repo = seeded_repositories["run_repo"]
    mention_repo = seeded_repositories["mention_repo"]
    _ = await workspace_repo.create(make_workspace(workspace_id="ws_1", slug="acme", created_at="2026-03-10T10:00:00"))
    _ = await run_repo.create(make_run(run_id="run_1", workspace_id="ws_1", created_at="2026-03-10T11:00:00"))
    mention = make_mention(
        mention_id="m_join",
        workspace_id="ws_1",
        run_id="run_1",
        mention_type="explicit",
        text="Deep join payload",
        citation_status="found",
        citation_url="https://docs.solara.ai/path?x=1#frag",
        citation_domain="docs.solara.ai",
        brand_id="brand_xyz",
    )

    await mention_repo.create_bulk([mention])
    fetched = await mention_repo.list_by_run("run_1")
    assert len(fetched) == 1
    assert fetched[0]["id"] == "m_join"
    assert fetched[0]["workspace_id"] == "ws_1"
    assert fetched[0]["run_id"] == "run_1"
    assert fetched[0]["brand_id"] == "brand_xyz"
    assert fetched[0]["mention_type"] == "explicit"
    assert fetched[0]["text"] == "Deep join payload"
    assert fetched[0]["citation"]["url"] == "https://docs.solara.ai/path?x=1#frag"
    assert fetched[0]["citation"]["domain"] == "docs.solara.ai"
    assert fetched[0]["citation"]["status"] == "found"


@pytest.mark.asyncio
async def test_mention_create_bulk_inserts_citation_fields_into_mentions_table(
    tmp_path: Path, seeded_repositories
) -> None:
    _ = tmp_path
    workspace_repo = seeded_repositories["workspace_repo"]
    run_repo = seeded_repositories["run_repo"]
    mention_repo = seeded_repositories["mention_repo"]
    mentions_state = seeded_repositories["mentions"]
    _ = await workspace_repo.create(make_workspace(workspace_id="ws_1", slug="acme", created_at="2026-03-10T10:00:00"))
    _ = await run_repo.create(make_run(run_id="run_1", workspace_id="ws_1", created_at="2026-03-10T11:00:00"))
    mentions = [
        make_mention(
            mention_id="m1",
            workspace_id="ws_1",
            run_id="run_1",
            mention_type="explicit",
            text="one",
            citation_status="found",
            citation_url="https://example.com/one",
            citation_domain="example.com",
        ),
        make_mention(
            mention_id="m2",
            workspace_id="ws_1",
            run_id="run_1",
            mention_type="absent",
            text="two",
            citation_status="no_citation",
        ),
    ]

    await mention_repo.create_bulk(mentions)
    mention_count = len(mentions_state)
    citation_count = sum(
        1 for mention in mentions_state.values() if mention["citation"]["status"] in {"found", "no_citation"}
    )
    assert mention_count == 2
    assert citation_count == 2


@pytest.mark.asyncio
async def test_mention_types_explicit_absent_and_citation_are_preserved(tmp_path: Path, seeded_repositories) -> None:
    _ = tmp_path
    workspace_repo = seeded_repositories["workspace_repo"]
    run_repo = seeded_repositories["run_repo"]
    mention_repo = seeded_repositories["mention_repo"]
    _ = await workspace_repo.create(make_workspace(workspace_id="ws_1", slug="acme", created_at="2026-03-10T10:00:00"))
    _ = await run_repo.create(make_run(run_id="run_1", workspace_id="ws_1", created_at="2026-03-10T11:00:00"))
    mentions = [
        make_mention(
            mention_id="m_explicit",
            workspace_id="ws_1",
            run_id="run_1",
            mention_type="explicit",
            text="explicit mention",
            citation_status="found",
            citation_url="https://example.com",
            citation_domain="example.com",
        ),
        make_mention(
            mention_id="m_absent",
            workspace_id="ws_1",
            run_id="run_1",
            mention_type="absent",
            text="absent mention",
            citation_status="no_citation",
        ),
        make_mention(
            mention_id="m_citation",
            workspace_id="ws_1",
            run_id="run_1",
            mention_type="citation",
            text="citation mention",
            citation_status="found",
            citation_url="https://example.com/citation",
            citation_domain="example.com",
        ),
    ]

    await mention_repo.create_bulk(mentions)
    fetched = await mention_repo.list_by_run("run_1")
    mention_types_by_id = {mention["id"]: mention["mention_type"] for mention in fetched}
    assert mention_types_by_id == {
        "m_explicit": "explicit",
        "m_absent": "absent",
        "m_citation": "citation",
    }


@pytest.mark.asyncio
async def test_metric_upsert_snapshot_creates_new_record(tmp_path: Path, seeded_repositories) -> None:
    _ = tmp_path
    workspace_repo = seeded_repositories["workspace_repo"]
    metric_repo = seeded_repositories["metric_repo"]
    _ = await workspace_repo.create(make_workspace(workspace_id="ws_1", slug="acme", created_at="2026-03-10T10:00:00"))
    snapshot = {
        "id": "metric_1",
        "workspace_id": "ws_1",
        "brand_id": "brand_1",
        "formula_version": "1.0.0",
        "visibility_score": 0.75,
        "citation_coverage": 0.0,
        "mention_count": 3,
        "competitor_wins": 0,
        "created_at": "2026-03-10T12:00:00",
    }

    created = await metric_repo.upsert_snapshot(cast(MetricSnapshotRecord, cast(object, snapshot)))
    assert created == snapshot
    assert await metric_repo.get_latest_by_workspace("ws_1") == snapshot


@pytest.mark.asyncio
async def test_metric_upsert_snapshot_updates_existing_same_id(tmp_path: Path, seeded_repositories) -> None:
    _ = tmp_path
    workspace_repo = seeded_repositories["workspace_repo"]
    metric_repo = seeded_repositories["metric_repo"]
    _ = await workspace_repo.create(make_workspace(workspace_id="ws_1", slug="acme", created_at="2026-03-10T10:00:00"))
    _ = await metric_repo.upsert_snapshot(
        {
            "id": "metric_1",
            "workspace_id": "ws_1",
            "brand_id": "brand_1",
            "formula_version": "1.0.0",
            "visibility_score": 0.60,
            "citation_coverage": 0.0,
            "mention_count": 2,
            "competitor_wins": 0,
            "created_at": "2026-03-10T11:00:00",
        }
    )
    updated = {
        "id": "metric_1",
        "workspace_id": "ws_1",
        "brand_id": "brand_1",
        "formula_version": "2.0.0",
        "visibility_score": 0.95,
        "citation_coverage": 0.42,
        "mention_count": 9,
        "competitor_wins": 0,
        "created_at": "2026-03-10T15:00:00",
    }

    _ = await metric_repo.upsert_snapshot(cast(MetricSnapshotRecord, cast(object, updated)))
    assert await metric_repo.get_latest_by_workspace("ws_1") == updated


@pytest.mark.asyncio
async def test_metric_get_latest_with_no_snapshots_returns_none(tmp_path: Path, seeded_repositories) -> None:
    _ = tmp_path
    workspace_repo = seeded_repositories["workspace_repo"]
    metric_repo = seeded_repositories["metric_repo"]
    _ = await workspace_repo.create(make_workspace(workspace_id="ws_1", slug="acme", created_at="2026-03-10T10:00:00"))

    assert await metric_repo.get_latest_by_workspace("ws_1") is None


@pytest.mark.asyncio
async def test_metric_get_latest_scoped_by_workspace_when_multiple_workspaces_exist(
    tmp_path: Path, seeded_repositories
) -> None:
    _ = tmp_path
    workspace_repo = seeded_repositories["workspace_repo"]
    metric_repo = seeded_repositories["metric_repo"]
    _ = await workspace_repo.create(make_workspace(workspace_id="ws_1", slug="acme", created_at="2026-03-10T10:00:00"))
    _ = await workspace_repo.create(
        make_workspace(workspace_id="ws_2", slug="globex", created_at="2026-03-10T10:05:00")
    )
    _ = await metric_repo.upsert_snapshot(
        {
            "id": "metric_1",
            "workspace_id": "ws_1",
            "brand_id": "brand_a",
            "formula_version": "1.0.0",
            "visibility_score": 0.10,
            "citation_coverage": 0.0,
            "mention_count": 1,
            "competitor_wins": 0,
            "created_at": "2026-03-10T11:00:00",
        }
    )
    ws2_latest = {
        "id": "metric_2",
        "workspace_id": "ws_2",
        "brand_id": "brand_b",
        "formula_version": "1.0.0",
        "visibility_score": 0.88,
        "citation_coverage": 0.63,
        "mention_count": 8,
        "competitor_wins": 0,
        "created_at": "2026-03-10T12:00:00",
    }
    _ = await metric_repo.upsert_snapshot(cast(MetricSnapshotRecord, cast(object, ws2_latest)))

    assert await metric_repo.get_latest_by_workspace("ws_2") == ws2_latest
    ws1_latest = await metric_repo.get_latest_by_workspace("ws_1")
    assert ws1_latest is not None
    assert ws1_latest["workspace_id"] == "ws_1"
