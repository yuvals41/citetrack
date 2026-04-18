#!/bin/bash
set -e

if [ ! -f /app/.venv/pyvenv.cfg ]; then
    echo "==> Creating venv..."
    uv venv /app/.venv
fi

if [ ! -f /app/.venv/.docker-synced ] || \
   [ /app/pyproject.toml -nt /app/.venv/.docker-synced ]; then
    echo "==> Syncing dependencies..."
    UV_INDEX_SOLARAAI_USERNAME=aws \
    UV_INDEX_SOLARAAI_PASSWORD="${CODEARTIFACT_AUTH_TOKEN:-}" \
    uv sync --frozen --no-dev 2>&1 || true
    touch /app/.venv/.docker-synced
fi

if [ ! -L /app/.venv/lib/python3.12/site-packages/prisma ]; then
    echo "==> Linking prisma client..."
    ln -sf /stanley/repos/prisma/dist/client-python \
           /app/.venv/lib/python3.12/site-packages/prisma
fi

if ! python -c "import tomlkit" 2>/dev/null; then
    uv pip install tomlkit 2>/dev/null
fi

PRISMA_HASH="393aa359c9ad4a4bb28630fb5613f9c281cde053"
ENGINE_DIR="/app/data/prisma-engines"
mkdir -p "$ENGINE_DIR"
if [ ! -f "$ENGINE_DIR/prisma-query-engine-debian-openssl-3.0.x" ]; then
    echo "==> Downloading Prisma query engine..."
    curl -sL "https://binaries.prisma.sh/all_commits/${PRISMA_HASH}/debian-openssl-3.0.x/query-engine.gz" \
        | gunzip > "$ENGINE_DIR/prisma-query-engine-debian-openssl-3.0.x"
    chmod +x "$ENGINE_DIR/prisma-query-engine-debian-openssl-3.0.x"
fi
OPENSSL_VER=$(openssl version | grep -oP '\d+\.\d+' | head -1)
ln -sf "$ENGINE_DIR/prisma-query-engine-debian-openssl-3.0.x" \
       "/app/prisma-query-engine-debian-openssl-3.0.x"
ln -sf "$ENGINE_DIR/prisma-query-engine-debian-openssl-3.0.x" \
       "/app/prisma-query-engine-debian-openssl-${OPENSSL_VER}.x"

if [ ! -d /app/.web/node_modules ]; then
    echo "==> Initializing Reflex frontend (first run)..."
    reflex init
fi

exec reflex run --loglevel "${LOG_LEVEL:-info}"
