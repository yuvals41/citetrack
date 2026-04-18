# @citetrack/web

Frontend application for **Citetrack AI** — built with TanStack Start, Tailwind CSS, and Clerk auth.

## Quick Links

- **[Architecture](./docs/architecture.md)** — tech stack, routing, state, data flow
- **[Development](./docs/development.md)** — running locally, testing, debugging
- **[Styling](./docs/styling.md)** — Tailwind, brand tokens, component conventions
- **[Auth](./docs/auth.md)** — Clerk integration, sign-in flow, protected routes
- **[Deployment](./docs/deployment.md)** — Vercel / Cloudflare Pages setup

---

## Quick Start

```bash
# From monorepo root
bun install

# Run web dev server
nx dev @citetrack/web
# → http://localhost:3000
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | [TanStack Start](https://tanstack.com/start) (React 19, SSR) |
| Routing | File-based via [TanStack Router](https://tanstack.com/router) |
| Data | [TanStack Query](https://tanstack.com/query) (server state) |
| Auth | [Clerk](https://clerk.com) (`@clerk/tanstack-react-start`) |
| Styling | [Tailwind CSS v4](https://tailwindcss.com) + [class-variance-authority](https://cva.style) |
| UI | [Shadcn](https://ui.shadcn.com/) primitives + shared `@citetrack/ui` |
| Icons | [Lucide React](https://lucide.dev) |
| Build | Vite 8 + [Nitro](https://nitro.unjs.io) (server) |
| Validation | [Zod](https://zod.dev) |
| Testing | Vitest + Testing Library |
| Linting | Biome (monorepo root config) |

---

## Project Structure

```
apps/web/
├── docs/                     # This documentation
├── public/                   # Static assets (favicon, og-image)
├── src/
│   ├── router.tsx            # Router config + type registration
│   ├── styles.css            # Tailwind entry + global tokens
│   ├── routes/
│   │   ├── __root.tsx        # Root layout (head, scripts, outlet)
│   │   ├── index.tsx         # "/" landing page
│   │   └── about.tsx         # "/about" sample route
│   └── components/
│       ├── Header.tsx
│       ├── Footer.tsx
│       └── ThemeToggle.tsx
├── package.json              # @citetrack/web
├── project.json              # NX targets (dev, build, test, typecheck)
├── tsconfig.json             # extends ../../tsconfig.base.json
└── vite.config.ts            # Vite + TanStack Start + Tailwind + Nitro
```

---

## Scripts

| Command | Purpose |
|---|---|
| `bun run dev` | Dev server on :3000 |
| `bun run build` | Production build (client + Nitro server) |
| `bun run preview` | Preview production build |
| `bun run test` | Run Vitest tests |
| `bun run typecheck` | TypeScript check |

From monorepo root: use `nx <target> @citetrack/web`.

---

## Shared Package Imports

The app imports from workspace packages via path aliases (see `tsconfig.base.json`):

```typescript
import { cn } from "@citetrack/ui";
import { citetrackApi } from "@citetrack/api-client";
import type { Workspace } from "@citetrack/types";
import { APP_NAME, AI_PROVIDERS } from "@citetrack/config";
```

---

## Environment Variables

Create `.env.local` in `apps/web/`:

```bash
# Clerk (get from clerk.com dashboard)
VITE_CLERK_PUBLISHABLE_KEY=pk_test_xxx
CLERK_SECRET_KEY=sk_test_xxx

# API
VITE_API_BASE_URL=http://localhost:8000
```

See root [`.env.example`](../../.env.example) for all variables.
