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

| Category | Exports |
|---|---|
| Domain models | `Workspace`, `VisibilityScore`, `ScanRun`, `Citation`, `DiagnosticFinding`, `AIProvider` |
| Degraded responses | `DegradedInfo`, `DegradedResponse` |
| Snapshot | `OverviewSnapshot`, `TrendPoint`, `TrendSeries`, `TrendResponse`, `Finding`, `FindingsSummary`, `ActionItem`, `ActionQueue`, `ProviderBreakdownItem`, `MentionTypeItem`, `SourceAttributionItem`, `HistoricalRunItem`, `TopPageItem`, `CompetitorComparisonItem`, `SnapshotBreakdowns`, `OverviewSnapshotResult`, `TrendResult`, `FindingsResult`, `ActionsResult`, `BreakdownsResult` |
| Runs | `PerProviderScanResult`, `RunScanResult`, `RunRecord`, `RunsResult` |
| AI responses | `ResponseMentionType`, `AIResponseCitation`, `AIResponseItem`, `AIResponsesList` |
| Analyzers | `ContentAnalysisDimension`, `ExtractabilityInput`, `CrawlerSimInput`, `QueryFanoutInput`, `EntityAnalysisInput`, `ShoppingAnalysisInput`, `ExtractabilityResult`, `CrawlerBotAccessResult`, `CrawlerSimResult`, `QueryFanoutItem`, `QueryFanoutResult`, `PresenceResult`, `EntityResult`, `GoogleShoppingResult`, `AIShoppingResult`, `ChatGPTShoppingResult`, `ShoppingResult` |
| Pixel | `PixelStats` |
| Workspace | `WorkspaceApiResponse`, `WorkspaceSettings`, `WorkspaceSettingsUpdate`, `ScanScheduleValue` |
| Competitor | `CompetitorRecord`, `CompetitorsList`, `CompetitorCreateInput` |
| Brand | `BrandDetail`, `BrandUpsertInput` |
| Prompt | `PromptRecord`, `PromptsResult` |

## Conventions

- **Dates** are ISO strings (`string`), never `Date` objects (JSON-safe)
- **IDs** are strings (UUIDs)
- **Enums** are string union types, not TypeScript `enum` (tree-shakable)
- **Status values** match backend exactly (don't invent new ones)
- **API contracts live here** — `@citetrack/api-client` re-exports them for backward compatibility

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
