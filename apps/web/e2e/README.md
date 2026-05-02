# @citetrack/web E2E Tests

Canonical real-browser smoke/auth/app-flow coverage for the Citetrack web app.

## Prerequisites

- Web dev server running automatically via Playwright `webServer` (`bunx vite dev --port 3002`)
- No separate backend process required for the current suite: authenticated app data is mocked at the network layer for determinism
- Clerk strategy: **A — Clerk testing tokens**
  - `apps/web/.env.local` already contains **test-mode** Clerk keys (`pk_test_...`, `sk_test_...`)
  - The suite uses a persistent seeded test user plus Clerk's Playwright helpers
  - This keeps sign-in/sign-out real while avoiding fragile shared backend state for dashboard/onboarding/brand flows

## Why strategy A

We have Clerk test keys locally, so the suite exercises real Clerk auth instead of stubbing it. Authenticated product flows still mock app API responses because the goal here is a stable frontend gate, not a backend seed orchestration layer.

If Clerk test keys are missing later, auth-required tests skip cleanly and `smoke.spec.ts` still runs.

## Run

From `apps/web/`:

```bash
bun run e2e
bun run e2e:smoke
bun run e2e:ui
bun run e2e:headed
```

From repo root:

```bash
bunx nx run @citetrack/web:e2e
```

## Suite Map

| File | Coverage | Auth required |
|---|---|---|
| `smoke.spec.ts` | root redirect, sign-in, sign-up, forgot-password, 404, title, initial console health | no |
| `auth.spec.ts` | sign-in UI, invalid credentials, valid sign-in, protected redirects, sign-out | partial |
| `onboarding.spec.ts` | 4-step wizard validation, canonical engine IDs, completion path | yes |
| `dashboard.spec.ts` | dashboard shell, KPI cards, charts, findings, actions, console health | yes |
| `brand-crud.spec.ts` | empty brand state, create, edit, alias add/remove, invalid domain | yes |
| `navigation.spec.ts` | sidebar routing, active nav state, page header updates, workspace switcher | yes |

## Determinism Rules

- No `page.waitForTimeout(...)`
- Auth state is isolated per test context via Playwright `storageState`
- App API responses are mocked per-page in `e2e/helpers/mock-api.ts`
- Brand/competitor mutations are in-memory and reset every test
- Slow flows are tagged with `@slow`

## Adding a Test

1. Pick the closest existing spec file before creating a new one
2. Prefer `data-testid` selectors for app-owned UI
3. Keep Clerk-real tests limited to auth behavior; mock app APIs for dashboard/product flows
4. Use `mockAuthenticatedApp(page, overrides)` for authenticated routes
5. Add test IDs only when a stable app-owned selector does not already exist

Quick template:

```ts
import { authFile } from "./global.setup";
import { mockAuthenticatedApp } from "./helpers/mock-api";
import { expect, test } from "./fixtures";

test.use({ storageState: authFile });

test("example flow", async ({ page }) => {
  await mockAuthenticatedApp(page);
  await page.goto("/dashboard");
  await expect(page.getByTestId("page-header-title")).toHaveText("Dashboard");
});
```

## CI Notes

- When CI is added, keep Clerk in **test mode** only
- Seed or update the persistent Clerk test user during Playwright setup
- Run `bunx nx run @citetrack/web:e2e` after typecheck/build
- Keep backend-independent mocks for frontend gate stability; add a separate full-stack E2E lane later if needed

## Traces and Reports

The suite records traces on retry and screenshots on failure.

```bash
bunx playwright show-report
```
