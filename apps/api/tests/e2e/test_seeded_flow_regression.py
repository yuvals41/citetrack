from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import cast
from unittest.mock import AsyncMock, patch

import pytest
from starlette.testclient import TestClient

from ai_visibility.api.routes import create_app
from ai_visibility.cli import recommend_latest, seed_demo
from ai_visibility.providers.gateway import ProviderResponse
from ai_visibility.metrics.engine import MetricsEngine
from ai_visibility.extraction.pipeline import ExtractionPipeline
from ai_visibility.runs.orchestrator import RunOrchestrator
from ai_visibility.storage.database import Database
from ai_visibility.storage.repositories.mention_repo import MentionRepository
from ai_visibility.storage.repositories.metric_repo import MetricRepository
from ai_visibility.storage.repositories.run_repo import RunRepository
from ai_visibility.storage.repositories.workspace_repo import WorkspaceRepository
from ai_visibility.storage.types import MetricSnapshotRecord, WorkspaceRecord


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _make_workspace(db_path: str, slug: str, brand_name: str) -> WorkspaceRecord:
    repo = WorkspaceRepository(db_path=db_path)
    record: WorkspaceRecord = {
        "id": str(uuid.uuid4()),
        "slug": slug,
        "brand_name": brand_name,
        "city": "",
        "region": "",
        "country": "",
        "created_at": _utc_now(),
    }
    return repo.create(record)


def _store_metric(db_path: str, workspace_id: str, run_id: str, brand_name: str) -> None:
    run_repo = RunRepository(db_path=db_path)
    metric_repo = MetricRepository(db_path=db_path)
    runs = run_repo.list_by_workspace(workspace_id)
    run_record = next(r for r in runs if r["id"] == run_id)

    parsed = ExtractionPipeline(brand_names=[brand_name]).extract(run_record["raw_response"] or "")
    snapshot = MetricsEngine().compute(
        workspace_id=workspace_id,
        run_id=run_id,
        mentions=parsed.mentions,
        citations=parsed.citations,
        prompt_version=run_record["prompt_version"],
        model=run_record["model"],
    )

    stored = cast(
        MetricSnapshotRecord,
        cast(
            object,
            {
                "id": str(uuid.uuid4()),
                "workspace_id": workspace_id,
                "brand_id": brand_name,
                "formula_version": snapshot.formula_version,
                "visibility_score": snapshot.visibility_score,
                "mention_count": snapshot.mentioned_count,
                "created_at": _utc_now(),
            },
        ),
    )
    metric_repo.upsert_snapshot(stored)


@pytest.fixture
def db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    path = tmp_path / "seeded_flow.db"
    monkeypatch.setenv("DB_PATH", str(path))
    Database(db_path=str(path)).initialize()
    return str(path)


def test_seeded_flow_seed_to_dashboard_snapshot(db_path: str) -> None:
    seed_result = seed_demo()
    assert seed_result["status"] == "success"
    assert seed_result["workspaces_created"] >= 1

    workspace_repo = WorkspaceRepository(db_path=db_path)
    acme = workspace_repo.get_by_slug("acme")
    assert acme is not None, "seed-demo must create 'acme' workspace"

    client = TestClient(create_app())

    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    workspaces = client.get("/api/v1/workspaces")
    assert workspaces.status_code == 200
    slugs = [item["slug"] for item in workspaces.json()["items"]]
    assert "acme" in slugs


def test_seeded_flow_scan_produces_diagnosis_and_recommendations(db_path: str) -> None:
    workspace = _make_workspace(db_path, slug="diag-brand", brand_name="DiagBrand")

    response = ProviderResponse(
        provider="openai",
        model="gpt-4",
        content=(
            "DiagBrand is a well-known analytics platform used by enterprise teams. "
            "See https://diagbrand.com/features for the product overview and "
            "https://example.com/review for third-party analysis."
        ),
        latency_ms=120,
        token_count=45,
    )

    with patch(
        "ai_visibility.providers.gateway.ProviderGateway.execute_prompt",
        new_callable=AsyncMock,
        return_value=response,
    ):
        result = RunOrchestrator(
            workspace_slug="diag-brand",
            provider="openai",
            model="gpt-4",
            brand_names=["DiagBrand"],
        ).scan()

    assert result.status in {"completed", "completed_with_partial_failures"}
    assert result.run_id

    run_repo = RunRepository(db_path=db_path)
    mention_repo = MentionRepository(db_path=db_path)

    runs = run_repo.list_by_workspace(workspace["id"])
    assert len(runs) >= 1

    mentions = mention_repo.list_by_run(result.run_id)
    assert mentions, "scan must produce at least one mention"

    _store_metric(db_path, workspace["id"], result.run_id, "DiagBrand")

    metric_repo = MetricRepository(db_path=db_path)
    stored = metric_repo.get_latest_by_workspace(workspace["id"])
    assert stored is not None
    assert 0.0 <= float(stored["visibility_score"]) <= 1.0

    recs = recommend_latest(workspace="diag-brand")
    assert "degraded" not in recs
    assert recs["workspace"] == "diag-brand"
    assert isinstance(recs["recommendations"], list)


def test_seeded_flow_full_pipeline_scan_to_api_snapshot(db_path: str) -> None:
    workspace = _make_workspace(db_path, slug="snap-brand", brand_name="SnapBrand")

    response = ProviderResponse(
        provider="openai",
        model="gpt-4",
        content=(
            "SnapBrand leads the market in real-time analytics with strong customer reviews. "
            "Reference: https://snapbrand.com/case-studies and https://techreview.example.com/snap."
        ),
        latency_ms=95,
        token_count=38,
    )

    with patch(
        "ai_visibility.providers.gateway.ProviderGateway.execute_prompt",
        new_callable=AsyncMock,
        return_value=response,
    ):
        result = RunOrchestrator(
            workspace_slug="snap-brand",
            provider="openai",
            model="gpt-4",
            brand_names=["SnapBrand"],
        ).scan()

    assert result.status in {"completed", "completed_with_partial_failures"}

    _store_metric(db_path, workspace["id"], result.run_id, "SnapBrand")

    client = TestClient(create_app())

    overview = client.get("/api/v1/snapshot/overview?workspace=snap-brand")
    assert overview.status_code == 200
    overview_data = overview.json()
    assert "degraded" not in overview_data or overview_data.get("degraded", {}).get("recoverable") is True

    trend = client.get("/api/v1/snapshot/trend?workspace=snap-brand")
    assert trend.status_code == 200

    findings = client.get("/api/v1/snapshot/findings?workspace=snap-brand")
    assert findings.status_code == 200

    actions = client.get("/api/v1/snapshot/actions?workspace=snap-brand")
    assert actions.status_code == 200


def test_seeded_flow_completed_with_partial_failures_status_is_correct(db_path: str) -> None:
    _make_workspace(db_path, slug="partial-brand", brand_name="PartialBrand")

    ok_response = ProviderResponse(
        provider="openai",
        model="gpt-4",
        content=(
            "PartialBrand is referenced in this response with enough context for extraction. "
            "Source: https://example.com/partial-context."
        ),
        latency_ms=80,
    )

    from ai_visibility.providers.gateway import ProviderError

    with patch(
        "ai_visibility.providers.gateway.ProviderGateway.execute_prompt",
        new_callable=AsyncMock,
        side_effect=[ok_response, ProviderError("provider down", error_code="provider_error"), ok_response],
    ):
        result = RunOrchestrator(
            workspace_slug="partial-brand",
            provider="openai",
            model="gpt-4",
            brand_names=["PartialBrand"],
        ).scan()

    assert result.status == "completed_with_partial_failures", (
        f"Expected 'completed_with_partial_failures', got '{result.status}'"
    )
    assert result.failed_providers, "failed_providers must be non-empty on partial failure"


def test_seeded_flow_workspace_isolation_across_scans(db_path: str) -> None:
    ws_x = _make_workspace(db_path, slug="iso-x", brand_name="IsoX")
    ws_y = _make_workspace(db_path, slug="iso-y", brand_name="IsoY")

    resp_x = ProviderResponse(
        provider="openai",
        model="gpt-4",
        content=(
            "IsoX is a trusted platform for data teams with proven reliability. "
            "See https://isox.example.com for details."
        ),
        latency_ms=70,
    )
    resp_y = ProviderResponse(
        provider="openai",
        model="gpt-4",
        content=(
            "IsoY provides workflow automation for operations teams at scale. See https://isoy.example.com for details."
        ),
        latency_ms=72,
    )

    with patch(
        "ai_visibility.providers.gateway.ProviderGateway.execute_prompt",
        new_callable=AsyncMock,
        return_value=resp_x,
    ):
        run_x = RunOrchestrator("iso-x", provider="openai", model="gpt-4", brand_names=["IsoX"]).scan()

    with patch(
        "ai_visibility.providers.gateway.ProviderGateway.execute_prompt",
        new_callable=AsyncMock,
        return_value=resp_y,
    ):
        run_y = RunOrchestrator("iso-y", provider="openai", model="gpt-4", brand_names=["IsoY"]).scan()

    run_repo = RunRepository(db_path=db_path)
    runs_x = run_repo.list_by_workspace(ws_x["id"])
    runs_y = run_repo.list_by_workspace(ws_y["id"])

    assert all(r["workspace_id"] == ws_x["id"] for r in runs_x), "runs for iso-x must belong to iso-x workspace"
    assert all(r["workspace_id"] == ws_y["id"] for r in runs_y), "runs for iso-y must belong to iso-y workspace"

    recs_x = recommend_latest(workspace="iso-x")
    recs_y = recommend_latest(workspace="iso-y")

    assert "degraded" not in recs_x
    assert "degraded" not in recs_y
    assert all(item["workspace_slug"] == "iso-x" for item in recs_x["recommendations"])
    assert all(item["workspace_slug"] == "iso-y" for item in recs_y["recommendations"])
