# Scan Entry-Point Map

## Files

### scan_executor.py
**Role:** Stateless scan-execution module for off-process jobs. It renders prompts, chooses provider adapters, executes prompts with bounded concurrency, extracts mentions/citations, and computes a `ScanOutput` without touching Prisma or repositories.

**Interface:** Public surface is effectively one async interface: `execute_scan(scan_input, on_progress=None) -> ScanOutput` (plus internal helpers). Surface area is small; implementation is ~456 LoC, so this is a deep module inside the stateless execution seam.

**Callers:** Production callers are `ai_visibility/worker_job.py` and `ai_visibility/job.py`; tests also call it directly in `tests/test_scan_executor.py`. Entry-point category is library function used by RabbitMQ and K8s job adapters.

**Depth:** **Deep, but duplicated.** The interface is narrow and hides real leverage (adapter setup, prompt fan-out, extraction, metrics), but much of the same hidden complexity also exists in `runs/orchestrator.py`, which reduces its leverage at the repo level.

### worker_job.py
**Role:** RabbitMQ topic consumer for scan jobs. It receives a `ScanInput` payload from `scan.ai_visibility`, sets Redis job state, forwards progress, calls `execute_scan`, and writes the terminal result back to Redis.

**Interface:** Public surface is one decorated async handler: `handle_scan(payload, correlation_id=None, pattern=None) -> dict`. Implementation is ~119 LoC and mostly messaging/status plumbing.

**Callers:** No in-repo Python code calls it directly; the runtime caller is `PikaApp` via `@pika_app.topic("scan.ai_visibility")`. Entry-point category is message-bus adapter.

**Depth:** **Shallow.** This module is a thin adapter seam around the deeper `scan_executor.execute_scan` interface and Redis status store.

### job.py
**Role:** Standalone K8s/one-shot job entry point. It reads `JOB_PAYLOAD`/`JOB_DATA` from environment, validates `ScanInput`, calls `execute_scan`, writes status to Redis, prints JSON, and exits.

**Interface:** Public surface is one async `main()` reached through `if __name__ == "__main__"`. Implementation is ~153 LoC and almost all of it is bootstrap/error/status handling.

**Callers:** No production Python module imports it; the caller is the process runtime that invokes `python -m ai_visibility.job` or equivalent container command. Entry-point category is process/CLI adapter for batch execution.

**Depth:** **Shallow.** This is another adapter seam around the same deep stateless execution interface used by `worker_job.py`.

### worker.py
**Role:** ARQ scheduled-scan worker and cron shell. It finds due workspaces, runs scans across a fixed provider list through `RunOrchestrator`, computes alert deltas, sends notifications, and exposes `WorkerSettings` for the ARQ runtime.

**Interface:** Public surface is `run_scheduled_scans(ctx)`, `compute_next_scan_display(...)`, and `WorkerSettings`. That is a somewhat wider surface than the two job adapters, while implementation is ~206 LoC with scheduling, alerting, and orchestration concerns mixed together.

**Callers:** `cli.run_scheduler(once=True)` imports and calls `run_scheduled_scans`; ARQ calls `WorkerSettings`/`cron(run_scheduled_scans, ...)`; deployment wiring references `ai_visibility.worker.WorkerSettings` in `docker-compose.yml` and README. Entry-point category is scheduled worker / cron adapter.

**Depth:** **Mostly shallow, with a little policy.** It owns scheduling and alert-postprocessing policy, but the scan-execution leverage itself is delegated to `RunOrchestrator`.

### runs/orchestrator.py
**Role:** Stateful scan/run orchestration module for the main app path. It loads workspace context from Prisma, renders prompts, executes provider calls, extracts evidence, computes metrics, persists scan job/execution/prompt/observation/citation/run records, and returns `ScanResult`.

**Interface:** Public surface is the `RunOrchestrator` class, mainly `scan(dry_run=False)` and `list_runs()`, plus the `ScanResult` model. Interface surface is still relatively small compared with ~847 LoC of implementation, so this is a deep module with high leverage.

**Callers:** Production callers are `api/scans_routes.py`, `api/onboarding_routes.py`, `cli.py`, `worker.py`, and `scheduler/executor.py`; tests across `tests/runs/`, `tests/e2e/`, and others also rely on it. Entry-point category is stateful library/orchestration interface used by HTTP, CLI, and scheduled worker adapters.

**Depth:** **Deep.** If deleted, the complexity would explode back into every HTTP route, CLI path, and scheduler path that currently calls `scan()`.

## Overlap analysis

The fragmentation is **partly legitimate and partly real duplication**.

Legitimate decomposition:
- `worker_job.py` and `job.py` are two shallow adapters for two different seams: message-bus consumption vs one-shot process execution.
- `worker.py` is a different seam again: scheduled multi-workspace execution plus alert side effects.
- `runs/orchestrator.py` is the main stateful application interface used by HTTP routes, onboarding, CLI, and the scheduler.

Real overlap / redundancy:
- `scan_executor.py` and `runs/orchestrator.py` both contain the same core scan-execution shape: resolve provider config, build/lookup adapters, render prompts, inject location, run prompt fan-out with `Semaphore(3)`, extract mentions/citations, and compute metrics.
- That means the repo currently has **two deep modules covering the same scan domain**, one stateless and one stateful. The adapter files are not the problem; the duplicate execution core is.
- `worker_job.py` and `job.py` also duplicate some Redis-status/result-marshalling code, but that duplication is small and local compared with the bigger execution overlap.

Deletion test:
- Delete `worker_job.py` or `job.py` and the complexity mostly reappears in a single deployment adapter. That is acceptable shallow duplication.
- Delete `worker.py` and scheduling/alert complexity reappears in the scheduler shell and CLI once-run path. Also acceptable.
- Delete `scan_executor.py` and stateless execution complexity reappears in two adapters — but it is not unique complexity, because a near-copy already exists in `runs/orchestrator.py`.
- Delete `runs/orchestrator.py` and the main app loses its scan interface; complexity would be scattered across HTTP, onboarding, CLI, and scheduled execution paths. That is high leverage.

## Deep module candidate

The actual scan-execution domain logic **currently lives most authoritatively in** `apps/api/ai_visibility/runs/orchestrator.py`.

It exposes the strongest in-repo interface: `RunOrchestrator(...).scan(dry_run=False) -> ScanResult`, and nearly every first-class application entry point calls into it. The other files are mostly entry-point adapters around either that interface (`worker.py`, HTTP routes, CLI, scheduler) or around a parallel stateless interface (`scan_executor.py`) that looks like an extracted core but has not become the single source of leverage yet.

Said differently: the hidden deep module candidate is not the adapter layer; it is the **scan execution engine embedded inside `RunOrchestrator`**. `scan_executor.py` is a competing extraction of that same engine.

## Recommendation

### Option A (no change)
Keep all five files as-is and treat them as legitimate entry-point decomposition.

**Why not:** this misses the real overlap. The shallow entry-point files are fine, but `scan_executor.py` vs `runs/orchestrator.py` is genuine redundancy.

### Option B (rename for clarity)
Keep the structure, but rename the shallow adapters so the seam is obvious:
- `worker_job.py` → `rabbitmq_scan_worker.py`
- `job.py` → `k8s_scan_job.py` or `batch_scan_job.py`
- `worker.py` → `scheduled_scan_worker.py`
- `scan_executor.py` → `stateless_scan_executor.py`

This increases leverage by making each module's entry-point category explicit without changing behavior.

### Option C (merge)
Do **not** merge all five files. Instead, target only the real duplicate seam: extract the shared prompt-execution engine so both `RunOrchestrator` and `scan_executor` call one deep interface, while keeping the current adapters separate.

**Why not now:** that is a real refactor, not a note-level cleanup. It is probably worthwhile later, but it is larger than the smallest change needed to reduce confusion today.

### Pick
**Pick: Option B (rename for clarity), and log a follow-up for a targeted core extraction later.**

Reason: the current fragmentation is **correct at the adapter level** but **confusing at the naming level**. Renaming gives immediate clarity about seam/category with low risk, while the deeper duplication between `scan_executor.py` and `runs/orchestrator.py` can be tracked as a separate architectural cleanup item instead of forcing a premature merge.
