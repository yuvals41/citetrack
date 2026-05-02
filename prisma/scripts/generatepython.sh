#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRISMA_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$PRISMA_ROOT/.." && pwd)"

cd "$PRISMA_ROOT"

PY="$(cd "$REPO_ROOT" && uv run python -c 'import sys; print(sys.executable)')"

# Upstream `prisma` is installed only to run the CLI, then removed in the trap
# because both packages register a `prisma` module and site-packages shadows
# the editable client. The trap fires on any exit so a failed generate doesn't
# leave the upstream package shadowing citetrack-prisma-client.
trap 'uv pip uninstall prisma --python "$PY" --quiet 2>/dev/null || true' EXIT

uv pip install -U prisma --python "$PY" --quiet

rm -rf client-python/prisma
mkdir -p client-python/prisma
touch client-python/prisma/__init__.py

"$PY" -m prisma generate --schema=prisma/schema --generator python

echo "Generated citetrack-prisma-client at $PRISMA_ROOT/client-python/prisma"
