# Citetrack AI

> Track how AI cites your brand across ChatGPT, Claude, Perplexity, Gemini, Grok, and AI Overviews.

## Documentation

- **[Architecture](./docs/architecture.md)** — system diagram, data flow, security
- **[Development](./docs/development.md)** — setup, workflow, troubleshooting
- **[Tech Stack](./docs/tech-stack.md)** — why every tool was chosen

### Per-app docs

- **[apps/web](./apps/web/README.md)** — TanStack Start frontend (+ `docs/architecture.md`, `docs/development.md`, `docs/styling.md`, `docs/auth.md`, `docs/deployment.md`)
- **[apps/api](./apps/api/README.md)** — Python FastAPI backend (+ `docs/research-report.md`, `docs/PHASE_2_PLAN.md`, `docs/PHASE_3_PLAN.md`, `docs/runbooks.md`)

### Per-package docs

- **[packages/ui](./packages/ui/README.md)** — Shared UI primitives
- **[packages/types](./packages/types/README.md)** — Shared TypeScript types
- **[packages/config](./packages/config/README.md)** — Shared constants
- **[packages/api-client](./packages/api-client/README.md)** — Typed fetch client

## Monorepo Structure

```
citetrack/
├── apps/
│   ├── web/          # TanStack Start frontend (React)
│   ├── api/          # Python FastAPI backend
│   └── worker/       # ARQ background workers
├── packages/
│   ├── ui/           # Shared UI components (Shadcn-based)
│   ├── types/        # Shared TypeScript types
│   ├── config/       # Shared configs
│   └── api-client/   # Typed API client for frontend
├── prisma/           # Database schema (Prisma)
└── tools/            # Build scripts, tooling
```

## Tech Stack

- **Monorepo:** NX + Bun workspaces (+ UV for Python)
- **Frontend:** TanStack Start + Tailwind + Shadcn/ui
- **Auth:** Clerk
- **Backend:** Python 3.11+ / FastAPI
- **Database:** Prisma + PostgreSQL
- **Workers:** ARQ + Redis
- **Payments:** Lemon Squeezy
- **Linting:** Biome (JS/TS), Ruff (Python)
- **Deployment:** Vercel (web) + Fly.io/Railway (api)

## Getting Started

```bash
# Install dependencies
bun install
uv sync

# Development
bun dev

# Build all
bun run build

# Test all
bun run test
```

## Environment Variables

See `.env.example` in each app for required environment variables.

## License

Proprietary. © 2026 Citetrack AI.
