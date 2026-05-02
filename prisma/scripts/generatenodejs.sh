#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRISMA_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PRISMA_ROOT"

rm -rf client-node

npx prisma generate --schema=prisma/schema --generator nodejs
