from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import ClassVar, Protocol, cast, runtime_checkable

RowLike = Mapping[str, object] | Sequence[object]
CursorDescription = Sequence[Sequence[object]] | None


class CursorProtocol(Protocol):
    description: CursorDescription

    def execute(self, statement: str, params: Sequence[object] | None = None) -> object: ...

    def fetchone(self) -> RowLike | None: ...

    def close(self) -> object: ...


class ConnectionProtocol(Protocol):
    def cursor(self) -> CursorProtocol: ...

    def commit(self) -> object: ...


@runtime_checkable
class AutocommitConnectionProtocol(ConnectionProtocol, Protocol):
    autocommit: bool


class MaintenanceSchedule:
    PARTMAN_TABLES: ClassVar[tuple[dict[str, str], ...]] = (
        {"table": "prompt_executions", "control": "created_at", "interval": "1 month"},
        {"table": "observations", "control": "created_at", "interval": "1 month"},
        {"table": "prompt_execution_citations", "control": "created_at", "interval": "1 month"},
    )
    CRON_JOBS: ClassVar[tuple[dict[str, str], ...]] = (
        {
            "name": "refresh-mv-workspace-overview-hourly",
            "schedule": "0 * * * *",
            "statement": "REFRESH MATERIALIZED VIEW CONCURRENTLY public.mv_workspace_overview",
        },
        {
            "name": "vacuum-scan-jobs-nightly",
            "schedule": "0 3 * * *",
            "statement": "VACUUM (ANALYZE) public.scan_jobs",
        },
    )
    BRIN_INDEXES: ClassVar[tuple[dict[str, str], ...]] = (
        {"name": "idx_brin_scan_jobs_created_at", "table": "scan_jobs", "column": "created_at"},
        {"name": "idx_brin_scan_executions_created_at", "table": "scan_executions", "column": "created_at"},
        {"name": "idx_brin_prompt_executions_created_at", "table": "prompt_executions", "column": "created_at"},
        {"name": "idx_brin_observations_created_at", "table": "observations", "column": "created_at"},
    )


_MAINTENANCE_SQL_PATH = Path(__file__).with_name("maintenance.sql")
_MATVIEW_NAME = "mv_workspace_overview"
_MATVIEW_REFRESH_SQL = f"REFRESH MATERIALIZED VIEW CONCURRENTLY public.{_MATVIEW_NAME}"
_MATVIEW_STATUS_SQL = """
SELECT
    schemaname,
    matviewname,
    hasindexes,
    ispopulated,
    definition,
    now() AS checked_at
FROM pg_matviews
WHERE schemaname = 'public' AND matviewname = %s
"""


def get_maintenance_sql() -> str:
    return _MAINTENANCE_SQL_PATH.read_text(encoding="utf-8")


def apply_matview_refresh(conn: ConnectionProtocol) -> None:
    autocommit_conn = conn if isinstance(conn, AutocommitConnectionProtocol) else None
    original_autocommit = autocommit_conn.autocommit if autocommit_conn is not None else None
    if autocommit_conn is not None:
        autocommit_conn.autocommit = True

    try:
        _execute_statement(conn, _MATVIEW_REFRESH_SQL)
    finally:
        if autocommit_conn is not None and original_autocommit is not None:
            autocommit_conn.autocommit = original_autocommit


def get_matview_status(conn: ConnectionProtocol) -> dict[str, object]:
    row = _fetchone(conn, _MATVIEW_STATUS_SQL, (_MATVIEW_NAME,))
    if row is None:
        return {"exists": False, "matviewname": _MATVIEW_NAME}

    status = dict(row)
    status["exists"] = True
    return status


def _execute_statement(conn: ConnectionProtocol, statement: str) -> None:
    cursor = conn.cursor()
    try:
        _ = cursor.execute(statement)
    finally:
        _ = cursor.close()

    _ = conn.commit()


def _fetchone(conn: ConnectionProtocol, statement: str, params: tuple[object, ...]) -> dict[str, object] | None:
    cursor = conn.cursor()
    try:
        _ = cursor.execute(statement, params)
        row = cursor.fetchone()
        description = cursor.description
    finally:
        _ = cursor.close()

    return _row_to_dict(row, description)


def _row_to_dict(row: RowLike | None, description: CursorDescription = None) -> dict[str, object] | None:
    if row is None:
        return None
    if isinstance(row, dict):
        return {str(key): value for key, value in row.items()}
    if hasattr(row, "keys"):
        row_mapping = cast(Mapping[str, object], row)
        return {key: row_mapping[key] for key in row_mapping.keys()}
    if description is None:
        raise TypeError("Row description is required for tuple results")

    keys = [str(column[0]) for column in description]
    return dict(zip(keys, row, strict=False))
