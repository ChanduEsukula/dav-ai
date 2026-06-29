"""Small signed bearer-token helper for DavAI portfolio-demo auth."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass
from uuid import UUID


DEFAULT_TOKEN_TTL_SECONDS = 60 * 60 * 24 * 7
DEFAULT_DEMO_SECRET = "dav-ai-local-demo-secret-change-me"


class AuthTokenError(ValueError):
    """Raised when a bearer token cannot be trusted."""


@dataclass(frozen=True)
class AuthTokenPayload:
    user_id: UUID
    email: str
    expires_at: int


def _secret() -> bytes:
    return os.getenv("AUTH_SECRET_KEY", DEFAULT_DEMO_SECRET).encode("utf-8")


def _base64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _sign(payload_part: str) -> str:
    digest = hmac.new(
        _secret(),
        payload_part.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return _base64url_encode(digest)


def create_auth_token(
    *,
    user_id: UUID,
    email: str,
    ttl_seconds: int = DEFAULT_TOKEN_TTL_SECONDS,
) -> str:
    """Create a compact signed bearer token."""

    expires_at = int(time.time()) + ttl_seconds
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expires_at,
    }
    payload_part = _base64url_encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    signature = _sign(payload_part)
    return f"{payload_part}.{signature}"


def verify_auth_token(token: str) -> AuthTokenPayload:
    """Verify and decode a signed bearer token."""

    try:
        payload_part, signature = token.split(".", 1)
    except ValueError as exc:
        raise AuthTokenError("Invalid bearer token format.") from exc

    expected_signature = _sign(payload_part)
    if not hmac.compare_digest(signature, expected_signature):
        raise AuthTokenError("Invalid bearer token signature.")

    try:
        payload = json.loads(_base64url_decode(payload_part))
        user_id = UUID(str(payload["sub"]))
        email = str(payload["email"])
        expires_at = int(payload["exp"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise AuthTokenError("Invalid bearer token payload.") from exc

    if expires_at <= int(time.time()):
        raise AuthTokenError("Bearer token has expired.")

    return AuthTokenPayload(
        user_id=user_id,
        email=email,
        expires_at=expires_at,
    )
