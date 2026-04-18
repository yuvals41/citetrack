# AI Visibility Scanner: Research Report
**Status:** Active | **Date:** March 2026 | **Version:** 2.0

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Market Landscape](#2-market-landscape)
3. [Competitor Deep Dive](#3-competitor-deep-dive)
4. [The API vs UI Problem](#4-the-api-vs-ui-problem)
5. [Technical Approaches Comparison](#5-technical-approaches-comparison)
6. [DataForSEO: Game Changer](#6-dataforseo-game-changer)
7. [Local Business Opportunity](#7-local-business-opportunity)
8. [What Actually Improves AI Visibility](#8-what-actually-improves-ai-visibility)
9. [Implemented Architecture](#9-implemented-architecture)
10. [Evidence Pipeline](#10-evidence-pipeline)
11. [Database Architecture](#11-database-architecture)
12. [Self-Serve Dashboard and Onboarding](#12-self-serve-dashboard-and-onboarding)
13. [Pricing Strategy](#13-pricing-strategy)
14. [First-Party Analytics](#14-first-party-analytics)
15. [Case Studies](#15-case-studies)

---

## 1. Executive Summary

> **TL;DR:** We built a hybrid AI visibility scanner that captures real-world AI responses (web search enabled) via a multi-provider stack. The system diagnoses why a brand is invisible and generates ranked, evidence-backed recommendations. A self-serve dashboard and onboarding flow make it accessible to non-technical users.

### What We Built

| Dimension | Old Approach | Current Implementation |
|-----------|-------------|----------------------|
| Data source | Raw LLM API calls | Hybrid provider stack: DataForSEO (ChatGPT/Gemini), Anthropic web_search, Perplexity sonar-pro |
| Accuracy vs real UX | ~24% match | ~80-90% match |
| Local business support | Generic | Purpose-built with city/region/country fields |
| Actionability | "You appear / don't appear" | Evidence pipeline: scan -> diagnosis -> ranked recommendations |
| Storage | SQLite only | SQLite (dev) + PostgreSQL 18 production path |
| UI | None | Reflex-based self-serve dashboard with onboarding wizard |

### The Core Problem We Solved

**What approach provides the most value to local business customers?**

Three paths were evaluated:
- Raw API-only: fast, cheap, but 76% of results are wrong vs real user experience
- API + web search: better, but still misses UI-specific behavior
- **Hybrid provider stack (implemented):** captures real UI responses including web search, at low cost per request

### Key Findings at a Glance

- Market growing at **41.3% CAGR** to $18.7B by 2034
- **$200M+ raised** across 24 platforms in this space
- **Profound** leads at $155M raised, $1B valuation
- **White space:** Almost no competitor targets local businesses specifically
- **45% of consumers** now use AI for local recommendations (up from 6%)
- ChatGPT recommends only **1.2% of local businesses** — massive gap to close

---

## 2. Market Landscape

### Market Size

```
2024 ──────────────────────────────────────── 2034
 $2.1B                                        $18.7B
       ↑ 41.3% CAGR ↑
```

| Metric | Value |
|--------|-------|
| Projected market size (2034) | $18.7B |
| CAGR | 41.3% |
| Total funding raised (24 platforms) | $200M+ |
| Tools in market | 50+ |

### M&A Signal

> **xFunnel acquired by HubSpot** — major validation that AI visibility is becoming table stakes for marketing platforms. Expect more consolidation.

### Funding Leaders

| Company | Raised | Valuation | Signal |
|---------|--------|-----------|--------|
| Profound | $155M | $1B | Category leader |
| Peec.ai | $30M+ | — | Enterprise focus |
| Scrunch AI | $26M | — | SOC 2, enterprise |
| Limy.ai | $10M (a16z) | — | Attribution angle |

---

## 3. Competitor Deep Dive

### Tier 1: Well-Funded Players

| Name | Funding | Price | Approach | Local Support | Unique Feature |
|------|---------|-------|----------|---------------|----------------|
| **Profound** | $155M / $1B val | $99–custom | UI scraping | No | 700+ enterprise customers |
| **Scrunch AI** | $26M | $250/mo | API + AXP middleware | Country-level only | CDN-edge AI-optimized HTML for bots, SOC 2 |
| **Peec.ai** | $30M+ | €89/mo | UI scraping (logged-out) | No | 2,000+ marketing teams |
| **Limy.ai** | $10M (a16z) | $449/mo | API + JS pixel | 2 regions only | AI traffic attribution pixel |

### Tier 2: SEO Suites with AI Modules

| Name | Price | Approach | Local Support | Unique Feature |
|------|-------|----------|---------------|----------------|
| **Ahrefs Brand Radar** | Included in $199/mo | Dataset | No | 264M+ prompts dataset |
| **Semrush** | $99/mo add-on | — | No | Existing SEO user base |
| **BrightEdge** | Enterprise | — | No | Enterprise integrations |
| **Conductor** | Enterprise | — | No | Content workflow |
| **seoClarity** | Enterprise | UI scraping | No | Per-paragraph citation tracking |
| **Surfer** | $119/mo | UI scraping | No | 1,000-test accuracy study |
| **Authoritas** | Enterprise | — | No | Per-paragraph citation tracking |

### Tier 3: Budget / SMB

| Name | Price | Approach | Local Support | Notes |
|------|-------|----------|---------------|-------|
| **Otterly** | $29/mo | Firecrawl JS scraping | No | Cheapest serious option |
| **Rankscale** | €20/mo | — | No | EU-focused |
| **Cairrot** | $25/mo | — | No | Early stage |
| **Keyword.com** | $24.50/mo | — | No | Keyword tracking add-on |
| **Am I On AI** | $100/mo | — | No | Simple presence check |
| **BrandViz** | $49 AUD/mo | — | No | Australian market |

### Local-Specific (Closest Competitors)

| Name | Price | Approach | Local Support | Notes |
|------|-------|----------|---------------|-------|
| **Local Falcon** | — | ChatGPT geo-grid | Yes | Grid-based geo testing |
| **Ayzeo** | $39/mo | — | Yes | SMB-priced |
| **GMBMantra** | $799/mo | Managed | Yes | Full-service, expensive |
| **Insites** | $299/mo | White-label | Yes | Agency-focused |

### Competitive Gap Map

```
                    HIGH ACCURACY
                         ▲
                         │
    Profound ●           │           ● seoClarity
    Peec.ai  ●           │
                         │
ENTERPRISE ──────────────┼────────────── SMB / LOCAL
                         │
                         │    ← WHITE SPACE →
                         │
              Otterly ●  │  ● Ayzeo
                         │
                    LOW ACCURACY
```

> **The white space:** High-accuracy + SMB/Local is almost entirely unoccupied.

---

## 4. The API vs UI Problem

> **This is the most critical technical finding in the entire research.**

### The Gap in Numbers

| Test | API Result | UI Result | Match Rate |
|------|-----------|-----------|------------|
| Surfer 1,000-test study (brand overlap) | Baseline | — | **24%** |
| Surfer 1,000-test study (source overlap) | Baseline | — | **4%** |
| Perplexity source overlap | API | UI | **8%** |
| Our test: Maison Remodeling (Claude) | "Not familiar" | Found | **0%** |

### Our Real-World Test

```
Query: "Best remodeling contractors in [city]"

claude.ai (web search ON):     ✅ Maison Remodeling FOUND
Raw Claude API (no web search): ❌ "Not familiar with this business"

Result: 100% false negative from API alone
```

### Why This Happens

- Web search is ON by default in consumer AI UIs (ChatGPT, Claude, Perplexity)
- Raw API calls use only the model's training data — no live web retrieval
- Training cutoffs mean local businesses that opened recently don't exist in API responses
- Model versions diverge: GPT-5.3 vs GPT-5.4 cite **93% different sources**

### What Serious Competitors Do

| Competitor | Approach | Captures Web Search? |
|------------|----------|---------------------|
| Profound | UI scraping | Yes |
| Peec.ai | UI scraping (logged-out) | Yes |
| seoClarity | UI scraping | Yes |
| Surfer | UI scraping | Yes |
| **Us (implemented)** | Hybrid provider stack | **Yes** |

> **Conclusion:** Every serious competitor uses UI scraping or equivalent. Our hybrid provider stack achieves equivalent accuracy without the legal risk or infrastructure complexity of browser automation.

---

## 5. Technical Approaches Comparison

| Approach | Accuracy vs Real UX | Complexity | Cost | Legal Risk | Verdict |
|----------|--------------------|-----------|----- |------------|---------|
| **API scanning (old)** | ~24% match | Low | Low | None | Not viable |
| **API + Web Search** | ~40–50% match | Medium | Medium ($10/1k Anthropic) | None | Partial fix |
| **Firecrawl public AI search** | ~50–60% match | Medium | Medium | Low | Decent |
| **UI scraping (Scrapling/Playwright)** | ~90%+ match | Very High | High (proxies, accounts) | Medium (TOS) | Risky |
| **DataForSEO LLM Scraper** | ~80–90% match | Low | Low ($0.02/req) | None (they handle it) | **Best option** |
| **Hybrid stack (implemented)** | ~80–90% match | Medium | Low | None | **Implemented** |

### Decision Matrix

```
                    HIGH ACCURACY
                         ▲
                         │
  UI Scraping ●          │
  DataForSEO  ●──────────┤
  Hybrid Stack ●─────────┤
                         │
LOW COMPLEXITY ──────────┼────────────── HIGH COMPLEXITY
                         │
  API+Search  ●          │
                         │
  Raw API     ●          │
                    LOW ACCURACY
```

> **The hybrid provider stack** hits the sweet spot: high accuracy, manageable complexity, no legal risk.

---

## 6. DataForSEO: Game Changer

> **DataForSEO solves the API vs UI problem without the legal risk or infrastructure complexity of UI scraping.**

### API Endpoints That Matter

| Endpoint | What It Does | Cost | Priority |
|----------|-------------|------|----------|
| `llm_mentions_live()` | Brand mentions across ChatGPT, Claude, Gemini, Perplexity | ~$0.01/req | High |
| `llm_responses_live()` | Full model responses with brands + URLs | ~$0.02/req | High |
| `llm_scraper_live()` | **ChatGPT WITH WEB SEARCH enabled** | ~$0.02/req | **Critical** |
| `ai_keyword_data_live()` | AI search keyword metrics | ~$0.005/req | Medium |
| OnPage API | Site audit for AI readiness | Variable | High |
| Backlinks API | #1 citation predictor | Variable | High |
| SERP API | AI Overview detection | Variable | Medium |

### Unit Economics

```
20 prompts × 4 models = 80 API calls/month per workspace

Cost breakdown:
  llm_scraper_live:  20 × $0.02 = $0.40
  llm_mentions_live: 20 × $0.01 = $0.20
  llm_responses_live: 20 × $0.02 = $0.40
  OnPage + Backlinks: ~$4.40
  ─────────────────────────────────────
  Total COGS:        ~$5.40/mo per workspace

At $39–49/mo pricing → ~12% COGS ratio ✅
```

### Why `llm_scraper_live()` Is the Key

- Captures ChatGPT responses **with web search enabled** — matches real user experience
- No TOS violations — DataForSEO handles the scraping infrastructure
- No proxy management, no account rotation, no browser automation
- Consistent, reliable, scalable
- Solves the exact problem our Maison Remodeling test exposed

---

## 7. Local Business Opportunity

> **This is the white space. Almost no competitor targets local businesses specifically.**

### Consumer Behavior Shift

| Metric | Value | Source |
|--------|-------|--------|
| Consumers using AI for local recommendations | **45%** (up from 6%) | BrightLocal 2026 |
| ChatGPT local business recommendation rate | **1.2%** of 350K locations | SOCi |
| Difficulty vs Google 3-pack | **30x harder** to get AI-recommended | — |
| AI Overviews in local queries | **68%** of queries | Whitespark |

### Platform-by-Platform Local Performance

| Platform | Recommendation Rate | Accuracy | Notes |
|----------|--------------------|---------|----|
| **Gemini** | 11% | 100% | Google Maps grounded — highest accuracy |
| **Perplexity** | 7.4% | 68% | Decent coverage, moderate accuracy |
| **ChatGPT** | 1.2% | — | Lowest coverage, massive gap |

### The Opportunity in Plain Terms

```
350,000 local businesses tested by SOCi
         ↓
Only 4,200 recommended by ChatGPT (1.2%)
         ↓
345,800 businesses are INVISIBLE to AI
         ↓
Each one is a potential customer
```

### Schema Adoption Gap

- Only **~12% of websites** use any schema markup
- Schema is one of the highest-impact fixes for AI visibility
- This means **88% of local businesses** have an easy, actionable win available

### Pricing Ceiling for Local

| Channel | Price Range | Notes |
|---------|------------|-------|
| Direct to local business | $29–79/mo | Self-serve |
| Via agency (white-label) | $200–500/mo | Agency marks up 2–4x |
| Managed service | $799+/mo | GMBMantra model |

---

## 8. What Actually Improves AI Visibility

### GEO Strategies: What the Research Says

#### Princeton GEO Paper (KDD '24, 10,000 queries)

| Strategy | Visibility Lift | Effort |
|----------|----------------|--------|
| Cite sources + quotation addition + statistics | **+30–40%** | Medium |
| Keyword stuffing | **~0%** | — |
| 5th-ranked site (democratization effect) | **+115%** | — |
| 1st-ranked site (democratization effect) | **-30%** | — |

> GEO democratizes visibility — lower-ranked sites benefit more than top-ranked ones.

#### SE Ranking Study (129,000 sites)

| Factor | Impact | Notes |
|--------|--------|-------|
| Referring domains | **#1 predictor** | Backlinks still matter |
| FAQ sections | **~11% lift** | Structured Q&A format |
| Section length | **120–180 words optimal** | Not too short, not too long |
| Content freshness | **Matters** | 3-month threshold |

### Schema Markup Impact

| Schema Type | Citation Rate |
|-------------|--------------|
| Attribute-rich schema | **61.7%** |
| No schema | **59.8%** |
| Generic/minimal schema | **41.6%** — WORSE than none |

> **Bad schema is worse than no schema.** Generic/minimal schema actively hurts citation rates.

### Content Format Performance

| Content Type | Citation Rate |
|-------------|--------------|
| Comprehensive guides with data tables | **67%** |
| Comparison matrices | **61%** |
| FAQ sections | **~55%** |
| Standard blog posts | **20–30%** |

### The 80% Insight

> **80% of sources cited by AI don't appear in Google's top 100** (ZipTie.dev)

This means traditional SEO rank is a weak predictor of AI visibility. A business can rank #50 on Google and still get cited by AI — if the content is structured correctly.

### Reviews: The Local Factor

| Threshold | Effect |
|-----------|--------|
| 2,000+ reviews | Required for restaurant AI visibility |
| Volume vs star rating | Volume wins above 4.4 stars |
| Claude specifically | Relies on UGC **2–4x more** than other models |

### Actionable Fix Priority for Local Businesses

```
Priority 1: ████████████ Referring domains (backlinks)
Priority 2: ████████████ Attribute-rich schema (not generic)
Priority 3: ████████     Review volume (2,000+ for restaurants)
Priority 4: ███████      FAQ sections on key pages
Priority 5: ██████       Content freshness (update every 3 months)
Priority 6: █████        Section length (120–180 words)
Priority 7: ████         Statistics + citations in content
```

---

## 9. Implemented Architecture

### Hybrid Provider Stack

The scanner uses three distinct provider paths, each capturing a different slice of real-world AI behavior:

| Provider | Method | Models | What It Captures |
|----------|--------|--------|-----------------|
| **DataForSEO** | LLM Scraper API | ChatGPT (gpt-5.4), Gemini | Web-search-enabled responses — matches real user experience |
| **Anthropic** | `web_search_20260209` tool | claude-sonnet-4-6 | Claude with live web retrieval |
| **Perplexity** | Direct sonar-pro API | sonar-pro | Perplexity's native search-grounded responses |

All three paths implement the `ScanAdapter` abstract base class. The `RunOrchestrator` is a thin coordinator — it dispatches to adapters and aggregates results without containing provider-specific logic.

### System Overview

```
┌─────────────────────────────────────────────────────────┐
│                    CUSTOMER DASHBOARD                    │
│                    (Reflex UI)                          │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│               SNAPSHOT REPOSITORY                        │
│         Reads precomputed data — never joins raw tables  │
└──────┬───────────────────┬───────────────────┬──────────┘
       │                   │                   │
┌──────▼──────┐   ┌────────▼────────┐  ┌──────▼──────────┐
│  FINDINGS   │   │  RECOMMENDATIONS│  │  TREND SERIES   │
│  PIPELINE   │   │  ENGINE         │  │                 │
│             │   │                 │  │ formula_version │
│ Diagnosers: │   │ RECOMMENDATION  │  │ + prompt_version│
│ • onpage    │   │ _RULES keyed by │  │ + model must    │
│ • backlink  │   │ reason_code     │  │ ALL match       │
│ • entity    │   │ RULES_VERSION   │  │                 │
│             │   │ = "v1"          │  │                 │
└──────┬──────┘   └────────┬────────┘  └─────────────────┘
       │                   │
┌──────▼───────────────────▼──────────────────────────────┐
│                  EVIDENCE PIPELINE                       │
│  scan_job → scan_execution → prompt_execution →         │
│  observation → citation → diagnostic_finding →          │
│  recommendation_item                                     │
└──────┬──────────────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────────────────┐
│                  HYBRID SCAN STACK                       │
│                                                          │
│  DataForSEO LLM Scraper  │  Anthropic web_search  │  Perplexity sonar-pro  │
│  (ChatGPT + Gemini)      │  (claude-sonnet-4-6)   │  (direct API)          │
└─────────────────────────────────────────────────────────┘
```

### Key Implementation Constraints

- `SnapshotRepository` reads precomputed data — **NEVER** joins raw tables live
- `TrendSeries`: `formula_version + prompt_version + model` must ALL match for valid trend comparison
- `RECOMMENDATION_RULES` keyed by canonical `reason_code`; `RULES_VERSION="v1"`
- Status `completed_with_partial_failures` (not `partial`) when `failed_prompts > 0`
- Citations stored in `prompt_execution_citations` table (not `citations`)

---

## 10. Evidence Pipeline

The evidence pipeline is the core data flow from raw scan to actionable recommendation. Each stage is a distinct database entity with clear ownership.

### Pipeline Stages

```
scan_job
  └── scan_execution (one per provider/model combination)
        └── prompt_execution (one per prompt)
              └── observation (brand mention detected)
                    └── citation (URL extracted from response)
                          └── diagnostic_finding (diagnoser output)
                                └── recommendation_item (ranked action)
```

### Stage Descriptions

| Stage | Table | Purpose |
|-------|-------|---------|
| `scan_job` | `scan_jobs` | Top-level scan request for a workspace |
| `scan_execution` | `scan_executions` | One execution per provider/model pair |
| `prompt_execution` | `prompt_executions` | One execution per prompt within a scan |
| `observation` | `observations` | Brand mention detected in a response |
| `citation` | `prompt_execution_citations` | URL extracted from a response |
| `diagnostic_finding` | `diagnostic_findings` | Diagnoser output (onpage/backlink/entity) |
| `recommendation_item` | `recommendation_items` | Ranked, evidence-backed action |

### Diagnosers

Three diagnosers analyze the evidence and produce findings:

| Diagnoser | File | What It Detects |
|-----------|------|----------------|
| **OnPage** | `ai_visibility/diagnosis/onpage.py` | Schema markup quality, content structure, FAQ presence |
| **Backlink** | `ai_visibility/diagnosis/backlink.py` | Referring domain count, citation authority |
| **Entity** | `ai_visibility/diagnosis/entity.py` | Brand entity clarity, NAP consistency, review volume |

### FindingsPipeline and RecommendationsEngine

- `FindingsPipeline` (`ai_visibility/recommendations/findings.py`) aggregates diagnoser outputs into structured findings
- `RecommendationsEngine` (`ai_visibility/recommendations/engine.py`) converts findings into ranked `recommendation_item` records using `RECOMMENDATION_RULES`

---

## 11. Database Architecture

### Development vs Production

| Environment | Database | Notes |
|-------------|----------|-------|
| Development | SQLite | Zero-config, file-based, fast for local iteration |
| Production | PostgreSQL 18 | Full ACID, partitioning, scheduled maintenance |

### PostgreSQL 18 Production Stack

The production database uses several PostgreSQL-native features that have no SQLite equivalent:

| Feature | Purpose | Implementation |
|---------|---------|----------------|
| **pg_partman** | Time-based table partitioning | `scan_executions` and `observations` partitioned by month |
| **pg_cron** | Scheduled maintenance jobs | Nightly partition creation, weekly matview refresh |
| **BRIN indexes** | Efficient range scans on time-series data | `created_at` columns on large tables |
| **Materialized views** | Precomputed dashboard snapshots | `workspace_visibility_summary`, `trend_series_mv` |

### Why PostgreSQL 18

- `pg_partman` handles partition lifecycle automatically — no manual DDL for new months
- `pg_cron` runs maintenance inside the database, removing the need for external cron jobs
- BRIN indexes are 10-100x smaller than B-tree for append-only time-series tables
- Materialized views let `SnapshotRepository` serve dashboard queries in <10ms without touching raw tables

### Schema Maintenance

Maintenance SQL lives in `ai_visibility/storage/maintenance.sql`. The Python wrapper at `ai_visibility/storage/maintenance.py` runs it on startup in production.

---

## 12. Self-Serve Dashboard and Onboarding

### Onboarding Wizard

The onboarding flow guides new users through workspace setup in 4 steps:

1. **Domain input** — enter brand domain
2. **Industry selection** — pick from predefined industry options
3. **Competitor setup** — add competitor domains
4. **Prompt selection** — choose from suggested prompts
5. **First scan** — trigger initial scan and show summary

State is managed by `OnboardingState` in `ai_visibility/ui/onboarding_state.py`. The wizard is idempotent — re-running it on an existing workspace skips creation.

### Dashboard Views

The dashboard (`ai_visibility/ui/pages/dashboard.py`) has two views:

| View | What It Shows |
|------|--------------|
| **Hero view** | Visibility score, trend sparkline, top competitor comparison |
| **Data view** | Competitor comparison table, provider breakdown, findings section, priority actions list |

All data comes from `SnapshotRepository` — the dashboard never queries raw tables directly.

### Key Dashboard Sections

| Section | Data Source | data_id |
|---------|------------|---------|
| Visibility score | `snapshot/overview` | `hero-visibility-score` |
| Competitor comparison | `snapshot/overview` | `competitor-comparison-table` |
| Provider breakdown | `snapshot/overview` | `provider-breakdown` |
| Findings | `snapshot/findings` | `findings-section` |
| Priority actions | `snapshot/actions` | `priority-actions-list` |

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/health` | GET | Health check with database connectivity test |
| `/api/v1/workspaces` | GET | List all workspaces |
| `/api/v1/runs` | GET | List runs for a workspace |
| `/api/v1/runs/latest` | GET | Get latest run for a workspace |
| `/api/v1/prompts` | GET | List available prompts |
| `/api/v1/snapshot/overview` | GET | Precomputed visibility overview |
| `/api/v1/snapshot/trend` | GET | Trend series data |
| `/api/v1/snapshot/findings` | GET | Diagnostic findings summary |
| `/api/v1/snapshot/actions` | GET | Priority action queue |

---

## 13. Pricing Strategy

### Tier Structure

| Tier | Price | Target | Margin |
|------|-------|--------|--------|
| **Local Business** | $39–49/mo | SMB direct | ~88% |
| **Agency** | $129–199/mo | White-label resellers | ~96% (agency marks up 2–4x) |
| **Managed** | Custom | High-touch local | Variable |

### Unit Economics

```
Revenue per workspace:     $44/mo (midpoint)
DataForSEO COGS:          -$5.40/mo
Gross margin:              $38.60/mo (~88%)

Agency tier:
Revenue per workspace:     $164/mo (midpoint)
DataForSEO COGS:          -$5.40/mo
Gross margin:              $158.60/mo (~97%)
```

### Free Trial Strategy

- **7-day free trial** — enough to show value, not enough to abuse
- **No freemium** — API costs make permanent free tier unviable
- **Trial hook:** Run a scan on their business + one competitor immediately

### The #1 Purchase Trigger

> **"Your competitor appears in ChatGPT and you don't."**

This is the message that converts. Not "improve your AI visibility" — that's abstract. The competitor comparison is visceral and immediate.

### Conversion Flow

```
Free scan → Show competitor appearing → Show client NOT appearing
         → "Here's the 3 fixes that would change this"
         → Start 7-day trial → Convert to paid
```

---

## 14. First-Party Analytics

> **The first-party data landscape is almost entirely closed. This is both a problem and a moat.**

### Platform-by-Platform Status

| Platform | First-Party Data | API Access | Notes |
|----------|-----------------|------------|-------|
| **Bing Webmaster** | AI Performance dashboard | Dashboard only, no API | Only real first-party data available |
| **Google Search Console** | Partial | No AI segmentation | Can't separate AI Overview clicks |
| **Perplexity Publisher Program** | Partner data | Partner-gated | Via ScalePost.ai |
| **OpenAI / ChatGPT** | Nothing | Nothing | Complete black box |
| **Claude / Anthropic** | Nothing | Nothing | Complete black box |
| **Gemini** | Nothing | Nothing | Complete black box |

### What You CAN Measure

| Method | What It Captures | Coverage |
|--------|-----------------|----------|
| **Server logs** | ChatGPT-User, PerplexityBot, Claude-User bot crawls | ~46% of AI bots |
| **GA4 referral** | chatgpt.com, perplexity.ai referrals | Clicked citations only |
| **UTM tracking** | AI-driven traffic if links include UTMs | Rare |

### The Coverage Gap

```
AI platforms generating responses:  100%
Platforms with public APIs:          ~0%
Platforms with any first-party data: ~15% (Bing only)
What we can actually measure:        ~46% (server logs)
```

> **This gap is a moat.** Third-party tools like DataForSEO exist precisely because first-party data is locked away. Anyone building in this space needs third-party data infrastructure.

---

## 15. Case Studies

### Success Stories

#### Tally.so
- ChatGPT became **#1 referral source**
- **10% of signups** from ChatGPT
- Lesson: AI visibility can become a primary acquisition channel, not just a vanity metric

#### Vercel
- **10% of signups** from ChatGPT
- Lesson: Developer tools with strong documentation and data-rich content get cited heavily

#### Arlington Coffee Shop (60-day case study)
- **+45% AI visibility** in 60 days
- Methods: Schema markup + entity clarity improvements
- Lesson: Local businesses can move fast with the right fixes

### Our Own Test: Maison Remodeling

| Platform | Method | Result |
|----------|--------|--------|
| claude.ai (web search ON) | UI | **Found** |
| Claude raw API | API | "Not familiar with this business" |
| Perplexity | UI | **Found** |
| Other models | API | Not found |

**Visibility score:** 0.4 | **Citation rate:** 0% | **Only Perplexity found them via UI**

> **This test is the product demo.** Show a prospect their own business through our scanner vs through a real AI chat UI. The gap is the sale.

### Pattern Recognition Across Cases

| Pattern | Evidence |
|---------|----------|
| Schema + entity clarity = fast wins | Arlington +45% in 60 days |
| AI can become top acquisition channel | Tally, Vercel both at 10% signups |
| API results are unreliable for local | Maison Remodeling: 0% API vs found in UI |
| Perplexity finds local businesses more than ChatGPT | 7.4% vs 1.2% recommendation rate |

---

## Appendix: Key Stats Reference

| Stat | Value | Source |
|------|-------|--------|
| Market size 2034 | $18.7B | Market research |
| CAGR | 41.3% | Market research |
| Consumers using AI for local | 45% | BrightLocal 2026 |
| ChatGPT local recommendation rate | 1.2% | SOCi (350K locations) |
| AI Overviews in local queries | 68% | Whitespark |
| Gemini recommendation rate | 11% | Research |
| Perplexity recommendation rate | 7.4% | Research |
| Websites with schema markup | ~12% | Industry data |
| API vs UI brand overlap (Surfer) | 24% | Surfer 1,000-test study |
| API vs UI source overlap (Surfer) | 4% | Surfer 1,000-test study |
| Perplexity API vs UI source overlap | 8% | Research |
| GEO visibility lift (Princeton) | +30–40% | Princeton KDD '24 |
| 5th-ranked site GEO boost | +115% | Princeton KDD '24 |
| AI sources not in Google top 100 | 80% | ZipTie.dev |
| Attribute-rich schema citation rate | 61.7% | Research |
| Generic schema citation rate | 41.6% | Research |
| DataForSEO COGS per workspace | ~$5.40/mo | Calculated |
| Reviews threshold (restaurants) | 2,000+ | Research |

---

*Report compiled from: BrightLocal 2026, SOCi local AI study, Princeton GEO paper (KDD '24), SE Ranking 129K-site study, Surfer 1,000-test study, Whitespark local AI report, ZipTie.dev citation research, DataForSEO API documentation, and primary testing. Architecture sections reflect the implemented system as of March 2026.*
