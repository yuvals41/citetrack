# Tech Stack

Detailed rationale for every tool choice in the Citetrack monorepo.

---

## Monorepo Layer

### NX

**What it does:** Task runner + dependency graph for multi-project repos.

**Why:**
- Incremental builds with caching (≥50% time saved on CI)
- Affected-only commands (`nx affected -t test` — don't test what didn't change)
- Plugin ecosystem (NX handles React, Python, Tailwind, etc.)
- Matches the Solara platform pattern — easier for AI agents to navigate

**Alternatives considered:**
- Turborepo — simpler but fewer plugins
- Lerna — outdated, poor DX
- Vanilla bun workspaces — no task caching

**Version:** 20.8.4

---

### Bun

**What it does:** JavaScript runtime + package manager + bundler + test runner.

**Why:**
- 10x faster than npm for install (30s vs 5min on this repo)
- Native workspace support (`workspaces: ["apps/*", "packages/*"]`)
- Runs TypeScript natively (no ts-node needed)
- Drop-in for Node.js — zero migration cost

**Alternatives considered:**
- pnpm — slower, uses symlinks (breaks some tooling)
- npm — slowest, but most compatible
- Yarn — no compelling advantages

**Version:** 1.3.8

---

### UV (Python)

**What it does:** Python package manager + venv manager + project manager.

**Why:**
- 50x faster than pip (Rust)
- Native workspace support (mirrors Bun's model)
- Auto-manages venv (`uv run` ensures venv is current)
- Deterministic builds via `uv.lock`

**Alternatives considered:**
- Poetry — slow, temperamental with build backends
- PDM — good but less momentum than UV
- pip + venv — manual, error-prone

**Version:** 0.9.11

---

## Frontend Layer

### TanStack Start

**What it does:** Full-stack React framework (SSR, routing, server functions).

**Why:**
- **Type-safe routing** — `<Link to="/dashboard">` errors at build if route doesn't exist
- **SSR + hydration** — fast first paint, interactive SPA
- **Server functions** — call Python-like functions that run server-side
- **Batteries included** — routing + data + SSR without 5 separate packages
- **Modern React 19** — concurrent features, use() hook
- **Officially partners with Clerk** — auth integration is trivial

**Alternatives considered:**
- Next.js 15 — great but over-engineered for side project
- Remix — merged into React Router, future uncertain
- SvelteKit — not React
- Astro — content-focused, wrong fit for app
- Vite + React + custom — too much boilerplate

**Version:** Latest RC

---

### TanStack Router

Built into TanStack Start. File-based routing with full type safety.

---

### TanStack Query

**What it does:** Server state management (fetch, cache, revalidate).

**Why:**
- Deduped requests across components
- Auto background refetching
- Optimistic updates
- Works perfectly with Server Components / loaders
- Best-in-class DevTools

**Alternatives considered:**
- SWR — simpler, fewer features
- Apollo Client — GraphQL-only
- Redux Toolkit Query — Redux lock-in

---

### Tailwind CSS v4

**What it does:** Utility-first CSS framework.

**Why:**
- Ship features fast (no context switching to CSS files)
- Built-in design system
- Small production bundle (only used classes)
- v4 uses Vite plugin (no `tailwind.config.js` needed)
- Dark mode built-in

**Alternatives considered:**
- CSS Modules — slow iteration, naming fatigue
- styled-components / emotion — runtime cost, SSR complexity
- Panda CSS — newer, less momentum

**Version:** 4.1.18

---

### Shadcn/ui

**What it does:** Copy-paste unstyled UI primitives built on Radix.

**Why:**
- You own the code — customize without fighting the library
- Accessible by default (WCAG AA)
- Composable — build complex UI from small pieces
- Ships to workspace (`@citetrack/ui`) for reuse

**Alternatives considered:**
- MUI — too opinionated, large bundle
- Ant Design — wrong aesthetic
- Chakra — solid but less Tailwind-integrated
- Headless UI — good but fewer components

---

### Clerk

**What it does:** Auth-as-a-service (sign-in, sign-up, MFA, SSO, orgs).

**Why:**
- **1-hour setup** — vs 2-week custom auth
- **10,000 MAU free tier** — covers first ~10k users
- **Built-in orgs** — multi-tenant support for free
- **Official TanStack partner** — first-class integration
- **SOC 2 compliant** — saves months of compliance work
- **JWT-based** — works with any backend (Python, Node, Go)

**Alternatives considered:**
- Better Auth — self-hosted, flexible, more work
- Auth.js (NextAuth) — free, flexible, less polished
- Supabase Auth — bundles auth + DB, creates lock-in
- Firebase Auth — Google lock-in, ancient
- Roll your own — multi-week effort, security risk

**Version:** 1.1.3

**Cost at scale:**
- 0-10k MAU: $0
- 10k-100k MAU: $25 + $0.02/MAU over 10k
- 100k+: ~$1,400/mo

---

### Lucide React

Icons. 1,200+ icons, tree-shakable.

---

### Zod

Runtime validation + TypeScript inference. Used for:
- API request/response validation
- Form inputs
- Environment variables

---

## Backend Layer

### FastAPI

**What it does:** Modern Python web framework.

**Why:**
- **Async-first** — perfect for I/O-heavy LLM calls
- **OpenAPI auto-generation** — `/docs` gives free API playground
- **Pydantic integration** — type-safe request/response models
- **Standards-based** — OAuth, JWT, CORS all built-in

**Alternatives considered:**
- Django — too heavy, sync-first
- Flask — minimal but lacks async + types
- Starlette — lower-level, more boilerplate
- NestJS (TypeScript) — rewrite entire backend

**Inherited from ai-visibility** — no migration cost.

---

### Pydantic

Type-safe data models. Source of truth for API contracts.

```python
class Workspace(BaseModel):
    id: str
    slug: str
    brand_name: str
    domain: str
```

---

### ARQ + Redis

**What it does:** Async job queue for Python.

**Why:**
- Async-native (works with FastAPI)
- Redis-backed (same Redis used for cache)
- Cron scheduling (daily scans at 06:00 UTC)
- Simple (500 LOC, auditable)

**Alternatives considered:**
- Celery — sync-first, heavier
- RQ — sync-only
- Dramatiq — good but less async support
- Trigger.dev — external service, cost

---

### Prisma

**What it does:** Type-safe ORM for Postgres.

**Why:**
- Schema-first (single `schema.prisma` file)
- Generates Python + TypeScript clients from same schema
- Migrations with `prisma migrate`
- Prisma Studio — DB UI for free

**Alternatives considered:**
- SQLAlchemy — Python-native but runtime types only
- Drizzle — TypeScript-only
- Raw SQL — fast but error-prone

**Shared with Solara** — saves from maintaining schema separately.

---

### Postgres

**What it does:** Relational database.

**Why:**
- JSONB for flexible data
- Full-text search built-in
- Materialized views for dashboard snapshots
- Battle-tested at any scale
- `pg_partman` for time-series partitioning

**Hosting options:**
- Supabase (free tier, easy)
- Neon (serverless, free tier)
- Railway Postgres
- AWS RDS (when at scale)

---

## Tooling Layer

### Biome

**What it does:** Linter + formatter + import organizer.

**Why:**
- **100x faster than ESLint + Prettier** (Rust)
- **Single tool** — no ESLint + Prettier + import sorter config
- **Compatible with existing ESLint/Prettier configs**
- **Active development** — by FormKit team

**Alternatives considered:**
- ESLint + Prettier — slow, two tools
- Oxlint — faster but less mature
- dprint — good but niche

**Version:** 1.9.4

---

### Ruff (Python)

**What it does:** Python linter (replaces flake8, isort, pylint).

**Why:**
- 50x faster than pylint
- Replaces 10+ Python tools
- By the same team as UV

---

### Vitest

**What it does:** Test runner (replaces Jest).

**Why:**
- Native ESM + TypeScript
- Vite-compatible (reuses vite config)
- 10x faster than Jest
- Jest-compatible API

---

### Pytest

Python test framework. Standard.

---

## Deployment Layer

### Vercel (Frontend)

- Best Next.js/React hosting
- Auto-deploys from GitHub
- Preview URLs for every PR
- Edge caching included
- $0 hobby → $20/mo Pro

---

### Fly.io (Backend)

- Global edge deployment for Python apps
- Simple `fly deploy`
- Postgres as service ($5/mo starter)
- Auto-scale to zero

**Alternatives:**
- Railway — similar, also simple
- Render — good but slower cold starts
- AWS Lambda — complex, cold start issues

---

### Upstash Redis

Serverless Redis. Free tier: 10,000 commands/day.

---

### Porkbun (Domains)

- Cheap (.ai $70/yr, .com $9/yr)
- Free WHOIS privacy
- Clean DNS UI

---

## Observability Layer

### Sentry

Error tracking + performance monitoring.

- $0 free (5k events/mo)
- $26/mo Team plan

---

### Plausible Analytics

Privacy-friendly analytics.

- $9/mo Starter

---

## Version Matrix (current)

| Tool | Version |
|---|---|
| Bun | 1.3.8 |
| NX | 20.8.4 |
| TypeScript | 5.9.3 |
| React | 19.2.0 |
| Tailwind | 4.1.18 |
| Vite | 8.0.0 |
| TanStack Start | latest RC |
| TanStack Router | latest |
| TanStack Query | 5.62+ |
| Clerk TanStack | 1.1.3 |
| Python | 3.13 |
| UV | 0.9.11 |
| FastAPI | 0.136.0 |
| ARQ | 0.28.0 |
| Pydantic | 2.13.2 |
| Prisma | latest |

Update with `bun update` and `uv sync --upgrade`.
