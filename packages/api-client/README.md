# @citetrack/api-client

Typed fetch client for the Citetrack AI API (`@citetrack/api`).

## Usage

```tsx
import { createCitetrackClient } from "@citetrack/api-client";
import { useAuth } from "@clerk/tanstack-react-start";

function Dashboard() {
  const { getToken } = useAuth();

  const client = createCitetrackClient({
    baseUrl: import.meta.env.VITE_API_URL,
    getToken,
  });

  // ...
}
```

## Example Request

```tsx
import { createCitetrackClient } from "@citetrack/api-client";

const client = createCitetrackClient({
  baseUrl: import.meta.env.VITE_API_URL,
  getToken,
});

const runs = await client.getRuns("my-workspace");
```

## Exports

| Export | Description |
|---|---|
| `createCitetrackClient(options)` | Authenticated API client factory for all frontend requests |
| `ApiClientError` | Error type with `status` and raw `body` |
| `isDegraded(value)` | Type guard for degraded snapshot-style responses |
| `*` type exports | Re-exported API contract types from `@citetrack/types` for backward compatibility |

## With TanStack Query

```tsx
import { useQuery } from "@tanstack/react-query";
import { createCitetrackClient } from "@citetrack/api-client";

function Dashboard() {
  const { getToken } = useAuth();
  const client = createCitetrackClient({ baseUrl: import.meta.env.VITE_API_URL, getToken });

  const { data, isPending } = useQuery({
    queryKey: ["runs", "my-workspace"],
    queryFn: () => client.getRuns("my-workspace"),
  });

  // ...
}
```

## With Route Loaders

```tsx
export const Route = createFileRoute("/dashboard")({
  loader: async () => {
    const { getToken } = await getAuth();
    const client = createCitetrackClient({
      baseUrl: import.meta.env.VITE_API_URL,
      getToken,
    });

    return client.getSnapshotOverview("default");
  },
  component: Dashboard,
});

function Dashboard() {
  const data = Route.useLoaderData();
  // ...
}
```

## Error Handling

All client methods throw `ApiClientError` on non-2xx responses:

```tsx
import { ApiClientError } from "@citetrack/api-client";

try {
  await client.getRuns("x");
} catch (error) {
  if (error instanceof ApiClientError) {
    console.error(error.status, error.body);
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
3. Add method to the object returned by `createCitetrackClient` in `src/index.ts`:

```typescript
createScan: (workspace: string) =>
  authedRequest<ScanRun>(`/api/v1/scans?workspace=${workspace}`, {
    method: "POST",
  }),
```

## Why Not Auto-Generate?

We could generate from Python's OpenAPI schema (via `openapi-typescript`). Deferred because:
- Manual is 20 lines total right now
- Keeps type exports clean (no 10,000-line generated file)
- Once we have 20+ endpoints, switch to generation
