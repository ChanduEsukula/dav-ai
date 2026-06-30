"""Password hashing helpers for portfolio-demo authentication.

This module intentionally uses only the Python standard library so the auth
foundation can stay small and dependency-light for the demo sprint.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets


PASSWORD_HASH_ALGORITHM = "pbkdf2_sha256"
PASSWORD_HASH_ITERATIONS = 260_000
SALT_BYTES = 16


class PasswordHashError(ValueError):
    """Raised when a stored password hash is malformed."""


def hash_password(password: str) -> str:
    """Return a salted PBKDF2 password hash string."""

    salt = secrets.token_hex(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PASSWORD_HASH_ITERATIONS,
    ).hex()

    return f"{PASSWORD_HASH_ALGORITHM}${PASSWORD_HASH_ITERATIONS}${salt}${digest}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Return True when a plaintext password matches a stored PBKDF2 hash."""

    try:
        algorithm, iterations_raw, salt, expected_digest = stored_hash.split("$", 3)
        iterations = int(iterations_raw)
    except ValueError as exc:
        raise PasswordHashError("Stored password hash is malformed.") from exc

    if algorithm != PASSWORD_HASH_ALGORITHM or iterations <= 0 or not salt:
        raise PasswordHashError("Stored password hash uses an unsupported format.")

    actual_digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    ).hex()

    return hmac.compare_digest(actual_digest, expected_digest)
