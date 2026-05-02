# pyright: reportMissingImports=false, reportUnknownParameterType=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false

from __future__ import annotations

import socket
from pathlib import Path

import pytest

BROWSER_E2E_FILES = {"test_full_e2e.py", "test_ui_browser.py"}


def _frontend_is_reachable(host: str = "127.0.0.1", port: int = 3000, timeout: float = 0.2) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    if _frontend_is_reachable():
        return

    skip_browser_e2e = pytest.mark.skip(reason="requires apps/web dev server at http://localhost:3000")
    for item in items:
        if Path(str(item.fspath)).name in BROWSER_E2E_FILES:
            item.add_marker(skip_browser_e2e)
