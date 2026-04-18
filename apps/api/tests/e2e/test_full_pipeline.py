from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import cast
from unittest.mock import AsyncMock, patch

import pytest
from starlette.testclient import TestClient

from ai_visibility.api.routes import create_app
from ai_visibility.cli import doctor, list_workspaces, recommend_latest, seed_demo
from ai_visibility.extraction.pipeline import ExtractionPipeline
from ai_visibility.providers.gateway import ProviderError, ProviderResponse
from ai_visibility.metrics.engine import MetricSnapshot, MetricsEngine
from ai_visibility.recommendations.engine import LOW_VISIBILITY
from ai_visibility.runs.orchestrator import RunOrchestrator
from ai_visibility.storage.database import Database
from ai_visibility.storage.repositories.mention_repo import MentionRepository
from ai_visibility.storage.repositories.metric_repo import MetricRepository
from ai_visibility.storage.repositories.run_repo import RunRepository
from ai_visibility.storage.repositories.workspace_repo import WorkspaceRepository
from ai_visibility.storage.types import MetricSnapshotRecord, WorkspaceRecord


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _create_workspace(db_path: str, slug: str, brand_name: str) -> WorkspaceRecord:
    repo = WorkspaceRepository(db_path=db_path)
    workspace: WorkspaceRecord = {
        "id": str(uuid.uuid4()),
        "slug": slug,
        "brand_name": brand_name,
        "city": "",
        "region": "",
        "country": "",
        "created_at": _utc_now(),
    }
    return repo.create(workspace)


def _persist_metric_snapshot(db_path: str, workspace_id: str, run_id: str, brand_name: str) -> MetricSnapshot:
    run_repo = RunRepository(db_path=db_path)
    metric_repo = MetricRepository(db_path=db_path)
    runs = run_repo.list_by_workspace(workspace_id)
    run_record = next(run for run in runs if run["id"] == run_id)

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
    _ = metric_repo.upsert_snapshot(stored)
    return snapshot


def _citations_for_run(db_path: str, run_id: str) -> list[dict[str, str | None]]:
    with Database(db_path=db_path).connect() as connection:
        rows = cast(
            list[sqlite3.Row],
            connection.execute(
                """
            SELECT citation_url AS url, citation_domain AS domain, citation_status AS status
            FROM mentions
            WHERE run_id = ?
            ORDER BY id ASC
            """,
                (run_id,),
            ).fetchall(),
        )
    return [
        {
            "url": row["url"],
            "domain": row["domain"],
            "status": row["status"],
        }
        for row in rows
    ]


@pytest.fixture
def db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    path = tmp_path / "e2e_pipeline.db"
    monkeypatch.setenv("DB_PATH", str(path))
    Database(db_path=str(path)).initialize()
    return str(path)


def test_full_scan_lifecycle_persists_run_mentions_citations_and_metric(db_path: str) -> None:
    workspace = _create_workspace(db_path, slug="test-brand", brand_name="TestBrand")

    response = ProviderResponse(
        provider="openai",
        model="gpt-4",
        content=(
            "TestBrand is a leading AI platform for enterprise teams. "
            "Visit https://testbrand.com for details and https://example.com/compare for context."
        ),
        latency_ms=150,
        token_count=50,
    )

    with patch(
        "ai_visibility.providers.gateway.ProviderGateway.execute_prompt",
        new_callable=AsyncMock,
        return_value=response,
    ):
        result = RunOrchestrator(
            workspace_slug="test-brand",
            provider="openai",
            model="gpt-4",
            brand_names=["TestBrand"],
        ).scan()

    run_repo = RunRepository(db_path=db_path)
    mention_repo = MentionRepository(db_path=db_path)
    metric_repo = MetricRepository(db_path=db_path)

    runs = run_repo.list_by_workspace(workspace["id"])
    assert len(runs) == 1
    assert runs[0]["id"] == result.run_id

    mentions = mention_repo.list_by_run(result.run_id)
    assert mentions
    assert all(mention["run_id"] == result.run_id for mention in mentions)

    citations = _citations_for_run(db_path, result.run_id)
    assert citations
    assert any(citation["url"] for citation in citations)

    snapshot = _persist_metric_snapshot(db_path, workspace["id"], result.run_id, "TestBrand")
    stored_snapshot = metric_repo.get_latest_by_workspace(workspace["id"])
    assert stored_snapshot is not None
    assert stored_snapshot["visibility_score"] == snapshot.visibility_score


def test_multiple_scans_same_workspace_returns_desc_order(db_path: str) -> None:
    workspace = _create_workspace(db_path, slug="test-brand", brand_name="TestBrand")

    response = ProviderResponse(
        provider="openai",
        model="gpt-4",
        content=(
            "TestBrand appears in this long answer for stability. "
            "See https://testbrand.com/features for the product overview."
        ),
        latency_ms=120,
        token_count=40,
    )

    with patch(
        "ai_visibility.providers.gateway.ProviderGateway.execute_prompt",
        new_callable=AsyncMock,
        return_value=response,
    ):
        orchestrator = RunOrchestrator("test-brand", provider="openai", model="gpt-4", brand_names=["TestBrand"])
        first = orchestrator.scan()
        second = orchestrator.scan()

    runs = RunRepository(db_path=db_path).list_by_workspace(workspace["id"])
    assert len(runs) == 2
    assert runs[0]["id"] == second.run_id
    assert runs[1]["id"] == first.run_id


def test_multiple_scans_latest_run_is_second(db_path: str) -> None:
    workspace = _create_workspace(db_path, slug="test-brand", brand_name="TestBrand")

    response = ProviderResponse(
        provider="openai",
        model="gpt-4",
        content=(
            "TestBrand keeps a strong market position in this stable response text. "
            "More at https://example.com/reference."
        ),
        latency_ms=111,
    )

    with patch(
        "ai_visibility.providers.gateway.ProviderGateway.execute_prompt",
        new_callable=AsyncMock,
        return_value=response,
    ):
        orchestrator = RunOrchestrator("test-brand", provider="openai", model="gpt-4", brand_names=["TestBrand"])
        _ = orchestrator.scan()
        second = orchestrator.scan()

    latest = RunRepository(db_path=db_path).get_latest_by_workspace(workspace["id"])
    assert latest is not None
    assert latest["id"] == second.run_id


def test_scan_with_brand_not_mentioned_has_zero_visibility(db_path: str) -> None:
    workspace = _create_workspace(db_path, slug="test-brand", brand_name="TestBrand")

    no_brand_response = ProviderResponse(
        provider="openai",
        model="gpt-4",
        content=(
            "Another platform dominates this category and receives broad praise in reviews. "
            "Read details at https://example.com/reviews for market context."
        ),
        latency_ms=104,
    )

    with patch(
        "ai_visibility.providers.gateway.ProviderGateway.execute_prompt",
        new_callable=AsyncMock,
        return_value=no_brand_response,
    ):
        result = RunOrchestrator("test-brand", provider="openai", model="gpt-4", brand_names=["TestBrand"]).scan()

    mentions = MentionRepository(db_path=db_path).list_by_run(result.run_id)
    assert any(mention["mention_type"] == "absent" for mention in mentions)

    snapshot = _persist_metric_snapshot(db_path, workspace["id"], result.run_id, "TestBrand")
    assert snapshot.visibility_score == 0.0


def test_scan_with_citations_extracts_url_and_domain(db_path: str) -> None:
    _ = _create_workspace(db_path, slug="test-brand", brand_name="TestBrand")

    citation_response = ProviderResponse(
        provider="openai",
        model="gpt-4",
        content=(
            "TestBrand provides analytics and planning support for teams. "
            "Sources: https://example.com and https://testbrand.com/blog/post."
        ),
        latency_ms=130,
    )

    with patch(
        "ai_visibility.providers.gateway.ProviderGateway.execute_prompt",
        new_callable=AsyncMock,
        return_value=citation_response,
    ):
        result = RunOrchestrator("test-brand", provider="openai", model="gpt-4", brand_names=["TestBrand"]).scan()

    citations = _citations_for_run(db_path, result.run_id)
    found = [citation for citation in citations if citation["status"] == "found"]
    assert found
    assert any(citation["url"] == "https://example.com" for citation in found)
    assert any(citation["domain"] == "example.com" for citation in found)


def test_scan_with_citations_computes_nonzero_citation_coverage(db_path: str) -> None:
    workspace = _create_workspace(db_path, slug="test-brand", brand_name="TestBrand")

    citation_response = ProviderResponse(
        provider="openai",
        model="gpt-4",
        content=(
            "TestBrand is trusted by many teams with proven outcomes over time. "
            "References include https://example.com/a and https://example.org/b."
        ),
        latency_ms=95,
    )

    with patch(
        "ai_visibility.providers.gateway.ProviderGateway.execute_prompt",
        new_callable=AsyncMock,
        return_value=citation_response,
    ):
        result = RunOrchestrator("test-brand", provider="openai", model="gpt-4", brand_names=["TestBrand"]).scan()

    snapshot = _persist_metric_snapshot(db_path, workspace["id"], result.run_id, "TestBrand")
    assert snapshot.citation_coverage > 0.0


def test_scan_partial_failure_marks_status_and_failed_provider(db_path: str) -> None:
    _ = _create_workspace(db_path, slug="test-brand", brand_name="TestBrand")

    ok_response = ProviderResponse(
        provider="openai",
        model="gpt-4",
        content=(
            "TestBrand appears in a sufficiently long response to pass parsing. "
            "Reference https://example.com/ok for details."
        ),
        latency_ms=84,
    )

    with patch(
        "ai_visibility.providers.gateway.ProviderGateway.execute_prompt",
        new_callable=AsyncMock,
        side_effect=[ok_response, ProviderError("provider down", error_code="provider_error"), ok_response],
    ):
        result = RunOrchestrator("test-brand", provider="openai", model="gpt-4", brand_names=["TestBrand"]).scan()

    assert result.status == "completed_with_partial_failures"
    assert result.failed_providers == ["openai"]


def test_scan_partial_failure_persists_run_error(db_path: str) -> None:
    workspace = _create_workspace(db_path, slug="test-brand", brand_name="TestBrand")

    ok_response = ProviderResponse(
        provider="openai",
        model="gpt-4",
        content=(
            "TestBrand is present in this response with enough length for extraction. "
            "Read https://example.com/context for context."
        ),
        latency_ms=72,
    )

    with patch(
        "ai_visibility.providers.gateway.ProviderGateway.execute_prompt",
        new_callable=AsyncMock,
        side_effect=[ProviderError("transient outage", error_code="provider_error"), ok_response, ok_response],
    ):
        result = RunOrchestrator("test-brand", provider="openai", model="gpt-4", brand_names=["TestBrand"]).scan()

    run = RunRepository(db_path=db_path).get_latest_by_workspace(workspace["id"])
    assert run is not None
    assert run["id"] == result.run_id
    assert run["status"] == "completed_with_partial_failures"
    assert run["error"] is not None


def test_recommendations_from_pipeline_data_include_low_visibility(db_path: str) -> None:
    workspace = _create_workspace(db_path, slug="test-brand", brand_name="TestBrand")

    low_visibility_response = ProviderResponse(
        provider="openai",
        model="gpt-4",
        content=(
            "CompetitorBrand receives stronger endorsements in analyst summaries today. "
            "Further reading: https://example.com/market-view for broad context."
        ),
        latency_ms=100,
    )

    with patch(
        "ai_visibility.providers.gateway.ProviderGateway.execute_prompt",
        new_callable=AsyncMock,
        return_value=low_visibility_response,
    ):
        orchestrator = RunOrchestrator("test-brand", provider="openai", model="gpt-4", brand_names=["TestBrand"])
        first = orchestrator.scan()
        second = orchestrator.scan()

    _ = _persist_metric_snapshot(db_path, workspace["id"], first.run_id, "TestBrand")
    _ = _persist_metric_snapshot(db_path, workspace["id"], second.run_id, "TestBrand")

    payload = recommend_latest(workspace="test-brand")
    assert "degraded" not in payload
    recommendations = payload["recommendations"]
    assert any(item["rule_code"] == LOW_VISIBILITY for item in recommendations)
    assert all(item["workspace_slug"] == "test-brand" for item in recommendations)


def test_workspace_isolation_for_runs_and_metrics(db_path: str) -> None:
    ws_a = _create_workspace(db_path, slug="brand-a", brand_name="BrandA")
    ws_b = _create_workspace(db_path, slug="brand-b", brand_name="BrandB")

    response_a = ProviderResponse(
        provider="openai",
        model="gpt-4",
        content=(
            "BrandA has an active footprint and this statement is deliberately long enough. "
            "Source https://a.example.com confirms supporting details."
        ),
        latency_ms=90,
    )
    response_b = ProviderResponse(
        provider="openai",
        model="gpt-4",
        content=(
            "BrandB appears in this output with contextual evidence for extraction. "
            "Source https://b.example.com adds more detail for analysis."
        ),
        latency_ms=89,
    )

    with patch(
        "ai_visibility.providers.gateway.ProviderGateway.execute_prompt",
        new_callable=AsyncMock,
        return_value=response_a,
    ):
        run_a = RunOrchestrator("brand-a", provider="openai", model="gpt-4", brand_names=["BrandA"]).scan()

    with patch(
        "ai_visibility.providers.gateway.ProviderGateway.execute_prompt",
        new_callable=AsyncMock,
        return_value=response_b,
    ):
        run_b = RunOrchestrator("brand-b", provider="openai", model="gpt-4", brand_names=["BrandB"]).scan()

    _ = _persist_metric_snapshot(db_path, ws_a["id"], run_a.run_id, "BrandA")
    _ = _persist_metric_snapshot(db_path, ws_b["id"], run_b.run_id, "BrandB")

    run_repo = RunRepository(db_path=db_path)
    metric_repo = MetricRepository(db_path=db_path)

    runs_a = run_repo.list_by_workspace(ws_a["id"])
    runs_b = run_repo.list_by_workspace(ws_b["id"])
    assert all(run["workspace_id"] == ws_a["id"] for run in runs_a)
    assert all(run["workspace_id"] == ws_b["id"] for run in runs_b)
    assert metric_repo.get_latest_by_workspace(ws_a["id"]) is not None
    assert metric_repo.get_latest_by_workspace(ws_b["id"]) is not None


def test_workspace_isolation_for_recommendations(db_path: str) -> None:
    _ = _create_workspace(db_path, slug="brand-a", brand_name="BrandA")
    _ = _create_workspace(db_path, slug="brand-b", brand_name="BrandB")

    response = ProviderResponse(
        provider="openai",
        model="gpt-4",
        content=(
            "Competitor narratives dominate this answer and reduce direct brand mentions. "
            "Evidence appears at https://example.com/neutral-report for context."
        ),
        latency_ms=77,
    )

    with patch(
        "ai_visibility.providers.gateway.ProviderGateway.execute_prompt",
        new_callable=AsyncMock,
        return_value=response,
    ):
        _ = RunOrchestrator("brand-a", provider="openai", model="gpt-4", brand_names=["BrandA"]).scan()
        _ = RunOrchestrator("brand-b", provider="openai", model="gpt-4", brand_names=["BrandB"]).scan()

    payload_a = recommend_latest(workspace="brand-a")
    payload_b = recommend_latest(workspace="brand-b")
    assert "degraded" not in payload_a
    assert "degraded" not in payload_b
    recs_a = payload_a["recommendations"]
    recs_b = payload_b["recommendations"]

    assert all(item["workspace_slug"] == "brand-a" for item in recs_a)
    assert all(item["workspace_slug"] == "brand-b" for item in recs_b)


def test_api_endpoint_integration_health_workspaces_prompts(db_path: str) -> None:
    _ = _create_workspace(db_path, slug="test-brand", brand_name="TestBrand")

    client = TestClient(create_app())

    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    workspaces = client.get("/api/v1/workspaces")
    assert workspaces.status_code == 200
    items = cast(list[dict[str, object]], workspaces.json()["items"])
    assert any(item["slug"] == "test-brand" for item in items)

    prompts = client.get("/api/v1/prompts")
    assert prompts.status_code == 200
    assert isinstance(prompts.json()["items"], list)
    assert prompts.json()["items"]


def test_cli_command_integration_doctor_seed_demo_list_workspaces(db_path: str) -> None:
    _ = db_path
    doctor_result = doctor()
    assert doctor_result["status"] == "healthy"
    assert "providers" in doctor_result

    seed_result = seed_demo()
    assert seed_result["status"] == "success"

    workspaces_result = list_workspaces()
    assert workspaces_result["status"] == "success"
    assert any(item["slug"] == "acme" for item in workspaces_result["workspaces"])


def test_empty_state_handling_returns_graceful_empty_results(db_path: str) -> None:
    client = TestClient(create_app())

    workspaces = client.get("/api/v1/workspaces")
    assert workspaces.status_code == 200
    assert workspaces.json()["items"] == []

    recommendations = recommend_latest(workspace="default")
    assert "degraded" not in recommendations
    assert recommendations["workspace"] == "default"
    assert recommendations["recommendations"] == []

    workspace = _create_workspace(db_path, slug="no-runs", brand_name="NoRunsBrand")
    latest_metric = MetricRepository(db_path=db_path).get_latest_by_workspace(workspace["id"])
    assert latest_metric is None


def test_data_integrity_links_runs_mentions_and_citations(db_path: str) -> None:
    workspace = _create_workspace(db_path, slug="test-brand", brand_name="TestBrand")

    response = ProviderResponse(
        provider="openai",
        model="gpt-4",
        content=(
            "TestBrand appears with references in this long answer for extraction accuracy. "
            "Visit https://example.com/insight for supporting context and analysis."
        ),
        latency_ms=101,
    )

    with patch(
        "ai_visibility.providers.gateway.ProviderGateway.execute_prompt",
        new_callable=AsyncMock,
        return_value=response,
    ):
        result = RunOrchestrator("test-brand", provider="openai", model="gpt-4", brand_names=["TestBrand"]).scan()

    with Database(db_path=db_path).connect() as connection:
        mention_rows = cast(
            list[sqlite3.Row],
            connection.execute(
                "SELECT id, run_id, workspace_id FROM mentions WHERE run_id = ?",
                (result.run_id,),
            ).fetchall(),
        )
        citation_rows = cast(
            list[sqlite3.Row],
            connection.execute(
                "SELECT id AS mention_id FROM mentions WHERE run_id = ? AND citation_status IN ('found', 'no_citation')",
                (result.run_id,),
            ).fetchall(),
        )

    mention_ids = {row["id"] for row in mention_rows}
    cited_mention_ids = {row["mention_id"] for row in citation_rows}

    assert mention_rows
    assert all(row["run_id"] == result.run_id for row in mention_rows)
    assert all(row["workspace_id"] == workspace["id"] for row in mention_rows)
    assert cited_mention_ids.issubset(mention_ids)


def test_orchestrator_list_runs_scoped_to_workspace(db_path: str) -> None:
    _ = _create_workspace(db_path, slug="brand-a", brand_name="BrandA")
    _ = _create_workspace(db_path, slug="brand-b", brand_name="BrandB")

    response_a = ProviderResponse(
        provider="openai",
        model="gpt-4",
        content=(
            "BrandA is directly referenced in this response and stays parse-safe. "
            "Source https://brand-a.example.com supports the statement."
        ),
        latency_ms=83,
    )
    response_b = ProviderResponse(
        provider="openai",
        model="gpt-4",
        content=(
            "BrandB is directly referenced in this response and stays parse-safe. "
            "Source https://brand-b.example.com supports the statement."
        ),
        latency_ms=83,
    )

    with patch(
        "ai_visibility.providers.gateway.ProviderGateway.execute_prompt",
        new_callable=AsyncMock,
        return_value=response_a,
    ):
        _ = RunOrchestrator("brand-a", provider="openai", model="gpt-4", brand_names=["BrandA"]).scan()

    with patch(
        "ai_visibility.providers.gateway.ProviderGateway.execute_prompt",
        new_callable=AsyncMock,
        return_value=response_b,
    ):
        _ = RunOrchestrator("brand-b", provider="openai", model="gpt-4", brand_names=["BrandB"]).scan()

    list_a = RunOrchestrator("brand-a", provider="openai", model="gpt-4", brand_names=["BrandA"]).list_runs()
    list_b = RunOrchestrator("brand-b", provider="openai", model="gpt-4", brand_names=["BrandB"]).list_runs()

    assert list_a
    assert list_b
    assert all(run["workspace_id"] != list_b[0]["workspace_id"] for run in list_a)


def test_scan_completed_status_when_all_prompts_succeed(db_path: str) -> None:
    _ = _create_workspace(db_path, slug="test-brand", brand_name="TestBrand")

    response = ProviderResponse(
        provider="openai",
        model="gpt-4",
        content=(
            "TestBrand is called out repeatedly in this response for deterministic extraction. "
            "Supporting citation: https://example.com/verified-source."
        ),
        latency_ms=70,
    )

    with patch(
        "ai_visibility.providers.gateway.ProviderGateway.execute_prompt",
        new_callable=AsyncMock,
        return_value=response,
    ):
        result = RunOrchestrator("test-brand", provider="openai", model="gpt-4", brand_names=["TestBrand"]).scan()

    assert result.status == "completed"
    assert result.failed_providers == []
    assert result.results_count == 3


def test_orchestrator_persists_metrics_after_scan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_file = tmp_path / "orchestrator_metrics.db"
    monkeypatch.setenv("DB_PATH", str(db_file))
    Database(db_path=str(db_file)).initialize()

    workspace = _create_workspace(str(db_file), slug="persist-brand", brand_name="PersistBrand")

    response = ProviderResponse(
        provider="openai",
        model="gpt-4",
        content=(
            "PersistBrand is a reliable analytics platform used by operations teams. "
            "Reference: https://persistbrand.com/features"
        ),
        latency_ms=88,
        token_count=42,
    )

    with patch(
        "ai_visibility.providers.gateway.ProviderGateway.execute_prompt",
        new_callable=AsyncMock,
        return_value=response,
    ):
        result = RunOrchestrator(
            workspace_slug="persist-brand",
            provider="openai",
            model="gpt-4",
            brand_names=["PersistBrand"],
        ).scan()

    assert result.status in {"completed", "completed_with_partial_failures"}

    with Database(db_path=str(db_file)).connect() as connection:
        row = cast(
            sqlite3.Row | None,
            connection.execute(
                """
                SELECT workspace_id, visibility_score, citation_coverage, competitor_wins, mention_count
                FROM metric_snapshots
                WHERE workspace_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """,
                (workspace["id"],),
            ).fetchone(),
        )

    assert row is not None
    visibility_score = float(cast(float | int, row["visibility_score"]))
    citation_coverage = float(cast(float | int, row["citation_coverage"]))
    competitor_wins = int(cast(int, row["competitor_wins"]))
    mention_count = int(cast(int, row["mention_count"]))

    assert cast(str, row["workspace_id"]) == workspace["id"]
    assert 0.0 <= visibility_score <= 1.0
    assert visibility_score > 0.0
    assert 0.0 <= citation_coverage <= 1.0
    assert competitor_wins >= 0
    assert mention_count >= 1
