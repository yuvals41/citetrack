import uuid
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from typing import Protocol

from ai_visibility.scheduler.executor import AsyncScanExecutor, ScheduledScanJob
from ai_visibility.scheduler.models import ExecutionResult, ScheduleDefinition


class ExecutorLike(Protocol):
    def run(self, jobs: Sequence[ScheduledScanJob]) -> list[ExecutionResult]: ...


class ScanScheduler:
    def __init__(
        self,
        *,
        provider_limits: dict[str, int] | None = None,
        jitter_range_ms: tuple[int, int] = (50, 200),
        max_retries: int = 3,
        retry_backoff_seconds: float = 0.25,
        executor: ExecutorLike | None = None,
    ) -> None:
        self._schedules: dict[str, ScheduleDefinition] = {}
        self._last_run: dict[str, datetime] = {}
        self._running: set[str] = set()
        self._executor: ExecutorLike
        self._executor = executor or AsyncScanExecutor(
            provider_limits=provider_limits,
            jitter_range_seconds=(jitter_range_ms[0] / 1000, jitter_range_ms[1] / 1000),
            max_retries=max_retries,
            backoff_base_seconds=retry_backoff_seconds,
        )

    def add_schedule(self, definition: ScheduleDefinition) -> str:
        schedule_id = str(uuid.uuid4())
        self._schedules[schedule_id] = definition
        return schedule_id

    def list_schedules(self) -> list[dict[str, object]]:
        return [
            {"schedule_id": schedule_id, **definition.model_dump()}
            for schedule_id, definition in self._schedules.items()
        ]

    def is_due(self, schedule_id: str) -> bool:
        definition = self._schedules.get(schedule_id)
        if not definition or not definition.enabled:
            return False

        last_run = self._last_run.get(schedule_id)
        if last_run is None:
            return True

        elapsed = datetime.now(timezone.utc) - last_run
        return elapsed >= timedelta(hours=definition.interval_hours)

    def get_missed_runs(self, schedule_id: str) -> int:
        definition = self._schedules.get(schedule_id)
        if not definition:
            return 0

        last_run = self._last_run.get(schedule_id)
        if last_run is None:
            return 1

        elapsed = datetime.now(timezone.utc) - last_run
        missed = int(elapsed.total_seconds() / (definition.interval_hours * 3600)) - 1
        return max(0, missed)

    def execute_due(self, schedule_id: str, dry_run: bool = False) -> ExecutionResult:
        prepared = self._prepare_job(schedule_id, dry_run=dry_run)
        if isinstance(prepared, ExecutionResult):
            return prepared

        return self._execute_jobs([prepared])[0]

    def _prepare_job(self, schedule_id: str, dry_run: bool = False) -> ExecutionResult | ScheduledScanJob:
        definition = self._schedules.get(schedule_id)
        if not definition:
            return ExecutionResult(
                schedule_id=schedule_id,
                workspace_slug="unknown",
                status="failed",
                error_message="Schedule not found",
            )

        if schedule_id in self._running:
            return ExecutionResult(
                schedule_id=schedule_id,
                workspace_slug=definition.workspace_slug,
                status="skipped_duplicate",
            )

        if not self.is_due(schedule_id):
            return ExecutionResult(
                schedule_id=schedule_id,
                workspace_slug=definition.workspace_slug,
                status="skipped_not_due",
            )

        self._running.add(schedule_id)
        return ScheduledScanJob(schedule_id=schedule_id, definition=definition, dry_run=dry_run)

    def _execute_jobs(self, jobs: Sequence[ScheduledScanJob]) -> list[ExecutionResult]:
        try:
            results = self._executor.run(jobs)
            for result in results:
                if result.status == "executed":
                    self._last_run[result.schedule_id] = datetime.now(timezone.utc)
            return results
        finally:
            for job in jobs:
                self._running.discard(job.schedule_id)

    def run_once(self, dry_run: bool = False) -> list[ExecutionResult]:
        if getattr(self.execute_due, "__func__", None) is not ScanScheduler.execute_due:
            fallback_results: list[ExecutionResult] = []
            for schedule_id in list(self._schedules.keys()):
                if self.is_due(schedule_id):
                    fallback_results.append(self.execute_due(schedule_id, dry_run=dry_run))
            return fallback_results

        planned_results: list[ExecutionResult | ScheduledScanJob] = []
        for schedule_id in list(self._schedules.keys()):
            if self.is_due(schedule_id):
                planned_results.append(self._prepare_job(schedule_id, dry_run=dry_run))

        queued_jobs = [item for item in planned_results if isinstance(item, ScheduledScanJob)]
        executed_results = iter(self._execute_jobs(queued_jobs)) if queued_jobs else iter(())

        results: list[ExecutionResult] = []
        for item in planned_results:
            if isinstance(item, ExecutionResult):
                results.append(item)
            else:
                results.append(next(executed_results))
        return results
