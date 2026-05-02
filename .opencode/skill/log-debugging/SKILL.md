---
name: log-debugging
description: Debug services using structured logs, correlation IDs, trace requests across services, and analyze error patterns without interactive debugger
license: MIT
metadata:
  author: solara-ai
  version: "1.0"
---

# Log-Based Debugging Skill

Debug production and development issues using structured JSON logs and correlation IDs. This skill assumes **no interactive debugger** is available.

## When to Use

- Investigating errors or unexpected behavior in any service
- Tracing requests across microservices (ApplicationServer → AgentFlow → Researcher)
- Debugging RabbitMQ message flows
- Performance analysis (slow requests, timeouts)
- Reproducing production issues locally

## Log Structure

All services emit structured JSON logs with these required fields:

| Field | Type | Description |
|-------|------|-------------|
| `ts` | string | ISO 8601 timestamp in UTC |
| `level` | string | ERROR, WARN, INFO, DEBUG |
| `service` | string | Service name (e.g., `application-server`, `agentflow`) |
| `env` | string | Environment (`local`, `staging`, `production`) |
| `request_id` | string | Correlation ID from `X-Request-ID` header |
| `msg` | string | Human-readable message |
| `duration_ms` | number | Request/operation duration (optional) |
| `route` | string | HTTP route or action name (optional) |
| `trace_id` | string | Distributed tracing ID (optional) |
| `span_id` | string | Span within trace (optional) |

**Never log**: passwords, tokens, PII, credit card numbers, API keys.

## Debugging Process

### 1. Reproduce

Capture identifying information:
```bash
# Get the request ID from response headers or logs
curl -i https://api.solaraai.local/api/v1/posts | grep -i x-request-id

# Or find user-specific requests
docker compose logs application-server | grep "user_id.*12345" | head -5
```

### 2. Focus

Narrow to relevant services and time window:
```bash
# Tail specific service
cd deployment && docker compose logs -f agentflow --since 5m

# Multiple services
docker compose logs -f application-server agentflow researcher --since 10m
```

### 3. Instrument

Add logs at decision points (temporarily if needed):
```typescript
// NestJS - before/after external calls
this.logger.debug({ request_id, action: 'calling_agentflow', payload }, 'Sending to AgentFlow');
const result = await this.agentflowClient.generate(payload);
this.logger.debug({ request_id, action: 'agentflow_response', duration_ms: elapsed }, 'AgentFlow responded');
```

```python
# Python - around critical branches
logger.debug("Processing message", request_id=request_id, message_type=msg.type)
if msg.type == "generate":
    logger.info("Starting generation", request_id=request_id, params=params)
```

### 4. Correlate

Follow `request_id` across services:
```bash
# Find all logs for a specific request
docker compose logs | grep "req_9f2c4d" | jq -s 'sort_by(.ts)'

# Across specific services
docker compose logs application-server agentflow | grep "req_9f2c4d"
```

### 5. Binary Search

Narrow down the failure point:
```bash
# Add sentinel logs to bisect the flow
logger.info("CHECKPOINT_1: Before validation", request_id=request_id)
# ... validation code ...
logger.info("CHECKPOINT_2: After validation", request_id=request_id)
```

### 6. Verify

After fixing, confirm with logs:
```bash
# Run the same request and verify no errors
curl -H "X-Request-ID: test_fix_001" https://api.solaraai.local/api/v1/posts
docker compose logs --since 1m | grep "test_fix_001" | grep -i error
# Should return nothing
```

## Examples

### NestJS Structured Logging (Pino)

```typescript
// logger.module.ts
import { LoggerModule } from 'nestjs-pino';

@Module({
  imports: [
    LoggerModule.forRoot({
      pinoHttp: {
        level: process.env.LOG_LEVEL || 'info',
        formatters: {
          level: (label) => ({ level: label }),
        },
        base: {
          service: 'application-server',
          env: process.env.NODE_ENV,
        },
        redact: ['req.headers.authorization', 'body.password'],
      },
    }),
  ],
})
export class AppLoggerModule {}

// posts.service.ts
import { Logger } from '@nestjs/common';

@Injectable()
export class PostsService {
  private readonly logger = new Logger(PostsService.name);

  async createPost(dto: CreatePostDto, requestId: string) {
    this.logger.log({
      request_id: requestId,
      action: 'create_post',
      user_id: dto.userId,
    });

    try {
      const post = await this.prisma.post.create({ data: dto });
      this.logger.log({
        request_id: requestId,
        action: 'post_created',
        post_id: post.id,
        duration_ms: elapsed,
      });
      return post;
    } catch (error) {
      this.logger.error({
        request_id: requestId,
        action: 'create_post_failed',
        error: error.message,
        stack: error.stack,
      });
      throw error;
    }
  }
}
```

### Python Logging (Loguru)

```python
# logging_config.py
import sys
from loguru import logger
from contextvars import ContextVar

request_id_ctx: ContextVar[str] = ContextVar('request_id', default='no_request_id')

def configure_logging(service_name: str):
    logger.remove()
    logger.add(
        sys.stdout,
        format=lambda r: json.dumps({
            "ts": r["time"].strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "level": r["level"].name,
            "service": service_name,
            "env": os.getenv("ENV", "local"),
            "request_id": request_id_ctx.get(),
            "msg": r["message"],
            **r["extra"],
        }) + "\n",
        level=os.getenv("LOG_LEVEL", "INFO"),
    )

# middleware.py
from starlette.middleware.base import BaseHTTPMiddleware

class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID", f"req_{uuid4().hex[:12]}")
        request_id_ctx.set(request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

# service.py
from loguru import logger

async def generate_content(params: dict):
    logger.info("Starting content generation", params=params)
    start = time.time()
    
    try:
        result = await llm_client.generate(params)
        logger.info(
            "Content generated",
            duration_ms=int((time.time() - start) * 1000),
            tokens_used=result.tokens,
        )
        return result
    except Exception as e:
        logger.error("Generation failed", error=str(e), params=params)
        raise
```

### Filtering Logs by Correlation ID

```bash
# Basic grep
docker compose logs | grep "req_abc123"

# Pretty JSON output
docker compose logs agentflow 2>&1 | grep "req_abc123" | jq '.'

# Extract specific fields
docker compose logs 2>&1 | grep "req_abc123" | jq '{ts, level, service, msg}'

# Sort by timestamp
docker compose logs 2>&1 | grep "req_abc123" | jq -s 'sort_by(.ts)[]'

# Filter errors only
docker compose logs 2>&1 | jq 'select(.level == "ERROR" and .request_id == "req_abc123")'

# Count by level
docker compose logs 2>&1 | grep "req_abc123" | jq -s 'group_by(.level) | map({level: .[0].level, count: length})'
```

## Correlation ID Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Client Request                                                         │
│  X-Request-ID: req_9f2c4d (or generated if missing)                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Application Server (NestJS)                                            │
│  logs: { request_id: "req_9f2c4d", service: "application-server", ... } │
│  → Publishes to RabbitMQ with header: x-request-id                     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
┌──────────────────────┐ ┌──────────────────┐ ┌──────────────────────────┐
│  AgentFlow (Python)  │ │ Researcher       │ │ Visual Content Generator │
│  request_id from     │ │ request_id from  │ │ request_id from          │
│  message headers     │ │ message headers  │ │ message headers          │
└──────────────────────┘ └──────────────────┘ └──────────────────────────┘
                    │               │               │
                    └───────────────┼───────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Social Publisher (NestJS)                                              │
│  logs: { request_id: "req_9f2c4d", service: "social-publisher", ... }  │
└─────────────────────────────────────────────────────────────────────────┘
```

## Guidelines

1. **Always include request_id** - Every log statement must have correlation ID
2. **Log at boundaries** - Before/after HTTP calls, queue publishes, DB queries
3. **Use appropriate levels**:
   - ERROR: Failures requiring attention
   - WARN: Recoverable issues, deprecations
   - INFO: Key business events, request lifecycle
   - DEBUG: Detailed troubleshooting (toggle dynamically)
4. **Structure over strings** - Use `{ action, user_id }` not `"action for user 123"`
5. **Include duration** - Add `duration_ms` for operations over 10ms
6. **Clean up after debugging** - Remove temporary checkpoint logs
7. **Keep useful logs** - Document retained logs in PR if they add value

## Commands

```bash
# Tail all services
cd deployment && docker compose logs -f

# Tail specific service with timestamp
docker compose logs -f --timestamps application-server

# Last N lines
docker compose logs --tail 100 agentflow

# Since time
docker compose logs --since "2024-01-15T10:00:00" researcher

# Pretty print JSON logs
docker compose logs agentflow 2>&1 | tail -50 | jq '.'

# Filter by level
docker compose logs 2>&1 | jq 'select(.level == "ERROR")'

# Search across all logs
docker compose logs 2>&1 | grep -E "(error|exception|failed)" -i

# Export for analysis
docker compose logs agentflow > /tmp/agentflow-debug.log
```

## Reference Files

- Logging standards: `docs/50_Standards/LOGGING.md`
- NestJS logger setup: `apps/api/src/common/logger/`
- Python logging config: `apps/api/src/logging_config.py`
- Correlation middleware: `apps/api/src/common/middleware/correlation.middleware.ts`
- Debug process: `AGENTS.md` section 5 (Log-Driven Debugging)
