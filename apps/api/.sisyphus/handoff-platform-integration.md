# Handoff: Platform Integration (Job SDK + Stateless Worker)

## Status
Branch: `fix/architecture-review` on ai-visibility repo.
All prior work committed. 818 tests passing. 0 compile errors.

## What's Done
- Architecture review: 7/11 issues resolved (orchestrator split, credentials, rename llm→providers, state.py extraction, sentiment, parallel prompts, silent excepts)
- Phase 3 complete: all Tier 1+2+3 features implemented + wired to UI
- Competitor discovery rewrite (Exa contents + summary)
- Brand name field + orchestrator brand resolution
- Docker setup (Dockerfile.reflex + docker-compose)

## What's Left: 3 Deferred Platform Integration Tasks

### Task 1: Create schema.py + stateless scan executor
**File**: `ai_visibility/schema.py` — Pydantic models following solaraai-job-sdk pattern
**File**: `ai_visibility/scan_executor.py` — Pure function: ScanInput → ScanOutput, NO DB

Reference: `/tmp/cgi/src/schema.py` (content-generation-image pattern)
SDK: `solaraai_job_sdk.BaseJobInput`, `BaseJobResult` at `repos/solaraai-packages/packages/python/solaraai-job-sdk/`

Models needed:
- `ScanInput(BaseJobInput)` — brand_name, domain, providers, prompts, competitors, location
- `ScanOutput(BaseJobResult)` — mentions list, metrics, provider_results
- `MentionResult` — provider, prompt, response, brand_mentioned, citations
- `ScanMetrics` — visibility_score, citation_coverage, avg_position
- `ScanProgress` — stage, provider, prompts_completed/total
- `PromptDefinition` — id, template, category, version
- `LocationContext` — country_code, city, region

The `execute_scan(ScanInput) → ScanOutput` function should:
1. Import adapters from `ai_visibility/providers/`
2. For each provider: instantiate adapter, execute prompts with Semaphore(3)
3. Extract mentions/citations from responses
4. Compute metrics
5. Return ScanOutput — NO Prisma, NO DB, NO repositories

### Task 2: Create worker.py (RabbitMQ consumer)
**File**: `ai_visibility/worker_job.py`
Reference: `/tmp/cgi/src/worker.py`

```python
from solaraai_messaging import PikaApp
from solaraai_job_sdk.stores.redis import RedisStatusStore
from solaraai_job_sdk.types import BaseJobResult, JobState, JobStatus

pika_app = PikaApp.get_instance()
redis_store = RedisStatusStore(redis_url=os.environ.get("REDIS_URL"))

@pika_app.topic("scan.ai_visibility")
async def handle_scan(payload: ScanInput, *, correlation_id=None) -> dict:
    # Set RUNNING → execute_scan() → Set COMPLETED/FAILED → return results
```

### Task 3: Create job.py (K8s entry point)
**File**: `ai_visibility/job.py`
Reference: `/tmp/cgi/src/job.py`

Reads `JOB_PAYLOAD` env var → parses ScanInput → calls execute_scan() → updates Redis → exits.

### Task 4: Create SDK client
**Dir**: `ai_visibility/sdks/python/src/solaraai_ai_visibility/`
Reference: `/tmp/cgi/sdks/python/src/solaraai_text_to_image/client.py`

```python
class ScanClient(BaseJobClient[ScanInput, ScanOutput, ScanProgress]):
    # validate_input, serialize_input, deserialize_result, deserialize_progress
```

### Task 5: Tests + regression

## Key Architecture Understanding

Flow: Job Scheduler → RabbitMQ → Agentflow → AI Visibility scan (stateless) → Agentflow saves to DB

The worker has NO DB connection. Agentflow polls Redis for completion and saves results.

SDK packages:
- `solaraai-job-sdk` — BaseJobInput, BaseJobResult, RedisStatusStore, K8sJobProvider
- `solaraai-messaging` — PikaApp with @pika_app.topic() decorator
- `solaraai-storage` — S3StorageService

Existing adapters: `ai_visibility/providers/adapters/` (chatgpt, claude, gemini, perplexity, grok, google_ai_overview, google_ai_mode_serpapi)
Extraction: `ai_visibility/extraction/pipeline.py`
Gateway: `ai_visibility/providers/gateway.py` — `execute_with_provider()`

## Files to Reference
- `/tmp/cgi/src/schema.py` — content-generation-image schema (PATTERN TO FOLLOW)
- `/tmp/cgi/src/worker.py` — content-generation-image worker (PATTERN TO FOLLOW)
- `/tmp/cgi/src/job.py` — content-generation-image K8s job (PATTERN TO FOLLOW)
- `/tmp/cgi/sdks/python/src/solaraai_text_to_image/client.py` — SDK client (PATTERN TO FOLLOW)
- `ai_visibility/runs/orchestrator.py` — current orchestrator (EXTRACT LOGIC FROM)
- `ai_visibility/providers/gateway.py` — adapter execution
- `ai_visibility/extraction/pipeline.py` — mention/citation extraction

## Constraints
- Worker must NOT import Prisma or any DB module
- Worker must NOT connect to database
- Use solaraai-job-sdk BaseJobInput/BaseJobResult
- Use solaraai-messaging PikaApp for RabbitMQ
- Use RedisStatusStore for job status
- Follow content-generation-image pattern exactly
- Run all existing 818+ tests after changes — 0 regressions allowed
