# apps/api Test Health

_Last triaged: 2026-05-03_
_Refactor commit: `c4d37180d2ecf1509493ac7ce8ed195ad62fdd47`_

## Summary

- Raw baseline before triage: **322 failed / 553 passed / 11 deselected** via `uv run pytest -m "not slow" --tb=no -q`
- Current baseline after triage + browser-E2E quarantine: **26 failed / 784 passed / 65 skipped / 11 deselected**
- Refactor-caused failures fixed: **1**
- Direct deferred failures remaining: **26 tests across 4 files**
- Browser-only environmental tests now quarantined: **65 tests across 2 files**
- Raw `322 failed` was heavily inflated by **230 order-dependent cascade failures** that disappear once browser E2E is skipped/excluded

## Refactor-Caused Failures Fixed

### A1 — Scan execution core extraction

| File | Test | Fix |
|------|------|-----|
| `tests/test_comprehensive.py` | `test_location_injection_only_for_gemini_and_grok` | Updated the test to use `ai_visibility.runs.execution_core.inject_location_prompt()` after location-prompt logic moved out of `RunOrchestrator` |

This was the only confirmed regression tied directly to the recent scan-execution refactor surface.

## Green-Set (largest clean subset)

`pytest-green-set`:

```bash
cd apps/api
uv run pytest -m "not slow" \
  --ignore=tests/e2e \
  --ignore=tests/test_pixel.py \
  --deselect=tests/test_platform_integration.py::TestJobEntryPoint::test_job_id_from_payload \
  -q
```

- Result: **769 passed / 11 deselected**
- Scope: **74 files**
- External services required: **none**
- Notes: excludes all current E2E debt, the import-order-sensitive `tests/test_pixel.py`, and the single `job_id` contract mismatch test

## Smoke Floor (fast refactor coverage)

`pytest-smoke-floor`:

```bash
cd apps/api
uv run pytest tests/runs/ tests/test_scan_executor.py tests/api/test_onboarding_routes.py -q
```

- Result: **70 passed**
- Scope: **9 files**
- Purpose: minimum fast suite covering the refactor hotspots (`execution_core`, `orchestrator`, `scan_executor`, onboarding provider-ID drift)

## Browser E2E Quarantine

Browser-only suites now skip automatically when the frontend dev server is not reachable at `http://localhost:3000`.

Implemented in:

- `tests/e2e/conftest.py`

Reason: the browser suites were producing `ERR_CONNECTION_REFUSED` failures and polluting the rest of the pytest run with follow-on failures.

## Pre-Existing Failures by Category

### B1 — Missing local frontend server (quarantined)

These require the web app running locally at `http://localhost:3000`.

| File | Tests affected | Symptom | Current handling |
|------|----------------|---------|------------------|
| `tests/e2e/test_full_e2e.py` | all 33 tests | `playwright._impl._errors.Error: Page.goto: net::ERR_CONNECTION_REFUSED` | auto-skipped if frontend is unavailable |
| `tests/e2e/test_ui_browser.py` | all 32 tests | `Page.goto` / hydration failures against `http://localhost:3000` | auto-skipped if frontend is unavailable |

### B2 — Legacy migration debt in old E2E/backend integration tests

These are not refactor regressions from this session. They are stale tests written against APIs that no longer exist.

| File | Tests affected | Symptom | Reason deferred |
|------|----------------|---------|-----------------|
| `tests/e2e/test_full_pipeline.py` | all 18 tests | `TypeError: WorkspaceRepository.__init__() got an unexpected keyword argument 'db_path'` | legacy SQLite-style repository construction no longer matches current Prisma-backed repositories |
| `tests/e2e/test_seeded_flow_regression.py` | all 5 tests | `TypeError: 'coroutine' object is not subscriptable` plus `coroutine 'seed_demo' was never awaited` warnings | tests still call async CLI helpers (`seed_demo`, `recommend_latest`) synchronously |

### B3 — Outdated route expectations in pixel tests

| File | Test | Symptom | Reason deferred |
|------|------|---------|-----------------|
| `tests/test_pixel.py` | `test_snippet_endpoint_returns_javascript_content_type` | expected `200`, got `401` | test assumes anonymous access, but `/api/v1/pixel/snippet/{workspace_id}` now requires auth |
| `tests/test_pixel.py` | `test_stats_endpoint_returns_mocked_payload` | expected `200`, got `401` | test assumes anonymous access, but `/api/v1/pixel/stats/{workspace_id}` now requires auth |

Additional note: `tests/test_pixel.py` is **import-order sensitive** when run alone because `ai_visibility.pixel.router` and `ai_visibility.api.routes` participate in a circular import during module import. In the full suite, earlier imports mask this; in isolated runs, collection can fail.

### B4 — Platform contract mismatch when SDK fallback is active

| File | Test | Symptom | Reason deferred |
|------|------|---------|-----------------|
| `tests/test_platform_integration.py` | `TestJobEntryPoint::test_job_id_from_payload` | `AttributeError: 'ScanInput' object has no attribute 'job_id'` | local fallback path (`BaseJobInput = BaseModel`) does not inject SDK-only fields; test assumes deployed-container behavior |

### E1 — Order-dependent cascade failures seen only in the raw baseline

These were **not independently broken**. They failed only in the original `322 failed` run because the browser E2E failures contaminated the rest of the session. Once browser E2E was quarantined, they passed again.

| File | Raw-suite failure count |
|------|-------------------------|
| `tests/services/test_competitor_discovery.py` | 38 |
| `tests/storage/test_deep_repositories.py` | 26 |
| `tests/onboarding/test_seed_demo.py` | 20 |
| `tests/test_scan_executor.py` | 18 |
| `tests/test_brand_entity.py` | 17 |
| `tests/test_google_ai_mode_serpapi.py` | 14 |
| `tests/llm/test_deep_gateway.py` | 11 |
| `tests/test_tier2_gaps_b.py` | 11 |
| `tests/test_deep_cli.py` | 10 |
| `tests/test_orchestrator_brand.py` | 8 |
| `tests/test_shopping_visibility.py` | 8 |
| `tests/llm/test_gateway.py` | 7 |
| `tests/test_tier2_gaps.py` | 6 |
| `tests/test_cli_recommendations.py` | 4 |
| `tests/runs/test_run_scan.py` | 4 |
| `tests/runs/test_asyncio_safety.py` | 3 |
| `tests/runs/test_deep_orchestrator.py` | 3 |
| `tests/runs/test_orchestrator.py` | 3 |
| `tests/scheduler/test_scheduler_controls.py` | 3 |
| `tests/storage/test_repositories.py` | 3 |
| `tests/runs/test_scan_persistence.py` | 2 |
| `tests/storage/test_workspace_repo.py` | 2 |
| `tests/storage/test_run_repo_validation.py` | 4 |
| `tests/runs/test_execution_core.py` | 1 |
| `tests/recommendations/test_data_flow.py` | 1 |

Treat these as **order-dependent / non-deterministic suite fallout**, not as independent product defects.

## Recommended Execution Modes

### Default local confidence run

```bash
cd apps/api
uv run pytest -m "not slow" \
  --ignore=tests/e2e \
  --ignore=tests/test_pixel.py \
  --deselect=tests/test_platform_integration.py::TestJobEntryPoint::test_job_id_from_payload \
  -q
```

### Browser E2E run

Start the frontend first, then run:

```bash
bunx nx dev @citetrack/web
cd apps/api
uv run pytest tests/e2e/test_full_e2e.py tests/e2e/test_ui_browser.py -q
```

### Legacy E2E debt bucket

Keep these separate from normal confidence runs until they are rewritten against current repository/CLI APIs:

```bash
cd apps/api
uv run pytest tests/e2e/test_full_pipeline.py tests/e2e/test_seeded_flow_regression.py -q
```
