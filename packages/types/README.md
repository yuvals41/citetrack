# @citetrack/types

Shared TypeScript types for Citetrack AI. API request/response contracts, domain models.

## Usage

```tsx
import type { Workspace, ScanRun, VisibilityScore, AIProvider } from "@citetrack/types";

function Dashboard({ runs }: { runs: ScanRun[] }) {
  // ...
}
```

## Exports

| Type | Description |
|---|---|
| `Workspace` | A tracked brand (id, slug, domain, brandName, createdAt) |
| `ScanRun` | A single scan execution (id, workspaceId, status, timestamps, providers) |
| `VisibilityScore` | Per-provider score (score, mentions, citations) |
| `Citation` | URL citation in an AI response (url, domain, provider, context) |
| `DiagnosticFinding` | Issue detected during scan (reasonCode, severity, provider, message, fix) |
| `AIProvider` | Union of provider IDs (re-exported from `@citetrack/config`) |

## Conventions

- **Dates** are ISO strings (`string`), never `Date` objects (JSON-safe)
- **IDs** are strings (UUIDs)
- **Enums** are string union types, not TypeScript `enum` (tree-shakable)
- **Status values** match backend exactly (don't invent new ones)

## Adding a Type

1. Add to `src/index.ts`
2. Re-export if needed from a submodule
3. Keep types **narrow** — prefer union strings over open `string`

Example:

```typescript
// Good — narrow
export type ScanStatus = "pending" | "running" | "completed" | "failed";

// Bad — too open
export type ScanStatus = string;
```

## Why Shared Types?

- Single source of truth between `@citetrack/web` (TypeScript) and `@citetrack/api` (Python)
- Prevents API contract drift — if Python response shape changes, TS will error
- Enables end-to-end type safety with `@citetrack/api-client`

## Keeping In Sync With Python

The Python backend (Pydantic models) is the source of truth for API contracts. When adding a new endpoint:

1. Define Pydantic model in `apps/api/ai_visibility/models/`
2. Export its TypeScript equivalent here
3. Add the endpoint to `@citetrack/api-client`

Future: auto-generate these types from Python's OpenAPI schema using `openapi-typescript`.
