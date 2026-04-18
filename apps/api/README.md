# AI Visibility

**Track how AI assistants see your brand.** Monitor mentions, citations, and competitor positioning across ChatGPT, Gemini, Claude, Perplexity, Grok, and Google AI Overviews — then get actionable recommendations to improve.

---

## In Plain English

**The problem:** When someone asks ChatGPT *"who's the best remodeling contractor in DC?"* — is your brand mentioned? Do they cite your website? Or does a competitor get all the credit?

Most businesses have no idea. This tool tells you.

**How it works in 4 steps:**

1. **Ask AI like a real buyer would.** We fire prompts across ChatGPT, Claude, Gemini, Perplexity, Grok, and Google AI Overviews — questions like *"best home remodelers near me"*, *"who do experts recommend for kitchen renovations?"*, *"compare [your brand] vs [competitor]"*.

2. **Record every mention and citation.** For each response, we track: Did your brand appear? Was your website cited? How did competitors do? This becomes your **visibility score** (0-100%).

3. **Diagnose why you're invisible.** Three diagnostic engines run automatically:
   - **On-Page** — Is your schema markup missing? Are AI assistants blocked from reading your content?
   - **Backlinks** — Do authoritative sites link to you? Are you cited in AI-friendly sources?
   - **Entity** — Does AI understand who you are? Is your brand ambiguous or confused with something else?

4. **Give you a ranked action list.** Each finding maps to a concrete fix: *"Add FAQ schema to your homepage"*, *"Get listed on [specific directory]"*, *"Clarify your brand entity on Wikipedia/Wikidata"*. Highest impact items come first.

---

## What Makes This Different

Most AI visibility tools tell you your score. We tell you **why** and **what to fix**.

**vs Peec.ai** (€85-205/mo, $29M raised):
- Peec monitors 3 AI models on their starter plan. We scan 6 providers on every plan.
- Peec shows visibility, position, sentiment. We show the same plus source attribution, granular diagnostics (8 finding types), and a Claude-powered actions engine that generates specific fixes.
- Peec uses UI scraping (browser automation). We use direct APIs + DataForSEO for authenticated, reliable data.
- Peec charges per seat. We have no seat limits.

**vs Limy.ai** ($449/mo growth plan):
- Limy focuses on revenue attribution (JS pixel tracking). We focus on the diagnostic layer — why AI ignores your brand and how to fix it.
- Limy's competitor discovery is manual. Ours is automated (Exa company search + Claude adaptive thinking filter + domain validation).
- Limy doesn't offer location-aware scanning with native `user_location` support. We do, for OpenAI, Anthropic, and Perplexity.

**vs OtterlyAI** ($29-489/mo):
- OtterlyAI has AI Crawler Simulation and Content Checker. We have both plus source attribution, position tracking, sentiment analysis, query fan-out, and YouTube/Reddit visibility.
- OtterlyAI charges extra for Gemini and Google AI Mode. We include all 6 providers.
- OtterlyAI limits seats on lower plans. We don't.

**vs Semrush AIO** (enterprise pricing):
- Semrush has 213M+ prompts and log file analysis. We're open-source, self-hosted, and free.
- Semrush's query fan-out analysis is enterprise-only. Ours is available at any price point.

**Our moat:**
1. **6 providers in one scan** — ChatGPT, Claude, Gemini, Perplexity, Grok, Google AI Overviews. No competitor covers all 6 at any price tier.
2. **Diagnostic depth** — 8 finding types (provider blind spots, position issues, source gaps, competitor outranking, negative sentiment, missing citations, low visibility, missing source platforms). Most tools stop at visibility score.
3. **Claude-powered actions engine** — not generic tips but specific, data-driven recommendations generated from your actual scan results and persisted to DB.
4. **Intelligent competitor discovery** — extracts site content via Tavily, auto-generates business description with Claude, searches via Exa company search (with `category: "company"` + `summary`) and Tavily (with `include_answer: true`) in parallel, deduplicates results, validates domain reachability, and filters with Claude adaptive thinking. Works for SaaS, local businesses, and niche solo practitioners.
5. **Location-aware scanning** — 249 countries + Nominatim city autocomplete. Native `user_location` for OpenAI, Anthropic, Perplexity. Prompt injection for Gemini and Grok.
6. **Open-source, self-hosted, no seat limits** — competitors charge $85-449/mo per seat. We charge nothing.
7. **Source attribution** — shows which websites AI cites when discussing your brand. Identifies source gaps (G2, Trustpilot, Reddit cited by AI but you're not listed).
8. **Real competitor scores** — computed from existing scan responses (no extra API calls). Shows real visibility scores, not "—".
9. **Content Extractability Analyzer** — scores how well AI can extract content from your pages (summary block, section integrity, modular content, schema markup, static content). No competitor offers this at SMB price.
10. **AI Crawler Simulation** — checks if each AI bot (GPTBot, ClaudeBot, PerplexityBot) can access your pages. Answers "why am I not cited" at the root cause level.
11. **Query Fan-Out Analysis** — shows the sub-queries AI runs behind the scenes. First tool to offer this at non-enterprise price.
12. **YouTube/Reddit Visibility** — tracks brand mentions on the #1 and #2 social platforms for AI citations.
13. **Alert System** — webhook notifications (Slack/Discord) when visibility drops or competitors surge. No competitor does this well.

---

## Features

- **Onboarding wizard** — domain, industry, competitor discovery, location, provider selection, then scan. Auto-discovers competitors via Tavily extract (site content), Claude auto-description, parallel Exa company search + Tavily search, deduplication, domain validation, and Claude adaptive thinking filter. Works for any business type (SaaS, local contractors, coaches, retail) without needing industry dropdown for query quality. Location-aware: includes geography for local businesses, omits country for global SaaS.
- **Location-aware scanning** — 249-country dropdown + Nominatim (OpenStreetMap) city autocomplete. Location context is passed to OpenAI, Anthropic, and Perplexity as `user_location` for locally relevant results.
- **6 AI providers** — ChatGPT (gpt-5.4), Claude (claude-sonnet-4-6), Gemini (gemini-3-flash-preview), Perplexity (sonar-pro), Grok (grok-4-1-fast-reasoning), Google AI Overviews. Select any combination per scan. All analysis tasks use Claude sonnet-4-6.
- **Interactive dashboard** — 5 Recharts visualizations: metric cards (integer percentages), provider bar chart (distinct questions per latest scan), mention type pie chart, competitor comparison bar chart, visibility trend line chart.
- **AI Responses page** — browse every question asked alongside the full AI response. Expandable per-response view with mention detection (word-split approach), citation detection (real URLs only), and per-provider filtering.
- **Multiple workspaces** — workspace switcher dropdown in the sidebar, plus New Workspace button and per-workspace delete (trash icon).
- **Evidence pipeline** — every scan produces a structured chain from raw LLM response to recommendation.
- **Deterministic recommendations** — rules-based engine (`RULES_VERSION=v1`), no LLM in the loop.

**Phase 2 additions:**

- **Source attribution** — bar chart showing which websites AI providers cite when discussing your brand.
- **Position tracking** — where in the response your brand appears (1 = top, 5 = bottom). Tracked per observation and surfaced on the dashboard.
- **Sentiment analysis** — keyword heuristics on the dashboard for a quick read; Claude sonnet-4-6 detailed analysis on the AI Responses page for per-response breakdown.
- **Competitor scanning** — real visibility scores for competitors, computed from existing scan responses with no extra API calls.
- **Daily automated scans** — ARQ + Redis worker, cron at 06:00 UTC, 24-hour minimum interval between scans per workspace.
- **Actions engine** — Claude sonnet-4-6 generates 3-5 specific, ranked recommendations per scan. Results are persisted to the database so they're not regenerated on every page load.
- **Granular diagnostics** — 8 finding types: provider blind spots, position issues, source gaps, competitor outranking, sentiment drift, entity confusion, content gaps, and technical barriers.
- **Loading spinners** — progressive dashboard loading with per-section spinners; workspace switching is instant.
- **Performance** — Claude API responses cached in DB; recommendations generated once per scan, not on demand.

**Phase 3 additions:**

- **DataForSEO LLM Mentions API** — client for searching 190M+ pre-indexed AI prompts, aggregated metrics, cross-domain comparison, and top cited domains/pages. Enables historical visibility tracking without live LLM calls.
- **DataForSEO Reasoning** — `use_reasoning=true` on ChatGPT and Gemini adapters. Captures chain-of-thought showing WHY AI mentioned or ignored the brand.
- **Custom Prompts** — add/remove custom questions in the onboarding wizard alongside the 20 defaults.
- **CSV Export** — download dashboard data and AI responses as CSV files for reporting.
- **Content Extractability Analyzer** — new `/content-analysis` page. Analyzes a website for AI extractability: summary block, section integrity, modular content, schema markup, static content scores (0-100). Powered by Tavily extract + Claude sonnet-4-6 structured analysis.
- **AI Crawler Simulation** — checks if GPTBot, ClaudeBot, PerplexityBot, Google-Extended, and Googlebot can access your pages. Tests robots.txt rules and HTTP response per bot.
- **Query Fan-Out Analysis** — generates the 5-8 sub-queries an AI would run behind the scenes to answer a prompt. Claude sonnet-4-6 generates sub-queries, checks where your brand ranks for each using DataForSEO SERP API.
- **YouTube/Reddit Visibility** — tracks brand mentions on YouTube and Reddit via Google SERP (`site:youtube.com` and `site:reddit.com` queries through DataForSEO).
- **AI Keyword Data** — AI-specific search volume from DataForSEO (`ai_keyword_data/keywords_search_volume`). Shows how often keywords are queried inside AI tools.
- **Alert System** — detects visibility drops (>10%), citation drops, competitor surges, and first scan completion. Sends notifications via Slack/Discord webhook. Integrated into ARQ worker.
- **Brand Entity Optimization** — tracks how AI understands your brand as an entity (not just keyword match). Scores Google Knowledge Graph, Wikidata, and Wikipedia relevance. Implementation: `ai_visibility/analysis/brand_entity.py`.
- **AI Shopping Visibility** — tracks products in ChatGPT Shopping, Google AI Mode, and Amazon Rufus. Monitors shopping results across multiple channels. Implementation: `ai_visibility/analysis/shopping_visibility.py`.
- **SerpAPI Google AI Mode (multi-turn)** — multi-turn conversation support via `subsequent_request_token` for extended AI Mode conversations. Implementation: `ai_visibility/llm/adapters/google_ai_mode_serpapi.py`.
- **Revenue Attribution Pixel** — JS snippet customers install on their site to track AI-referred traffic. Connects: prompt → mention → visit → conversion → revenue. Implementation: `ai_visibility/pixel/` (JS snippet + FastAPI endpoints + event storage).
- **PDF Export** — generates PDF reports for dashboard metrics and AI responses via `fpdf2`. Implementation: `ai_visibility/export/pdf_export.py`.
- **Email Alerts** — sends HTML alert emails via SMTP alongside existing webhook notifications. Implementation: `ai_visibility/alerts/email_alert.py`.
- **JS Rendering Check** — heuristic detection of pages requiring JavaScript rendering (SPA root divs, noscript tags, minimal text with scripts). Added to crawler simulation.
- **LLM Mentions Top Pages** — DataForSEO `top_pages` endpoint for most-cited pages. Implementation: `ai_visibility/integrations/dataforseo_mentions.py`.
- **Editable Brand Name** — onboarding step 2 shows auto-detected brand name that users can edit. Prompts use the user-provided brand name instead of the domain slug.

---

## How It Works (Technical)

```
                        You enter a brand
                              |
                              v
                    +-------------------+
                    |   Onboarding UX   |
                    | domain, industry, |
                    | competitors,      |
                    | location,         |
                    | providers         |
                    +-------------------+
                              |
                              v
              +-------------------------------+
              |       Prompt Catalog          |
              | prompts x 4 categories        |
              | (discovery, comparison,       |
              |  reputation, deep-dive)       |
              +-------------------------------+
                              |
                              v
    +---------------------------------------------------+
    |              Run Orchestrator                      |
    |  thin coordinator -- no provider-specific logic    |
    +---------------------------------------------------+
       |       |       |       |       |       |
       v       v       v       v       v       v
  +------+ +------+ +------+ +------+ +------+ +------+
  |ChatGPT| |Claude| |Gemini| |Perplx| | Grok | |Google|
  |gpt-5.4| |sonnet| |3-flas| |sonar-| |grok-4| |AI Ov.|
  |       | |-4-6  | |prev. | |pro   | |1-fast| |      |
  +------+ +------+ +------+ +------+ +------+ +------+
       |       |       |       |       |       |
       +-------+-------+-------+-------+-------+
                              |
                              v
              +-------------------------------+
              |     Evidence Pipeline         |
              +-------------------------------+
                              |
                              v
              +-------------------------------+
              |   Reflex Dashboard (port 3000)|
              +-------------------------------+
```

## Evidence Pipeline

Every scan produces a structured evidence chain from raw LLM responses down to actionable recommendations:

```
scan_job                    "Scan Maison Remodeling on OpenAI"
    |
    v
scan_execution              provider=openai, model=gpt-5.4
    |
    v
prompt_execution            "Best remodeling companies in DC area"
    |
    +---> observation       mentioned=true, sentiment=positive, position=3
    |
    +---> citation          url=maisonremodeling.com, context="top choice"
    |
    v
diagnostic_finding          reason_code=content_answer_gap
    |
    v
recommendation_item         "Add FAQ schema to answer 'cost of kitchen remodel'"
```

Each row has an `idempotency_key` (SHA-256) for safe retries via `ON CONFLICT DO NOTHING`.

---

## Architecture

```
ai-visibility/
├── ai_visibility/
│   ├── cli.py                    # 12 CLI commands
│   ├── config.py                 # Pydantic settings
│   │
│   ├── contracts/                # Pydantic models for scan I/O
│   │   └── scan_contracts.py     # ScanRequest, ScanResult, PromptResult
│   │
│   ├── prompts/                  # Prompt engineering
│   │   ├── library.py            # PromptLibrary -- load/filter prompts
│   │   ├── default_set.py        # Built-in prompts (shown in onboarding preview)
│   │   └── renderer.py           # Template rendering with brand context
│   │
│   ├── llm/                      # Provider adapters
│   │   ├── adapters/
│   │   │   ├── base.py           # ScanAdapter ABC
│   │   │   ├── chatgpt.py        # OpenAI adapter (DataForSEO LLM Responses API)
│   │   │   ├── gemini.py         # Gemini adapter (DataForSEO LLM Responses API)
│   │   │   ├── claude.py         # Anthropic adapter
│   │   │   ├── perplexity.py     # Perplexity direct API
│   │   │   ├── grok.py           # xAI Grok adapter
│   │   │   ├── google_ai_overview.py  # Google AI Overviews (DataForSEO SERP API)
│   │   │   └── stub.py           # Test double
│   │   ├── gateway.py            # ProviderGateway with LocationContext
│   │   └── config.py             # Provider credentials
│   │
│   ├── runs/                     # Scan execution
│   │   ├── orchestrator.py       # RunOrchestrator (thin coordinator)
│   │   └── scan_strategy.py      # Provider selection logic
│   │
│   ├── extraction/               # Post-scan processing
│   │   └── pipeline.py           # ExtractionPipeline: parse -> persist
│   │
│   ├── diagnosis/                # What's wrong?
│   │   ├── onpage.py             # OnPageDiagnoser (schema, content gaps)
│   │   ├── backlinks.py          # BacklinkDiagnoser (authority gaps)
│   │   └── entity.py             # EntityDiagnoser (Knowledge Graph gaps)
│   │
│   ├── recommendations/          # What to do about it
│   │   ├── findings.py           # FindingsPipeline (dedupe by reason_code)
│   │   └── engine.py             # RECOMMENDATION_RULES + RULES_VERSION=v1
│   │
│   ├── metrics/                  # Scoring
│   │   ├── engine.py             # MetricsEngine (visibility, citations)
│   │   └── snapshot.py           # SnapshotRepository (precomputed reads)
│   │
│   ├── analysis/                 # Analysis engines
│   │   ├── sentiment.py          # Keyword heuristics + Claude sonnet-4-6 detailed sentiment
│   │   ├── actions.py            # Claude sonnet-4-6 actions engine (3-5 recommendations)
│   │   ├── content_extractability.py  # Page AI-readability scoring (5 dimensions via Claude sonnet-4-6)
│   │   ├── crawler_simulation.py # Test GPTBot/ClaudeBot/PerplexityBot access to URLs
│   │   ├── query_fanout.py       # Claude sonnet-4-6 generates sub-queries + check SERP rankings per query
│   │   └── social_visibility.py  # YouTube/Reddit brand mentions via DataForSEO SERP
│   │
│   ├── integrations/             # External API clients
│   │   ├── dataforseo_mentions.py # LLM Mentions API (190M+ prompts, historical tracking)
│   │   └── dataforseo_keywords.py # AI Keyword Data (AI-specific search volume)
│   │
│   ├── alerts/                   # Notification system
│   │   ├── engine.py             # Detect visibility drops, citation drops, competitor surges
│   │   └── webhook.py            # Send alerts to Slack/Discord via webhook
│   │
│   ├── worker.py                 # ARQ worker (WorkerSettings, daily cron at 06:00 UTC)
│   │
│   ├── scheduler/                # Async job execution
│   │   └── executor.py           # AsyncScanExecutor with semaphores
│   │
│   ├── storage/                  # Database
│   │   ├── prisma_connection.py  # Prisma async client
│   │   ├── schema.sql            # DDL with idempotency indexes
│   │   ├── maintenance.sql       # pg_partman, pg_cron, BRIN, matviews
│   │   ├── maintenance.py        # Maintenance schedule helpers
│   │   ├── types.py              # TypedDict definitions
│   │   └── repositories/         # Data access layer
│   │
│   ├── ui/                       # Reflex web dashboard
│   │   ├── pages/
│   │   │   ├── dashboard.py      # KPI cards, charts, sources, sentiment, position, findings
│   │   │   ├── citations.py      # AI Responses — full response viewer with mention/citation detail
│   │   │   ├── recommendations.py # Action Plan — persisted Claude recommendations from DB
│   │   │   ├── runs.py           # Scan History — table with status badges and timestamps
│   │   │   ├── prompts.py        # Questions — rendered prompts with brand name
│   │   │   ├── content_analysis.py # Content Extractability + Crawler Sim + Query Fan-Out
│   │   │   ├── prompt_detail.py  # Single response detail view
│   │   │   └── onboarding.py     # Multi-step wizard (domain, industry, competitors, location, providers, prompts)
│   │   ├── state.py              # DashboardState
│   │   ├── onboarding_state.py   # OnboardingState (competitor discovery, location)
│   │   ├── layout.py             # Sidebar + topbar + workspace switcher
│   │   └── app.py                # Route registration
│   │
│   ├── api/                      # FastAPI endpoints
│   ├── models/                   # Domain models
│   └── degraded/                 # Graceful degradation states
│
├── tests/                        # 248+ passing tests
│   ├── test_phase1_fixes.py      # 24 tests — brand name, citation detection, location stripping
│   ├── test_phase2.py            # 64 tests — source attribution, position, sentiment, competitor scanning
│   ├── test_phase3.py            # 23 tests — content analyzer, crawler sim, fan-out, alerts, webhook
│   ├── test_comprehensive.py     # 36 tests — mention detection, domain cleaning, industry resolution
│   ├── test_google_ai_overview.py # 18 tests — DataForSEO SERP parser, location codes
│   ├── test_data_accuracy.py     # 8 tests — DB data verification, recommendation persistence
│   ├── e2e/                      # Browser E2E (31 Playwright tests) + pipeline + location
│   ├── onboarding/               # Onboarding flow tests
│   ├── runs/                     # Orchestrator and scan tests
│   ├── contracts/                # Doc/schema contract tests
│   └── storage/                  # Repository tests
│
├── docs/
│   ├── PHASE_2_PLAN.md           # Phase 2 features (completed)
│   ├── PHASE_3_PLAN.md           # Phase 3 features (Tier 1+2 completed, Tier 3 planned)
│   ├── research-report.md        # Full system documentation
│   └── runbooks.md               # Operations guide
│
└── docker-compose.yml            # app, postgres, redis services
```

---

## Provider Stack

| Provider | Model | Access Method |
|----------|-------|---------------|
| **OpenAI** | gpt-5.4 | DataForSEO LLM Responses API |
| **Anthropic** | claude-sonnet-4-6 | solaraai-llm + `user_location` support |
| **Gemini** | gemini-3-flash-preview | DataForSEO LLM Responses API |
| **Perplexity** | sonar-pro | Direct API + `web_search_options.user_location` |
| **Grok** | grok-4-1-fast-reasoning | solaraai-llm |
| **Google AI Overviews** | (SERP) | DataForSEO SERP API (`/serp/google/ai_mode`) |

All adapters implement the same `ScanAdapter` ABC. The orchestrator doesn't know or care which method is used.

Location context (`city`, `region`, `country`) is passed as `user_location` to Anthropic and Perplexity when set. OpenAI and Google AI Overviews use `web_search_country_iso_code` for country-level targeting.

---

## Key Architecture Concepts

**State management**: Reflex uses reactive state classes. `DashboardState` (ui/state.py) is the main state — holds all dashboard data, loaded via `refresh()` which is an async generator that yields for progressive UI updates. `OnboardingState` (ui/onboarding_state.py) manages the multi-step wizard. `CitationState` (ui/pages/citations.py) manages the AI Responses page. `RecommendationState` (ui/pages/recommendations.py) reads persisted recommendations from DB. `ContentAnalysisState` (ui/pages/content_analysis.py) manages on-demand analysis.

**Data flow**: Onboarding creates workspace in DB via `cli.create_workspace()` -> `RunOrchestrator.scan()` runs prompts across selected providers -> prompt executions stored in `ai_vis_prompt_executions` -> `DashboardState.refresh()` queries prompt executions and computes all metrics (visibility, citations, sentiment, position, sources, competitors, findings) on-the-fly -> recommendations generated by Claude and persisted to `ai_vis_recommendation_items`.

**Mention detection**: Uses word-split approach in Python (not SQL). The brand slug is split at every possible position to generate candidate terms. Example: "maisonremodeling" generates "maison remodeling", "ma isonremodeling", etc. Checks each term against lowercased response text. This catches "Maison Remodeling Group" even when the slug has no spaces.

**Citation detection**: Only counts real URLs (`https://...`) containing the brand domain. Bare domain mentions in text ("maisonremodeling.com" without a link) are NOT counted as citations.

**Recommendations**: Generated once per scan by Claude sonnet-4-6, persisted to `ai_vis_recommendation_items` table. Dashboard reads from DB cache — never re-generates on page load. Fallback heuristic engine used when Claude is unavailable.

**On-demand analysis** (costs API credits, not called automatically):
- Content Extractability: Tavily extract + Claude sonnet-4-6 structured analysis
- Crawler Simulation: HTTP HEAD requests with each bot's User-Agent
- Query Fan-Out: Claude sonnet-4-6 generates sub-queries + DataForSEO SERP checks rankings
- Social Visibility: DataForSEO SERP with `site:youtube.com` and `site:reddit.com`
- LLM Mentions: DataForSEO pre-indexed database (190M+ prompts)
- AI Keyword Data: DataForSEO AI-specific search volume

**Scheduled scans**: ARQ + Redis worker runs daily at 06:00 UTC. After each scan, alert engine checks for visibility drops, citation drops, and competitor surges. Sends webhooks if `ALERT_WEBHOOK_URL` is configured.

---

## Dashboard

The dashboard reads from precomputed `metric_snapshots` — it never joins raw scan tables at request time.

**Metric cards** show integer percentages (no floating point) for: visibility score, citation coverage, mention rate, and competitor gap.

**Provider bar chart** counts distinct questions answered per provider in the latest scan, not raw mention counts.

**Citation coverage** is computed from real URL detection only. Bare domain text in a response body does not count as a citation.

**Charts and sections:**
1. Metric cards (KPI row)
2. Provider bar chart
3. Mention type pie chart
4. Competitor comparison bar chart (real scores, no extra API calls)
5. Visibility trend line chart
6. Source attribution bar chart (which websites AI cites for your brand)
7. Sentiment summary (keyword heuristics, color-coded)
8. Position distribution (where in responses your brand appears)
9. Granular findings (8 finding types with severity and fix guidance)
10. Actions panel (3-5 Claude-generated recommendations, persisted per scan)

---

## AI Responses Page

Browse every prompt asked during a scan alongside the full AI response text.

- Responses are expandable per-provider
- Mention detection uses a word-split approach (whole-word matching, not substring)
- Citation detection looks for real URLs only — bare domain text in prose does not count
- Location context is stripped from the displayed prompt text so the question reads naturally
- All 6 providers appear in one view with per-provider filtering
- Claude sonnet-4-6 detailed sentiment analysis shown per response (positive / neutral / negative with reasoning)

---

## Onboarding

The wizard collects everything needed before the first scan:

1. **Domain input** — Enter key submits; brand name is inferred from the domain via `_humanize_brand` (e.g. `maison-remodeling.com` becomes "Maison Remodeling")
2. **Industry selection** — 20 preset options plus "Other" with a free-text custom input
3. **Competitor discovery** — Tavily extract fetches and cleans the business's website content, Claude sonnet-4-6 generates a 1-sentence business description (e.g. "AI-powered marketing automation platform" or "home remodeling contractor serving Los Angeles, California"), Exa company search (with `category: "company"` + `summary`) and Tavily search (with `include_answer: true`) run in parallel using the auto-generated description as the query, results are merged and deduplicated by domain, domain validation checks reachability via HEAD/GET requests, and Claude sonnet-4-6 with adaptive thinking (120s timeout) evaluates which candidates are true direct competitors
4. **Location selection** — 249-country dropdown plus Nominatim city autocomplete (no API key required)
5. **Provider selection** — 6 checkboxes, all selected by default
6. **Prompts preview** — shows the actual prompts from `default_set.py` that will be sent, rendered with the brand name

---

## Workspace Management

- **Workspace switcher** — dropdown in the sidebar to switch between tracked brands
- **New Workspace** — button to start the onboarding wizard for a new brand
- **Delete workspace** — trash icon per workspace; removes all associated scan data

---

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **UI framework** | Reflex | Python-native reactive web framework, no separate JS codebase |
| **Database** | PostgreSQL via Prisma | Shared schema, async client, production-grade |
| **Orchestrator pattern** | Thin coordinator | No provider-specific branching -- adapters handle everything |
| **Idempotency** | SHA-256 keys + `ON CONFLICT DO NOTHING` | Safe retries without duplicates |
| **Recommendations** | Deterministic rules (`RULES_VERSION=v1`) | Reproducible, auditable, no LLM in the loop |
| **Findings dedup** | By `reason_code` | Same issue from multiple prompts -> one finding |
| **Snapshot reads** | Precomputed `metric_snapshots` table | Dashboard never joins raw scan tables |
| **Trend comparison** | Must match `formula_version + prompt_version + model` | Prevents apples-to-oranges comparisons |
| **Status values** | `completed` / `completed_with_partial_failures` / `failed` | Partial failures don't retry |
| **Competitor discovery** | Tavily extract (site content) -> Claude auto-description -> parallel Exa + Tavily search -> dedup -> domain validation -> Claude adaptive thinking filter | No industry dropdown needed; works for any business type; location-aware; comprehensive logging |
| **City autocomplete** | Nominatim (OpenStreetMap) | Free, no API key required |
| **Mention detection** | Word-split (whole-word matching) | Avoids false positives from substring matches |
| **Citation detection** | Real URL detection only | Prevents inflated citation coverage from bare domain text |
| **Sentiment analysis** | Keyword heuristics (dashboard) + Claude sonnet-4-6 (per-response) | Fast overview without API cost; deep analysis on demand |
| **Actions engine** | Claude sonnet-4-6, persisted per scan | Generated once, not on every page load |
| **Competitor scores** | Computed from existing responses | No extra API calls; uses the same scan data |
| **Scheduled scans** | ARQ + Redis, cron at 06:00 UTC | Reliable background jobs without a separate process manager |

---

## Canonical Reason Codes

| Code | Diagnoser | Meaning |
|------|-----------|---------|
| `schema_missing` | OnPage | No structured data / JSON-LD |
| `content_answer_gap` | OnPage | Content doesn't answer common queries |
| `technical_barrier` | OnPage | Crawlability or rendering issues |
| `backlink_gap` | Backlink | Weak domain authority vs competitors |
| `grounded_search_authority_weak` | Backlink | Low citation authority for grounded search |
| `competitor_gap` | Entity | Competitors mentioned more often |
| `entity_clarity_weak` | Entity | Brand entity not clear to LLMs |
| `ambiguous_brand` | Entity | Brand name conflicts with common words |
| `kg_presence_missing` | Entity | No Knowledge Graph entry |
| `provider_blind_spot` | Analysis | Brand absent from one or more providers entirely |
| `position_weak` | Analysis | Brand consistently appears late in responses |
| `source_gap` | Analysis | No authoritative sources citing the brand |
| `competitor_outranking` | Analysis | Competitor appears earlier or more often |
| `sentiment_drift` | Analysis | Sentiment trending negative across recent scans |

---

## Quick Start

### 1. Install

```bash
git clone <repo>
cd ai-visibility
uv sync
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your API keys (see Environment Variables below)
```

### 3. Start PostgreSQL

```bash
docker compose up -d postgres
```

### 4. Push Prisma schema

```bash
cd ../stanley/repos/prisma
npx prisma db push
```

### 5. Launch the web dashboard

```bash
uv run reflex run
```

On first run, Reflex installs frontend dependencies automatically. This takes about a minute.

### 6. Open the app

```
http://localhost:3000
```

### 7. Walk through onboarding

1. Enter your domain (e.g. `yourbrand.com`) and press Enter
2. Select your industry (20 options, or "Other" for a custom label)
3. Review auto-discovered competitors (Tavily extracts site content, Claude auto-describes the business, Exa + Tavily search in parallel, results deduplicated and validated, Claude filters for true competitors)
4. Confirm or adjust your location (249-country dropdown + Nominatim city autocomplete)
5. Select which AI providers to scan (all 6 selected by default)
6. Preview the prompts that will be sent, then run the scan

---

## Environment Variables

All required keys must be set in `.env`:

| Variable | Required | Description |
|----------|----------|-------------|
| `EXA_API_KEY` | Yes | Exa API key (primary for competitor discovery) |
| `OPENAI_API_KEY` | Yes | OpenAI API key (used for scans and analysis) |
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key |
| `GEMINI_API_KEY` | Yes | Google Gemini API key (also accepted as `GOOGLE_API_KEY`) |
| `XAI_API_KEY` | Yes | xAI Grok API key |
| `PERPLEXITY_API_KEY` | Yes | Perplexity API key |
| `TAVILY_API_KEY` | Yes | Tavily API key (content extraction and search fallback for competitor discovery) |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `PROVIDERS` | Yes | Comma-separated list of active providers |
| `LOG_LEVEL` | No | `DEBUG`, `INFO`, `WARNING`, `ERROR` (default: `INFO`) |

You only need keys for the providers you intend to use. Competitor discovery requires `EXA_API_KEY` and `TAVILY_API_KEY` (Tavily extracts site content and provides search results with `include_answer: true`). All analysis tasks use Claude sonnet-4-6. OpenAI, Gemini, and Google AI Overviews route through DataForSEO (credentials are bundled; no separate DataForSEO key is needed in `.env`).

---

## CLI Commands

All commands use `uv run python -m ai_visibility.cli <command>`.

| Command | Description |
|---------|-------------|
| `doctor` | Health check -- DB, providers, config |
| `seed-demo` | Load sample workspaces and fixture data |
| `create-workspace` | Register a brand with competitors |
| `run-scan` | Execute prompts against an LLM provider |
| `list-runs` | Show scan history for a workspace |
| `list-workspaces` | Show all registered workspaces |
| `list-prompts` | Show prompt catalog |
| `summarize-latest` | Compute visibility metrics from latest scan |
| `recommend-latest` | Generate recommendations from latest scan |
| `run-scheduler` | Execute scheduled scans (supports `--once --dry-run`) |
| `print-schema` | Display JSON schema for a domain model |
| `parse-fixture` | Parse a raw LLM response fixture |

**Examples:**

```bash
# Health check
uv run python -m ai_visibility.cli doctor --format json

# Create a workspace
uv run python -m ai_visibility.cli create-workspace \
  --brand-name "Maison Remodeling" \
  --domain "maisonremodeling.com" \
  --competitor "Case Design" \
  --competitor "BOWA" \
  --city "Washington" \
  --region "DC" \
  --country "US"

# Run a scan
uv run python -m ai_visibility.cli run-scan \
  --workspace maison-remodeling \
  --provider openai \
  --format json

# Get results
uv run python -m ai_visibility.cli summarize-latest --workspace maison-remodeling
uv run python -m ai_visibility.cli recommend-latest --workspace maison-remodeling
```

## Scheduled Scans

Automatic daily scans run via ARQ (async job queue) backed by Redis. The worker picks up a cron task at 06:00 UTC and scans every workspace that hasn't been scanned in the last 24 hours.

```bash
# Start Redis
docker compose up -d redis

# Start the ARQ worker (runs continuously, cron at 06:00 UTC)
arq ai_visibility.worker.WorkerSettings

# Or trigger a one-off schedule check without the persistent worker
python -m ai_visibility.cli run-scheduler --once
```

The worker class is `ai_visibility.worker.WorkerSettings`. It requires `REDIS_URL` in `.env` (defaults to `redis://localhost:6379`).

---

## Running Tests

200+ tests pass across the suite. The test files are split by speed and dependency:

```bash
# Non-browser tests
uv run pytest tests/test_comprehensive.py tests/test_phase1_fixes.py tests/test_google_ai_overview.py tests/test_data_accuracy.py tests/e2e/test_location.py tests/e2e/test_pipeline_e2e.py -m "not slow"

# Phase 2 analysis tests
uv run pytest tests/analysis/ -m "not slow"

# Browser E2E tests (requires running app at localhost:3000)
uv run pytest tests/e2e/test_ui_browser.py --base-url http://localhost:3000

# All slow integration tests (real API calls)
uv run pytest -m "slow"

# Core unit tests
uv run pytest tests/onboarding/ tests/runs/ tests/test_cli_recommendations.py tests/test_deep_cli.py
```

Note: `tests/runs/test_run_scan.py` has 10 pre-existing failures due to an old constructor pattern that predates the current Prisma mock approach. They are not regressions.

---

## Production Database

PostgreSQL 18 with:

- **pg_partman** — automatic monthly partitioning of `prompt_executions` and `observations`
- **pg_cron** — scheduled materialized view refreshes (no DBA intervention)
- **BRIN indexes** — fast range scans on time-series data
- **Materialized views** — `mv_workspace_overview` for dashboard reads

See `ai_visibility/storage/maintenance.sql` for the full DDL.

---

## Docker

The `docker-compose.yml` defines three services:

| Service | Description |
|---------|-------------|
| `postgres` | PostgreSQL 18 database |
| `redis` | Redis 7 (session/cache) |
| `app` | Production app container |
| `app-dev` | Dev container with live-reload (profile: `dev`) |

```bash
# Start infrastructure only (for local dev)
docker compose up -d postgres redis

# Start full stack
docker compose up -d

# Dev mode with live reload
docker compose --profile dev up -d app-dev
```

---

## Known Limitations

- **Competitor discovery** is non-deterministic for niche or solo businesses. When Tavily returns few results, the LLM extraction step may produce fewer than 3 competitors or none at all.
- **Reflex hot-reload crashes the granian worker.** Saving a file during development kills the worker process; a full restart (`uv run reflex run`) is required. This is a granian reload signal issue, not a bug in the app logic.
- **10 pre-existing test failures** in `tests/runs/test_run_scan.py` use an old direct-DB constructor pattern. They are not regressions and are tracked for cleanup in Phase 2.

---

## Phase 2 Scope

Phase 2 is complete. The following remain out of scope for now:

- Authentication / authorization / RBAC
- Billing / subscription management
- Team / organization management
- Multi-tenant isolation (beyond workspace slugs)
- Custom prompts per workspace
- PDF / CSV export

See `docs/PHASE_3_PLAN.md` for what's planned in Phase 3.

---

## License

Proprietary -- Solara AI
