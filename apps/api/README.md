# @citetrack/api

FastAPI backend for Citetrack AI.

## Development

```bash
# From monorepo root
uv sync

# Run dev server
nx dev @citetrack/api
# or
cd apps/api && uv run uvicorn ai_visibility.api.app:app --reload --port 8000
```

## Tests

```bash
nx test @citetrack/api
```
