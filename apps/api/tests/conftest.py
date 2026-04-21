"""Pytest configuration and shared fixtures for ai-visibility tests."""

# pyright: reportMissingImports=false

import base64
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock, MagicMock, patch

import jwt as pyjwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def _stub_row(**overrides: object) -> SimpleNamespace:
    """Return a SimpleNamespace that satisfies any ``_*_from_model`` converter.

    Every field used across workspace_repo, run_repo, mention_repo,
    metric_repo, and scan_evidence_repo is pre-populated with a sensible
    default.  Individual tests can override via ``return_value`` or
    ``side_effect`` as needed.
    """
    now = datetime.now(timezone.utc)
    defaults: dict[str, object] = {
        "id": str(uuid.uuid4()),
        "slug": "stub",
        "brandName": "Stub Brand",
        "city": "",
        "region": "",
        "country": "",
        "createdAt": now,
        "updatedAt": now,
        # Run fields
        "workspaceId": str(uuid.uuid4()),
        "brandId": str(uuid.uuid4()),
        "status": "completed",
        "provider": "openai",
        "mentionCount": 0,
        "visibilityScore": 0.0,
        "startedAt": now,
        "completedAt": now,
        # Mention fields
        "runId": str(uuid.uuid4()),
        "promptTemplate": "",
        "llmResponse": "",
        "mentioned": False,
        "sentiment": "neutral",
        "rank": 0,
        "citationUrl": "",
        "context": "",
        "modelName": "",
        "modelVersion": "",
        "promptVersion": "",
        # Metric snapshot fields
        "formulaVersion": "v1",
        "citationCoverage": 0.0,
        "competitorWins": 0,
        # Scan evidence fields
        "scanJobId": str(uuid.uuid4()),
        "scanExecutionId": str(uuid.uuid4()),
        "promptExecutionId": str(uuid.uuid4()),
        "observationId": str(uuid.uuid4()),
        "template": "",
        "renderedPrompt": "",
        "strategyVersion": "v1",
        "executionMs": 0,
        "rawResponse": "",
        "adapter": "stub",
        "promptExecutionCitationId": str(uuid.uuid4()),
        "url": "",
        "text": "",
        "kind": "citation",
        "name": "",
        "period": "daily",
        "description": "",
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_model_mock() -> MagicMock:
    model = MagicMock()
    model.create = AsyncMock(side_effect=lambda **kw: _stub_row())
    model.find_unique = AsyncMock(return_value=None)
    model.find_first = AsyncMock(return_value=None)
    model.find_many = AsyncMock(return_value=[])
    model.update = AsyncMock(side_effect=lambda **kw: _stub_row())
    model.upsert = AsyncMock(side_effect=lambda **kw: _stub_row())
    model.delete = AsyncMock(return_value=None)
    model.delete_many = AsyncMock(return_value=None)
    model.count = AsyncMock(return_value=0)
    return model


def _base64url_uint(value: int) -> str:
    raw = value.to_bytes((value.bit_length() + 7) // 8, byteorder="big")
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


@pytest.fixture
def mock_prisma() -> MagicMock:
    """Mock Prisma client with all ai-visibility models (async CRUD methods)."""
    prisma = MagicMock()
    prisma.is_connected.return_value = True

    prisma.aivisworkspace = _make_model_mock()
    prisma.aivisrun = _make_model_mock()
    prisma.aivismention = _make_model_mock()
    prisma.aivismetricsnapshot = _make_model_mock()
    prisma.aivisscanevidence = _make_model_mock()
    prisma.aivisbrand = _make_model_mock()
    prisma.aiviscompetitor = _make_model_mock()

    prisma.aivisscanjob = _make_model_mock()
    prisma.aivisscanexecution = _make_model_mock()
    prisma.aivispromptexecution = _make_model_mock()
    prisma.aivisobservation = _make_model_mock()
    prisma.aivispromptexecutioncitation = _make_model_mock()

    prisma.query_raw = AsyncMock(return_value=[])
    prisma.execute_raw = AsyncMock(return_value=None)
    prisma.disconnect = AsyncMock(return_value=None)
    prisma.connect = AsyncMock(return_value=None)

    return prisma


@pytest.fixture
def patch_get_prisma(mock_prisma: MagicMock):
    """Patch get_prisma() to return mock_prisma for the test duration."""

    async def _fake_get_prisma():
        return mock_prisma

    with (
        patch("ai_visibility.storage.prisma_connection.get_prisma", new=_fake_get_prisma),
        patch("ai_visibility.api.routes.get_prisma", new=_fake_get_prisma),
        patch("ai_visibility.pixel.events.get_prisma", new=_fake_get_prisma),
        patch("ai_visibility.runs.orchestrator.get_prisma", new=_fake_get_prisma),
        patch("ai_visibility.cli.get_prisma", new=_fake_get_prisma),
    ):
        yield mock_prisma


@pytest.fixture(scope="session")
def rsa_key_pair() -> dict[str, object]:
    """Generate an RSA key pair once per session for signing test JWTs."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    public_numbers = private_key.public_key().public_numbers()
    jwk = {
        "kty": "RSA",
        "use": "sig",
        "alg": "RS256",
        "kid": "test-kid-1",
        "n": _base64url_uint(public_numbers.n),
        "e": _base64url_uint(public_numbers.e),
    }
    return {
        "private_key": private_key,
        "private_pem": private_pem,
        "jwks": {"keys": [jwk]},
    }


@pytest.fixture
def clerk_test_token(rsa_key_pair: dict[str, object]) -> str:
    """Produce a valid Clerk-shaped JWT signed with the test RSA key."""
    now = int(time.time())
    payload = {
        "sub": "user_test_abc123",
        "iss": "https://test.clerk.accounts.dev",
        "azp": "http://localhost:3000",
        "sid": "sess_test_xyz",
        "exp": now + 60,
        "nbf": now - 10,
        "iat": now,
    }
    private_pem = str(rsa_key_pair["private_pem"])
    return pyjwt.encode(payload, private_pem, algorithm="RS256", headers={"kid": "test-kid-1"})


@pytest.fixture
def mock_jwks_response(rsa_key_pair: dict[str, object]) -> dict[str, object]:
    """Return the JWKS payload used by Clerk auth tests."""
    return cast(dict[str, object], rsa_key_pair["jwks"])


@pytest.fixture
def mock_jwks(
    monkeypatch: pytest.MonkeyPatch,
    mock_jwks_response: dict[str, object],
):
    """Patch Clerk auth settings and JWKS cache to use local test keys."""
    from ai_visibility.api import auth as auth_module

    monkeypatch.setenv("CLERK_JWKS_URL", "https://test.clerk.accounts.dev/.well-known/jwks.json")
    monkeypatch.setenv("CLERK_JWT_ISSUER", "https://test.clerk.accounts.dev")
    monkeypatch.setenv("CLERK_AUTHORIZED_PARTIES", "http://localhost:3000")

    auth_module.CLERK_JWKS_URL = "https://test.clerk.accounts.dev/.well-known/jwks.json"
    auth_module.CLERK_JWT_ISSUER = "https://test.clerk.accounts.dev"
    auth_module.CLERK_AUTHORIZED_PARTIES = ["http://localhost:3000"]
    auth_module._jwks_cache = mock_jwks_response
    auth_module._jwks_fetched_at = time.time()

    yield

    auth_module._jwks_cache = {}
    auth_module._jwks_fetched_at = 0.0


@pytest.fixture
def auth_client(clerk_test_token: str, mock_jwks, patch_get_prisma) -> TestClient:
    _ = patch_get_prisma
    _ = mock_jwks
    from ai_visibility.api import create_app

    client = TestClient(create_app())
    client.headers.update({"Authorization": f"Bearer {clerk_test_token}"})
    return client


@pytest.fixture
def unauth_client(patch_get_prisma) -> TestClient:
    _ = patch_get_prisma
    from ai_visibility.api import create_app

    return TestClient(create_app())
