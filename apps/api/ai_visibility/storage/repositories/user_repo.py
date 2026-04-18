# pyright: reportAny=false, reportUnknownVariableType=false

"""Phase 3d file-backed user↔workspace repository.

This is a temporary stub until real Prisma tables exist for users and
workspace ownership. The public interface is intentionally Prisma-ready so the
implementation can be swapped later without changing route logic.
"""

from __future__ import annotations

import json
from pathlib import Path

_storage_path = Path(__file__).resolve().parents[3] / ".cache" / "user_associations.json"


class UserRepository:
    def __init__(self, storage_path: Path | None = None) -> None:
        self._storage_path: Path = storage_path or _storage_path

    def add_workspace_to_user(self, user_id: str, workspace_slug: str) -> None:
        associations = self._read_associations()
        user_workspaces = associations.get(user_id, [])
        if workspace_slug not in user_workspaces:
            user_workspaces.append(workspace_slug)
            associations[user_id] = user_workspaces
            self._write_associations(associations)

    def list_workspaces_for_user(self, user_id: str) -> list[str]:
        associations = self._read_associations()
        return list(associations.get(user_id, []))

    def get_workspace_owner(self, workspace_slug: str) -> str | None:
        associations = self._read_associations()
        for user_id, workspace_slugs in associations.items():
            if workspace_slug in workspace_slugs:
                return user_id
        return None

    def user_owns_workspace(self, user_id: str, slug: str) -> bool:
        return slug in self.list_workspaces_for_user(user_id)

    def _read_associations(self) -> dict[str, list[str]]:
        if not self._storage_path.exists():
            return {}

        try:
            payload_raw: object = json.loads(self._storage_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

        if not isinstance(payload_raw, dict):
            return {}

        payload = payload_raw
        associations: dict[str, list[str]] = {}
        for user_id, workspace_slugs in payload.items():
            if not isinstance(user_id, str) or not isinstance(workspace_slugs, list):
                continue
            normalized_slugs = [slug for slug in workspace_slugs if isinstance(slug, str)]
            associations[user_id] = normalized_slugs
        return associations

    def _write_associations(self, associations: dict[str, list[str]]) -> None:
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        _ = self._storage_path.write_text(
            json.dumps(associations, indent=2, sort_keys=True),
            encoding="utf-8",
        )
