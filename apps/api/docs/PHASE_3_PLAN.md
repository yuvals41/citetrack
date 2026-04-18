# Phase 3 Plan — AI Visibility Tool

Based on deep research of DataForSEO, SerpAPI, Scrapling/Crawl4AI, and competitors
(OtterlyAI, Semrush AIO, Ahrefs Brand Radar, Profound, Goodie AI, Limy.ai, Peec.ai).

## Tier 1: Build Now [COMPLETED]

### 0. Exa Integration for Competitor Discovery [COMPLETED]
Integrated Exa's company search API as the primary competitor discovery method.
Uses geographic bias (userLocation) for location-aware results.
Claude adaptive thinking filter evaluates company size and relevance.
Tavily search serves as fallback when Exa results are limited.
Significantly improves competitor discovery for SaaS, local businesses, and niche practitioners.

### 1. DataForSEO LLM Mentions API
190M+ pre-indexed prompts covering Google AI Overviews + ChatGPT (GPT-5).
Enables historical tracking, competitor benchmarking, and AI search volume
without live LLM calls. $0.02/request vs $0.003+ per live query.

Endpoints:
- `POST /v3/ai_optimization/llm_mentions/search/live` — search brand mentions
- `POST /v3/ai_optimization/llm_mentions/aggregated_metrics/live` — visibility over time
- `POST /v3/ai_optimization/llm_mentions/cross_aggregated_metrics/live` — competitor comparison
- `POST /v3/ai_optimization/llm_mentions/top_domains/live` — most-cited domains
- `POST /v3/ai_optimization/llm_mentions/top_pages/live` — most-cited pages

Requires $100/mo minimum commitment.

### 2. DataForSEO Reasoning
`use_reasoning=true` parameter on LLM Responses API.
Shows WHY each AI mentioned/ignored the brand — chain-of-thought reasoning.
Automatic for ChatGPT, opt-in for Claude and Gemini.
Response includes `reasoning` item with full chain-of-thought + `reasoning_tokens` count.

### 3. Custom Prompts
Let users add their own questions beyond the 20 defaults.
Every competitor offers this (Peec, Otterly, Profound, Limy).
Store in DB per workspace. Show in Questions page with add/edit/delete.

### 4. Export/Reports
CSV and PDF export of scan results. Agencies need this for client reporting.
Peec has Looker Studio connector. Otterly has CSV on all plans.
Minimum: CSV export of dashboard data + AI responses.

### 5. Content Extractability Analyzer
Check which paragraphs on a website AI can actually extract.
Based on OtterlyAI's Content Checker (Section Integrity, Modular Content,
Paragraph Cohesion, Semantic Repetition, Static Content scores).
No competitor offers this at SMB price. Differentiating feature.

Implementation: fetch page via Tavily extract or Crawl4AI, analyze structure
with GPT-5.4, score each section for AI extractability.

## Tier 2: Build Next [COMPLETED]

### 6. AI Crawler Simulation
Check if GPTBot, ClaudeBot, PerplexityBot can access your pages.
Profound calls this "Agent Analytics". Otterly has "Crawlability Checker".
Semrush tracks 30 bots (20 search + 10 AI) via log file analysis.

Implementation: send HEAD requests with each bot's User-Agent,
check robots.txt rules, verify JS rendering accessibility.

### 7. Query Fan-Out Analysis (simplified)
When ChatGPT answers a question, it runs 5-20 sub-queries behind the scenes.
Show which sub-queries it ran and where the brand ranks for each.
Semrush Enterprise has this ($$$). Ahrefs uses it as methodology.
Nobody offers this at SMB price — first-mover opportunity.

Implementation: use DataForSEO SERP API to check rankings for
auto-generated fan-out queries derived from the main prompt.

### 8. YouTube/Reddit Visibility
Reddit is #1 social platform for AI citations (46.4% of social citations).
YouTube is #2 (31.8%). Ahrefs Brand Radar tracks these.
40.83% of AI-cited YouTube videos have fewer than 10,000 views.

Implementation: use SerpAPI Google Search with site:reddit.com
and site:youtube.com filters to find brand mentions.

### 9. DataForSEO AI Keyword Data
AI-specific search volume — how often keywords are queried inside AI tools.
Endpoint: `POST /v3/ai_optimization/ai_keyword_data/keywords_search_volume/live`
Covers 94 locations. Shows last month volume + 12-month trend by LLM platform.

### 10. Alert System
Email/Slack notifications when visibility drops, competitor surges,
or new sources appear. No competitor does this well.
Implementation: check scan results in ARQ worker, send alerts via
webhook or email when thresholds are crossed.

## Tier 3: Build Later [COMPLETED - except Looker Studio]

### 11. Brand Entity Optimization [COMPLETED]
Track how AI understands your brand as an entity (not just keyword match).
Ahrefs Brand Radar v2.0 has entity-level filtering.
Goodie AI has "AEO Periodic Table" mapping 15 entity factors.

**Implementation**: `ai_visibility/analysis/brand_entity.py`
- Google Knowledge Graph entity scoring
- Wikidata entity matching and disambiguation
- Wikipedia relevance scoring
- Multi-source entity confidence calculation

### 12. AI Shopping Visibility [COMPLETED]
Track products in ChatGPT Shopping, Google AI Mode, Amazon Rufus.
Profound has Shopping Analysis. Goodie has Agentic Commerce Optimizer.
Projected $1.7 trillion market by 2030.

**Implementation**: `ai_visibility/analysis/shopping_visibility.py`
- Google Shopping integration via DataForSEO
- AI Mode shopping results detection
- ChatGPT shopping plugin visibility tracking
- Multi-channel product visibility scoring

### 13. SerpAPI Google AI Mode (multi-turn) [COMPLETED]
SerpAPI has dedicated endpoint with `subsequent_request_token` for
multi-turn AI Mode conversations. DataForSEO only does single query.

**Implementation**: `ai_visibility/llm/adapters/google_ai_mode_serpapi.py`
- Multi-turn conversation support via `subsequent_request_token`
- Conversation state management
- Response parsing and analysis
- Integration with existing LLM adapter pattern

### 14. Looker Studio Connector [SKIPPED]
Agency reporting integration. Peec and Otterly both offer this.
Low effort, table stakes for enterprise deals.

**Status**: Not implemented per user decision.

### 15. Revenue Attribution Pixel [COMPLETED]
JS snippet customers install on their site to track AI-referred traffic.
Limy.ai's biggest differentiator. Connects: prompt -> mention -> visit -> conversion -> $.

**Implementation**: `ai_visibility/pixel/`
- JavaScript snippet for client-side event tracking
- FastAPI endpoints for event ingestion and storage
- Event schema: source, prompt, timestamp, user_id, conversion_data
- Dashboard integration for revenue attribution analysis

## Not Recommended

### Scrapling/Crawl4AI for Replacing DataForSEO
At 100 queries/day, infrastructure cost ($350-460/mo) exceeds DataForSEO ($9-30/mo).
Legal risk: scraping ChatGPT/Perplexity violates their ToS explicitly.
Peec.ai does UI scraping but has $29M funding and legal counsel backing.

### SerpAPI as Primary Provider
No LLM query capability (can't query ChatGPT/Claude/Perplexity directly).
Use DataForSEO for AI visibility. Add SerpAPI only for Knowledge Graph or Scholar.

## Tool Decisions

| Use Case | Tool | Why |
|----------|------|-----|
| LLM brand monitoring | DataForSEO LLM Mentions | 190M+ prompt database, pre-indexed |
| Direct LLM queries | DataForSEO LLM Responses | ChatGPT, Claude, Gemini, Perplexity |
| Google AI Overviews | DataForSEO SERP (current) | Already integrated |
| AI search volume | DataForSEO AI Keyword Data | Only tool with this data |
| Google AI Mode (multi-turn) | SerpAPI | Dedicated endpoint with conversation |
| Knowledge Graph | SerpAPI | Direct kgmid lookup |
| Content extraction | Crawl4AI or Tavily | For content analysis features |
| Scheduled scraping | Keep DataForSEO | Legal, reliable, cost-effective at our scale |

## Pricing Context

DataForSEO: pay-as-you-go, credits never expire, $50 minimum top-up.
- LLM Mentions: $0.02/request + $0.00003/data row ($100/mo minimum)
- LLM Responses: base fee + LLM API cost (variable)
- SERP API: $0.0006-0.002/request
- AI Keyword Data: $0.01/task + $0.0001/keyword

SerpAPI: subscription, credits expire monthly.
- $75/mo for 5,000 searches
- $275/mo for 30,000 searches

Estimated Phase 3 monthly cost: $150-300/mo for DataForSEO + $75/mo SerpAPI = $225-375/mo total.
