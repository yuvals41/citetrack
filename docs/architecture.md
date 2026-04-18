# Architecture

End-to-end architecture of the Citetrack AI monorepo.

## System Diagram

```
                        ┌────────────────────┐
                        │  User (browser)    │
                        └──────────┬─────────┘
                                   │
                                   ▼
                        ┌────────────────────┐
                        │  apps/web          │
                        │  TanStack Start    │
                        │  (Vercel/CF Pages) │
                        └──────────┬─────────┘
                                   │ fetch() + JWT
                                   ▼
                        ┌────────────────────┐
                        │  apps/api          │
                        │  FastAPI (Python)  │
                        │  (Fly / Railway)   │
                        └──────────┬─────────┘
                                   │
                 ┌─────────────────┼─────────────────┐
                 │                 │                 │
                 ▼                 ▼                 ▼
          ┌──────────┐      ┌──────────┐      ┌──────────┐
          │ Postgres │      │  Redis   │      │  LLM     │
          │(Prisma)  │      │ (ARQ)    │      │  APIs    │
          └──────────┘      └──────────┘      └──────────┘
```

---

## Monorepo Structure

```
  citetrack/
  │
  ├── apps/
  │   ├── web/          TanStack Start (frontend)
  │   ├── api/          FastAPI (backend)
  │   └── worker/       ARQ worker (future — split from api)
  │
  ├── packages/
  │   ├── ui/           Shared UI components (cn, Shadcn primitives)
  │   ├── types/        Shared TS types (Workspace, ScanRun, etc.)
  │   ├── config/       Shared constants (APP_NAME, AI_PROVIDERS)
  │   └── api-client/   Typed fetch client
  │
  ├── prisma/           Database schema
  └── tools/            Build scripts, dev tools
```

---

## Why NX + Bun + UV?

### NX
- Task orchestration across projects
- Incremental builds (cache → skip if nothing changed)
- Dependency graph (`nx graph` shows what depends on what)
- Affected commands (`nx affected -t test` runs only what changed)

### Bun
- Fastest JS package manager (30s install vs 3min for npm)
- Native workspace support
- Compatible with npm registry
- Runs JS/TS natively (no tsx/ts-node needed)

### UV (Python)
- Fastest Python package manager (50x faster than pip)
- Native workspace support (linked with NX)
- Handles venv creation automatically
- Reproducible via `uv.lock`

---

## Tech Stack

| Layer | Tool | Why |
|---|---|---|
| **Frontend framework** | TanStack Start | Modern React 19, SSR, type-safe routing |
| **Routing** | TanStack Router | File-based, fully typed links |
| **Data** | TanStack Query | Best-in-class server state |
| **Auth** | Clerk | Auth-as-a-service, 10k MAU free |
| **Styling** | Tailwind v4 | Utility-first, fast iteration |
| **UI primitives** | Shadcn/Radix | Copy-paste, own your code |
| **Backend framework** | FastAPI | Python + async + OpenAPI |
| **ORM** | Prisma | Type-safe DB access, migrations |
| **Queue** | ARQ | Redis-backed async job queue |
| **DB** | Postgres | Battle-tested, JSON support |
| **Payments** | Lemon Squeezy | Merchant of record (handles tax) |
| **Hosting (web)** | Vercel | Best Next-gen React hosting |
| **Hosting (api)** | Fly.io or Railway | Simple Python deploy |

---

## Data Flow

### Scan Execution

```
  1. User clicks "Run scan" in apps/web
  2. POST /api/v1/scans → apps/api (FastAPI)
  3. FastAPI enqueues job in Redis (ARQ)
  4. Worker picks up job:
     ├─ Calls ChatGPT API (via DataForSEO)
     ├─ Calls Claude API (via solaraai-llm)
     ├─ Calls Gemini API (via DataForSEO)
     ├─ Calls Perplexity API (direct)
     ├─ Calls Grok API (via solaraai-llm)
     └─ Calls Google AI Overviews (via DataForSEO SERP)
  5. Results aggregated → prompt_executions table
  6. Diagnostic engines run → diagnostic_findings
  7. Actions engine (Claude) → recommendation_items
  8. Worker updates job status → "completed"
  9. apps/web polls via TanStack Query → displays results
```

### Real-Time Updates

For long-running scans, use Server-Sent Events (SSE):

```python
# apps/api/ai_visibility/api/sse.py
from fastapi.responses import EventSourceResponse

@app.get("/api/v1/scans/{id}/stream")
async def scan_stream(id: str):
    async def event_generator():
        while True:
            status = await get_scan_status(id)
            yield {"data": status}
            if status == "completed": break
            await asyncio.sleep(2)
    return EventSourceResponse(event_generator())
```

```tsx
// apps/web
const eventSource = new EventSource(`/api/v1/scans/${id}/stream`);
eventSource.onmessage = (e) => setStatus(JSON.parse(e.data));
```

---

## Authentication Flow

```
  1. User hits apps/web → not authenticated → redirect /sign-in
  2. Clerk hosted UI collects email + code
  3. Clerk issues JWT cookie (HttpOnly, Secure)
  4. apps/web reads JWT via @clerk/tanstack-react-start
  5. On API call:
       Authorization: Bearer <JWT>
  6. apps/api validates JWT via Clerk JWKS (public keys)
  7. User ID extracted → scoped queries: WHERE user_id = X
```

See [apps/web/docs/auth.md](../apps/web/docs/auth.md) for frontend details.

---

## Deployment Topology

### Development

```
  localhost:3000 → apps/web (vite dev)
  localhost:8000 → apps/api (uvicorn --reload)
  localhost:5432 → Postgres (docker-compose)
  localhost:6379 → Redis (docker-compose)
```

### Staging

```
  staging.citetrack.ai → apps/web (Vercel preview)
  staging-api.citetrack.ai → apps/api (Fly staging)
  Postgres → Supabase free tier
  Redis → Upstash free tier
```

### Production

```
  citetrack.ai → apps/web (Vercel prod)
  api.citetrack.ai → apps/api (Fly.io prod, 2 regions)
  Postgres → Supabase Pro (or managed RDS)
  Redis → Upstash Pro
  Monitoring → Sentry + Plausible
```

---

## CI/CD (Future)

Planned GitHub Actions:

```yaml
# .github/workflows/ci.yml
on: [pull_request, push]
jobs:
  test:
    - bun install
    - nx affected -t lint typecheck test
  
  preview:
    if: github.event_name == 'pull_request'
    - Vercel preview deploy (auto)
  
  deploy-prod:
    if: github.ref == 'refs/heads/master'
    - nx affected -t build
    - Vercel promote to production
    - Fly deploy apps/api (if changed)
```

---

## Security

### Secrets

- **Never commit secrets** — all in `.env.local` (git-ignored)
- **Clerk keys** — server-only (`CLERK_SECRET_KEY`)
- **LLM API keys** — server-only (apps/api)
- **Webhook secrets** — verify all incoming webhooks

### API Authorization

Every endpoint that touches user data checks:

```python
from ai_visibility.auth.clerk import require_user

@app.get("/api/v1/runs")
async def list_runs(user = Depends(require_user)):
    return await repo.list_for_user(user.id)
```

### Database

- Row-level security via user ID scoping
- Prisma prevents SQL injection by default
- Encrypt PII at rest (Postgres pgcrypto)

### Rate Limiting

Planned: `slowapi` on FastAPI + Upstash rate limit on Vercel edge.

---

## Performance

### Frontend Budgets

| Metric | Target |
|---|---|
| LCP | < 2.0s |
| INP | < 150ms |
| CLS | < 0.08 |
| First load JS | < 200 KB gzipped |
| Bundle size per route | < 50 KB |

### Backend Budgets

| Metric | Target |
|---|---|
| API p95 latency | < 200ms (excluding LLM calls) |
| Scan end-to-end | < 60s for 6 providers |
| Worker throughput | 10 scans/min |

### Optimization Levers

- Vercel edge caching for static routes
- React Server Components where possible
- Prisma connection pooling (PgBouncer)
- Precomputed metric snapshots (no runtime joins)
- Redis cache for LLM responses (90% hit rate for same prompt)
