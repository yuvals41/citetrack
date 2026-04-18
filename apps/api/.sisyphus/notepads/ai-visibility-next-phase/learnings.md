- Added provider-agnostic contracts under `ai_visibility/contracts/scan_contracts.py` with strict `extra="forbid"` and required version metadata on entities that drive longitudinal comparisons.
- Added JSON fixtures under `tests/contracts/fixtures/` for all new evidence entities so contract tests can validate schema shape without touching live providers.
- Enforced version metadata via pydantic required fields; negative coverage uses missing `rule_version` fixture to assert validation failure.
- Added strategy source-of-truth module `ai_visibility/runs/scan_strategy.py` with versioned defaults (`v1`) and explicit execution modes (`HIGH_FIDELITY`, `WEB_SEARCH`, `DIRECT`) per provider.
- `get_strategy_for_mode()` now applies scan-mode prompt budgets (onboarding=5, scheduled=20) while preserving model, retry, and cost guardrails for chatgpt/gemini/anthropic/perplexity.
- `validate_strategy()` enforces non-empty strategy versions, positive total ceilings, positive prompt budgets for enabled providers, and a 3x ceiling sanity check across provider budgets.
- Added `AbstractDatabase`, `SQLiteDatabase`, `PostgreSQLDatabase`, and `get_database()` in `ai_visibility/storage/database.py` while keeping `Database` as the SQLite-compatible default to avoid repository and CLI regressions.
- Extended `ai_visibility/storage/schema.sql` with additive next-phase tables and kept legacy `citations` untouched; the new prompt-level citation scaffold lives in `prompt_execution_citations` because SQLite cannot host a second `citations` table without altering the existing one.

## Task 4: Fixture Expansion (Prompt Catalog + Demo Workspaces)

- Added `PROMPT_VERSION = "v1"` module-level constant to `ai_visibility/prompts/default_set.py` for catalog versioning.
- Expanded `seed_demo()` in `ai_visibility/cli.py` with 3 new fixture workspaces:
  - `acme-saas`: Standard B2B SaaS brand (no location), exercises normal scan scenario
  - `local-plumber`: Local service brand (Denver, Colorado, US), exercises location-aware scan edge case
  - `echo-brand`: Ambiguous brand name (Echo), exercises competitor name collision edge case (Amazon Echo, Echelon Fitness)
- All 5 demo workspaces (acme, beta-brand, acme-saas, local-plumber, echo-brand) are idempotent via `get_by_slug()` check before create.
- Updated test expectations in `tests/onboarding/test_seed_demo.py`:
  - Changed workspace count assertions from 2 to 5 in `test_seed_demo_creates_or_skips_workspaces` and `test_cli_seed_demo_creates_or_skips_workspaces`
  - Added 3 new test methods to validate acme-saas, local-plumber, and echo-brand fixture creation and location fields
- All 414 tests pass (20 seed_demo tests + 394 others).
- Evidence files captured:
  - `.sisyphus/evidence/task-4-seed-demo.json`: seed-demo output showing 0 created, 5 skipped (idempotent second run)
  - `.sisyphus/evidence/task-4-list-prompts.json`: list-prompts output showing all 20 prompts with version metadata
- Commit: `test(fixtures): expand prompt catalog and demo workspaces` (6 files changed, 834 insertions)

## Task 5: Orchestrator/Adapter Split

- `RunOrchestrator` now acts as a coordinator: strategy lookup, prompt render, adapter dispatch, lifecycle transitions, and run persistence only.
- Added adapter seam under `ai_visibility/llm/adapters/` with `ScanAdapter` interface and `AdapterResult` contract; `GatewayScanAdapter` wraps existing provider gateway and `StubAdapter` enables deterministic tests.
- Coordinator validates adapter output via `AdapterResult.model_validate(...)`; malformed payloads now fail fast and set run status to `failed`.
- Lifecycle statuses align on `queued`, `running`, `partial`, `failed`, `completed` (with `dry_run` retained only for non-persistent dry-run responses).
- Added focused coordinator tests in `tests/runs/test_orchestrator.py` for lifecycle assertions, adapter dispatch shape, and malformed adapter output rejection.

## [Task 5 Fix] Mention persistence pattern
ExtractionPipeline and MentionRepository must be called inside orchestrator.scan()
after the adapter loop to persist mentions/citations. The status "completed_with_partial_failures"
(not LifecycleStatus.PARTIAL.value which equals "partial") must be used when failed_prompts > 0.
ScanResult Literal must include "completed_with_partial_failures".

## [Task 5 Fix] Test status string: old "partial" -> "completed_with_partial_failures"

## [Guardrail Fix] Canonical citations/status enforcement

- Removed legacy `CREATE TABLE citations` from `ai_visibility/storage/schema.sql`; canonical citation table remains `prompt_execution_citations`.
- Normalized lifecycle status strings to `completed_with_partial_failures` in contracts + orchestrator and removed standalone `partial` enum/literal status values.
- To keep mention persistence without the legacy table, mentions now store `citation_url`, `citation_domain`, and `citation_status` inline; `MentionRepository` writes/reads those columns directly.
- Updated storage/e2e tests that queried `citations` to assert against mention citation columns and canonical status values.
