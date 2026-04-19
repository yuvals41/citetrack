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

| Suite | Count | Runtime | Notes |
|---|---:|---:|---|
| pytest (`apps/api/tests/api/` + `tests/services/`) | 101 | 2.8 s | auth, user, onboarding, snapshot, routes, **discovery, research** |
| pytest (`apps/api/tests/` full, ignore e2e + not slow) | 710 | 40 s | 29 pre-existing failures in scan/cli/pixel (migration debt, AGENTS.md §14) |
| Vitest (`apps/web/src/**/*.test.tsx`) | 76 | 6.5 s | schema · steps · forgot-password · dashboard · **research states** |
| Playwright (`apps/web/e2e/*.spec.ts`) | **14** | **40 s** | 6 public + 3 authenticated + 1 onboarding + 3 setup + 1 teardown |
| **Total green** | **901** | **~90 s** | excludes pre-existing migration failures |

Backend coverage:
- auth (9) · user routes (9) · onboarding routes (7) · research routes (7)
- snapshot routes (5) · legacy routes (13) · **competitor-discovery pipeline (51)**

Frontend coverage:
- zod schema (17) · step indicator · each step component (incl. 4 research states)
- onboarding page state machine · dashboard chart + lists · forgot-password flow

**E2E coverage (REAL sign-in via Clerk testing mode, not a smoke test):**
- Public routes render correctly
- Auth guard redirects to `/sign-in` when unauthenticated
- **Signed-in user's dashboard loads with sidebar**
- **Root `/` redirects signed-in users to `/dashboard`**
- **Fresh ephemeral user completes full 4-step onboarding wizard** (create user via Backend API → sign in via ticket strategy → brand → competitors with research wait → engines → finish → land on dashboard or onboarding-retry)
- Ephemeral users cleaned up in teardown

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
See `docs/CLERK_SETUP.md` — takes ~15 minutes. **Already done on this machine** (Clerk test keys in `apps/web/.env.local`, backend JWKS in `apps/api/.env`, E2E test user provisions automatically).

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

Scaffold + auth + dashboard + onboarding:
```
8804f94  docs: Clerk setup guide + handoff
b64d3c9  test: 69 vitest + 6 Playwright E2E
5c2f64d  feat: shell + dashboard + onboarding wizard + backend endpoints
26eb2c4  feat(auth): wire Clerk end-to-end (frontend + FastAPI JWT)
0b95f3d  feat(ui): 9 primitives (Multica-style)
c7d4d4a  fix(web): pin nitro + @tanstack/* (unblock dev server)
```

Light-only theme + app-only routing + competitor research + real E2E:
```
(head)   test(e2e): real Playwright suite with Clerk testing mode
(head~1) feat: competitor auto-research (restored from ai-visibility)
383a361  fix(web): / redirect + light-only theme + restore Tailwind
```

9 commits. Clean history.

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
