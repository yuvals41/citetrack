import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import cast

import pytest
from pydantic import TypeAdapter, ValidationError

from ai_visibility.scheduler import ExecutionResult, ScanScheduler, ScheduleDefinition


def test_schedule_definition_valid() -> None:
    definition = ScheduleDefinition(workspace_slug="acme", interval_hours=24)

    assert definition.workspace_slug == "acme"
    assert definition.interval_hours == 24


def test_schedule_definition_invalid_interval() -> None:
    with pytest.raises(ValidationError):
        _ = ScheduleDefinition(workspace_slug="acme", interval_hours=0)


def test_scheduler_instantiation() -> None:
    scheduler = ScanScheduler()

    assert scheduler is not None


def test_add_schedule() -> None:
    scheduler = ScanScheduler()

    schedule_id = scheduler.add_schedule(ScheduleDefinition(workspace_slug="acme", interval_hours=24))

    assert schedule_id


def test_list_schedules() -> None:
    scheduler = ScanScheduler()
    schedule_id = scheduler.add_schedule(ScheduleDefinition(workspace_slug="acme", interval_hours=24))

    schedules = scheduler.list_schedules()

    assert schedules == [
        {
            "schedule_id": schedule_id,
            "workspace_slug": "acme",
            "interval_hours": 24,
            "provider": "openai",
            "model": None,
            "enabled": True,
        }
    ]


def test_is_due_when_never_run() -> None:
    scheduler = ScanScheduler()
    schedule_id = scheduler.add_schedule(ScheduleDefinition(workspace_slug="acme", interval_hours=24))

    assert scheduler.is_due(schedule_id) is True


def test_is_due_when_recently_run() -> None:
    scheduler = ScanScheduler()
    schedule_id = scheduler.add_schedule(ScheduleDefinition(workspace_slug="acme", interval_hours=24))
    last_run = cast(dict[str, datetime], scheduler.__dict__["_last_run"])
    last_run[schedule_id] = datetime.now(timezone.utc) - timedelta(hours=1)

    assert scheduler.is_due(schedule_id) is False


def test_is_due_when_overdue() -> None:
    scheduler = ScanScheduler()
    schedule_id = scheduler.add_schedule(ScheduleDefinition(workspace_slug="acme", interval_hours=24))
    last_run = cast(dict[str, datetime], scheduler.__dict__["_last_run"])
    last_run[schedule_id] = datetime.now(timezone.utc) - timedelta(hours=25)

    assert scheduler.is_due(schedule_id) is True


def test_duplicate_protection() -> None:
    scheduler = ScanScheduler()
    schedule_id = scheduler.add_schedule(ScheduleDefinition(workspace_slug="acme", interval_hours=24))
    running = cast(set[str], scheduler.__dict__["_running"])
    running.add(schedule_id)

    result = scheduler.execute_due(schedule_id)

    assert isinstance(result, ExecutionResult)
    assert result.status == "skipped_duplicate"


def test_missed_run_catch_up() -> None:
    scheduler = ScanScheduler()
    schedule_id = scheduler.add_schedule(ScheduleDefinition(workspace_slug="acme", interval_hours=24))
    last_run = cast(dict[str, datetime], scheduler.__dict__["_last_run"])
    last_run[schedule_id] = datetime.now(timezone.utc) - timedelta(hours=96)

    assert scheduler.get_missed_runs(schedule_id) >= 1


def test_cli_run_scheduler_once() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ai_visibility.cli",
            "run-scheduler",
            "--once",
            "--dry-run",
            "--format",
            "json",
        ],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"stderr: {result.stderr}"
    payload_adapter: TypeAdapter[dict[str, object]] = TypeAdapter(dict[str, object])
    payload = payload_adapter.validate_json(result.stdout)
    assert "executed_jobs" in payload
