# Development

## Prerequisites

| Tool | Version | Install |
|---|---|---|
| Bun | ≥ 1.3 | `curl -fsSL https://bun.sh/install \| bash` |
| Node | ≥ 20 | (for NX) |
| Git | ≥ 2.40 | system |

---

## First-Time Setup

```bash
# Clone
git clone https://github.com/yuvals41/citetrack.git
cd citetrack

# Install all Node deps (creates .venv for Python too)
bun install

# Copy env template
cp apps/web/.env.example apps/web/.env.local
# Edit .env.local with real Clerk keys (get from clerk.com)

# Start dev server
nx dev @citetrack/web
# → http://localhost:3000
```

---

## Daily Workflow

```bash
# Pull latest
git pull

# Update deps if package.json changed
bun install

# Run dev
nx dev @citetrack/web

# In another terminal: run tests in watch mode
nx test @citetrack/web --watch
```

---

## NX Commands

All commands run from monorepo root.

| Command | What it does |
|---|---|
| `nx dev @citetrack/web` | Dev server with HMR |
| `nx build @citetrack/web` | Production build |
| `nx test @citetrack/web` | Run tests once |
| `nx typecheck @citetrack/web` | TypeScript check |
| `nx lint` | Biome lint (whole monorepo) |
| `nx graph` | Open dependency graph in browser |
| `nx affected -t test` | Run tests only for affected projects |

### Tips

```bash
# Force rebuild (skip cache)
nx build @citetrack/web --skip-nx-cache

# Reset all NX caches
bun run clean

# Run multiple targets in parallel
nx run-many -t dev --parallel
```

---

## Adding a Route

File-based routing — just create a file.

```bash
# Create src/routes/dashboard.tsx
```

```tsx
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/dashboard")({
  component: Dashboard,
});

function Dashboard() {
  return <div>Dashboard</div>;
}
```

The router auto-detects the new file. Routes are typed — `<Link to="/dashboard" />` works immediately.

### Nested routes

```
  src/routes/
  ├── dashboard/
  │   ├── index.tsx              → /dashboard
  │   ├── scans.tsx              → /dashboard/scans
  │   └── scans.$id.tsx          → /dashboard/scans/:id
```

### Layout routes (no URL impact)

Files prefixed with `_` are layouts:

```
  src/routes/
  ├── _authed.tsx                → Layout (checks auth, redirects if no user)
  │   ├── _authed.dashboard.tsx  → /dashboard (uses _authed layout)
  │   └── _authed.settings.tsx   → /settings (uses _authed layout)
```

---

## Adding a Component

Colocate in `src/components/` if app-specific, or add to `packages/ui/` if reusable.

```tsx
// src/components/MetricCard.tsx
import { cn } from "@citetrack/ui";

type Props = {
  label: string;
  value: number;
  className?: string;
};

export function MetricCard({ label, value, className }: Props) {
  return (
    <div className={cn("rounded-lg border p-4", className)}>
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  );
}
```

---

## Testing

```bash
# Run all tests (via NX)
nx test @citetrack/web

# Watch mode
nx test @citetrack/web --watch

# Coverage
nx test @citetrack/web --coverage
```

### Writing tests

```tsx
// src/components/MetricCard.test.tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MetricCard } from "./MetricCard";

describe("MetricCard", () => {
  it("renders label and value", () => {
    render(<MetricCard label="Visibility" value={87} />);
    expect(screen.getByText("Visibility")).toBeInTheDocument();
    expect(screen.getByText("87")).toBeInTheDocument();
  });
});
```

Testing library used: **Vitest** + `@testing-library/react`.

---

## Debugging

### TanStack DevTools

Built-in to dev builds. Look for the floating icon in the bottom-right of the browser.

- Router tree
- Query cache
- Pending loaders
- Server function calls

### Network requests

```bash
# In terminal, log all API calls
DEBUG=citetrack:api nx dev @citetrack/web
```

### Production source maps

Enabled by default in `vite.config.ts`. Use Chrome DevTools → Sources to debug production bundles.

---

## Code Quality

### Biome (lint + format)

Configured at monorepo root (`biome.json`).

```bash
# Lint
bun run lint

# Fix auto-fixable issues
bun run lint:fix

# Format only
bun run format
```

### TypeScript

```bash
# Typecheck
nx typecheck @citetrack/web

# Watch mode
cd apps/web && bun tsc --noEmit --watch
```

### Pre-commit hooks

(Add later with `lefthook` or `husky`.)

---

## Common Issues

### "Module not found: @citetrack/ui"

```bash
# Did you run install from the root?
cd /path/to/citetrack
bun install
```

### TanStack Router shows stale routes

```bash
# Clear the generated routeTree
rm apps/web/src/routeTree.gen.ts
nx dev @citetrack/web
```

### Clerk "publishable key missing"

```bash
# Copy env template and add keys
cp apps/web/.env.example apps/web/.env.local
# Get keys from https://dashboard.clerk.com
```

### Vite HMR stopped working

```bash
# Kill all vite processes and restart
pkill -f vite
nx dev @citetrack/web
```

---

## Git Workflow

```bash
# Feature branch
git checkout -b feat/dashboard-kpi-cards

# Commit with conventional prefix
git commit -m "feat(web): add KPI cards to dashboard"

# Push and open PR
git push -u origin feat/dashboard-kpi-cards
```

Commit prefixes:
- `feat(web):` — new feature
- `fix(web):` — bug fix
- `refactor(web):` — no behavior change
- `style(web):` — formatting only
- `test(web):` — test changes
- `docs(web):` — docs only
- `chore(web):` — tooling/deps
