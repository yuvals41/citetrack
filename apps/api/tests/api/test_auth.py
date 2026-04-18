"""Unit tests for Clerk JWT authentication helpers."""

# pyright: reportMissingImports=false

from __future__ import annotations

import time
from typing import Any

import httpx
import jwt as pyjwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from ai_visibility.api import auth as auth_module


def _encode_token(
    private_pem: str,
    *,
    claims: dict[str, Any] | None = None,
    kid: str | None = "test-kid-1",
) -> str:
    now = int(time.time())
    payload: dict[str, Any] = {
        "sub": "user_test_abc123",
        "iss": "https://test.clerk.accounts.dev",
        "azp": "http://localhost:3000",
        "sid": "sess_test_xyz",
        "exp": now + 60,
        "nbf": now - 10,
        "iat": now,
    }
    if claims:
        payload.update(claims)

    headers: dict[str, str] = {}
    if kid is not None:
        headers["kid"] = kid

    return pyjwt.encode(payload, private_pem, algorithm="RS256", headers=headers)


def test_valid_token_returns_user_id(
    clerk_test_token: str,
    mock_jwks,
    rsa_key_pair: dict[str, object],
) -> None:
    _ = rsa_key_pair
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=clerk_test_token)

    user_id = auth_module.get_current_user_id(credentials)

    assert user_id == "user_test_abc123"


def test_expired_token_raises_401(rsa_key_pair: dict[str, object], mock_jwks) -> None:
    _ = mock_jwks
    private_pem = str(rsa_key_pair["private_pem"])
    token = _encode_token(private_pem, claims={"exp": int(time.time()) - 5, "nbf": int(time.time()) - 10})

    with pytest.raises(HTTPException) as exc_info:
        auth_module.verify_clerk_token(token)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Token has expired"


def test_invalid_signature_raises_401(mock_jwks) -> None:
    _ = mock_jwks
    other_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    other_private_pem = other_private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    token = _encode_token(other_private_pem)

    with pytest.raises(HTTPException) as exc_info:
        auth_module.verify_clerk_token(token)

    assert exc_info.value.status_code == 401
    assert "Invalid token:" in str(exc_info.value.detail)


def test_missing_bearer_returns_401(unauth_client) -> None:
    response = unauth_client.get("/api/v1/workspaces")

    assert response.status_code in {401, 403}


def test_bad_azp_raises_401(rsa_key_pair: dict[str, object], mock_jwks) -> None:
    _ = mock_jwks
    token = _encode_token(str(rsa_key_pair["private_pem"]), claims={"azp": "http://evil.example"})

    with pytest.raises(HTTPException) as exc_info:
        auth_module.verify_clerk_token(token)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid token: Invalid authorized party"


def test_missing_kid_raises_401(rsa_key_pair: dict[str, object], mock_jwks) -> None:
    _ = mock_jwks
    token = _encode_token(str(rsa_key_pair["private_pem"]), kid=None)

    with pytest.raises(HTTPException) as exc_info:
        auth_module.verify_clerk_token(token)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid token: missing kid header"


def test_jwks_unreachable_raises_503(monkeypatch: pytest.MonkeyPatch, rsa_key_pair: dict[str, object]) -> None:
    token = _encode_token(str(rsa_key_pair["private_pem"]))

    monkeypatch.setenv("CLERK_JWKS_URL", "https://test.clerk.accounts.dev/.well-known/jwks.json")
    monkeypatch.setenv("CLERK_JWT_ISSUER", "https://test.clerk.accounts.dev")
    monkeypatch.setenv("CLERK_AUTHORIZED_PARTIES", "http://localhost:3000")
    auth_module.CLERK_JWKS_URL = "https://test.clerk.accounts.dev/.well-known/jwks.json"
    auth_module.CLERK_JWT_ISSUER = "https://test.clerk.accounts.dev"
    auth_module.CLERK_AUTHORIZED_PARTIES = ["http://localhost:3000"]
    auth_module._jwks_cache = {}
    auth_module._jwks_fetched_at = 0.0

    def _raise_http_error(*_args: object, **_kwargs: object) -> object:
        raise httpx.ConnectError("boom")

    monkeypatch.setattr(auth_module.httpx, "get", _raise_http_error)

    with pytest.raises(HTTPException) as exc_info:
        auth_module.verify_clerk_token(token)

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "Could not fetch Clerk JWKS"


def test_missing_sub_claim_raises_401(
    monkeypatch: pytest.MonkeyPatch,
    rsa_key_pair: dict[str, object],
    mock_jwks,
) -> None:
    _ = mock_jwks
    token = _encode_token(str(rsa_key_pair["private_pem"]), claims={"sub": "user_test_abc123"})
    payload = auth_module.verify_clerk_token(token)
    payload.pop("sub", None)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    monkeypatch.setattr(auth_module, "verify_clerk_token", lambda _token: payload)

    with pytest.raises(HTTPException) as exc_info:
        auth_module.get_current_user_id(credentials)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid token: missing sub claim"


def test_auth_context_exposes_session_and_issuer(clerk_test_token: str, mock_jwks) -> None:
    _ = mock_jwks
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=clerk_test_token)

    context = auth_module.get_auth_context(credentials)

    assert context.user_id == "user_test_abc123"
    assert context.session_id == "sess_test_xyz"
    assert context.issuer == "https://test.clerk.accounts.dev"
    assert context.payload["sub"] == "user_test_abc123"
