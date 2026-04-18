# Development Guide

## Quick Start

```bash
# Clone
git clone https://github.com/yuvals41/citetrack.git
cd citetrack

# Install everything (Node + Python)
bun install   # installs Node deps + creates Python venv + installs Python deps

# Start all apps in parallel
bun dev
```

---

## Prerequisites

| Tool | Min version | Purpose |
|---|---|---|
| Bun | 1.3+ | Package manager, JS/TS runtime |
| Node | 20+ | NX compatibility |
| Python | 3.11+ | Backend |
| uv | 0.9+ | Python package manager |
| Docker | 24+ | Postgres + Redis (optional, can use Supabase/Upstash) |
| Git | 2.40+ | Version control |

### Installing Tools

```bash
# Bun
curl -fsSL https://bun.sh/install | bash

# uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Docker (optional)
# See https://docs.docker.com/engine/install/
```

---

## Running Individual Apps

```bash
# Web only
nx dev @citetrack/web           # → http://localhost:3000

# API only
nx dev @citetrack/api            # → http://localhost:8000

# Both in parallel
nx run-many -t dev --parallel
```

---

## Running Tests

```bash
# All tests (parallel)
bun test

# Specific app
nx test @citetrack/web
nx test @citetrack/api

# Only affected by my changes
nx affected -t test
```

---

## Linting & Formatting

```bash
# Lint whole monorepo
bun lint

# Auto-fix
bun lint:fix

# Format
bun format
```

Biome handles JS/TS. Ruff handles Python (run via `nx lint @citetrack/api`).

---

## Type Checking

```bash
# Whole monorepo
bun typecheck

# Specific app
nx typecheck @citetrack/web
```

---

## Git Conventions

### Branch naming

```
  feat/<scope>/<description>   # New feature
  fix/<scope>/<description>    # Bug fix
  refactor/<scope>/<description>
  chore/<scope>/<description>
  docs/<scope>/<description>
```

Examples:
- `feat/web/dashboard-kpi-cards`
- `fix/api/clerk-jwt-validation`
- `docs/root/add-architecture-doc`

### Commit messages

```
  <type>(<scope>): <short description>

  <optional longer explanation>

  <optional footer for breaking changes>
```

Types: `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `style`, `chore`, `build`, `ci`

Scopes: `web`, `api`, `ui`, `types`, `config`, `api-client`, `deps`, `infra`, or `all`

Examples:

```
  feat(web): add KPI cards to dashboard

  fix(api): correct JWT validation for Clerk tokens
  
  chore(deps): bump tanstack-router to v1.200.0
  
  refactor(all): extract auth logic to @citetrack/auth package
```

### Pull Requests

1. Branch from `master`
2. Make changes
3. Ensure `bun check` passes
4. Push: `git push -u origin <branch>`
5. Open PR on GitHub
6. Wait for Vercel preview URL
7. Self-review the preview
8. Merge (squash preferred)

---

## Environment Variables

### Hierarchy

```
  .env              # Never commit — overrides everything
  .env.local        # Gitignored — local machine overrides
  .env.development  # Gitignored — dev-only vars
  .env.example      # Committed — template with all required vars
```

### Per-app vs shared

- **Shared** (`citetrack/.env.local`) — DB URLs, Clerk keys, LLM API keys
- **Per-app** — rare; mostly for overrides like `PORT`, `NODE_ENV`

### Required variables

See `.env.example` at the repo root and in `apps/web/` and `apps/api/`.

---

## Docker Compose (Local Infra)

```bash
# Start Postgres + Redis
cd apps/api
docker compose up -d postgres redis

# Full stack (api + web + db + redis)
docker compose up -d
```

---

## NX Cheat Sheet

```bash
# See all projects
nx show projects

# See one project's config
nx show project @citetrack/web

# Run a target on a specific project
nx <target> <project>

# Run a target on all projects
nx run-many -t <target>

# Run on all projects matching a tag
nx run-many -t <target> --projects="tag:scope:web"

# Only projects affected by git changes since master
nx affected -t <target>

# Visualize dependencies
nx graph

# Reset NX cache
nx reset
```

---

## Common Gotchas

### "Module not found @citetrack/..."

Forgot to `bun install` from the root.

```bash
cd /path/to/citetrack
bun install
```

### Python imports failing

Workspace venv not activated.

```bash
# From apps/api — uv auto-activates
cd apps/api
uv run python ...

# Or explicitly
source .venv/bin/activate
```

### "Port 3000 already in use"

Another vite process running.

```bash
pkill -f vite
# or
lsof -ti:3000 | xargs kill -9
```

### Clerk sign-in redirects loop

Check Clerk dashboard → Paths → Home URL matches your dev URL exactly.

### Biome errors after `bun install`

Biome version mismatch between root and an app's `node_modules`.

```bash
rm -rf **/node_modules
bun install
```

---

## IDE Setup

### VS Code

Recommended extensions:

- Biome (`biomejs.biome`)
- Python (`ms-python.python`)
- Pylance (`ms-python.vscode-pylance`)
- Ruff (`charliermarsh.ruff`)
- TanStack Router (`tanstack.router`)
- Tailwind CSS IntelliSense (`bradlc.vscode-tailwindcss`)
- Prisma (`Prisma.prisma`)

Settings (`.vscode/settings.json`):

```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "biomejs.biome",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff"
  },
  "python.analysis.typeCheckingMode": "strict"
}
```

---

## Adding a New App

```bash
# 1. Create the directory
mkdir apps/admin

# 2. Add package.json (name as @citetrack/admin)
# 3. Add project.json with NX targets
# 4. Update root package.json workspaces if needed (wildcard covers apps/*)
# 5. Run `bun install`
# 6. Verify: `nx show projects` should list it
```

---

## Adding a New Package

```bash
# 1. Create the directory
mkdir packages/auth

# 2. Add package.json (name as @citetrack/auth)
# 3. Add src/index.ts
# 4. Update tsconfig.base.json "paths" to include the new alias
# 5. Use it in apps: `"@citetrack/auth": "workspace:*"`
# 6. Run `bun install`
```

---

## Debugging

### Frontend

- **TanStack DevTools** — bottom-right icon in dev builds
- **React DevTools** — browser extension
- **Vite error overlay** — errors appear in browser

### Backend

- **FastAPI docs** — http://localhost:8000/docs (Swagger UI)
- **ReDoc** — http://localhost:8000/redoc
- **Python debugger** — `breakpoint()` in code, runs in uvicorn

### Network

- **Browser DevTools → Network** — see all requests
- **API logs** — uvicorn logs in terminal
- **Redis** — `redis-cli monitor` shows all commands

---

## Performance Profiling

```bash
# Frontend
nx build @citetrack/web
npx serve apps/web/.output/public
# Use Lighthouse in DevTools

# Backend
cd apps/api
uv run python -m cProfile -o profile.stats -m uvicorn ai_visibility.api.app:app
uv run python -m pstats profile.stats
```

---

## Production Build (Local)

```bash
# Build everything
bun run build

# Preview web
cd apps/web && bun run preview  # → http://localhost:4173

# Preview api
cd apps/api && uv run uvicorn ai_visibility.api.app:app --port 8000
```
