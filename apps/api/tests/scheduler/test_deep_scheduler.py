from datetime import datetime, timedelta, timezone
from typing import cast

import pytest

from ai_visibility.scheduler.models import ScheduleDefinition
from ai_visibility.scheduler.scheduler import ScanScheduler


def test_add_schedule_returns_schedule_id() -> None:
    scheduler = ScanScheduler()
    schedule_id = scheduler.add_schedule(ScheduleDefinition(workspace_slug="acme", interval_hours=24))
    assert isinstance(schedule_id, str)
    assert schedule_id


def test_add_schedule_id_appears_in_list_schedules() -> None:
    scheduler = ScanScheduler()
    schedule_id = scheduler.add_schedule(ScheduleDefinition(workspace_slug="acme", interval_hours=24))

    listed_ids = {entry["schedule_id"] for entry in scheduler.list_schedules()}
    assert schedule_id in listed_ids


def test_is_due_for_brand_new_schedule_is_true() -> None:
    scheduler = ScanScheduler()
    schedule_id = scheduler.add_schedule(ScheduleDefinition(workspace_slug="acme", interval_hours=12))
    assert scheduler.is_due(schedule_id) is True


def test_is_due_when_just_ran_is_false() -> None:
    scheduler = ScanScheduler()
    schedule_id = scheduler.add_schedule(ScheduleDefinition(workspace_slug="acme", interval_hours=12))
    last_run = cast(dict[str, datetime], scheduler.__dict__["_last_run"])
    last_run[schedule_id] = datetime.now(timezone.utc)

    assert scheduler.is_due(schedule_id) is False


def test_is_due_when_interval_elapsed_is_true() -> None:
    scheduler = ScanScheduler()
    schedule_id = scheduler.add_schedule(ScheduleDefinition(workspace_slug="acme", interval_hours=12))
    last_run = cast(dict[str, datetime], scheduler.__dict__["_last_run"])
    last_run[schedule_id] = datetime.now(timezone.utc) - timedelta(hours=12, minutes=1)

    assert scheduler.is_due(schedule_id) is True


def test_get_missed_runs_never_ran_returns_one() -> None:
    scheduler = ScanScheduler()
    schedule_id = scheduler.add_schedule(ScheduleDefinition(workspace_slug="acme", interval_hours=4))

    assert scheduler.get_missed_runs(schedule_id) == 1


def test_get_missed_runs_just_ran_returns_zero() -> None:
    scheduler = ScanScheduler()
    schedule_id = scheduler.add_schedule(ScheduleDefinition(workspace_slug="acme", interval_hours=4))
    last_run = cast(dict[str, datetime], scheduler.__dict__["_last_run"])
    last_run[schedule_id] = datetime.now(timezone.utc)

    assert scheduler.get_missed_runs(schedule_id) == 0


def test_execute_due_dry_run_returns_dry_run_and_does_not_execute() -> None:
    scheduler = ScanScheduler()
    schedule_id = scheduler.add_schedule(ScheduleDefinition(workspace_slug="acme", interval_hours=24))

    result = scheduler.execute_due(schedule_id, dry_run=True)

    assert result.status == "dry_run"
    last_run = cast(dict[str, datetime], scheduler.__dict__["_last_run"])
    assert schedule_id not in last_run


def test_execute_due_nonexistent_schedule_returns_failed_result() -> None:
    scheduler = ScanScheduler()
    result = scheduler.execute_due("missing-id")

    assert result.status == "failed"
    assert result.error_message == "Schedule not found"
    assert result.workspace_slug == "unknown"


def test_execute_due_already_running_returns_skipped_duplicate() -> None:
    scheduler = ScanScheduler()
    schedule_id = scheduler.add_schedule(ScheduleDefinition(workspace_slug="acme", interval_hours=24))
    running = cast(set[str], scheduler.__dict__["_running"])
    running.add(schedule_id)

    result = scheduler.execute_due(schedule_id)

    assert result.status == "skipped_duplicate"
    assert result.workspace_slug == "acme"


def test_run_once_executes_all_due_schedules(monkeypatch: pytest.MonkeyPatch) -> None:
    scheduler = ScanScheduler()
    due_a = scheduler.add_schedule(ScheduleDefinition(workspace_slug="acme", interval_hours=24))
    due_b = scheduler.add_schedule(ScheduleDefinition(workspace_slug="beta", interval_hours=24))

    calls: list[str] = []
    original_execute_due = scheduler.execute_due

    def fake_execute_due(schedule_id: str, dry_run: bool = False):
        _ = dry_run
        calls.append(schedule_id)
        return original_execute_due(schedule_id, dry_run=True)

    monkeypatch.setattr(scheduler, "execute_due", fake_execute_due)
    results = scheduler.run_once(dry_run=False)

    assert len(results) == 2
    assert set(calls) == {due_a, due_b}
    assert all(result.status == "dry_run" for result in results)


def test_run_once_with_no_due_schedules_returns_empty_list() -> None:
    scheduler = ScanScheduler()
    schedule_id = scheduler.add_schedule(ScheduleDefinition(workspace_slug="acme", interval_hours=24))
    last_run = cast(dict[str, datetime], scheduler.__dict__["_last_run"])
    last_run[schedule_id] = datetime.now(timezone.utc)

    assert scheduler.run_once() == []
