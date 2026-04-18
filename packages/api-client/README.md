# @citetrack/api-client

Typed fetch client for the Citetrack AI API (`@citetrack/api`).

## Usage

```tsx
import { citetrackApi } from "@citetrack/api-client";

// Health check
const health = await citetrackApi.health();
// → { status: "ok", version: "1.0.0" }

// List workspaces
const workspaces = await citetrackApi.listWorkspaces();

// With auth token (from Clerk)
const { getToken } = useAuth();
const token = await getToken();

const runs = await citetrackApi.listRuns("my-workspace", { token });
```

## Exports

| Method | Endpoint | Returns |
|---|---|---|
| `health()` | `GET /api/v1/health` | `{ status, version }` |
| `listWorkspaces()` | `GET /api/v1/workspaces` | `{ items: Workspace[] }` |
| `latestRun(workspace)` | `GET /api/v1/runs/latest?workspace=X` | `ScanRun` |
| `listRuns(workspace)` | `GET /api/v1/runs?workspace=X` | `{ items: ScanRun[] }` |
| `snapshotOverview(workspace)` | `GET /api/v1/snapshot/overview?workspace=X` | `{ scores: VisibilityScore[] }` |

All methods accept optional `opts`:

```typescript
type RequestOptions = {
  baseUrl?: string;    // Override API_BASE_URL for this call
  token?: string;       // Auth token (Clerk JWT)
  signal?: AbortSignal; // Cancellation
};
```

## With TanStack Query

```tsx
import { useQuery } from "@tanstack/react-query";
import { citetrackApi } from "@citetrack/api-client";

function Dashboard() {
  const { data, isPending } = useQuery({
    queryKey: ["runs", "my-workspace"],
    queryFn: ({ signal }) => citetrackApi.listRuns("my-workspace", { signal }),
  });

  // ...
}
```

## With Route Loaders

```tsx
export const Route = createFileRoute("/dashboard")({
  loader: async () => {
    const { getToken } = await getAuth();
    const token = await getToken();
    return citetrackApi.snapshotOverview("default", { token });
  },
  component: Dashboard,
});

function Dashboard() {
  const data = Route.useLoaderData();
  // ...
}
```

## Error Handling

All methods throw `Error` on non-2xx responses:

```tsx
try {
  await citetrackApi.latestRun("x");
} catch (error) {
  if (error instanceof Error) {
    console.error(error.message); // "API 404: Not found"
  }
}
```

Consider wrapping with a `Result<T, E>` type if preferred:

```typescript
type Result<T> = { ok: true; data: T } | { ok: false; error: string };

async function safe<T>(fn: () => Promise<T>): Promise<Result<T>> {
  try {
    return { ok: true, data: await fn() };
  } catch (e) {
    return { ok: false, error: String(e) };
  }
}
```

## Adding a Method

1. Add Python endpoint in `apps/api/ai_visibility/api/routes.py`
2. Add response type in `@citetrack/types`
3. Add method in `src/index.ts`:

```typescript
createScan: (workspace: string, opts?: RequestOptions) =>
  request<ScanRun>(`/api/v1/scans?workspace=${workspace}`, opts, "POST"),
```

## Why Not Auto-Generate?

We could generate from Python's OpenAPI schema (via `openapi-typescript`). Deferred because:
- Manual is 20 lines total right now
- Keeps type exports clean (no 10,000-line generated file)
- Once we have 20+ endpoints, switch to generation
