# pyright: reportAny=false, reportUnknownVariableType=false

"""File-backed brand alias repository.

Temporary stub: the AiVisBrand Prisma model does not currently have an
`aliases` column, but the frontend + API contract expect aliases to round-trip.
Following the same pattern as `UserRepository`, this repo persists aliases to
a local JSON file keyed by `workspace_id` until real Prisma schema support
exists.

The public interface is intentionally simple so it can be swapped for a
Prisma-backed implementation without touching callers.
"""

from __future__ import annotations

import json
from pathlib import Path

_storage_path = Path(__file__).resolve().parents[3] / ".cache" / "brand_aliases.json"


class BrandAliasRepository:
    def __init__(self, storage_path: Path | None = None) -> None:
        self._storage_path: Path = storage_path or _storage_path

    def get_aliases(self, workspace_id: str) -> list[str]:
        store = self._read_store()
        return list(store.get(workspace_id, []))

    def set_aliases(self, workspace_id: str, aliases: list[str]) -> list[str]:
        seen: set[str] = set()
        normalized: list[str] = []
        for raw in aliases:
            if not isinstance(raw, str):
                continue
            trimmed = raw.strip()
            if not trimmed or trimmed in seen:
                continue
            seen.add(trimmed)
            normalized.append(trimmed)
            if len(normalized) >= 10:
                break

        store = self._read_store()
        if normalized:
            store[workspace_id] = normalized
        else:
            store.pop(workspace_id, None)
        self._write_store(store)
        return normalized

    def delete_for_workspace(self, workspace_id: str) -> None:
        store = self._read_store()
        if workspace_id in store:
            store.pop(workspace_id)
            self._write_store(store)

    def _read_store(self) -> dict[str, list[str]]:
        if not self._storage_path.exists():
            return {}

        try:
            payload_raw: object = json.loads(self._storage_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

        if not isinstance(payload_raw, dict):
            return {}

        store: dict[str, list[str]] = {}
        for workspace_id, aliases in payload_raw.items():
            if not isinstance(workspace_id, str) or not isinstance(aliases, list):
                continue
            normalized = [alias for alias in aliases if isinstance(alias, str)]
            if normalized:
                store[workspace_id] = normalized
        return store

    def _write_store(self, store: dict[str, list[str]]) -> None:
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        _ = self._storage_path.write_text(
            json.dumps(store, indent=2, sort_keys=True),
            encoding="utf-8",
        )
