"""Clerk JWT authentication helpers for FastAPI dependencies.

This module verifies Clerk-issued Bearer tokens by:
1. Reading the unverified JWT header to extract the ``kid``.
2. Fetching and caching the Clerk JWKS document.
3. Resolving the matching RSA public key from the JWKS.
4. Verifying the token signature and time-based claims.
5. Enforcing the expected issuer and ``azp`` (authorized party) when configured.

Expected Clerk claims include:
- ``sub``: Clerk user id
- ``sid``: Clerk session id
- ``iss``: Clerk issuer URL
- ``azp``: authorized frontend origin
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Annotated, Any

import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.algorithms import RSAAlgorithm

CLERK_JWKS_URL = os.getenv("CLERK_JWKS_URL", "")
CLERK_JWT_ISSUER = os.getenv("CLERK_JWT_ISSUER")
CLERK_AUTHORIZED_PARTIES = [
    party.strip() for party in os.getenv("CLERK_AUTHORIZED_PARTIES", "").split(",") if party.strip()
]

_JWKS_CACHE_TTL_SECONDS = 3600
_jwks_cache: dict[str, Any] = {}
_jwks_fetched_at: float = 0.0

bearer_scheme = HTTPBearer(auto_error=True)


@dataclass(slots=True)
class ClerkAuthContext:
    user_id: str
    session_id: str | None
    issuer: str | None
    payload: dict[str, Any]


def _configured_issuer() -> str | None:
    return os.getenv("CLERK_JWT_ISSUER") or CLERK_JWT_ISSUER


def _configured_authorized_parties() -> list[str]:
    env_value = os.getenv("CLERK_AUTHORIZED_PARTIES")
    if env_value is not None:
        return [party.strip() for party in env_value.split(",") if party.strip()]
    return CLERK_AUTHORIZED_PARTIES


def _configured_jwks_url() -> str:
    return os.getenv("CLERK_JWKS_URL") or CLERK_JWKS_URL


def _fetch_jwks() -> dict[str, Any]:
    global _jwks_cache, _jwks_fetched_at

    now = time.time()
    if _jwks_cache and (now - _jwks_fetched_at) < _JWKS_CACHE_TTL_SECONDS:
        return _jwks_cache

    jwks_url = _configured_jwks_url()
    if not jwks_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Clerk JWKS URL is not configured",
        )

    response = httpx.get(jwks_url, timeout=10.0)
    response.raise_for_status()
    jwks = response.json()
    if not isinstance(jwks, dict):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Invalid Clerk JWKS response")

    _jwks_cache = jwks
    _jwks_fetched_at = now
    return jwks


def _get_public_key(token: str) -> Any:
    try:
        header = jwt.get_unverified_header(token)
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {exc}") from exc

    kid = header.get("kid")
    if not isinstance(kid, str) or not kid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token: missing kid header")

    jwks = _fetch_jwks()
    keys = jwks.get("keys", [])
    if not isinstance(keys, list):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Invalid Clerk JWKS response")

    for key_data in keys:
        if isinstance(key_data, dict) and key_data.get("kid") == kid:
            return RSAAlgorithm.from_jwk(json.dumps(key_data))

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token: no matching JWK for kid")


def verify_clerk_token(token: str) -> dict[str, Any]:
    issuer = _configured_issuer()
    authorized_parties = _configured_authorized_parties()

    try:
        public_key = _get_public_key(token)
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            issuer=issuer if issuer else None,
            options={
                "verify_exp": True,
                "verify_nbf": True,
                "verify_iss": bool(issuer),
                "verify_aud": False,
            },
        )
        if not isinstance(payload, dict):
            raise jwt.InvalidTokenError("Decoded payload is not an object")

        azp = payload.get("azp")
        if not isinstance(azp, str) or azp not in authorized_parties:
            raise jwt.InvalidTokenError("Invalid authorized party")

        return payload
    except HTTPException:
        raise
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not fetch Clerk JWKS",
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {exc}") from exc


def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> str:
    payload = verify_clerk_token(credentials.credentials)
    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token: missing sub claim")
    return user_id


CurrentUserId = Annotated[str, Depends(get_current_user_id)]


def get_auth_context(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> ClerkAuthContext:
    payload = verify_clerk_token(credentials.credentials)
    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token: missing sub claim")

    session_id = payload.get("sid")
    issuer = payload.get("iss")

    return ClerkAuthContext(
        user_id=user_id,
        session_id=session_id if isinstance(session_id, str) else None,
        issuer=issuer if isinstance(issuer, str) else None,
        payload=payload,
    )
