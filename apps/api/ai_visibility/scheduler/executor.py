import asyncio
import concurrent.futures
import random
from collections.abc import Awaitable, Callable, Coroutine, Sequence
from dataclasses import dataclass
from typing import TypeVar, cast

from ai_visibility.scheduler.models import ExecutionResult, ScheduleDefinition

T = TypeVar("T")

SleepFn = Callable[[float], Awaitable[object]]
OrchestratorFactory = Callable[[ScheduleDefinition], object]


@dataclass(frozen=True, slots=True)
class ScheduledScanJob:
    schedule_id: str
    definition: ScheduleDefinition
    dry_run: bool = False


@dataclass(frozen=True, slots=True)
class ScanExecutionOutcome:
    run_id: str | None
    failed: bool
    error_message: str | None


class AsyncScanExecutor:
    _provider_limits: dict[str, int]
    _default_provider_limit: int
    _jitter_range_seconds: tuple[float, float]
    _max_retries: int
    _backoff_base_seconds: float
    _sleep: SleepFn
    _jitter: Callable[[float, float], float]
    _orchestrator_factory: OrchestratorFactory
    _provider_semaphores: dict[str, asyncio.Semaphore]

    def __init__(
        self,
        *,
        provider_limits: dict[str, int] | None = None,
        default_provider_limit: int = 1,
        jitter_range_seconds: tuple[float, float] = (0.05, 0.2),
        max_retries: int = 3,
        backoff_base_seconds: float = 0.25,
        sleep: SleepFn | None = None,
        jitter: Callable[[float, float], float] | None = None,
        orchestrator_factory: OrchestratorFactory | None = None,
    ) -> None:
        self._provider_limits = provider_limits or {}
        self._default_provider_limit = max(1, default_provider_limit)
        self._jitter_range_seconds = jitter_range_seconds
        self._max_retries = max(0, max_retries)
        self._backoff_base_seconds = max(0.0, backoff_base_seconds)
        self._sleep = sleep or asyncio.sleep
        self._jitter = jitter or random.uniform
        self._orchestrator_factory = orchestrator_factory or self._build_orchestrator
        self._provider_semaphores = {}

    def run(self, jobs: Sequence[ScheduledScanJob]) -> list[ExecutionResult]:
        if not jobs:
            return []
        return self._run_async(self.execute(jobs))

    def _run_async(self, coro: Coroutine[object, object, T]) -> T:
        try:
            _ = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        except RuntimeError:
            return asyncio.run(coro)

    async def execute(self, jobs: Sequence[ScheduledScanJob]) -> list[ExecutionResult]:
        if not jobs:
            return []

        self._provider_semaphores = {}
        results: list[ExecutionResult | None] = [None] * len(jobs)
        queue: asyncio.Queue[tuple[int, ScheduledScanJob] | None] = asyncio.Queue()

        for indexed_job in enumerate(jobs):
            await queue.put(indexed_job)

        worker_count = max(1, len(jobs))
        for _ in range(worker_count):
            await queue.put(None)

        workers = [asyncio.create_task(self._worker(queue, results)) for _ in range(worker_count)]
        await queue.join()
        _ = await asyncio.gather(*workers)
        return [result for result in results if result is not None]

    async def _worker(
        self,
        queue: asyncio.Queue[tuple[int, ScheduledScanJob] | None],
        results: list[ExecutionResult | None],
    ) -> None:
        while True:
            queued_item = await queue.get()
            try:
                if queued_item is None:
                    return

                index, job = queued_item
                results[index] = await self._execute_job(job)
            finally:
                queue.task_done()

    async def _execute_job(self, job: ScheduledScanJob) -> ExecutionResult:
        if job.dry_run:
            return ExecutionResult(
                schedule_id=job.schedule_id,
                workspace_slug=job.definition.workspace_slug,
                status="dry_run",
            )

        last_error_message: str | None = None
        for attempt in range(self._max_retries + 1):
            try:
                _ = await self._sleep(self._next_jitter_seconds())
                semaphore = self._semaphore_for(job.definition.provider)
                async with semaphore:
                    outcome = await asyncio.to_thread(self._scan_job, job.definition)

                if outcome.failed:
                    raise RuntimeError(outcome.error_message or "Scheduled scan failed")

                return ExecutionResult(
                    schedule_id=job.schedule_id,
                    workspace_slug=job.definition.workspace_slug,
                    status="executed",
                    run_id=outcome.run_id,
                )
            except Exception as exc:
                last_error_message = str(exc)
                if attempt >= self._max_retries:
                    break
                _ = await self._sleep(self._backoff_seconds(attempt))

        return ExecutionResult(
            schedule_id=job.schedule_id,
            workspace_slug=job.definition.workspace_slug,
            status="failed",
            error_message=last_error_message,
        )

    def _scan_job(self, definition: ScheduleDefinition) -> ScanExecutionOutcome:
        orchestrator = self._orchestrator_factory(definition)
        scan = cast(Callable[..., object], getattr(orchestrator, "scan"))
        scan_result = scan(dry_run=False)
        status = str(getattr(scan_result, "status", "failed"))
        failed_providers = cast(list[str], getattr(scan_result, "failed_providers", []))
        error_message = cast(str | None, getattr(scan_result, "error_message", None))
        run_id = cast(str | None, getattr(scan_result, "run_id", None))
        return ScanExecutionOutcome(
            run_id=run_id,
            failed=status == "failed",
            error_message=error_message,
        )

    def _build_orchestrator(self, definition: ScheduleDefinition) -> object:
        from ai_visibility.runs.orchestrator import RunOrchestrator

        return RunOrchestrator(
            workspace_slug=definition.workspace_slug,
            provider=definition.provider,
            model=definition.model,
        )

    def _semaphore_for(self, provider: str) -> asyncio.Semaphore:
        semaphore = self._provider_semaphores.get(provider)
        if semaphore is None:
            semaphore = asyncio.Semaphore(self._provider_limit(provider))
            self._provider_semaphores[provider] = semaphore
        return semaphore

    def _provider_limit(self, provider: str) -> int:
        limit = self._provider_limits.get(provider, self._default_provider_limit)
        return max(1, limit)

    def _next_jitter_seconds(self) -> float:
        minimum, maximum = self._jitter_range_seconds
        if maximum < minimum:
            minimum, maximum = maximum, minimum
        return max(0.0, self._jitter(minimum, maximum))

    def _backoff_seconds(self, attempt: int) -> float:
        return self._backoff_base_seconds * (1 << attempt)
