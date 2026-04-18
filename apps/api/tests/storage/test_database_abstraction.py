import sqlite3
from pathlib import Path
from typing import cast

import pytest

from ai_visibility.storage.database import Database, PostgreSQLDatabase, SQLiteDatabase, get_database


def _table_names(db_path: Path) -> set[str]:
    with sqlite3.connect(db_path) as connection:
        rows = cast(
            list[tuple[object, ...]],
            connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall(),
        )
    return {str(row[0]) for row in rows}


def test_sqlite_database_connect_initializes_schema(tmp_path: Path) -> None:
    db_path = tmp_path / "storage.db"
    database = SQLiteDatabase(db_path=str(db_path))

    with database.connect() as connection:
        _ = connection.execute(
            """
            INSERT INTO scan_jobs (
                id,
                workspace_slug,
                strategy_version,
                prompt_version,
                created_at,
                idempotency_key,
                status,
                scan_mode
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "job_1",
                "acme",
                "strategy-v1",
                "prompt-v1",
                "2026-03-14T10:00:00",
                "scan-job-key-1",
                "queued",
                "onboarding",
            ),
        )

    assert db_path.exists()
    assert "scan_jobs" in _table_names(db_path)

    with sqlite3.connect(db_path) as connection:
        row = cast(
            tuple[object, ...] | None,
            connection.execute("SELECT id, workspace_slug FROM scan_jobs WHERE id = ?", ("job_1",)).fetchone(),
        )

    assert row == ("job_1", "acme")


def test_database_alias_remains_sqlite_default(tmp_path: Path) -> None:
    db_path = tmp_path / "database_alias.db"
    database = Database(db_path=str(db_path))

    database.initialize()

    assert db_path.exists()
    assert isinstance(database, SQLiteDatabase)


def test_get_database_returns_sqlite_for_default_and_sqlite_urls(tmp_path: Path) -> None:
    default_database = get_database()
    sqlite_database = get_database(f"sqlite://{tmp_path / 'factory.db'}")

    assert isinstance(default_database, SQLiteDatabase)
    assert isinstance(sqlite_database, SQLiteDatabase)


def test_get_database_returns_postgresql_database_for_postgres_url() -> None:
    database = get_database("postgresql://user:pass@localhost:5432/ai_visibility")

    assert isinstance(database, PostgreSQLDatabase)


def test_postgresql_database_stub_raises_not_implemented() -> None:
    database = PostgreSQLDatabase("postgresql://user:pass@localhost:5432/ai_visibility")

    with pytest.raises(NotImplementedError, match="not implemented"):
        database.migrate_schema()

    with pytest.raises(NotImplementedError, match="not implemented"):
        database.initialize()

    with pytest.raises(NotImplementedError, match="not implemented"):
        with database.connect():
            pass
