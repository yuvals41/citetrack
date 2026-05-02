# Citetrack Domain Glossary

Single source of truth for terminology used across code, docs, and AI sessions.
When a term gets ambiguous in code review or design discussion, the definition here is canonical.

## Workspace

A multi-tenant scoping unit that groups a brand, its competitors, and all scan history under one slug. Every database record carries a `workspace_id` as its top-level isolation key. Defined in `apps/api/ai_visibility/models/workspace.py` and `packages/types/src/index.ts`.

## Brand

The monitored entity within a workspace: a name, a primary domain, and an optional list of aliases. The brand is what the system checks for mentions and citations in AI responses. Defined in `apps/api/ai_visibility/models/brand.py` and `packages/types/src/index.ts` (`BrandDetail`).

## Brand Alias

An alternative name or spelling for a brand that the mention-detection pipeline also matches against. Stored as a list on `BrandDetail.aliases`. Useful when a brand is commonly referred to by a shortened name or a former name.

## Competitor

A rival entity tracked within the same workspace. Competitors are discovered automatically during onboarding (via Tavily + Exa + Claude) and stored with a name and domain. The system computes real visibility scores for competitors from existing scan responses without extra API calls. Defined in `apps/api/ai_visibility/models/brand.py` (`Competitor`).

## Scan Run

A single end-to-end execution of prompts across one or more AI providers for a workspace. A scan run has a lifecycle status (`pending`, `running`, `completed`, `completed_with_partial_failures`, `failed`) and produces prompt executions, observations, citations, and a metric snapshot. Defined in `packages/types/src/index.ts` (`ScanRun`) and `apps/api/ai_visibility/models/run.py`.

## Prompt

A question template sent to AI providers during a scan. Templates contain `{brand}` and `{competitor}` placeholders that the renderer fills in before execution. Prompts belong to a workspace and are versioned. Defined in `apps/api/ai_visibility/models/prompt.py`.

## Prompt Execution

The record of a single rendered prompt being sent to a single provider and the raw response received. Each prompt execution links to a scan execution and carries an idempotency key (SHA-256) so retries are safe. The raw response may include a reasoning blob appended after a separator. Stored in `ai_vis_prompt_executions` in the database.

## Provider

One of the six AI engines the system queries: ChatGPT (OpenAI), Claude (Anthropic), Gemini (Google), Perplexity, Grok (xAI), and Google AI Overviews. Each provider has a canonical string ID (`chatgpt`, `claude`, `gemini`, `perplexity`, `grok`, `google_ai_overview`) — the canonical list lives in `packages/config/src/index.ts` (`AI_PROVIDERS`). The set of active providers is configured per scan.

## Provider Adapter

A concrete implementation of the `ScanAdapter` ABC that handles the mechanics of calling one specific provider. Each adapter returns an `AdapterResult` with `raw_response`, `citations`, `provider`, `model_name`, `model_version`, and `strategy_version`. Adapters live in `apps/api/ai_visibility/providers/adapters/`. The orchestrator never contains provider-specific branching.

## Provider Gateway

The `ProviderGateway` class that wraps `solaraai-llm` and direct SDK calls, resolves model names, injects location context, and handles fallback chains. It sits between the orchestrator and the individual adapters for providers that go through the shared LLM library. Defined in `apps/api/ai_visibility/providers/gateway.py`.

## Citation

A real URL (`https://...`) that an AI provider includes in its response when discussing a brand. Only actual hyperlinks count; bare domain text in prose does not. Citations are extracted from adapter results and stored in `ai_vis_prompt_execution_citations`. Defined in `packages/types/src/index.ts` (`Citation`) and `packages/types/src/index.ts` (`AIResponseCitation`).

## Mention

A detected occurrence of a brand name in an AI response. Mentions are classified by type: `explicit` (brand named directly), `implicit` (described without naming), `comparative` (named alongside a competitor), or `absent` (brand not found). Detection uses a word-split approach on the brand slug to catch multi-word variants. Defined in `apps/api/ai_visibility/models/mention.py`.

## Mention Type

The classification of how a brand appears in an AI response. Values: `explicit`, `implicit`, `comparative`, `absent`. Defined as `MentionType` enum in `apps/api/ai_visibility/models/mention.py` and as `ResponseMentionType` in `packages/types/src/index.ts`.

## Visibility Score

A 0-100 float representing how often a brand is mentioned across all prompts in a scan, weighted by provider. Computed by `MetricsEngine` and stored in a `MetricSnapshot`. Trend comparisons are only valid between snapshots sharing the same `formula_version`, `prompt_version`, and model. Defined in `packages/types/src/index.ts` (`VisibilityScore`) and `apps/api/ai_visibility/models/metric.py`.

## Run Orchestrator

The `RunOrchestrator` class that coordinates a full scan: prepares context, executes prompts in parallel (semaphore of 3), builds the evidence chain, computes metrics, and persists everything to the database. It is a thin coordinator with no provider-specific logic. Defined in `apps/api/ai_visibility/runs/orchestrator.py`.

## Scan Executor

The stateless scan-execution engine in `apps/api/ai_visibility/scan_executor.py`. It accepts a `ScanInput`, resolves provider adapters, runs prompts with bounded concurrency, extracts mentions and citations, and returns a `ScanOutput` — without touching Prisma or repositories. The `AsyncScanExecutor` in `apps/api/ai_visibility/scheduler/executor.py` is a separate scheduler wrapper that enforces the 24-hour minimum interval and triggers scans from the daily cron at 06:00 UTC; do not confuse the two.

## Finding

A diagnosed issue detected from scan results, identified by a `reason_code` (e.g. `provider_blind_spot`, `source_gap`, `competitor_outranking`). Findings are deduplicated by `reason_code` so the same issue from multiple prompts produces one finding. Defined in `packages/types/src/index.ts` (`Finding`).

## Action Plan

The set of 3-5 ranked, specific recommendations generated by Claude from a scan's findings and persisted to the database. The dashboard reads from this persisted cache; Claude is never called again on page load. Defined in `packages/types/src/index.ts` (`ActionItem`, `ActionQueue`).

## Recommendation

A single actionable item in the action plan, with a `recommendation_code`, priority (`high`, `medium`, `low`), title, and description. Backed by the deterministic rules engine (`RULES_VERSION=v1`) as a fallback when Claude is unavailable. Defined in `apps/api/ai_visibility/models/recommendation.py`.

## Source Attribution

The breakdown of which external domains AI providers cite when discussing a brand. Surfaces as a bar chart on the dashboard. Identifies source gaps: domains that AI cites frequently (e.g. G2, Trustpilot, Reddit) where the brand has no presence. Defined in `packages/types/src/index.ts` (`SourceAttributionItem`).

## Pixel Snippet

A JavaScript snippet customers install on their site to track AI-referred traffic. Connects the chain from prompt to mention to site visit to conversion to revenue. The backend receives events at FastAPI endpoints under `ai_visibility/pixel/`. Stats are exposed via `PixelStats` in `packages/types/src/index.ts`.
