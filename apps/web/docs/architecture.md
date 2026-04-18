# Architecture

## Overview

`@citetrack/web` is a **server-rendered React SPA** built on TanStack Start. Routes are file-based, data fetching uses TanStack Query, auth is Clerk, and everything is typed end-to-end with TypeScript.

---

## Rendering Strategy

```
  User request
       │
       ▼
  ┌────────────────────────┐
  │   Nitro server         │  SSR: Render matched routes on server
  │   (vite dev / build)   │  Stream HTML + hydration payload
  └────────┬───────────────┘
           │
           ▼
  ┌────────────────────────┐
  │   Browser (hydrates)   │  React hydrates server HTML
  │                        │  Subsequent nav = client-side SPA
  └────────────────────────┘
```

- **First page load** — server-rendered HTML, fully hydratable
- **Subsequent navigation** — client-side SPA (no full page reload)
- **Data loaders** — run on server during SSR, on client during navigation
- **Server functions** — `createServerFn()` for mutations that only run server-side

---

## Routing

File-based via [TanStack Router](https://tanstack.com/router). Files in `src/routes/` become routes automatically:

```
  src/routes/
  ├── __root.tsx          → Root layout (wraps all routes)
  ├── index.tsx           → /
  ├── about.tsx           → /about
  ├── dashboard/
  │   ├── index.tsx       → /dashboard
  │   └── scans.tsx       → /dashboard/scans
  ├── _auth.tsx           → Layout route (doesn't affect URL)
  │   ├── sign-in.tsx     → /sign-in (inside _auth layout)
  │   └── sign-up.tsx     → /sign-up
  └── api/
      └── webhook.ts      → /api/webhook (server-only handler)
```

**Type safety** — every route path, param, and search string is fully typed. `<Link to="/dashboard">` will error at build time if the route doesn't exist.

---

## Data Fetching

Three mechanisms, in order of preference:

### 1. Route loaders (preferred for page data)

```tsx
export const Route = createFileRoute("/dashboard")({
  loader: async () => {
    return citetrackApi.snapshotOverview("default");
  },
  component: Dashboard,
});

function Dashboard() {
  const data = Route.useLoaderData();
  return <Chart data={data.scores} />;
}
```

- Runs on server during SSR → no loading flash
- Deduped automatically via TanStack Query
- Cached per route

### 2. TanStack Query (dynamic data)

```tsx
const { data, isPending } = useQuery({
  queryKey: ["runs", workspaceId],
  queryFn: () => citetrackApi.listRuns(workspaceId),
});
```

Use for:
- Data that changes during the user's session
- Optimistic updates
- Background refetches

### 3. Server functions (mutations)

```tsx
const createWorkspace = createServerFn({ method: "POST" })
  .validator(z.object({ domain: z.string() }))
  .handler(async ({ data }) => {
    // Runs server-side only (safe for secrets, DB access)
  });
```

---

## State Management

| State type | Tool | Example |
|---|---|---|
| Server state | TanStack Query | Workspaces, scan runs, metrics |
| URL state | TanStack Router search params | `?workspace=foo&period=30d` |
| Local UI state | `useState` / `useReducer` | Modal open, form inputs |
| Global UI state | Zustand (add when needed) | Theme, sidebar collapse |
| Auth state | Clerk (`useAuth`, `useUser`) | User, session, org |

**No Redux.** Most "global state" is either server state (→ TanStack Query) or URL state (→ Router search).

---

## Auth

Clerk handles auth end-to-end. See [auth.md](./auth.md) for details.

```
  Unauthenticated user → /sign-in → Clerk hosted UI → JWT cookie set
                                                         │
                                                         ▼
                                            Authenticated → /dashboard
```

Protected routes use a `beforeLoad` guard that redirects to `/sign-in` if no user.

---

## Styling

Tailwind CSS v4 with brand tokens in `src/styles.css`. See [styling.md](./styling.md).

- Utility-first (no CSS modules, no styled-components)
- Components use `cn()` from `@citetrack/ui` for conditional classes
- Shadcn primitives for complex components (dialog, dropdown, toast)
- Brand: monochrome black/white, Helvetica-adjacent (Inter / Geist)

---

## API Integration

The web app talks to `@citetrack/api` (Python FastAPI) via a typed client:

```
  apps/web              packages/api-client           apps/api
     │                        │                          │
     │  import citetrackApi   │                          │
     │──────────────────────▶│                          │
     │                        │  fetch() with types      │
     │                        │─────────────────────────▶│
     │                        │◀─────────────────────────│
     │◀──────────────────────│  ScanRun[], etc.         │
```

- `packages/api-client/src/index.ts` — fetch wrappers
- `packages/types/src/index.ts` — shared request/response types
- Auth — Clerk session token passed as `Authorization: Bearer <jwt>`

---

## Error Boundaries

Every route has error boundaries:

```tsx
export const Route = createFileRoute("/dashboard")({
  errorComponent: ({ error }) => <ErrorView error={error} />,
  pendingComponent: () => <DashboardSkeleton />,
  component: Dashboard,
});
```

- `pendingComponent` shown while loader runs
- `errorComponent` catches loader + render errors
- Root route has a fallback for uncaught errors

---

## Performance

- **Streaming SSR** — HTML streams as soon as available (no waiting for all data)
- **Code splitting** — each route is a separate chunk
- **Prefetching** — `<Link preload="intent">` preloads on hover
- **Image optimization** — use `<img loading="lazy">` for below-fold images
- **Fonts** — Google Fonts via `<link rel="preconnect">`, subset with `&display=swap`

Target Core Web Vitals (for GEO ranking):
- LCP < 2.0s
- INP < 150ms
- CLS < 0.08
