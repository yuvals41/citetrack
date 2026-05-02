import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Protocol, cast

from fastapi.testclient import TestClient

from ai_visibility.api import create_app
from ai_visibility.degraded import DegradedReason, DegradedState, is_degraded
from ai_visibility.storage.database import Database

ROOT = Path(__file__).resolve().parents[2]


class MonkeyPatchLike(Protocol):
    def setattr(self, target: object, name: str, value: object) -> None: ...


def _assert_degraded_payload(payload: dict[str, object]) -> dict[str, object]:
    assert "degraded" in payload
    degraded_value = payload["degraded"]
    assert isinstance(degraded_value, dict)
    degraded = cast(dict[str, object], degraded_value)
    assert set(degraded.keys()) == {"reason", "message", "recoverable"}
    assert isinstance(degraded["reason"], str)
    assert isinstance(degraded["message"], str)
    assert isinstance(degraded["recoverable"], bool)
    return degraded


def _run_cli(*args: str, env: dict[str, str]) -> dict[str, object]:
    result = subprocess.run(
        [sys.executable, "-m", "ai_visibility.cli", *args, "--format", "json"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "Traceback" not in result.stdout
    assert "Traceback" not in result.stderr
    payload = cast(dict[str, object], json.loads(result.stdout))
    return payload


def test_degraded_state_model_validates() -> None:
    state = DegradedState(
        reason=DegradedReason.MISSING_API_KEY,
        message="Missing provider credential",
        recoverable=True,
        context={"provider": "openai"},
    )

    assert state.reason == DegradedReason.MISSING_API_KEY
    assert state.message == "Missing provider credential"
    assert state.recoverable is True
    assert state.context == {"provider": "openai"}


def test_is_degraded_helper() -> None:
    assert is_degraded(None) is False
    assert (
        is_degraded(
            DegradedState(
                reason=DegradedReason.PROVIDER_FAILURE,
                message="Provider unavailable",
                recoverable=True,
            )
        )
        is True
    )


def test_health_returns_degraded_json_when_db_unavailable(monkeypatch: MonkeyPatchLike) -> None:
    async def broken_get_prisma() -> object:
        raise sqlite3.OperationalError("db offline")

    monkeypatch.setattr("ai_visibility.api.routes.get_prisma", broken_get_prisma)

    client = TestClient(create_app())
    response = client.get("/api/v1/health")
    payload = cast(dict[str, object], response.json())

    assert response.status_code == 200
    degraded = _assert_degraded_payload(payload)
    assert degraded["reason"] == DegradedReason.PROVIDER_FAILURE.value


def test_cli_run_scan_unknown_workspace_returns_degraded_json(tmp_path: Path) -> None:
    env = {**os.environ, "DB_PATH": str(tmp_path / "resilience.db")}

    payload = _run_cli("run-scan", "--workspace", "nonexistent", env=env)

    degraded = _assert_degraded_payload(payload)
    assert degraded["reason"] == DegradedReason.WORKSPACE_NOT_FOUND.value


def test_cli_summarize_latest_unknown_workspace_returns_degraded_json(tmp_path: Path) -> None:
    env = {**os.environ, "DB_PATH": str(tmp_path / "resilience.db")}

    payload = _run_cli("summarize-latest", "--workspace", "nonexistent", env=env)

    degraded = _assert_degraded_payload(payload)
    assert degraded["reason"] == DegradedReason.WORKSPACE_NOT_FOUND.value


def test_cli_recommend_latest_unknown_workspace_returns_degraded_json(tmp_path: Path) -> None:
    env = {**os.environ, "DB_PATH": str(tmp_path / "resilience.db")}

    payload = _run_cli("recommend-latest", "--workspace", "nonexistent", env=env)

    degraded = _assert_degraded_payload(payload)
    assert degraded["reason"] == DegradedReason.WORKSPACE_NOT_FOUND.value
