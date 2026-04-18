from collections.abc import Callable
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from typing import cast


def _load_maintenance_module() -> ModuleType:
    module_path = Path(__file__).resolve().parents[2] / "ai_visibility" / "storage" / "maintenance.py"
    spec = spec_from_file_location("test_maintenance_module", module_path)
    assert spec is not None
    assert spec.loader is not None

    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


get_maintenance_sql = cast(Callable[[], str], _load_maintenance_module().get_maintenance_sql)


def test_maintenance_sql_loads() -> None:
    sql = get_maintenance_sql()

    assert sql.strip()
    for table_name in ("prompt_executions", "observations", "prompt_execution_citations"):
        assert table_name in sql


def test_matview_sql_idempotent() -> None:
    sql = get_maintenance_sql()

    assert "CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_workspace_overview" in sql


def test_brin_indexes_present() -> None:
    sql = get_maintenance_sql()

    for index_name in (
        "idx_brin_scan_jobs_created_at",
        "idx_brin_scan_executions_created_at",
        "idx_brin_prompt_executions_created_at",
        "idx_brin_observations_created_at",
    ):
        assert index_name in sql
        assert "USING brin" in sql


def test_cron_schedule_present() -> None:
    sql = get_maintenance_sql()

    assert "cron.schedule(" in sql
    assert "0 * * * *" in sql
    assert "0 3 * * *" in sql
