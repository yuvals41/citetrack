---
name: python-fastapi
description: |
  Skill for developing Python/FastAPI endpoints and services in Citetrack.
  Triggers: "FastAPI endpoint", "Python service", "UV", "add endpoint", "create API", 
  "FastAPI router", "Python microservice", "agentflow", "researcher", "visual-content-generator",
  "job-scheduler", "uv sync", "uv add", "pytest", "Pydantic model", "async endpoint"
license: MIT
metadata:
  author: solara-ai
  version: "1.0"
---

# Python/FastAPI Service Development

## When to Use

- Creating new FastAPI endpoints or routers
- Adding Pydantic request/response models
- Implementing async service logic
- Setting up RabbitMQ message handlers (aio-pika)
- Adding database operations via Prisma Python client
- Writing pytest tests for Python services
- Managing dependencies with UV runtime

## Quick Start

```bash
# Navigate to service
cd apps/api  # or researcher, visual-content-generator, job-scheduler

# Install dependencies (NEVER use pip)
uv sync

# Add a new package
uv add package-name

# Remove a package
uv remove package-name

# Run tests
uv run pytest

# Run dev server
uv run python server.py --host 0.0.0.0 --port 8091 --reload

# Type checking
uv run mypy .

# Linting
uv run ruff check .
```

## Project Locations

| Service | Path | Port | Purpose |
|---------|------|------|---------|
| agentflow | `apps/api` | 5000 | AI orchestration engine |
| visual-content-generator | `apps/api` | varies | Media generation (5 replicas) |
| researcher | `apps/api` | 5001 | Semantic search via Milvus |
| job-scheduler | `apps/api` | - | Background job processing |

## Endpoint Structure

```
repos/<service>/
├── pyproject.toml          # UV dependencies (NEVER requirements.txt)
├── uv.lock                  # Locked versions
├── server.py               # FastAPI app entry point
├── src/
│   ├── routers/            # FastAPI routers
│   │   ├── __init__.py
│   │   └── feature_router.py
│   ├── services/           # Business logic
│   │   └── feature_service.py
│   ├── models/             # Pydantic models
│   │   └── feature_models.py
│   └── middleware/         # Correlation ID, logging
│       └── correlation.py
└── tests/
    └── test_feature.py
```

## Examples

### Router (src/routers/content_router.py)

```python
from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from src.models.content_models import ContentRequest, ContentResponse
from src.services.content_service import ContentService
from src.middleware.correlation import get_correlation_id

router = APIRouter(prefix="/content", tags=["content"])

@router.post("/generate", response_model=ContentResponse)
async def generate_content(
    request: ContentRequest,
    correlation_id: str = Depends(get_correlation_id),
    service: ContentService = Depends(),
) -> ContentResponse:
    logger.bind(correlation_id=correlation_id).info(
        "Generating content", topic=request.topic
    )
    try:
        result = await service.generate(request, correlation_id)
        return ContentResponse(content=result, status="completed")
    except Exception as e:
        logger.bind(correlation_id=correlation_id).error(f"Generation failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
```

### Service (src/services/content_service.py)

```python
from loguru import logger
from src.models.content_models import ContentRequest

class ContentService:
    async def generate(self, request: ContentRequest, correlation_id: str) -> str:
        logger.bind(correlation_id=correlation_id).debug(
            "Processing request", tone=request.tone
        )
        # Business logic here
        return f"Generated content for: {request.topic}"
```

### Pydantic Models (src/models/content_models.py)

```python
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class ToneEnum(str, Enum):
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    EDUCATIONAL = "educational"

class ContentRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=500)
    tone: ToneEnum = ToneEnum.PROFESSIONAL
    max_length: Optional[int] = Field(default=1000, ge=100, le=5000)

class ContentResponse(BaseModel):
    content: str
    status: str
    error: Optional[str] = None
```

### Correlation ID Middleware (src/middleware/correlation.py)

```python
import uuid
from fastapi import Request

def get_correlation_id(request: Request) -> str:
    return request.headers.get("X-Request-ID", str(uuid.uuid4()))
```

### Health Endpoint (required for all services)

```python
from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check() -> dict:
    return {"status": "healthy", "service": "agentflow"}
```

## Guidelines

### Always
- Use `uv sync` / `uv add` / `uv run` (NEVER pip)
- Include type hints on all functions
- Use Pydantic for request/response validation
- Add correlation_id to all log entries
- Use async/await for I/O operations
- Write pytest tests for new endpoints
- Expose `/health` endpoint

### Ask First
- Adding new dependencies (check if similar exists)
- Creating new services or routers
- Database schema changes (user handles migrations)
- RabbitMQ exchange/queue changes

### Never
- Use `pip install` or `requirements.txt`
- Skip type hints
- Use synchronous blocking I/O in async functions
- Hardcode secrets (use environment variables)
- Delete existing tests to make CI pass

## Commands

```bash
# Development
uv run python server.py --host 0.0.0.0 --port 5000 --reload

# Testing
uv run pytest                           # All tests
uv run pytest -m "not slow"             # Fast tests only
uv run pytest tests/test_feature.py     # Single file
uv run pytest --cov                     # With coverage (target 95%)

# Quality
uv run mypy .                           # Type checking
uv run ruff check .                     # Linting
uv run ruff check . --fix               # Auto-fix lint issues

# Docker (from deployment/)
docker compose up -d --build agentflow
docker compose logs -f agentflow
```

## Reference Files

| Purpose | Path |
|---------|------|
| Router example | `apps/api/src/routers/` |
| Service pattern | `apps/api/src/services/` |
| Pydantic models | `apps/api/src/models/` |
| Health endpoint | `apps/api/server.py` |
| Test examples | `apps/api/tests/` |
| UV config | `apps/api/pyproject.toml` |
