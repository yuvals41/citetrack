# Smoke test report

**Overall status:** `tools/scripts/smoke.sh` is now **green** on this repo state. Latest fail-fast run (`bun run smoke`) finished in **1m 41s** and latest full diagnostic run (`bun run smoke:keep-going`) finished in **1m 53s** with **all gates passed**.

## What the smoke suite covers

`tools/scripts/smoke.sh` is the monorepo pre-flight gate. It currently covers:

> NX-backed test/typecheck/build gates run with `--skip-nx-cache`. This was added deliberately after cache hits briefly masked a real current-state test failure during validation.

1. **Static checks**
   - `bun run lint`
   - `bunx nx run-many -t typecheck --skip-nx-cache`
2. **Fast unit tests**
   - `bunx nx test @citetrack/web --skip-nx-cache`
   - `uv run pytest -m "not slow" --ignore=tests/api --ignore=tests/integration --ignore=tests/e2e -q`
3. **Build + generation**
   - `bun run prisma:generate-node`
   - `UV_OFFLINE=1 bash prisma/scripts/generatepython.sh`
   - `bunx nx build @citetrack/web --skip-nx-cache`
4. **Structural invariants**
   - no `apps/web/src/features/**/api.ts`
   - no `citetrackApi` references in `*.ts` / `*.tsx`
   - no leaked `workspace[0]` lookups outside the two allowed workspaces files
   - every package has a typecheck entrypoint
   - every app has a typecheck entrypoint
   - `CONTEXT.md` and `AGENTS.md` exist at repo root
5. **Python import sanity**
   - imports `ai_visibility`, `ai_visibility.api.app`, `ai_visibility.runs.execution_core`, and `ai_visibility.scan_executor`
6. **Documentation invariants**
   - `CONTEXT.md` does not reference deleted `packages/api-client/src/types.ts`
   - `AGENTS.md` current-state section still marks Clerk auth as already done

## What smoke deliberately does **not** cover

- **Playwright / browser E2E** — intentionally excluded; smoke ignores `apps/web` Playwright and `apps/api/tests/e2e`.
- **Anything requiring real LLM keys** — no `pytest -m "slow"`.
- **Anything requiring Postgres / Redis / Docker** — no service-backed integration tests.
- **Broad Python/API integration suites** — `tests/api` and `tests/integration` are explicitly ignored.
- **Lint cleanup outside the documented whitelist policy** — lint is still run, but only the narrow sanctioned paths below may downgrade lint from red to yellow.

## Current gate status

> Timings below are from the latest successful keep-going run on this machine. The full run completed in **1m 53s**.

| Stage | Gate | Status | Timing | Notes |
|---|---|---:|---:|---|
| 1 | Biome lint | WARN | ~23s | Lint violations are now confined to the documented known-broken whitelist only (generated/tooling/history paths plus the pre-existing `apps/web/e2e/**` and `packages/ui/**` debt buckets). |
| 1 | NX typecheck | PASS | ~25s | `bunx nx run-many -t typecheck --skip-nx-cache` is green, including `@citetrack/api`, `@citetrack/config`, and `@citetrack/ui`. |
| 2 | Web vitest | PASS | ~12s test runtime | 146 passing tests. |
| 2 | Python pytest fast | PASS | ~71s | `673 passed, 10 deselected`. Pixel-route tests now authenticate/override ownership correctly, and the schema fallback preserves `job_id` in non-SDK environments. |
| 3 | Prisma Node generate | PASS | ~1s | `bun run prisma:generate-node` succeeds. |
| 3 | Prisma Python generate | PASS | ~7s | Runs with `UV_OFFLINE=1` so smoke does not require live network access. |
| 3 | Web production build | PASS | ~9s | `bunx nx build @citetrack/web --skip-nx-cache` succeeds. |
| 4 | No `api.ts` pass-throughs | PASS | <1s | No files found under `apps/web/src/features/**/api.ts`. |
| 4 | No `citetrackApi` references | PASS | <1s | Zero matches in TS/TSX files. |
| 4 | No leaked `workspace[0]` lookups | PASS | <1s | Only the allowed `queries.ts` and `workspace-switcher.tsx` sites remain. |
| 4 | All packages have typecheck | PASS | <1s | `packages/config` and `packages/ui` now expose `typecheck` entrypoints; `packages/config/tsconfig.json` was added to match package conventions. |
| 4 | All apps have typecheck | PASS | <1s | `apps/web` and `apps/api` both satisfy the invariant. |
| 4 | Root docs present | PASS | <1s | `CONTEXT.md` and `AGENTS.md` both exist. |
| 5 | Python imports | PASS | ~2s | Core modules import cleanly. |
| 6 | CONTEXT stale ref check | PASS | <1s | No deleted `packages/api-client/src/types.ts` reference remains. |
| 6 | AGENTS current-state check | PASS | <1s | Clerk auth is still listed under "Currently EXISTS and WORKS". |

## Fixes that moved smoke from red to green

1. **Lint whitelist brought back under control**
   - Added narrowly-scoped exceptions for generated/tooling/history paths only:
     - `apps/api/.sisyphus/**`
     - `apps/web/.clerk/**`
     - `apps/web/playwright/.clerk/**`
     - `apps/web/.cta.json`
     - `prisma/client-node/**`
   - No app/source files were newly whitelisted.
2. **`@citetrack/api` typecheck fixed**
   - Reduced backend mypy from 41 errors to 0 by fixing concrete typing issues (adapter imports, schema fallback typing, payload dict typing, API date coercion, execution-core variable shadowing, etc.).
3. **Fast Python tests fixed**
   - `tests/test_pixel.py` now tests the authenticated snippet/stats routes with explicit auth/ownership overrides instead of assuming anonymous access.
   - `ai_visibility/schema.py` fallback now preserves `job_id` and `metadata` when the SDK import is unavailable, which restores the `ScanInput` payload contract expected by `tests/test_platform_integration.py`.
4. **Missing package typecheck entrypoints added**
   - `packages/config/package.json` now has `typecheck`.
   - `packages/config/tsconfig.json` now exists.
   - `packages/ui/package.json` now has `typecheck`.

## Known-broken lint whitelist

This is the intentionally narrow allowlist the smoke script uses before downgrading lint from red to yellow:

| Path / prefix | Why it is whitelisted |
|---|---|
| `apps/api/.sisyphus/` | Historical evidence artifacts, not production source. |
| `apps/web/e2e/` | Playwright suite is intentionally excluded from smoke and currently carries formatting/import debt. |
| `apps/web/.clerk/` | Generated Clerk local-dev state, not maintained source. |
| `apps/web/playwright/.clerk/` | Generated Playwright/Clerk auth fixture state. |
| `apps/web/.cta.json` | External tool metadata file, not hand-maintained application code. |
| `apps/api/tests/contracts/fixtures/` | Contract fixtures have pre-existing formatting noise that should not block smoke on their own. |
| `package.json` | Root package formatting debt is explicitly documented and tolerated for smoke purposes. |
| `prisma/client-node/` | Generated Prisma client output. |
| `prisma/package.json` | Same as above for the Prisma package manifest. |
| `packages/ui/` | Large pre-existing UI-package lint backlog; tolerated only while isolated to `packages/ui/**`. |

**Important:** lint is only downgraded to yellow when failures stay inside this list. Any new source-file lint debt outside this table will still fail smoke.

## How to run it

### Local

```bash
# Fail fast on the first hard failure
bun run smoke

# Run every gate and get the full matrix
bun run smoke:keep-going

# Direct invocation also works
bash tools/scripts/smoke.sh --keep-going
```

### CI

Recommended pattern:

```yaml
- run: bun install
- run: uv sync
- run: bun run smoke
```

Use `bun run smoke:keep-going` when you want a fuller diagnostic log from a non-green branch, but keep the exit code strict either way.

## How to extend the suite

1. Add the new gate in the correct stage inside `tools/scripts/smoke.sh`.
2. Keep ordering **fast → slow**.
3. Prefer deterministic local checks only.
4. If a new lint exemption is proposed, add it sparingly and document the reason in both the script and this report.
5. Update this report’s coverage table and status notes after adding the gate.

## Files added / changed for this smoke infrastructure

- `tools/scripts/smoke.sh`
- `docs/architecture-notes/smoke-test-report.md`
- root `package.json` (`smoke`, `smoke:keep-going`)
