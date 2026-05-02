# AGENTS.md — Citetrack AI Standards

**Single source of truth for all development standards, tooling decisions, and conventions.**

> Read this file first before making any changes. Every decision here was made deliberately.

---

## Quick Orientation

**You are working on Citetrack AI** — a stealth-brand SaaS built in a monorepo.

```
  GitHub:    https://github.com/yuvals41/citetrack
  Local:     /home/yuval/Documents/solaraai/citetrack
  Brand:     Citetrack AI — citetrack.ai (monochrome black/white logo)
  Owner:     Yuval Strutti (solo founder, side project separate from Solara AI)
  Status:    Auth + dashboard + onboarding complete — see "Current State vs Target State" below
```

**Commands that work RIGHT NOW:**

```bash
bun install                         # Install Node deps (apps + packages)
uv sync                             # Install Python deps (apps/api)
bunx nx dev @citetrack/web          # Frontend dev server → :3000 (scaffold)
bunx nx dev @citetrack/api          # Backend dev server → :8000 (migrated code)
bunx nx show projects               # List all NX projects
bun run lint                        # Biome lint
bun run typecheck                   # TypeScript check
bun run format                      # Biome format
```

---

## Table of Contents

- [0. Hard Rules](#0-hard-rules)
- [1. Tooling Decisions](#1-tooling-decisions-opinionated)
- [2. Project Structure](#2-project-structure)
- [3. Architecture](#3-architecture)
- [4. Code Standards](#4-code-standards)
- [5. Testing Philosophy](#5-testing-philosophy)
- [6. Git & CI/CD](#6-git--cicd)
- [7. Database](#7-database)
- [8. Monorepo Rules](#8-monorepo-specific-rules)
- [9. What We Don't Use](#9-what-we-do-not-use)
- [10. Skills & Agent Roles](#10-skills--agent-roles)
- [11. Common Commands](#11-common-commands)
- [12. Environment & Secrets](#12-environment--secrets)
- [13. Stealth Brand Separation](#13-stealth-brand-separation)
- [14. Known Tech Debt / Current Limitations](#14-known-tech-debt--current-limitations)
- [15. Agent Mental Checklist](#15-keep-in-mind--agent-mental-checklist)

---

## Current State vs Target State

This repo is new. Most patterns in this doc describe **target state**, not current state.

**Currently EXISTS and WORKS:**

- ✅ NX + Bun workspaces configured (6 projects discovered)
- ✅ `apps/web/` — TanStack Start SPA with auth, onboarding, and dashboard (not scaffold-only)
- ✅ `apps/api/` — Full FastAPI backend migrated from ai-visibility (248+ tests)
- ✅ `packages/ui/` — 61 Shadcn-based components (`Button`, `Dialog`, `Input`, `Sidebar`, etc.)
- ✅ `packages/types/` — domain types (`Workspace`, `ScanRun`, `Citation`, `VisibilityScore`, etc.)
- ✅ `packages/config/` — constants (`APP_NAME`, `AI_PROVIDERS`)
- ✅ `packages/api-client/` — typed fetch wrappers for FastAPI endpoints
- ✅ Brand assets in `brand/official/` (SVG + PNG + favicon)
- ✅ Python env — installed via `uv sync`
- ✅ Node env — installed via `bun install`
- ✅ Pushed to GitHub (yuvals41/citetrack)
- ✅ Clerk auth — end-to-end (ClerkProvider + auth routes + FastAPI JWT verifier)
- ✅ Auth pages — `/sign-in/$`, `/sign-up/$`, `/forgot-password`
- ✅ `apps/web/src/features/` — `dashboard/` and `onboarding/` feature folders with components, lib, pages
- ✅ `QueryClientProvider` in `src/routes/__root.tsx`
- ✅ Onboarding wizard — 4-step flow with Zod validation
- ✅ Dashboard shell — sidebar + page header
- ✅ Dashboard page — KPI cards, trend chart, findings, actions (real API wiring)
- ✅ `docs/AUTH_DASHBOARD_ONBOARDING_COMPLETE.md` — completion record for auth+dashboard workstream

**Does NOT exist yet (labeled TARGET in this doc where relevant):**

- ❌ Citetrack-specific Prisma schema (uses Solara's local-path client via stanley repo)
- ❌ Lemon Squeezy payment integration
- ❌ Sentry / Plausible analytics
- ❌ Git hooks (no lefthook, no pre-commit)
- ❌ CI/CD pipeline (no GitHub Actions)
- ❌ Public landing page (citetrack.ai has no content yet)
- ❌ Registered sub-routes for `/dashboard/brands`, `/dashboard/competitors`, etc. (sidebar nav items use `<a href>` because the routes don't exist yet)
- ❌ Clerk dashboard setup (keys not yet created — see `docs/CLERK_SETUP.md`)

> **When this doc says something like `import { Button } from "@citetrack/ui/button"`, that pattern now works.** The `@citetrack/ui` package has 61 components with per-file exports. Sections still labeled TARGET PATTERN refer to router context with `queryClient` and auth guards via `beforeLoad`.

---

## 0) Hard Rules

- **NEVER revert uncommitted work.** No `git reset --hard`, no `git checkout -- .`, no `git clean -fd`. Use `git stash` to save work, `git stash apply` (never `pop`) to restore.
- **No lying.** A green CI does not mean the feature works. It works when the real user-visible behavior works end-to-end.
- **No workarounds.** Don't mask problems with flags, stubs, or cosmetic checks. Find root cause → fix → verify.
- **If you think it's fixed, prove it.** Reproduce → fix → verify with tests AND a manual sanity run of the actual flow.
- **Fight complexity at all costs.** Always prefer simple, obvious solutions. Write code a tired developer can understand at 3 AM.
- **Respect the stealth brand.** See §13 — Citetrack AI is intentionally separate from Solara AI. Never cross-link, cross-commit, or cross-tool between repos without deliberate reason.

---

## 1) Tooling Decisions (Opinionated)

Every tool here was chosen deliberately. Do NOT introduce alternatives without explicit approval.

### Bun — Package Manager & JS Runtime

**Choice:** Bun
**Replaces:** npm, pnpm, yarn
**Why:**

- 10-30x faster installs than npm/pnpm
- Built-in TypeScript execution (no ts-node, tsx, etc.)
- Native workspace support via `workspaces` in package.json
- Compatible with Node.js ecosystem (99%+ of npm packages work)
- Single binary — simpler CI setup

**Rules:**

- `bun install` for dependencies — NEVER `npm install` or `pnpm install`
- `bun add <package>` to add deps — NEVER `npm install <package>`
- `bun remove <package>` to remove deps
- `bun run <script>` or just `bun <script>` to run scripts
- `bunx` instead of `npx` for one-off executables
- Lockfile is `bun.lock` — always commit it
- Workspace packages use `"workspace:*"` protocol for internal deps

### Biome — Linter & Formatter

**Choice:** Biome
**Replaces:** ESLint + Prettier + config packages
**Why:**

- Single tool replaces two — fewer deps, fewer configs, fewer conflicts
- 100x faster than ESLint (written in Rust)
- No plugin hell — opinionated defaults
- One config file (`biome.json`)

**Rules:**

- `biome.json` at repo root — single config for entire monorepo
- `bun run lint` to check, `bun run lint:fix` to auto-fix
- `bun run format` to format, `bun run format:check` to verify
- NO ESLint. NO Prettier. If Biome doesn't cover a rule, we don't need it.

**Note:** The root `package.json` script is `"lint": "biome check ."` — invoke via `bun run lint`, not `bun lint` (which would try to find a `lint` binary).

### NX — Monorepo Orchestrator

**Choice:** NX 20.8.4 (20.x line)
**Replaces:** Turborepo, Lerna, manual scripts
**Why:**

- Polyglot support (TypeScript + Python) — Turborepo is JS-only
- Affected-only builds (`nx affected -t build`) — only rebuild what changed
- Task caching
- Dependency graph visualization (`nx graph`)

**Rules:**

- Task targets: `build`, `test`, `lint`, `typecheck`, `dev`
- Use `nx affected` in CI — never build everything
- `nx.json` at repo root defines task pipelines and caching
- Projects auto-detected from `workspaces` in package.json (Node) and `project.json` files (all projects)
- Use `bunx nx <target> <project>` or `bunx nx run-many -t <target>`

### UV — Python Dependency Manager

**Choice:** UV 0.9.x
**Python Version:** 3.11+ required (3.13 locally installed)
**Replaces:** pip, pip-tools, poetry, conda
**Why:**

- 10-100x faster than pip (Rust)
- Handles virtual environments automatically
- Lockfile support (`uv.lock`) for reproducible builds
- Workspace support mirrors Bun

**Rules:**

- `uv sync` to install Python deps — NEVER `pip install`
- `uv add <package>` to add — NEVER `pip install <package>`
- `uv run pytest` to run tests — uses the managed virtualenv
- `uv run python ...` to run Python scripts
- Root `pyproject.toml` defines UV workspace members
- Each Python app has its own `pyproject.toml`

**⚠️ Local path dependencies (portability concern):**

`apps/api/pyproject.toml` currently uses ABSOLUTE paths for two deps:

```toml
[tool.uv.sources]
solaraai-llm = { path = "/home/yuval/Documents/solaraai/stanley/repos/solaraai-packages/packages/python/solaraai-llm", editable = true }
solaraai-prisma-client = { path = "/home/yuval/Documents/solaraai/stanley/repos/prisma/dist/client-python", editable = true }
```

This **breaks on any other machine**. See §14 for the migration plan. For now, only Yuval's laptop can `uv sync` this repo.

### TypeScript 5.9+ — Strict Mode

**Choice:** TypeScript 5.9.3 with strict mode enabled
**Why:**

- Catches bugs at compile time instead of runtime
- Better IDE support with stricter types

**Rules:**

- Root `tsconfig.base.json` with `strict: true` — all apps/packages extend it
- NEVER use `as any`, `@ts-ignore`, or `@ts-expect-error` to suppress type errors
- NEVER use `any` as a type — use `unknown` if truly unknown, then narrow
- Empty catch blocks `catch(e) {}` are forbidden — always handle or rethrow
- Prefer `type` over `interface` unless extending
- `verbatimModuleSyntax: true` — use explicit `import type` for types

---

## 2) Project Structure

```
  citetrack/
  ├── AGENTS.md, CLAUDE.md     ← This file (single source of truth)
  ├── README.md                ← Navigation hub
  ├── biome.json, nx.json      ← Root tool configs
  ├── package.json, bun.lock   ← Bun workspaces
  ├── tsconfig.base.json       ← Shared TS config
  ├── pyproject.toml, uv.lock  ← UV Python workspace
  ├── .gitignore, .env.example
  │
  ├── docs/                    ← Repo-level documentation
  │   ├── architecture.md
  │   ├── development.md
  │   └── tech-stack.md
  │
  ├── apps/
  │   ├── web/                 ← TanStack Start SPA (frontend)
  │   ├── api/                 ← Python FastAPI (backend)
  │   └── (worker/)            ← Future: separate ARQ worker
  │
  ├── packages/
  │   ├── ui/                  ← @citetrack/ui — shared React primitives
  │   ├── types/               ← @citetrack/types — shared TS types
  │   ├── config/              ← @citetrack/config — shared constants
  │   └── api-client/          ← @citetrack/api-client — typed fetch client
  │
  ├── prisma/                  ← Database schema (future)
  ├── brand/                   ← Logo, colors, brand assets
  └── tools/scripts/           ← Build scripts, migrations
```

**Key conventions:**

- `apps/*` — deployable applications (one Dockerfile each)
- `packages/*` — shared code, never deployed directly
- `docs/` at root — repo-level architecture, development guides
- Each app has its own `docs/` folder for app-specific docs
- Every app/package has a `README.md`
- `brand/` holds the logo, colors, and related assets (not consumed by apps — apps import from `public/` or `packages/ui`)

---

## 3) Architecture

### Polyglot Monorepo

TypeScript (frontend + shared) and Python (backend) coexist. Separate dependency management, shared NX orchestrator.

### Stack Overview

| Layer | Tool | Notes |
|---|---|---|
| **Web framework** | TanStack Start | SPA + SSR via Vite + Nitro |
| **Routing** | TanStack Router | File-based, fully typed |
| **Data** | TanStack Query | Server state, caching, mutations |
| **Forms** | TanStack Form + Zod | Type-safe, validated |
| **Styling** | Tailwind CSS v4 | CSS-first config |
| **UI primitives** | Shadcn/ui + `@citetrack/ui` | Owned code, not black-box |
| **Auth** | Clerk (`@clerk/tanstack-react-start`) | 10k MAU free |
| **Icons** | Lucide React | Tree-shakable |
| **Payments** | Lemon Squeezy | Merchant of record |
| **Backend framework** | FastAPI (Python 3.11+) | Async, OpenAPI auto-gen |
| **ORM** | Prisma | Generates TS + Python clients |
| **Queue** | ARQ + Redis | Async Python jobs |
| **Database** | Postgres | Supabase / Neon for hosting |
| **Observability** | Plausible + Sentry | Privacy-friendly + error tracking |

### Communication

```
  Browser
    │
    ▼
  @citetrack/web (TanStack Start, Vercel)
    │ fetch() + Clerk JWT
    ▼
  @citetrack/api (FastAPI, Fly.io / Railway)
    │
    ├─▶ Postgres (Prisma)
    ├─▶ Redis (ARQ queue)
    └─▶ LLM APIs (ChatGPT, Claude, Perplexity, Gemini, Grok, AI Overviews)
```

- JWT for authentication (Clerk issues, FastAPI validates via JWKS)
- `X-Request-ID` correlation header traced through all services
- WebSocket / Server-Sent Events for real-time scan progress (future)

---

## 4) Code Standards

### Simplicity Above All

**COMPLEXITY IS THE ENEMY.** This is the #1 rule.

- **Say NO** to unnecessary abstractions. The best code is code that doesn't exist.
- **No early abstraction.** Wait for patterns to emerge. Let code be "ugly" first while learning the domain.
- **Copy-paste can be better** than a convoluted abstraction. Wrong abstraction is worse than duplication.
- **Locality of behavior > Separation of concerns.** Put code on the thing that does the thing.
- **Design for the common case.** Layer APIs — simple for simple cases, complex only when needed.

### Expression Simplicity

```typescript
// BAD — hard to debug, impossible to read at 3 AM
if (contact && !contact.isActive() && (contact.inGroup(FAMILY) || contact.inGroup(FRIENDS))) { ... }

// GOOD — each condition is named, easy to debug
const isInactive = !contact.isActive();
const isFamilyOrFriends = contact.inGroup(FAMILY) || contact.inGroup(FRIENDS);
if (contact && isInactive && isFamilyOrFriends) { ... }
```

### Naming

- Functions: verb + noun (`createUser`, `parseConfig`, `validateToken`)
- Booleans: `is`, `has`, `should`, `can` prefix (`isActive`, `hasPermission`)
- Constants: UPPER_SNAKE_CASE (`MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- Files: kebab-case (`user-profile.service.ts`, `auth-guard.ts`)
- No abbreviations unless universally understood (`id`, `url`, `api` are fine; `usr`, `cfg`, `mgr` are not)

### Error Handling

- NEVER empty catch blocks — always handle, log, or rethrow
- Use typed errors with context: `throw new UnauthorizedError('Token expired', { userId })`
- Log the error with correlation ID at the boundary, not deep in the stack
- Fail fast — if something is wrong, throw immediately, don't pass invalid state downstream

### Logging

- Structured JSON to stdout — never write to files
- Required fields: `ts` (UTC), `level`, `service`, `request_id`, `msg`
- Levels: ERROR (broken), WARN (degraded), INFO (business events), DEBUG (dev only)
- Include `duration_ms` for any network call or DB query
- NEVER log secrets, tokens, passwords, or PII

---

### Frontend Conventions (apps/web)

The frontend at `apps/web` is a **TanStack Start SPA** that consumes the shared UI library `@citetrack/ui` (located at `packages/ui`). The brand is monochrome black/white (see [brand/](./brand/) and `apps/web/docs/styling.md`).

#### Stack

- **TanStack Start** — client-first React meta-framework, SPA mode. Runs on Vite.
- **TanStack Router** — file-based routing with full end-to-end type safety. Routes live in `src/routes/`, the route tree is generated at build time into `src/routeTree.gen.ts` (never hand-edit; gitignored).
- **React 19** — pure client components. No `"use client"` directives (TanStack Start has no RSC boundary).
- **Tailwind CSS v4** — CSS-first config (`@import "tailwindcss"`), no `tailwind.config.js`.
- **Bun** — runtime and package manager.

#### The TanStack Ecosystem — use these for new work

- **[TanStack Query](https://tanstack.com/query)** (`@tanstack/react-query`) — all server state (fetching, caching, mutations, background refetch). Never `useEffect`+`fetch` for data.
- **[TanStack Form](https://tanstack.com/form)** (`@tanstack/react-form` + `@tanstack/zod-form-adapter` + `zod`) — **always** for forms. Never manage form state with `useState`/`useReducer` manually. Pair with `zod` schemas.
- **[TanStack Router](https://tanstack.com/router)** — routing. Use typed `<Link>` and typed search params.
- **[TanStack Table](https://tanstack.com/table)** (`@tanstack/react-table`) — any data grid. Headless — pair with `@citetrack/ui` primitives for styling.
- **[TanStack Virtual](https://tanstack.com/virtual)** (`@tanstack/react-virtual`) — virtualize any long list.
- **TanStack DevTools** — mount `ReactQueryDevtools` and `TanStackRouterDevtoolsPanel` in dev mode.

#### Router Context

> 🎯 **TARGET PATTERN** — not yet implemented. The current `src/routes/__root.tsx` uses a module-level `QueryClient` singleton, not `createRootRouteWithContext`.

The root route should use `createRootRouteWithContext<{ queryClient: QueryClient }>()`. The query client will be available to every route loader via `context.queryClient`, so loaders can prefetch queries before the component renders.

#### TanStack Query Standards

> 🎯 **TARGET PATTERN** — `src/features/` exists with `dashboard/` and `onboarding/`. Apply this pattern when building new features.

**Query keys — factory pattern, always.** Never inline raw arrays in `useQuery`. Put query keys and options in a `queries.ts` file next to the feature code:

```ts
// features/workspaces/queries.ts
import { queryOptions } from "@tanstack/react-query";
import { citetrackApi } from "@citetrack/api-client";

export const workspaceQueries = {
  all: ["workspaces"] as const,
  lists: () => [...workspaceQueries.all, "list"] as const,
  list: () =>
    queryOptions({
      queryKey: [...workspaceQueries.lists()] as const,
      queryFn: ({ signal }) => citetrackApi.listWorkspaces({ signal }),
      staleTime: 1000 * 60, // 1 min
    }),
  details: () => [...workspaceQueries.all, "detail"] as const,
  detail: (slug: string) =>
    queryOptions({
      queryKey: [...workspaceQueries.details(), slug] as const,
      queryFn: ({ signal }) => citetrackApi.latestRun(slug, { signal }),
      staleTime: 1000 * 60 * 5,
    }),
};
```

Consume via `useQuery(workspaceQueries.list())` or `useSuspenseQuery(workspaceQueries.detail(slug))`.

**Caching rules:**

- **`staleTime` is per-query**, not global. Tune per domain.
- **`gcTime`** defaults to 5 min.
- **Never fetch in `useEffect`.** Always `useQuery` / `useSuspenseQuery`.
- **Use `select`** for derived data — avoids re-rendering when unrelated fields change.
- **Always pass `signal`** to fetch for free cancellation.
- **`enabled`** for conditional queries — never wrap `useQuery` in `if` statements.
- **`placeholderData: keepPreviousData`** for pagination/filter UX.

**Mutations:**

- Wrap in a hook: `useCreateWorkspace()` returning `useMutation(...)`. Never inline.
- On success: `queryClient.invalidateQueries({ queryKey: workspaceQueries.all })`.
- Use optimistic updates via `onMutate` + rollback in `onError` for fast UX.

**Prefetching — do it in the router loader, not on mount:**

```ts
export const Route = createFileRoute("/workspaces/$slug")({
  loader: ({ context, params }) =>
    context.queryClient.ensureQueryData(workspaceQueries.detail(params.slug)),
  component: WorkspaceDetail,
});
```

Then `useSuspenseQuery(workspaceQueries.detail(slug))` reads from cache — no loading state on first mount.

---

#### TanStack Router Standards

- **File-based routing only.** Never use `createRoute` directly — always `createFileRoute(path)`. The Vite plugin auto-generates `routeTree.gen.ts`.
- **Routes are thin.** A route file should: declare the route, wire `loader` / `beforeLoad` / `validateSearch`, and render a single imported feature component. If a route file has business logic, move it to `features/<feature>/<component>.tsx`.
- **Typed `<Link>` only.** Never `<a href>` for internal nav.
- **`useNavigate()` for imperative nav.** Never `window.location.href` or `history.pushState`.
- **Search params are state.** Use them for anything shareable/bookmarkable. Validate with zod:
  ```ts
  const searchSchema = z.object({
    q: z.string().optional(),
    page: z.number().int().positive().catch(1),
  });
  export const Route = createFileRoute("/workspaces")({
    validateSearch: searchSchema,
    loaderDeps: ({ search: { q, page } }) => ({ q, page }),
    loader: ({ context, deps }) =>
      context.queryClient.ensureQueryData(workspaceQueries.list(deps)),
    component: WorkspaceList,
  });
  ```
  `loaderDeps` tells the router which search params the loader depends on.
- **Auth guards via `beforeLoad`**, not inside components (TARGET — currently handled inside components, not yet via `beforeLoad`):
  ```ts
  // TARGET PATTERN — requires router context to include auth state
  beforeLoad: ({ context, location }) => {
    if (!context.auth.user) {
      throw redirect({ to: "/sign-in", search: { redirect: location.href } });
    }
  },
  ```
- **`pendingComponent` / `errorComponent` / `notFoundComponent`** on the route, not inline `{isLoading && ...}`.
- **`defaultPreload: "intent"`** — hovering a `<Link>` prefetches the route + loader. Leave enabled.
- **Code splitting is automatic** via `tanstackRouter({ autoCodeSplitting: true })`. Don't manually `React.lazy` routes.

---

#### TanStack Form Standards

- **Always with zod** via `@tanstack/zod-form-adapter`.
- **Field-level validators** > form-level when the rule is single-field. Form-level for cross-field rules.
- **`<form.Subscribe>` for fine-grained reactivity.** Avoid `form.state.values` in a parent — use `<form.Subscribe selector={s => s.values.email}>`.
- **Async validators with debounce** for server-side checks (e.g. "is this email taken").
- **Extract large forms to their own file.** A form > ~100 lines moves to `features/<feature>/<form>.tsx`.
- **Never `useState` for form fields.** Use TanStack Form.

---

#### Caching & Performance

**Rules of thumb — in order of importance:**

1. **TanStack Query IS your cache for server state.** Never duplicate server data in React state, Redux, Zustand, or anywhere else.
2. **Prefer URL state over React state** for anything shareable/bookmarkable (filters, tabs, modals, pagination). React state only for ephemeral UI (hover, focus, animation phase).
3. **Prefetch via route loaders.** First-paint waterfall is the #1 perceived-slowness bug.
4. **`defaultPreload: "intent"`** — already enabled.
5. **Automatic route code splitting** — already enabled.
6. **Lazy-load heavy third-party libraries** (> 50KB gzipped): `const loadChartLib = () => import("recharts");`
7. **Memoize only when profiling says so.** `useMemo` / `useCallback` / `React.memo` have a cost.
8. **`useMemo` is required** for: TanStack Table column defs, stable object props to memoized children, expensive pure computations (> 1ms).
9. **`useCallback` only** when passing a function to a `React.memo`'d child or to a dependency array.
10. **Stable references in dependency arrays.** Never object/array literals in `useEffect` / `useMemo` deps.
11. **Images** — native `<img>` with explicit `width` and `height` (prevent CLS). `loading="lazy"` for below-fold.
12. **Bundle analysis** before any perf complaint: `bunx vite-bundle-visualizer`.
13. **Measure before optimizing.** Chrome DevTools → Performance tab → record → profile.

**Core Web Vitals targets** (critical for GEO ranking — we dogfood):

- LCP < 2.0s
- INP < 150ms
- CLS < 0.08

---

#### Clean Code & File Splitting

> 🎯 **TARGET PATTERN** — `src/features/` exists with `dashboard/` and `onboarding/`. Apply this layout when building new features.

**The 400-line rule is a hard cap, not a target.** If a file approaches 300 lines, start thinking about splitting.

**Split triggers — extract immediately when:**

- A component file grows past ~200 lines → move helpers into sibling files
- A hook grows past ~50 lines → its own file in `hooks/`
- A type definition grows past ~30 lines → `types.ts`
- A component has > 5 props that form a logical group → extract a sub-component
- You're about to copy-paste → extract a utility (but see "three strikes" below)
- A route file has any business logic → move it to `features/<feature>/`

**Three-strikes rule for extraction.** Don't pre-abstract. Duplicate twice — on the third occurrence, extract.

**Feature-based folder layout.** Each non-trivial feature gets a folder under `src/features/`:

```
src/features/workspaces/
  workspace-list.tsx          # main component (imported by the route)
  workspace-detail.tsx        # sibling components in the same feature
  workspace-form.tsx
  queries.ts                  # TanStack Query factories
  mutations.ts                # mutation hooks
  schemas.ts                  # zod schemas
  types.ts                    # shared types
  api.ts                      # raw fetch functions (thin, only called by queries/mutations)
  hooks.ts                    # feature-specific hooks
  utils.ts                    # pure functions
  constants.ts                # magic numbers, enums, labels
```

Routes (`src/routes/workspaces.tsx`) import from the feature folder:

```ts
// src/routes/workspaces.tsx — thin, ~15 lines
import { createFileRoute } from "@tanstack/react-router";
import { WorkspaceList } from "#/features/workspaces/workspace-list";
import { workspaceQueries } from "#/features/workspaces/queries";
import { workspaceSearchSchema } from "#/features/workspaces/schemas";

export const Route = createFileRoute("/workspaces")({
  validateSearch: workspaceSearchSchema,
  loaderDeps: ({ search }) => ({ search }),
  loader: ({ context, deps }) =>
    context.queryClient.ensureQueryData(workspaceQueries.list(deps.search)),
  component: WorkspaceList,
});
```

**Naming:**

- Files: `kebab-case.tsx`
- Components (exports): `PascalCase`
- Hooks (exports): `useCamelCase`
- Query/mutation factories: `camelCase` object (`workspaceQueries`, `scanMutations`)
- Zod schemas: `camelCaseSchema`
- Types/interfaces: `PascalCase`

**One component per file.** Multi-component files are banned. Exception: tiny internal helpers (< 10 lines) used exclusively by the main component in the same file.

**Component body structure** (top to bottom):

1. Imports
2. Types / schemas (if small; else extract)
3. Hooks at the top of the component (destructure props → local state → query hooks → mutation hooks → derived values → effects)
4. Event handlers
5. Early returns (loading, error, empty)
6. Main JSX

**Never inline** giant JSX. If a JSX block is > 30 lines, extract a sub-component.

---

#### Design System — Citetrack Brand

- **Monochrome first** — pure black and white. The logo is a white seed-of-life rosette on black. Avoid heavy use of gray.
- **Brand assets** live in `/brand/` at repo root (logo SVGs, favicon, og-image).
- **Design tokens** live in `apps/web/src/styles.css` using Tailwind v4's `@theme` block. Use semantic tokens (`bg-background`, `text-foreground`), never hardcoded colors.
- **Borders on inputs, textareas, selects** — use `--color-border` (near-black), not `border-gray-200` / `border-gray-300`.
- **Focus rings** — dark/black, not colored or light.
- **Typography** — Inter or Geist. Enable tabular numerals: `font-variant-numeric: tabular-nums`.
- **Avoid `text-gray-400`** for placeholder/label text — prefer token-based or `text-neutral-*`.
- **All recommended a11y rules active** — button types, alt text, ARIA, semantic HTML.

#### `@citetrack/ui` Library

**Current state:**
- 61 Shadcn-based components in `packages/ui/src/components/` (`button`, `dialog`, `input`, `sidebar`, `card`, `chart`, and more)
- Per-file exports via package.json `exports` map
- Per-file imports: `import { Button } from "@citetrack/ui/button"` (NOT barrel)
- `cn()` utility also exported from `"@citetrack/ui"`

**When adding a new component:**

1. Copy from Shadcn docs to `packages/ui/src/components/<name>.tsx`
2. Adapt to Citetrack tokens (black/white, no gray defaults)
3. Add entry to `packages/ui/package.json` `exports`:
   ```json
   "exports": {
     ".": "./src/index.ts",
     "./lib/utils": "./src/lib/utils.ts",
     "./<name>": "./src/components/<name>.tsx"
   }
   ```
4. Verify: `import { ComponentName } from "@citetrack/ui/<name>"` works in `apps/web`

---

### Backend Conventions (apps/api)

The backend at `apps/api` is a **FastAPI service** in Python 3.11+.

- Async-first — all handlers are `async def`
- Pydantic models as source of truth for request/response contracts
- Structured JSON logging with `loguru`
- Health check at `/api/v1/health`
- OpenAPI auto-generated at `/docs`
- JWT validated via Clerk JWKS (see `apps/web/docs/auth.md` for end-to-end)
- Database access via shared `solaraai-prisma-client` (local workspace link)
- Background jobs via ARQ + Redis

**File organization:**

```
apps/api/ai_visibility/
├── api/                    # FastAPI app, routes
│   ├── app.py             # Entry point: create_app()
│   └── routes.py          # Route definitions
├── analysis/              # LLM response analysis
├── providers/             # Per-provider adapters (ChatGPT, Claude, etc.)
├── runs/                  # Scan orchestration
├── storage/               # Prisma wrappers, repositories
├── alerts/                # Webhooks, email notifications
├── integrations/          # External APIs (DataForSEO, Tavily, Exa)
├── recommendations/       # Deterministic rules engine
├── scheduler/             # ARQ worker, cron
└── config.py              # Pydantic Settings from env
```

**Rules:**

- NEVER `print()` in production code — use `loguru`
- NEVER bare `except:` — always specific exception types
- NEVER hardcode API keys — only `pydantic-settings`
- Prefer `asyncio.gather()` over sequential `await`s for parallel work
- Use `httpx.AsyncClient` for HTTP (never `requests` — it's sync)

---

## 5) Testing Philosophy

### Current State

This repo was bootstrapped from `ai-visibility` (248+ existing Python tests). Frontend tests are minimal (just TanStack Start scaffold).

### Rules

- **Integration tests > unit tests.** Less brittle, more confidence.
- **Coverage ≥ 95%** for touched areas when writing tests.
- **Never delete/skip/rename tests** to make CI pass. Fix the root cause.
- **Bug fix protocol:** write a failing test that reproduces the bug → fix → verify test passes.
- **Real systems in tests** — Docker containers for Postgres / Redis. Mock ONLY unavoidable third-party APIs (Clerk, LLM providers, Lemon Squeezy).

### Commands

```bash
# TypeScript
bunx nx test @citetrack/web
bunx nx test @citetrack/web --coverage

# Python
cd apps/api
uv run pytest
uv run pytest --cov
uv run pytest -m "not slow"  # Skip tests that hit real LLM APIs
```

### Definition of Done

A task is NOT done until:

1. Real flow tested end-to-end against real services (or Docker-backed integrations)
2. Automated tests cover the new/changed behavior
3. Coverage ≥ 95% for touched areas
4. Debug logs cleaned up; useful structured logs kept
5. TypeScript passes (`nx typecheck`)
6. Biome lint passes (`bun run lint`)
7. No new secrets in git history
8. PR documented

---

## 6) Git & CI/CD

### Repository

- **GitHub:** https://github.com/yuvals41/citetrack
- **Default branch:** `master` (deliberate — matches Solara platform convention, not the modern "main" default)
- **Owner:** yuvals41 (Yuval Strutti's personal GitHub account)

### Git Conventions

- **Conventional Commits:** `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`, `perf:`, `ci:`
- **Scopes:** `web`, `api`, `ui`, `types`, `config`, `api-client`, `deps`, `infra`, or `all`
- Examples:
  - `feat(web): add KPI cards to dashboard`
  - `fix(api): correct JWT validation for Clerk tokens`
  - `chore(deps): bump tanstack-router to v1.200.0`
- **Branch naming:** `feat/<scope>-<description>` or `fix/<scope>-<description>` — e.g. `feat/web-dashboard-kpi-cards`
- **Trunk-based development:** short-lived branches, merge to `master` frequently
  - Solo founder reality: most small changes commit directly to master
  - Use feature branches for anything > 2 commits or experimental

### Git Hooks

**None configured yet.** No lefthook, no husky, no pre-commit. Commits are NOT checked locally until GitHub CI runs.

When adding hooks later: use [lefthook](https://github.com/evilmartians/lefthook) (matches Solara platform).

### CI Pipeline (future)

Not yet configured. Target GitHub Actions pipeline:

- Triggered on push and PR
- `bunx nx affected -t lint test typecheck build` — only affected projects
- Vercel preview deploy on every PR (auto — already linked)
- Vercel production deploy on merge to master (auto — already linked)

### Deployment

- **apps/web** → Vercel (not yet configured)
- **apps/api** → Fly.io or Railway (not yet configured)
- **Postgres** → Supabase Pro or Neon (not yet set up — uses Solara's local Prisma client)
- **Redis** → Upstash (not yet set up)
- **Domain** → citetrack.ai (registered via Porkbun, no content yet)

See `apps/web/docs/deployment.md` and `apps/api/docs/runbooks.md` for target deployment steps.

---

## 7) Database

### Prisma ORM

- Shared schema in `prisma/` at monorepo root (future)
- For now, uses the Solara platform's prisma client via `/home/yuval/Documents/solaraai/stanley/repos/prisma/dist/client-python` (local path)
- Default rule: **do not create Prisma migrations unless explicitly asked**
- When migration is needed: keep schema change + migration + client generation together
- Both TypeScript (future) and Python services consume the generated client

### Migration Path

Eventually, Citetrack will have its own Prisma schema (separate from Solara's). Plan:

1. Copy relevant schema fragments from `solaraai/stanley/repos/prisma/schema.prisma` into `citetrack/prisma/schema.prisma`
2. Keep only the `ai_vis_*` tables (workspaces, runs, prompt_executions, etc.)
3. Drop Solara-specific tables (content-generation, social-publishing, etc.)
4. Generate Citetrack-specific Prisma clients

---

## 8) Monorepo-Specific Rules

### Workspace Dependencies

```jsonc
// Internal package dependency — use workspace protocol
{ "dependencies": { "@citetrack/ui": "workspace:*" } }

// External dependency — pin exact version or use caret
{ "dependencies": { "react": "^19.2.0" } }
```

### Adding a New App

1. Create directory under `apps/<name>/`
2. Add `package.json` (TS) or `pyproject.toml` (Python) with proper name (`@citetrack/<name>`)
3. Add `project.json` with NX targets (`dev`, `build`, `test`, `typecheck`)
4. Add `README.md` with quick start
5. Add `docs/` folder with at minimum `architecture.md` and `development.md`
6. Verify with `bunx nx show projects`

### Adding a New Package

1. Create directory under `packages/<name>/`
2. Add `package.json` with name `@citetrack/<name>`
3. Add `src/index.ts` with public exports
4. Update `tsconfig.base.json` `paths` to include the new alias
5. Add `README.md`
6. Use in apps via `"@citetrack/<name>": "workspace:*"`
7. Run `bun install`

### NX Task Pipeline

```
build → depends on upstream ^build (build deps first)
test → depends on nothing (can run immediately)
typecheck → depends on nothing
lint → depends on nothing
dev → depends on nothing (but excluded from affected commands)
```

---

## 9) What We Do NOT Use

| Tool | Reason |
|---|---|
| npm / pnpm / yarn | Replaced by Bun |
| ESLint | Replaced by Biome (TS/JS) |
| Prettier | Replaced by Biome (TS/JS) |
| flake8 / black / isort | Replaced by Ruff (Python) |
| ts-node / tsx | Bun runs TypeScript natively |
| Jest | Using Vitest (comes with TanStack Start scaffold) |
| Turborepo | NX (polyglot, matches platform pattern) |
| Poetry / pip / conda | Replaced by UV |
| Redux / Zustand (for server state) | TanStack Query |
| NextAuth | Clerk (faster to ship, 10k MAU free) |
| `useState` for forms | TanStack Form |
| `useEffect`+`fetch` | TanStack Query |
| `styled-components` / Emotion | Tailwind v4 |
| Reflex (from original ai-visibility) | Dropped — replaced by TanStack Start |

---

## 10) Skills & Agent Roles

When working on a specific domain, load the relevant **skill** (specialized knowledge) and act under the relevant **role** (ownership boundary).

### Skills

| Skill | Domain |
|---|---|
| **tanstack** | TanStack Start/Router/Query/Form/Table/Virtual, Vite, React 19, `@citetrack/ui` — see §4 Frontend Conventions |
| **python-fastapi** | FastAPI, UV, pytest, Pydantic, async patterns, structured logging |
| **prisma** | Schema design, migrations, cross-app data access |
| **clean-code** | Simplicity, file size, naming, error handling — applies everywhere |

### Roles

| Role | Owns | Key Rule |
|---|---|---|
| **Frontend** | `apps/web/`, `packages/ui/`, `packages/api-client/`, `packages/types/`, `packages/config/` | TanStack stack. `@citetrack/ui` for shared components. Brand tokens for styling. Never introduce state mgmt competing with TanStack Query. |
| **Backend** | `apps/api/` (and future `apps/worker/`) | FastAPI + async. Pydantic as contract source. Structured logging with correlation IDs. `/health` on every service. |
| **Prisma Manager** | `prisma/` (future) | Single authority on schema. Never creates migrations automatically — documents required changes for human review. Validates backward compatibility. |

**Interaction flow:** When Frontend needs an API field, it asks Backend. When Backend needs a schema change, it asks Prisma Manager; it never touches `prisma/` itself.

---

## 11) Common Commands

Run from monorepo root unless noted.

```bash
# Install everything (Node + Python)
bun install
uv sync --all-packages

# Development
bunx nx dev @citetrack/web            # → http://localhost:3000
bunx nx dev @citetrack/api            # → http://localhost:8000
bunx nx run-many -t dev --parallel   # Both in parallel

# Build
bunx nx build @citetrack/web
bunx nx run-many -t build            # All projects

# Test
bunx nx test @citetrack/web
cd apps/api && uv run pytest
bunx nx affected -t test             # Only affected by git changes

# Lint
bun run lint                          # Biome across everything
bun run lint:fix                      # Auto-fix
cd apps/api && uv run ruff check .    # Python

# Type check
bunx nx typecheck @citetrack/web
bunx nx run-many -t typecheck

# Everything (pre-push sanity check)
bun run check                         # lint + typecheck across monorepo

# NX tools
bunx nx show projects                 # List all projects
bunx nx graph                         # Dependency graph (opens browser)
bunx nx reset                         # Clear all caches
```

---

## 12) Environment & Secrets

### `.env` Hierarchy

```
  .env              # Gitignored — never commit
  .env.local        # Gitignored — local machine overrides
  .env.development  # Gitignored — dev-only vars
  .env.example      # Committed — template with all required vars
```

### Required Variables

See `.env.example` at repo root. Categories:

- **Clerk Auth** — `VITE_CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY`, `CLERK_WEBHOOK_SECRET`
- **Database** — `DATABASE_URL`
- **Redis** — `REDIS_URL`
- **LLM Providers** — `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `PERPLEXITY_API_KEY`, `XAI_API_KEY`
- **Integrations** — `TAVILY_API_KEY`, `EXA_API_KEY`, `DATAFORSEO_LOGIN`, `DATAFORSEO_PASSWORD`
- **Payments** — `LEMONSQUEEZY_API_KEY`, `LEMONSQUEEZY_STORE_ID`, `LEMONSQUEEZY_WEBHOOK_SECRET`

### Secret Handling

- NEVER commit `.env*` files (except `.env.example`)
- NEVER log secrets
- NEVER include secrets in git history (use `git-filter-repo` if one leaks)
- NEVER share secrets in chat / screenshots / commit messages
- Production secrets in Vercel / Fly.io dashboards only

---

## 13) Stealth Brand Separation

Citetrack AI is a **separate, discreet brand** from Solara AI (Yuval's primary startup). This separation is intentional.

### The Rules

- **Never commit to Citetrack from a Solara-affiliated git identity.** Git config at repo root:
  ```bash
  git config user.email "[email protected]"
  git config user.name "Yuval Strutti"
  ```
- **Never cross-reference Solara in public-facing copy.** No "Built by Solara AI" on the Citetrack marketing site.
- **Never deploy Citetrack from Solara infrastructure** — separate Vercel/Fly accounts, separate DNS, separate payment processor.
- **Local development is OK** — the two repos live on the same laptop (`/home/yuval/Documents/solaraai/stanley/` vs `/home/yuval/Documents/solaraai/citetrack/`), but artifacts stay separate.
- **Shared Python packages** (`solaraai-llm`, `solaraai-prisma-client`) are currently linked via **local path**, not registry. This is a temporary bridge — long term we need our own versions or a published registry.
- **IP separation** — an IP separation memo was sent to the Solara board. Any changes to the boundary need written acknowledgment.

### Why It Matters

If Solara investors or the board discover undisclosed side work, it creates friction. The separation protects:

1. **Fiduciary duty** — Solara AI is Yuval's primary responsibility.
2. **Time allocation** — Side work is capped at 10-15 hrs/week.
3. **IP clarity** — Citetrack tool was built as a personal project, not on Solara time.
4. **Future optionality** — a separate brand can be sold or spun out cleanly.

### Current Brand

- **Name:** Citetrack AI
- **Domain:** citetrack.ai (primary), citetrack.com + sitetrack.ai (defensive redirects)
- **Tagline:** "Track how AI cites your brand"
- **Logo:** White seed-of-life rosette on black (see `/brand/official/`)
- **Target:** B2B SaaS marketing managers + small agencies
- **Pricing:** Free tier / $49/mo / $149/mo agency tier
- **Business model:** Self-serve SaaS + optional high-ticket inbound (concierge audits)

See [AI_VISIBILITY_LAUNCH_PLAYBOOK.md](../stanley/AI_VISIBILITY_LAUNCH_PLAYBOOK.md) (stored in stanley, out of repo) for full strategy context.

---

## 14) Known Tech Debt / Current Limitations

Honest list of things that need fixing but haven't been addressed yet.

### 🔴 Critical (blocks other machines / CI)

**Local-path Python dependencies**

`apps/api/pyproject.toml` has absolute paths to Yuval's Solara stanley repo:

```toml
solaraai-llm = { path = "/home/yuval/Documents/solaraai/stanley/repos/solaraai-packages/packages/python/solaraai-llm", editable = true }
solaraai-prisma-client = { path = "/home/yuval/Documents/solaraai/stanley/repos/prisma/dist/client-python", editable = true }
```

**Impact:** `uv sync` fails on any machine that isn't Yuval's laptop. CI cannot install deps. Contributors cannot onboard.

**Fix options:**

1. Publish `solaraai-llm` and `solaraai-prisma-client` as private PyPI packages (needs registry setup)
2. Vendor the relevant code into `citetrack/packages/python/` (heavier, tighter coupling)
3. Refactor `apps/api` to not depend on either package (use `prisma-client-py` directly + replace `solaraai-llm` with `mirascope` or `openai` SDK)

**Priority:** Must fix before any contributor/CI onboarding.

### 🟡 Important (but not blocking current work)

**Prisma schema ownership unclear**

`apps/api` imports the Prisma client from Solara's stanley repo. Citetrack has NO schema of its own. Tables used by the API (`ai_vis_workspaces`, `ai_vis_runs`, etc.) live inside Solara's schema.

**Impact:** Citetrack is effectively reading/writing to Solara's database schema. Any schema change requires coordination with Solara.

**Fix:** Fork the relevant schema fragments into `citetrack/prisma/schema.prisma`, generate our own Prisma clients, migrate data if needed.

**Priority:** Fix before launching to real customers. Stealth brand can't cleanly separate from Solara while sharing a database schema.

**Legacy folders still in `apps/api/`**

Migrated from ai-visibility but not cleaned up:

- `apps/api/.sisyphus/` — 47 evidence files from previous task tracking system. Historical artifact. Can delete or move to `docs/history/`.
- `apps/api/data/` — 244KB of seed data. May or may not be used.
- `apps/api/docker/` — Old Docker configs alongside the root `Dockerfile` / `docker-compose.yml`. May overlap.
- `apps/api/Dockerfile`, `Dockerfile.dev` — Pre-date the monorepo context. Build paths may be wrong.
- `apps/api/docker-compose.yml` — Still references ai-visibility by name in places.

**Fix:** Audit each, keep what's used, delete or archive the rest.

### 🟡 Documentation claims not yet real

This `AGENTS.md` describes many patterns as if they exist. Progress tracker:

**Done (as of auth+dashboard+onboarding workstream):**
- ✅ `src/features/` folder in `apps/web` (dashboard + onboarding)
- ✅ Shadcn primitives in `@citetrack/ui` (61 components)
- ✅ Clerk integration — end-to-end (frontend ClerkProvider + auth routes + FastAPI JWT verifier)
- ✅ `QueryClientProvider` in `src/routes/__root.tsx` (module-level singleton, not `createRootRouteWithContext`)
- ✅ Auth pages: `/sign-in/$`, `/sign-up/$`, `/forgot-password` (with Clerk-less fallback)
- ✅ Onboarding wizard: 4-step flow with Zod validation
- ✅ Dashboard shell: sidebar + 48px page header
- ✅ Dashboard page: KPI cards + trend chart + findings + actions (real API wiring)
- ✅ `apps/web/src/lib/` — `clerk-appearance.ts`, `require-auth.ts`, `logger.ts`
- ✅ `docs/AUTH_DASHBOARD_ONBOARDING_COMPLETE.md` — completion record

**Still pending:**
- ❌ Lemon Squeezy integration
- ❌ Sentry / Plausible
- ❌ GitHub Actions
- ❌ lefthook / pre-commit
- ❌ Registered sub-routes for `/dashboard/brands`, `/dashboard/competitors`, etc. (sidebar nav items currently use `<a href>` because the routes don't exist yet)
- ❌ Clerk dashboard setup (keys not yet created — see `docs/CLERK_SETUP.md`)
- ❌ Router context with `queryClient` via `createRootRouteWithContext` (currently module-level singleton)
- ❌ Auth guards via `beforeLoad` (currently handled inside components)

All pending items labeled as TARGET PATTERN in the sections where they appear. Don't trust examples without first checking the file.

### 🟡 Test running without API keys

`apps/api` tests include a `@pytest.mark.slow` marker for tests that hit real LLM APIs. To run tests without keys:

```bash
cd apps/api
uv run pytest -m "not slow"
```

This skips the ~20 tests that require real API keys (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.), but **it is no longer a green command by itself**.

As of 2026-05-03, the raw `uv run pytest -m "not slow"` baseline is dominated by non-key-related test debt:

- browser E2E files that require `apps/web` running on `http://localhost:3000`
- legacy E2E files still written against removed SQLite-style repository constructors / sync CLI helpers
- a small number of stale contract tests (`tests/test_pixel.py`, `tests/test_platform_integration.py`)

Use the documented green-set in `apps/api/docs/test-health.md` for the current no-keys confidence run:

```bash
cd apps/api
uv run pytest -m "not slow" \
  --ignore=tests/e2e \
  --ignore=tests/test_pixel.py \
  --deselect=tests/test_platform_integration.py::TestJobEntryPoint::test_job_id_from_payload \
  -q
```

That command is the current smoke-suite floor and passes without external services or API keys.

### 🟢 Quality-of-life improvements (nice to have)

- Add `lefthook.yml` with pre-commit Biome + pre-push typecheck
- Add GitHub Actions workflow (at minimum: lint + typecheck on PR)
- Add `CONTRIBUTING.md` (even if solo — helps future you)
- Add Storybook for `@citetrack/ui` (matches Solara platform pattern)
- Add `CHANGELOG.md` per-app using Changesets
- Add `.env.local` template auto-generator

### 🟢 Brand / launch prep not started

Separate from code debt, the business side has its own todo list (documented in `AI_VISIBILITY_LAUNCH_PLAYBOOK.md` in the Solara stanley directory, not this repo). Key items:

- Social accounts not claimed (@citetrack on X, LinkedIn, etc.)
- Osek Patur not registered
- Lemon Squeezy account not created
- No landing page on citetrack.ai
- No free tool / SEO content

---

## 15) Keep In Mind — Agent Mental Checklist

Before you act, pause and run this checklist:

- Did I read and follow `AGENTS.md` first, instead of relying on habit or assumptions?
- Am I solving the real problem, not masking it with a workaround or cosmetic patch?
- Am I staying inside the repo's chosen tools, architecture, and package-manager rules?
- Am I preserving existing behavior unless the user explicitly asked to change it?
- Am I keeping the solution simple, local, and easy for a tired developer to understand later?
- When writing UI code, am I following the existing established patterns, components, tokens, and visual guidelines (monochrome black/white, Citetrack tokens)?
- Before inventing a new component or pattern, did I check `@citetrack/ui` and nearby screens?
- Is my component filling up with implementation details, and should those details move into their own file?
- Did I avoid unnecessary abstraction, duplication cleanup, or refactors that the task did not require?
- If I claim something works, have I actually verified it with the strongest check available?
- Am I respecting the stealth brand separation (§13)?
- Did I run `bun run lint` and `bun run typecheck` before claiming the change is done?

---

**This document is the source of truth. If something contradicts it, fix AGENTS.md first, then the code.**
