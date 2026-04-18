"""Async Prisma client singleton for ai-visibility."""

# pyright: reportAny=false, reportExplicitAny=false, reportUnnecessaryCast=false

from importlib import import_module
from typing import Any, cast

Prisma = Any

_client: Any | None = None


async def get_prisma() -> Prisma:
    """Get or create the shared Prisma client, connecting if needed."""
    global _client
    if _client is None:
        prisma_module = import_module("prisma")
        client_cls = getattr(prisma_module, "Prisma")
        _client = client_cls()

    client = _client
    if client is None:
        raise RuntimeError("Prisma client was not initialized")
    if not client.is_connected():
        await client.connect()
    return cast(Prisma, client)


async def disconnect_prisma() -> None:
    """Disconnect the shared Prisma client."""
    global _client
    if _client is not None and _client.is_connected():
        await _client.disconnect()
        _client = None
