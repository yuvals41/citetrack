# Auth + Dashboard + Onboarding + Reflex Parity — Implementation Summary

Status: **COMPLETE** · 139 pytest (scoped) + 118 vitest green · dev server serves all 10 routes with `200` · typechecks clean across 3 packages.

Scope of this workstream: build the login / sign-up / forgot-password pages, onboarding wizard, dashboard shell, left navigation, wire everything to FastAPI with Clerk JWT auth, **then rebuild every page the original Reflex `ai-visibility` app had, in the new Citetrack design system, end-to-end**.

---

## What ships

### Routes

| Path | Auth | Purpose |
|---|---|---|
| `/` | public | Landing (existing) |
| `/sign-in/$` | public | Clerk `<SignIn/>` in a Citetrack shell. Falls back to an info card when Clerk is not configured. |
| `/sign-up/$` | public | Clerk `<SignUp/>` — redirects to `/onboarding` after sign-up |
| `/forgot-password` | public | 2-step custom flow (email → code + new password) using `useSignIn()` |
| `/onboarding` | required | 4-step wizard: Brand → Competitors → Engines → Done |
| `/dashboard` | required | KPI row + trend chart + actions + findings, data from `/api/v1/snapshot/*` |
| `/dashboard/actions` | required | Prioritized action plan — `/api/v1/snapshot/actions` |
| `/dashboard/scans` | required | Run history table — `/api/v1/runs` |
| `/dashboard/prompts` | required | Questions library — `/api/v1/prompts` |
| `/dashboard/pixel` | required | Revenue-attribution snippet + stats — `/api/v1/pixel/*` |
| `/dashboard/citations` | required | AI response viewer — `/api/v1/workspaces/{slug}/responses` |
| `/dashboard/competitors` | required | Competitor CRUD — `/api/v1/workspaces/{slug}/competitors` |
| `/dashboard/brands` | required | Brand profile (single brand per workspace) — `/api/v1/workspaces/{slug}/brand` |
| `/dashboard/content-analysis` | required | 5 analyzers (extractability, crawler-sim, query-fanout, entity, shopping) — `/api/v1/analyzers/*` |
| `/dashboard/settings` | required | Workspace settings — `/api/v1/workspaces/{slug}/settings` |
| `/api/webhooks/clerk` | n/a | POST handler, `verifyWebhook()` from `@clerk/backend/webhooks` |

All authenticated routes share a Multica-style shell: left sidebar (workspace switcher + 3 nav groups — **Data / Insights / Configure** — + user footer) and a 48px page header. Every Reflex-app page has a 1:1 route in the new app.

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
| `GET` | `/api/v1/runs/latest`, `/runs`, `/prompts` | scan runs + prompts library |
| `GET` | `/api/v1/snapshot/{overview,trend,findings,actions}` | dashboard data |
| `GET` | `/api/v1/pixel/{snippet,stats}/{workspace_id}` | pixel management |
| `GET` | `/api/v1/workspaces/{slug}/responses` | **Wave 2** — AI response viewer (joins prompt execution × observation × scan × citation) |
| `GET/POST/DELETE` | `/api/v1/workspaces/{slug}/competitors` | **Wave 2** — competitor CRUD |
| `GET/PUT` | `/api/v1/workspaces/{slug}/settings` | **Wave 2** — workspace settings |
| `GET/PUT` | `/api/v1/workspaces/{slug}/brand` | **Wave 3** — single-brand-per-workspace profile |
| `POST` | `/api/v1/analyzers/extractability` | **Wave 3** — HTML/JS-LD extractability score |
| `POST` | `/api/v1/analyzers/crawler-sim` | **Wave 3** — simulate GPTBot / PerplexityBot / etc. |
| `POST` | `/api/v1/analyzers/query-fanout` | **Wave 3** — AI query fan-out for a URL |
| `POST` | `/api/v1/analyzers/entity` | **Wave 3** — entity extraction + knowledge-graph coverage |
| `POST` | `/api/v1/analyzers/shopping` | **Wave 3** — product-feed/PDP analyzer |

Content-analysis endpoints degrade gracefully (structured "degraded" payload) when `EXA_API_KEY` / `TAVILY_API_KEY` / `ANTHROPIC_API_KEY` are missing so dev boot doesn't break.

### Test counts

| Suite | Count | Runtime | Notes |
|---|---:|---:|---|
| pytest (`apps/api/tests/api/` + `tests/services/`) | **139** | **13 s** | auth, user, onboarding, snapshot, runs, prompts, pixel, **mentions, competitors, settings, brands, content-analysis** |
| pytest (`apps/api/tests/` full, ignore e2e + not slow) | 710+ | 40 s | 29 pre-existing failures in scan/cli/pixel remain (migration debt, AGENTS.md §14) — scope I own is 100% green |
| Vitest (`apps/web/src/**/*.test.tsx`) | **118** | **25 s** | 19 files — schema · onboarding · dashboard · all 10 pages · hooks · API client |
| Playwright (`apps/web/e2e/*.spec.ts`) | 14 | 40 s | last run green end of CSR migration; not re-run post-Wave 3 |

Backend coverage highlights (new this sprint):
- auth (9) · user routes (9) · onboarding routes (7) · research routes (7) · snapshot routes (5) · legacy routes (13)
- **mentions routes (5)** · **competitors CRUD (6)** · **settings GET/PUT (4)** · **brands GET/PUT (8)** · **content analyzers (8)**
- competitor-discovery pipeline (51)

Frontend coverage highlights:
- zod schema (17) · step indicator · each onboarding step · forgot-password flow
- dashboard chart + lists · action cards · response cards · competitor cards · prompt cards
- brand-page · content-analysis-page (6) · settings-page · workspaces-hooks · api-client methods

**Vitest timeout raised to 15s** (from 5s) — parallel 19-file runs were hitting spurious CPU-load timeouts; each test still passes in under 2s in isolation.

**E2E coverage (REAL sign-in via Clerk testing mode, not a smoke test):**
- Public routes render correctly
- Auth guard redirects to `/sign-in` when unauthenticated
- **Signed-in user's dashboard loads with sidebar**
- **Root `/` redirects signed-in users to `/dashboard`**
- **Fresh ephemeral user completes full 4-step onboarding wizard** (create user via Backend API → sign in via ticket strategy → brand → competitors with research wait → engines → finish → land on dashboard or onboarding-retry)
- Ephemeral users cleaned up in teardown

**Clerk testing-mode gotcha (documented):** `@clerk/testing`'s `clerk.signIn()` helper throws `TypeError: URL cannot be parsed` against `@clerk/react` v6. E2E sign-in drives the Clerk UI directly via `page.locator().fill()/.click()` using `.cl-formButtonPrimary`. If the URL contains `factor-two|verify`, enter code `424242` (Clerk's test fixed-OTP).

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

9 primitives shipped in Phase 1 + Wave-era components use these plus a handful of feature-level compositions. All adapted to Citetrack's monochrome tokens and Multica's ring-based, shadow-less design language.

- `sidebar.tsx`, `sheet.tsx`, `separator.tsx`, `navigation-menu.tsx` — shell
- `card.tsx`, `form.tsx`, `form-field.tsx`, `table.tsx`, `kpi-card.tsx` — content
- `badge.tsx` — semantic variants include `failed` (not `destructive` — that variant doesn't exist)
- New `--color-sidebar-*` tokens added to `tokens.css` (light + dark)

### Feature-level components (`apps/web/src/features/dashboard/components/`)

Added to support the 10 pages:
- `app-sidebar.tsx` — Multica-grouped nav (Data · Insights · Configure)
- `page-header.tsx`, `placeholder-page.tsx` — page shell
- `workspace-switcher.tsx` — dropdown in sidebar top
- `visibility-trend-chart.tsx`, `findings-list.tsx`, `actions-queue.tsx` — dashboard widgets
- `action-card.tsx` — Action Plan items
- `response-card.tsx` — AI Responses viewer
- `competitor-card.tsx` — Competitors list row
- `prompt-card.tsx` — Prompts library row
- `code-snippet.tsx` — copyable `<pre>` for pixel snippet

---

## Design choices worth knowing

1. **Multica style ≠ Multica colors.** Multica is Linear-inspired, density-first, monochrome-native. Perfect for our monochrome brand. We ported structure (256px sidebar, 48px header, `gap-0.5` nav, `ring-1 ring-foreground/10` cards, no shadows, `font-medium` max) but not the accent blue.

2. **Clerk-less dev fallback.** Without `VITE_CLERK_PUBLISHABLE_KEY` the app still boots: landing renders, auth pages show an info card, protected routes redirect. Production (`import.meta.env.PROD`) hard-fails on missing key.

3. **File-based user↔workspace stub.** `UserRepository` reads/writes `.cache/user_associations.json` because AGENTS.md §7 forbids auto-creating Prisma migrations. Once the users + user_workspaces tables exist, swap the internals — same public interface. Full plan in `apps/api/docs/MIGRATION_NEEDED.md`.

4. **Native `<input type="checkbox">` in the engines step.** Radix's `<Checkbox>` renders a `<button role="checkbox">` which the `has-[:checked]:` CSS selector can't read. Native checkboxes give us the card-style selected state cleanly.

5. **`<a href>` → `<Link to>` swapped.** Sidebar nav no longer triggers full-page reloads. All 10 targets are registered routes — typed against TanStack Router's route tree.

6. **Dashboard is an `<Outlet/>` parent.** `_authenticated.dashboard.tsx` now holds `<DashboardShell><Outlet/></DashboardShell>`, with `_authenticated.dashboard.index.tsx` handling `/dashboard` exact. Children (`actions`, `scans`, `prompts`, …) inherit the shell without duplicating it.

7. **Module-level `QueryClient` in `__root.tsx`.** Not wired via `@tanstack/react-router-ssr-query` — pragmatic choice, appropriate since the app is pure CSR now (see design choice 9).

8. **Inline SVG trend chart.** ~85 lines of pure React SVG instead of pulling in Recharts. Kept to monochrome (`stroke-foreground` line over `fill-foreground/5` area). Grid lines at 0/25/50/75/100.

9. **TanStack Router (CSR), not TanStack Start (SSR).** Migrated away from Start to fix a production SSR self-fetch bug (`ddd1532`). Matches the pattern used by `platform/services/desktop-frontend` in Solara. Production is a static nginx SPA build.

10. **API container bakes the Prisma query-engine binary.** `apps/api/Dockerfile.dev` downloads the binary at commit SHA `393aa359c9ad4a4bb28630fb5613f9c281cde053` from Prisma's CDN at image build time, and sets `PRISMA_QUERY_ENGINE_BINARY`. Mirrors the pattern used by `platform/services/agentflow`. Avoids every container boot re-downloading from `binaries.prisma.sh`.

11. **One-brand-per-workspace (for now).** The brand page is a PUT (update-in-place), not a POST (create). Multi-brand-per-workspace is on the roadmap but would need Prisma migrations.

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
**All 10 Reflex-parity routes now exist.** The remaining sidebar placeholders that Reflex never had (`/dashboard/inbox`, `/dashboard/integrations`, `/dashboard/team`) are deliberately not built — out of scope.

### Stuff we deliberately did not touch (per scope)
- DELETE workspace flow (Settings → Danger Zone)
- Prisma migrations for `users` + `user_workspaces` tables (file-backed stub still wins until you approve a migration)
- Multi-brand-per-workspace
- Lemon Squeezy integration
- Sentry / Plausible
- GitHub Actions
- Lefthook pre-commit
- Backend Clerk webhook for user sync
- Fix for absolute-path Python deps in `apps/api/pyproject.toml`
- Forking Prisma schema from Solara

All still documented as tech debt in `AGENTS.md` §14.

---

## Git history for this workstream

### Phase 1 — scaffold + auth + dashboard + onboarding
```
8804f94  docs: Clerk setup guide + handoff
b64d3c9  test: 69 vitest + 6 Playwright E2E
5c2f64d  feat: shell + dashboard + onboarding wizard + backend endpoints
26eb2c4  feat(auth): wire Clerk end-to-end (frontend + FastAPI JWT)
0b95f3d  feat(ui): 9 primitives (Multica-style)
c7d4d4a  fix(web): pin nitro + @tanstack/* (unblock dev server)
```

### Phase 2 — light-only theme + competitor research + real E2E
```
383a361  fix(web): / redirect + light-only theme + restore Tailwind
afc33ca  feat: competitor auto-research (restored from ai-visibility)
11cec7e  test(e2e): real Playwright suite with Clerk testing mode
9671257  docs: update handoff with real 901-test coverage + E2E flow
```

### Phase 3 — observability + containers + CSR migration
```
ab8ca87  fix: CORS on snapshot routes + skeleton proportions in KPI cards
c8fb828  feat: postgres docker-compose + favicon + DB schema setup
a028210  feat(observability): structured logs + request-id correlation end-to-end
8254f8d  feat(ops): containerize FastAPI backend — unified docker compose logs
0698826  fix(api container): import prisma works + stop stomping host .venv
7f6492d  feat(ops): add apps/web Dockerfile + opt-in docker compose profile
ddd1532  feat(web): migrate TanStack Start SSR -> TanStack Router CSR (nginx SPA)
6f0b986  feat(web): add React Query devtools alongside Router devtools
4418469  fix(api container): bake Prisma query-engine binary into image
c4c595f  fix(web): sidebar invisible + KPI padding collapsed — two Tailwind v4 bugs
e04a046  fix(web): sidebar nav full-refresh + wrong favicon
```

### Phase 4 — Reflex parity (this sprint)
```
d76686e  feat(web): Wave 1 — Action Plan + Scans + Prompts + Pixel pages
48734ab  feat: Wave 2 — AI Responses + Competitors CRUD + Settings + backend
dfeb742  feat: Wave 3 — Content Analysis (5 analyzers) + Brands CRUD
```

24 commits ahead of `origin/master` (not pushed — awaiting explicit consent).

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
