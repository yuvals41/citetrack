# Auth + Dashboard + Onboarding — Implementation Summary

Status: **COMPLETE** · 118/118 tests green · dev server boots · typechecks clean across 3 packages.

Scope of this workstream: build the login / sign-up / forgot-password pages, onboarding wizard, dashboard shell, left navigation, and wire everything to the FastAPI backend with Clerk JWT auth. Write extensive tests.

---

## What ships

### Routes

| Path | Auth | Purpose |
|---|---|---|
| `/` | public | Landing (existing) |
| `/sign-in/$` | public | Clerk `<SignIn/>` in a Citetrack shell. Falls back to an info card when Clerk is not configured. |
| `/sign-up/$` | public | Clerk `<SignUp/>` — redirects to `/onboarding` after sign-up |
| `/forgot-password` | public | 2-step custom flow (email → code + new password) using `useSignIn()` |
| `/dashboard` | required | KPI row + trend chart + actions + findings, data from `/api/v1/snapshot/*` |
| `/onboarding` | required | 4-step wizard: Brand → Competitors → Engines → Done |
| `/api/webhooks/clerk` | n/a | POST handler, `verifyWebhook()` from `@clerk/backend/webhooks` |

All authenticated routes share a Multica-style shell: left sidebar (workspace switcher + 3 nav groups + user footer) and a 48px page header.

### Backend endpoints

All routes JWT-protected via `Depends(get_current_user_id)` except where noted.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/v1/health` | **public** liveness |
| `POST` | `/api/v1/pixel/event` | **public** external tracker ingress |
| `GET` | `/api/v1/me` | current user + workspace count + onboarding flag |
| `GET` | `/api/v1/workspaces/mine` | list user's workspaces |
| `POST` | `/api/v1/workspaces` | create workspace |
| `POST` | `/api/v1/onboarding/complete` | idempotent onboarding submission |
| `GET` | `/api/v1/workspaces` | list all workspaces (legacy — kept) |
| `GET` | `/api/v1/runs/latest`, `/runs`, `/prompts` | existing data |
| `GET` | `/api/v1/snapshot/{overview,trend,findings,actions}` | dashboard data |
| `GET` | `/api/v1/pixel/{snippet,stats}/{workspace_id}` | pixel management |

### Test counts

| Suite | Count | Runtime |
|---|---:|---:|
| pytest (`apps/api/tests/api/`) | 43 | 2.71 s |
| Vitest (`apps/web/src/**/*.test.tsx`) | 69 | 6.5 s |
| Playwright (`apps/web/e2e/*.spec.ts`) | 6 | 6.4 s |
| **Total** | **118** | **~15 s** |

Backend coverage: auth (9) · user routes (9) · onboarding routes (7) · existing routes refreshed with auth (13) · snapshot routes with auth (5).

Frontend coverage: zod schema (17) · step indicator · each step component · onboarding page flow · dashboard chart + lists · forgot-password flow.

E2E coverage: landing renders · auth pages render (Clerk-less fallback) · forgot-password interactions · `/dashboard` and `/onboarding` redirect to sign-in when unauthenticated.

---

## Architecture

### Client-side auth flow

```
User → /sign-in/$                 Clerk <SignIn/>
                                     │ success
                                     ▼
        /dashboard  (protected)  ← beforeLoad(auth()) passes
                                     │
                                     ▼ fetch w/ Bearer <Clerk JWT>
                               FastAPI Depends(get_current_user_id)
                                     │ verify RS256 against JWKS
                                     │ check azp ∈ AUTHORIZED_PARTIES
                                     ▼
                            return payload["sub"] as user_id
```

### Server-side stack (apps/api)

```
ai_visibility/api/auth.py           JWKS fetch + cache (TTL 1h)
                                    RS256 verify, issuer, azp checks
                                    get_current_user_id dependency
                                    ClerkAuthContext dataclass
                                  
ai_visibility/api/user_routes.py    GET /me, GET /workspaces/mine,
                                    POST /workspaces
                                  
ai_visibility/api/onboarding_routes.py
                                    POST /onboarding/complete — idempotent:
                                    generates slug, creates workspace,
                                    associates user, stores metadata
                                  
storage/repositories/user_repo.py   file-backed stub at
                                    .cache/user_associations.json
                                    (swaps to Prisma once migrations land;
                                    see docs/MIGRATION_NEEDED.md)
```

### UI primitives added (`packages/ui/src/components/`)

9 new primitives shipped in Phase 1. All adapted to Citetrack's monochrome tokens and Multica's ring-based, shadow-less design language.

- `sidebar.tsx`, `sheet.tsx`, `separator.tsx`, `navigation-menu.tsx` — shell
- `card.tsx`, `form.tsx`, `form-field.tsx`, `table.tsx`, `kpi-card.tsx` — content
- New `--color-sidebar-*` tokens added to `tokens.css` (light + dark)

---

## Design choices worth knowing

1. **Multica style ≠ Multica colors.** Multica is Linear-inspired, density-first, monochrome-native. Perfect for our monochrome brand. We ported structure (256px sidebar, 48px header, `gap-0.5` nav, `ring-1 ring-foreground/10` cards, no shadows, `font-medium` max) but not the accent blue.

2. **Clerk-less dev fallback.** Without `VITE_CLERK_PUBLISHABLE_KEY` the app still boots: landing renders, auth pages show an info card, protected routes redirect. Production (`import.meta.env.PROD`) hard-fails on missing key.

3. **File-based user↔workspace stub.** `UserRepository` reads/writes `.cache/user_associations.json` because AGENTS.md §7 forbids auto-creating Prisma migrations. Once the users + user_workspaces tables exist, swap the internals — same public interface. Full plan in `apps/api/docs/MIGRATION_NEEDED.md`.

4. **Native `<input type="checkbox">` in the engines step.** Radix's `<Checkbox>` renders a `<button role="checkbox">` which the `has-[:checked]:` CSS selector can't read. Native checkboxes give us the card-style selected state cleanly.

5. **`<a href>` for unregistered nav routes.** Sidebar items link to `/dashboard/brands`, `/dashboard/competitors`, etc. — none registered yet. TanStack Router's `<Link to>` is strictly typed against the route tree; we use plain anchors until those routes exist, then swap.

6. **Module-level `QueryClient` in `__root.tsx`.** Not wired via `@tanstack/react-router-ssr-query` — pragmatic choice that works now. SSR-query integration is a future improvement.

7. **Inline SVG trend chart.** ~85 lines of pure React SVG instead of pulling in Recharts. Kept to monochrome (`stroke-foreground` line over `fill-foreground/5` area). Grid lines at 0/25/50/75/100.

---

## What's next (not in scope for this workstream)

### Setup you need to do
See `docs/CLERK_SETUP.md` — takes ~15 minutes. Without it, sign-up and sign-in don't work end-to-end (but the app still renders).

### Backend pending Prisma migrations
See `apps/api/docs/MIGRATION_NEEDED.md`:
- Add `users` table (Clerk user_id as PK)
- Add `user_workspaces` junction table
- Swap `UserRepository` file-reads for Prisma calls

### Frontend pending registered sub-routes
The sidebar has 9 nav items; only `/dashboard` and `/onboarding` actually exist. Add routes for:
- `/dashboard/inbox`, `/dashboard/brands`, `/dashboard/competitors`, `/dashboard/prompts`, `/dashboard/scans`, `/dashboard/integrations`, `/dashboard/team`, `/dashboard/settings`

Each should live inside `_authenticated/` so they inherit the shell + auth guard. Swap `<a href>` in `app-sidebar.tsx` for `<Link to>` once routes are registered.

### Stuff we deliberately did not touch (per scope)
- Lemon Squeezy integration
- Sentry / Plausible
- GitHub Actions
- Lefthook pre-commit
- Fix for absolute-path Python deps in `apps/api/pyproject.toml`
- Forking Prisma schema from Solara

All still documented as tech debt in `AGENTS.md` §14.

---

## Git history for this workstream

```
b64d3c9  test: add 69 vitest unit tests + 6 Playwright E2E tests (118 green total)
5c2f64d  feat: dashboard shell + page + onboarding wizard + backend endpoints
26eb2c4  feat(auth): wire Clerk end-to-end (frontend + FastAPI JWT)
0b95f3d  feat(ui): add 9 primitives for auth+dashboard (Multica-style)
c7d4d4a  fix(web): pin nitro + @tanstack/* to stable versions (unblock dev server)
```

5 commits. Clean history, no squashing needed.

---

## How to verify locally

```bash
# 1. Dependency install
bun install
cd apps/api && uv sync && cd ../..

# 2. Typecheck (3 packages)
bunx tsc -p packages/ui/tsconfig.json --noEmit
bunx tsc -p packages/api-client/tsconfig.json --noEmit
bunx tsc -p apps/web/tsconfig.json --noEmit

# 3. Tests
cd apps/api && uv run pytest tests/api/ -v && cd ../..
bunx nx test @citetrack/web
cd apps/web && bunx playwright test --reporter=list

# 4. Dev server
bunx nx dev @citetrack/web
# → http://localhost:3002/  (or 3000/3001 if those are free)
```

All five should be green. If the dev server shows "Clerk not configured" — that's expected until you follow `docs/CLERK_SETUP.md`.
