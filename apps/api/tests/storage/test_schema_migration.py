import sqlite3
from pathlib import Path
from typing import cast

from ai_visibility.storage.database import Database


def _column_names(db_path: Path, table_name: str) -> set[str]:
    with sqlite3.connect(db_path) as connection:
        rows = cast(
            list[tuple[object, ...]],
            connection.execute(f"PRAGMA table_info({table_name})").fetchall(),
        )
    return {str(row[1]) for row in rows}


def _create_legacy_metric_snapshots_table(
    db_path: Path,
    *,
    include_citation_coverage: bool,
    include_competitor_wins: bool,
) -> None:
    columns = [
        "id TEXT PRIMARY KEY",
        "workspace_id TEXT NOT NULL",
        "brand_id TEXT NOT NULL",
        "formula_version TEXT NOT NULL",
        "visibility_score REAL NOT NULL",
        "mention_count INTEGER NOT NULL",
        "created_at TEXT NOT NULL",
    ]
    if include_citation_coverage:
        columns.insert(5, "citation_coverage REAL NOT NULL DEFAULT 0.0")
    if include_competitor_wins:
        insert_at = 6 if include_citation_coverage else 5
        columns.insert(insert_at, "competitor_wins INTEGER NOT NULL DEFAULT 0")

    with sqlite3.connect(db_path) as connection:
        _ = connection.execute(f"CREATE TABLE metric_snapshots ({', '.join(columns)})")
        connection.commit()


def _create_legacy_workspaces_table(db_path: Path) -> None:
    with sqlite3.connect(db_path) as connection:
        _ = connection.execute(
            """
            CREATE TABLE workspaces (
                id TEXT PRIMARY KEY,
                slug TEXT NOT NULL UNIQUE,
                brand_name TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.commit()


def test_initialize_creates_metric_snapshot_columns_for_new_db(tmp_path: Path) -> None:
    db_path = tmp_path / "fresh.db"

    Database(db_path=str(db_path)).initialize()

    columns = _column_names(db_path, "metric_snapshots")
    assert "citation_coverage" in columns
    assert "competitor_wins" in columns


def test_initialize_creates_workspace_location_columns_for_new_db(tmp_path: Path) -> None:
    db_path = tmp_path / "fresh_workspace.db"

    Database(db_path=str(db_path)).initialize()

    columns = _column_names(db_path, "workspaces")
    assert "city" in columns
    assert "region" in columns
    assert "country" in columns


def test_initialize_creates_next_phase_tables_for_new_db(tmp_path: Path) -> None:
    db_path = tmp_path / "next_phase.db"

    Database(db_path=str(db_path)).initialize()

    expected_columns = {
        "scan_jobs": {
            "id",
            "workspace_slug",
            "strategy_version",
            "prompt_version",
            "created_at",
            "idempotency_key",
            "status",
            "scan_mode",
        },
        "scan_executions": {
            "id",
            "scan_job_id",
            "provider",
            "model_name",
            "model_version",
            "executed_at",
            "idempotency_key",
            "status",
        },
        "prompt_executions": {
            "id",
            "scan_execution_id",
            "prompt_id",
            "prompt_text",
            "raw_response",
            "executed_at",
            "idempotency_key",
            "parser_version",
        },
        "observations": {
            "id",
            "prompt_execution_id",
            "brand_mentioned",
            "brand_position",
            "response_excerpt",
            "idempotency_key",
            "strategy_version",
        },
        "prompt_execution_citations": {
            "id",
            "prompt_execution_id",
            "url",
            "title",
            "cited_text",
            "idempotency_key",
        },
        "diagnostic_findings": {
            "id",
            "workspace_slug",
            "finding_type",
            "reason_code",
            "confidence",
            "evidence_refs",
            "created_at",
            "rule_version",
            "applicability_context",
        },
        "recommendation_items": {
            "id",
            "workspace_slug",
            "finding_id",
            "code",
            "reason",
            "evidence_refs",
            "impact",
            "next_step",
            "confidence",
            "rule_version",
        },
        "snapshot_versions": {
            "id",
            "strategy_version",
            "model_version",
            "rule_version",
            "created_at",
        },
    }

    for table_name, columns in expected_columns.items():
        assert columns.issubset(_column_names(db_path, table_name))


def test_initialize_migrates_missing_workspace_location_columns(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy_workspace.db"
    _create_legacy_workspaces_table(db_path)

    Database(db_path=str(db_path)).initialize()

    columns = _column_names(db_path, "workspaces")
    assert "city" in columns
    assert "region" in columns
    assert "country" in columns


def test_initialize_migrates_missing_citation_coverage_column(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy_missing_citation.db"
    _create_legacy_metric_snapshots_table(
        db_path,
        include_citation_coverage=False,
        include_competitor_wins=True,
    )

    Database(db_path=str(db_path)).initialize()

    columns = _column_names(db_path, "metric_snapshots")
    assert "citation_coverage" in columns


def test_initialize_migrates_missing_competitor_wins_column(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy_missing_competitor.db"
    _create_legacy_metric_snapshots_table(
        db_path,
        include_citation_coverage=True,
        include_competitor_wins=False,
    )

    Database(db_path=str(db_path)).initialize()

    columns = _column_names(db_path, "metric_snapshots")
    assert "competitor_wins" in columns


def test_initialize_migration_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "idempotent.db"
    _create_legacy_metric_snapshots_table(
        db_path,
        include_citation_coverage=False,
        include_competitor_wins=False,
    )

    Database(db_path=str(db_path)).initialize()
    Database(db_path=str(db_path)).initialize()

    columns = _column_names(db_path, "metric_snapshots")
    assert "citation_coverage" in columns
    assert "competitor_wins" in columns


def test_initialize_migration_preserves_existing_rows(tmp_path: Path) -> None:
    db_path = tmp_path / "preserve_rows.db"
    _create_legacy_metric_snapshots_table(
        db_path,
        include_citation_coverage=False,
        include_competitor_wins=False,
    )

    with sqlite3.connect(db_path) as connection:
        _ = connection.execute(
            """
            INSERT INTO metric_snapshots (
                id, workspace_id, brand_id, formula_version, visibility_score, mention_count, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("snapshot-1", "ws-1", "brand-1", "v1", 0.55, 3, "2026-03-13T10:00:00"),
        )
        connection.commit()

    Database(db_path=str(db_path)).initialize()

    with sqlite3.connect(db_path) as connection:
        row = cast(
            tuple[object, ...] | None,
            connection.execute(
                """
            SELECT id, workspace_id, brand_id, formula_version, visibility_score, mention_count,
                   citation_coverage, competitor_wins
            FROM metric_snapshots
            WHERE id = ?
            """,
                ("snapshot-1",),
            ).fetchone(),
        )

    assert row is not None
    assert row[0] == "snapshot-1"
    assert row[1] == "ws-1"
    assert row[2] == "brand-1"
    assert row[3] == "v1"
    assert row[4] == 0.55
    assert row[5] == 3
    assert row[6] == 0.0
    assert row[7] == 0
