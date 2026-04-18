from __future__ import annotations

from abc import ABC, abstractmethod
import sqlite3
from collections.abc import Iterator
from contextlib import AbstractContextManager, contextmanager
from pathlib import Path
from typing import cast
from typing_extensions import override

from ai_visibility.config import get_settings


def _migrate_schema(connection: sqlite3.Connection) -> None:
    scan_jobs_sql_row = cast(
        tuple[object] | None,
        connection.execute("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'scan_jobs'").fetchone(),
    )
    scan_jobs_sql = str(scan_jobs_sql_row[0]) if scan_jobs_sql_row and scan_jobs_sql_row[0] else ""
    if "'partial'" in scan_jobs_sql and "completed_with_partial_failures" not in scan_jobs_sql:
        _ = connection.execute("PRAGMA foreign_keys = OFF")
        _ = connection.execute("ALTER TABLE scan_jobs RENAME TO scan_jobs_legacy")
        _ = connection.execute(
            """
            CREATE TABLE scan_jobs (
                id TEXT PRIMARY KEY,
                workspace_slug TEXT NOT NULL,
                strategy_version TEXT NOT NULL,
                prompt_version TEXT NOT NULL,
                created_at TEXT NOT NULL,
                idempotency_key TEXT NOT NULL,
                status TEXT NOT NULL CHECK (
                    status IN (
                        'queued',
                        'running',
                        'completed_with_partial_failures',
                        'failed',
                        'completed'
                    )
                ),
                scan_mode TEXT NOT NULL CHECK (scan_mode IN ('onboarding', 'scheduled'))
            )
            """
        )
        _ = connection.execute(
            """
            INSERT INTO scan_jobs (id, workspace_slug, strategy_version, prompt_version, created_at, idempotency_key, status, scan_mode)
            SELECT
                id,
                workspace_slug,
                strategy_version,
                prompt_version,
                created_at,
                idempotency_key,
                CASE
                    WHEN status = 'partial' THEN 'completed_with_partial_failures'
                    ELSE status
                END,
                scan_mode
            FROM scan_jobs_legacy
            """
        )
        _ = connection.execute("DROP TABLE scan_jobs_legacy")
        _ = connection.execute("PRAGMA foreign_keys = ON")

    migrations: list[tuple[str, str, str]] = [
        ("metric_snapshots", "citation_coverage", "REAL DEFAULT 0.0"),
        ("metric_snapshots", "competitor_wins", "INTEGER DEFAULT 0"),
        ("workspaces", "city", "TEXT DEFAULT ''"),
        ("workspaces", "region", "TEXT DEFAULT ''"),
        ("workspaces", "country", "TEXT DEFAULT ''"),
        ("scan_jobs", "idempotency_key", "TEXT"),
        ("scan_executions", "idempotency_key", "TEXT"),
        ("prompt_executions", "idempotency_key", "TEXT"),
        ("observations", "idempotency_key", "TEXT"),
        ("prompt_execution_citations", "idempotency_key", "TEXT"),
        ("mentions", "citation_url", "TEXT"),
        ("mentions", "citation_domain", "TEXT"),
        ("mentions", "citation_status", "TEXT DEFAULT 'no_citation'"),
    ]

    for table, column, type_default in migrations:
        pragma_rows = cast(
            list[tuple[object, ...]],
            connection.execute(f"PRAGMA table_info({table})").fetchall(),
        )
        existing_cols = {str(row[1]) for row in pragma_rows}
        if column not in existing_cols:
            _ = connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {type_default}")

    _ = connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_scan_jobs_idempotency_key ON scan_jobs(idempotency_key)"
    )
    _ = connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_scan_executions_idempotency_key ON scan_executions(idempotency_key)"
    )
    _ = connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_prompt_executions_idempotency_key ON prompt_executions(idempotency_key)"
    )
    _ = connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_observations_idempotency_key ON observations(idempotency_key)"
    )
    _ = connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_prompt_execution_citations_idempotency_key ON prompt_execution_citations(idempotency_key)"
    )

    connection.commit()


class AbstractDatabase(ABC):
    def __init__(self) -> None:
        self._initialized: bool = False

    def initialize(self) -> None:
        if self._initialized:
            return

        self.migrate_schema()
        self._initialized = True

    @abstractmethod
    def migrate_schema(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def connect(self) -> AbstractContextManager[sqlite3.Connection]:
        raise NotImplementedError


class SQLiteDatabase(AbstractDatabase):
    def __init__(self, db_path: str | None = None) -> None:
        super().__init__()
        self.db_path: str = _resolve_sqlite_path(db_path)

    @override
    def migrate_schema(self) -> None:
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as connection:
            _ = connection.execute("PRAGMA foreign_keys = ON")
            _ = connection.executescript((Path(__file__).with_name("schema.sql")).read_text())
            _migrate_schema(connection)
            connection.commit()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        self.initialize()
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        _ = connection.execute("PRAGMA foreign_keys = ON")

        try:
            yield connection
            connection.commit()
        finally:
            connection.close()


class PostgreSQLDatabase(AbstractDatabase):
    def __init__(self, url: str) -> None:
        super().__init__()
        self.url: str = url

    @override
    def migrate_schema(self) -> None:
        raise NotImplementedError("PostgreSQL storage is not implemented yet")

    @override
    def connect(self) -> AbstractContextManager[sqlite3.Connection]:
        raise NotImplementedError("PostgreSQL storage is not implemented yet")


def _resolve_sqlite_path(db_path: str | None) -> str:
    candidate = db_path or get_settings().db_path
    if candidate.startswith("sqlite://"):
        sqlite_path = candidate.removeprefix("sqlite://")
        return sqlite_path or get_settings().db_path
    return candidate


def get_database(url: str | None = None) -> AbstractDatabase:
    if not url:
        return SQLiteDatabase()
    if url.startswith("postgresql://"):
        return PostgreSQLDatabase(url)
    return SQLiteDatabase(db_path=url)


class Database(SQLiteDatabase):
    pass
