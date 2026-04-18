import threading
import time
from collections.abc import Sequence
from types import SimpleNamespace

import pytest

from ai_visibility.scheduler.executor import AsyncScanExecutor, ScheduledScanJob
from ai_visibility.scheduler.models import ExecutionResult, ScheduleDefinition
from ai_visibility.scheduler.scheduler import ScanScheduler


def _job(schedule_id: str, provider: str = "openai", dry_run: bool = False) -> ScheduledScanJob:
    return ScheduledScanJob(
        schedule_id=schedule_id,
        definition=ScheduleDefinition(workspace_slug=f"workspace-{schedule_id}", provider=provider),
        dry_run=dry_run,
    )


@pytest.mark.asyncio
async def test_executor_limits_concurrent_provider_calls() -> None:
    lock = threading.Lock()
    active_calls = 0
    max_active_calls = 0

    class FakeOrchestrator:
        _definition: ScheduleDefinition

        def __init__(self, definition: ScheduleDefinition) -> None:
            self._definition = definition

        def scan(self, dry_run: bool = False) -> SimpleNamespace:
            assert dry_run is False
            nonlocal active_calls, max_active_calls
            with lock:
                active_calls += 1
                max_active_calls = max(max_active_calls, active_calls)
            time.sleep(0.02)
            with lock:
                active_calls -= 1
            return SimpleNamespace(
                run_id=f"run-{self._definition.workspace_slug}", status="completed", failed_providers=[]
            )

    def orchestrator_factory(definition: ScheduleDefinition) -> object:
        return FakeOrchestrator(definition)

    executor = AsyncScanExecutor(
        provider_limits={"openai": 1},
        jitter_range_seconds=(0.0, 0.0),
        orchestrator_factory=orchestrator_factory,
    )

    results = await executor.execute([_job("one"), _job("two")])

    assert [result.status for result in results] == ["executed", "executed"]
    assert max_active_calls == 1


@pytest.mark.asyncio
async def test_executor_applies_jitter_before_provider_execution() -> None:
    sleep_calls: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleep_calls.append(delay)

    class FakeOrchestrator:
        _definition: ScheduleDefinition

        def __init__(self, definition: ScheduleDefinition) -> None:
            self._definition = definition

        def scan(self, dry_run: bool = False) -> SimpleNamespace:
            assert dry_run is False
            return SimpleNamespace(
                run_id=f"run-{self._definition.workspace_slug}", status="completed", failed_providers=[]
            )

    def orchestrator_factory(definition: ScheduleDefinition) -> object:
        return FakeOrchestrator(definition)

    executor = AsyncScanExecutor(
        jitter_range_seconds=(0.05, 0.2),
        sleep=fake_sleep,
        jitter=lambda _min, _max: 0.123,
        orchestrator_factory=orchestrator_factory,
    )

    results = await executor.execute([_job("jitter")])

    assert results[0].status == "executed"
    assert sleep_calls == [0.123]


@pytest.mark.asyncio
async def test_executor_caps_retries_with_exponential_backoff() -> None:
    sleep_calls: list[float] = []
    attempts = 0

    async def fake_sleep(delay: float) -> None:
        sleep_calls.append(delay)

    class FailingOrchestrator:
        _definition: ScheduleDefinition

        def __init__(self, definition: ScheduleDefinition) -> None:
            self._definition = definition

        def scan(self, dry_run: bool = False) -> SimpleNamespace:
            assert dry_run is False
            nonlocal attempts
            attempts += 1
            raise RuntimeError("boom")

    def orchestrator_factory(definition: ScheduleDefinition) -> object:
        return FailingOrchestrator(definition)

    executor = AsyncScanExecutor(
        jitter_range_seconds=(0.05, 0.2),
        max_retries=2,
        backoff_base_seconds=0.5,
        sleep=fake_sleep,
        jitter=lambda _min, _max: 0.05,
        orchestrator_factory=orchestrator_factory,
    )

    results = await executor.execute([_job("retry")])

    assert results[0].status == "failed"
    assert attempts == 3
    assert sleep_calls == [0.05, 0.5, 0.05, 1.0, 0.05]


def test_scheduler_executes_due_jobs_via_executor() -> None:
    class StubExecutor:
        def __init__(self) -> None:
            self.jobs: list[ScheduledScanJob] = []

        def run(self, jobs: Sequence[ScheduledScanJob]) -> list[ExecutionResult]:
            self.jobs.extend(jobs)
            return [
                ExecutionResult(
                    schedule_id=job.schedule_id,
                    workspace_slug=job.definition.workspace_slug,
                    status="executed",
                    run_id=f"run-{job.schedule_id}",
                )
                for job in jobs
            ]

    executor = StubExecutor()
    scheduler = ScanScheduler(executor=executor)
    schedule_id = scheduler.add_schedule(ScheduleDefinition(workspace_slug="acme"))

    results = scheduler.run_once()

    assert [job.schedule_id for job in executor.jobs] == [schedule_id]
    assert results[0].status == "executed"
    assert results[0].run_id == f"run-{schedule_id}"
