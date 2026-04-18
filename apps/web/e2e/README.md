# Playwright E2E tests

## Run locally

From `apps/web`:

```bash
bunx playwright test
```

Run one file:

```bash
bunx playwright test e2e/landing.spec.ts
```

Run with the Playwright UI:

```bash
bunx playwright test --ui
```

## Traces and reports

The config records traces on the first retry.

To open the HTML report after a run:

```bash
bunx playwright show-report
```

## Notes for this phase

- These tests are designed to pass without `VITE_CLERK_PUBLISHABLE_KEY`.
- They cover public pages, unauthenticated route protection, and auth-shell rendering only.
- Forgot-password stops short of a real reset because Clerk is intentionally unconfigured in this phase.

## TODO: authenticated flow tests

Once `VITE_CLERK_PUBLISHABLE_KEY` is set in `apps/web/.env.local`, extend coverage with:

1. Real sign-in with a seeded test user.
2. Real sign-up flow for a disposable test user.
3. Post-auth dashboard rendering and protected navigation.
4. Onboarding completion after authentication.
5. Password reset progression against Clerk test credentials.
