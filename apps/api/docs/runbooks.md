# Operator Runbook: AI Visibility Scanner

**Audience:** Developers and operators running the AI Visibility Scanner in local dev or staging.
**Working directory for all commands:** `/path/to/ai-visibility` (repo root)

---

## Table of Contents

1. [Health Check](#1-health-check)
2. [Seed Demo Data](#2-seed-demo-data)
3. [Run a Scan](#3-run-a-scan)
4. [Scheduler Dry-Run](#4-scheduler-dry-run)
5. [Recommendations](#5-recommendations)
6. [Full Test Suite](#6-full-test-suite)
7. [Common Failure Modes](#7-common-failure-modes)
8. [Release Verification Checklist](#8-release-verification-checklist)

---

## 1. Health Check

Verify the API server is up and the database is reachable.

```bash
curl -s http://127.0.0.1:8000/api/v1/health
```

**Expected response:**
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

**Degraded response (database unreachable):**
```json
{
  "degraded": {
    "reason": "provider_failure",
    "message": "Database unavailable: ...",
    "recoverable": true
  }
}
```

**Start the server if not running:**
```bash
uv run uvicorn ai_visibility.api.routes:app --host 127.0.0.1 --port 8000
```

---

## 2. Seed Demo Data

Populate the database with demo workspaces, runs, and mentions. Safe to run multiple times — idempotent.

```bash
uv run python -m ai_visibility.cli seed-demo --format json
```

**Expected response:**
```json
{
  "status": "success",
  "workspaces_created": 5,
  "workspaces_skipped": 0,
  "runs_created": 2,
  "mentions_created": 2
}
```

If run a second time, `workspaces_skipped` will equal 5 and `workspaces_created` will be 0 — that's correct behavior.

**Demo workspaces created:**
- `acme` — Acme Corp (generic B2B brand)
- `beta-brand` — Beta Brand
- `acme-saas` — Acme SaaS (standard B2B SaaS, no location)
- `local-plumber` — Joe's Plumbing, Denver CO (local service brand)
- `echo-brand` — Echo (ambiguous brand name)

---

## 3. Run a Scan

### Dry-run (no API calls, no database writes)

```bash
uv run python -m ai_visibility.cli run-scan --workspace acme --dry-run --format json
```

### Live scan (requires provider API keys)

```bash
uv run python -m ai_visibility.cli run-scan --workspace acme --provider openai --format json
```

**Expected response (success):**
```json
{
  "run_id": "...",
  "workspace_slug": "acme",
  "status": "completed",
  "results_count": 3,
  "provider": "openai",
  "started_at": "2026-03-14T..."
}
```

**Partial failure response:**
```json
{
  "run_id": "...",
  "workspace_slug": "acme",
  "status": "completed_with_partial_failures",
  ...
}
```

Note: `completed_with_partial_failures` (not `partial`) is the correct status when some prompts fail.

### Check available providers

```bash
uv run python -m ai_visibility.cli doctor --format json
```

---

## 4. Scheduler Dry-Run

Test the scheduler without executing real scans or writing to the database.

```bash
uv run python -m ai_visibility.cli run-scheduler --once --dry-run --format json
```

**Expected response (jobs found and dry-run executed):**
```json
{
  "executed_jobs": 1,
  "results": [...]
}
```

**Degraded response (no due jobs):**
```json
{
  "degraded": {
    "reason": "scheduler_miss",
    "message": "Scheduler had no due jobs to execute",
    "recoverable": true
  }
}
```

A `scheduler_miss` degraded response is normal on a fresh database — no jobs are scheduled yet. Seed demo data first, then retry.

---

## 5. Recommendations

Get ranked recommendations for a workspace.

```bash
uv run python -m ai_visibility.cli recommend-latest --workspace acme --format json
```

**Expected response:**
```json
{
  "workspace": "acme",
  "recommendations": [
    {
      "rule_code": "low_visibility",
      "workspace_slug": "acme",
      ...
    }
  ],
  "explanations_enabled": true
}
```

**Empty recommendations (no scan history):**
```json
{
  "workspace": "acme",
  "recommendations": [],
  "explanations_enabled": true
}
```

---

## 6. Full Test Suite

Run all tests before any release.

```bash
uv run pytest tests/ -v --tb=short
```

Run only E2E and contract tests:

```bash
uv run pytest tests/e2e tests/contracts -v --tb=short
```

Run a specific test file:

```bash
uv run pytest tests/e2e/test_full_pipeline.py -v --tb=short
```

**Expected output:** All tests pass, zero failures.

---

## 7. Common Failure Modes

### `MISSING_API_KEY` degraded response

```json
{
  "degraded": {
    "reason": "missing_api_key",
    "message": "Missing API key for provider: openai",
    "recoverable": true
  }
}
```

**Fix:** Set the required environment variable:
```bash
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export PERPLEXITY_API_KEY=pplx-...
```

Or add them to `.env` in the repo root.

### `WORKSPACE_NOT_FOUND` degraded response

```json
{
  "degraded": {
    "reason": "workspace_not_found",
    "message": "Workspace not found: my-brand",
    "recoverable": true
  }
}
```

**Fix:** Create the workspace first:
```bash
uv run python -m ai_visibility.cli create-workspace --brand-name "My Brand" --workspace my-brand
```

Or seed demo data if you just need test workspaces:
```bash
uv run python -m ai_visibility.cli seed-demo
```

### `EMPTY_HISTORY` degraded response

```json
{
  "degraded": {
    "reason": "empty_history",
    "message": "No completed history found for workspace: acme",
    "recoverable": true
  }
}
```

**Fix:** Run a scan for the workspace:
```bash
uv run python -m ai_visibility.cli run-scan --workspace acme --dry-run
```

### Database file not found

```
sqlite3.OperationalError: unable to open database file
```

**Fix:** Check `DB_PATH` environment variable. Default is `ai_visibility.db` in the working directory.
```bash
export DB_PATH=/path/to/ai_visibility.db
```

### `completed_with_partial_failures` status

This is not an error — it means some prompts succeeded and some failed. The run still produced usable data. Check `error` field in the run record for details on which providers failed.

### Snapshot endpoints return empty data

The snapshot endpoints (`/api/v1/snapshot/*`) read from precomputed materialized views. If they return empty data after a scan, the matviews may not have refreshed yet.

**Fix:** In production (PostgreSQL), `pg_cron` refreshes matviews nightly. In development (SQLite), the snapshot data is computed on-demand from the `SnapshotRepository`.

---

## 8. Release Verification Checklist

Run these steps in order before tagging a release.

### Step 1: Seed and health check

```bash
uv run python -m ai_visibility.cli seed-demo --format json
curl -s http://127.0.0.1:8000/api/v1/health
```

Both must succeed with no `degraded` key in the response.

### Step 2: Scheduler dry-run

```bash
uv run python -m ai_visibility.cli run-scheduler --once --dry-run --format json
```

Must return `executed_jobs` >= 0 (degraded `scheduler_miss` is acceptable on fresh DB).

### Step 3: Full test suite

```bash
uv run pytest tests/ -v --tb=short
```

Zero failures required.

### Step 4: E2E and contract tests specifically

```bash
uv run pytest tests/e2e tests/contracts -v --tb=short
```

Zero failures required.

### Step 5: Verify API endpoints

```bash
curl -s http://127.0.0.1:8000/api/v1/workspaces
curl -s http://127.0.0.1:8000/api/v1/prompts
curl -s "http://127.0.0.1:8000/api/v1/snapshot/overview?workspace=acme"
curl -s "http://127.0.0.1:8000/api/v1/snapshot/findings?workspace=acme"
curl -s "http://127.0.0.1:8000/api/v1/snapshot/actions?workspace=acme"
```

All must return 200 with valid JSON (no `degraded` key, or `degraded` with `recoverable: true`).

### Step 6: Recommendations

```bash
uv run python -m ai_visibility.cli recommend-latest --workspace acme --format json
```

Must return `recommendations` array (may be empty if no scan history).

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_PATH` | `ai_visibility.db` | SQLite database file path |
| `OPENAI_API_KEY` | — | OpenAI API key (for openai provider) |
| `ANTHROPIC_API_KEY` | — | Anthropic API key (for anthropic provider) |
| `PERPLEXITY_API_KEY` | — | Perplexity API key (for perplexity provider) |
| `DATAFORSEO_LOGIN` | — | DataForSEO login email |
| `DATAFORSEO_PASSWORD` | — | DataForSEO API password |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `LLM_FRAMEWORK` | `openai` | Default LLM framework |

---

*Runbook version: 1.0 | Last updated: March 2026*
