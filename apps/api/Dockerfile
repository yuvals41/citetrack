FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

RUN apt-get update \
    && apt-get install --no-install-recommends -y ca-certificates curl libatomic1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
COPY apps/api/pyproject.toml ./apps/api/
COPY prisma ./prisma

RUN uv sync --all-packages --frozen --no-dev --no-install-project

COPY apps/api/ai_visibility ./apps/api/ai_visibility

RUN bash prisma/scripts/generatepython.sh \
    && uv pip install -e ./prisma/client-python


FROM python:3.13-slim AS runtime

ARG BUILD_DATE
ARG VCS_REF

LABEL org.opencontainers.image.title="ai-visibility" \
      org.opencontainers.image.description="AI visibility FastAPI service" \
      org.opencontainers.image.version="0.1.0" \
      org.opencontainers.image.source="https://github.com/solaraai/ai-visibility" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.licenses="Proprietary"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:${PATH}" \
    UV_NO_SYNC=1 \
    DATABASE_URL="postgresql://ai_visibility:ai_visibility@postgres:5432/ai_visibility_db" \
    PROVIDERS="openai,anthropic" \
    LOG_LEVEL="INFO"

WORKDIR /app

RUN apt-get update \
    && apt-get install --no-install-recommends -y ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv \
    && groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --create-home --shell /usr/sbin/nologin app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/pyproject.toml /app/uv.lock ./
COPY --from=builder /app/apps/api/pyproject.toml ./apps/api/
COPY --from=builder /app/apps/api/ai_visibility ./apps/api/ai_visibility
COPY --from=builder /app/prisma ./prisma

RUN mkdir -p /app/data \
    && chown -R app:app /app

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=5)" || exit 1

CMD ["uv", "run", "uvicorn", "ai_visibility.api.routes:app", "--host", "0.0.0.0", "--port", "8000"]
