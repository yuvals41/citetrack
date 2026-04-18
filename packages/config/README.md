# @citetrack/config

Shared constants and configuration for Citetrack AI apps.

## Usage

```tsx
import { APP_NAME, APP_URL, API_BASE_URL, AI_PROVIDERS } from "@citetrack/config";

console.log(APP_NAME);        // "Citetrack AI"
console.log(APP_URL);         // "https://citetrack.ai"
console.log(API_BASE_URL);    // env-aware, defaults to localhost:8000
console.log(AI_PROVIDERS);    // ["chatgpt", "claude", ...]
```

## Exports

| Export | Type | Value |
|---|---|---|
| `APP_NAME` | `"Citetrack AI"` | Product name (use in titles, OG tags) |
| `APP_URL` | `"https://citetrack.ai"` | Canonical production URL |
| `API_BASE_URL` | `string` | API base (env-aware, `process.env.API_BASE_URL` or localhost) |
| `AI_PROVIDERS` | `readonly string[]` | Provider IDs — source of truth |
| `AIProvider` | type | `(typeof AI_PROVIDERS)[number]` |

## Why a Shared Package?

Prevents magic strings scattered across codebases. One change here → propagates everywhere.

Example:

```typescript
// ❌ Bad — magic string, breaks if "gemini-pro" ever changes
if (provider === "gemini-pro") { ... }

// ✅ Good — type-checked, centralized
import type { AIProvider } from "@citetrack/config";
if (provider === "gemini") { ... }  // TS errors if invalid
```

## Environment Variables

`API_BASE_URL` checks `process.env.API_BASE_URL`. In browser builds, Vite replaces this at build time. To override in dev:

```bash
API_BASE_URL=https://staging-api.citetrack.ai bun dev
```

## Adding a Constant

Only add things that are **truly shared** — used by 2+ apps/packages.

1. Add to `src/index.ts`
2. Export from `packages/config/package.json` if introducing a submodule path
3. Document here
