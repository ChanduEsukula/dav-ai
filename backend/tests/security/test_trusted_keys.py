import pytest

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)

from app.security.staging_authorization import AuthorizationRejected
from app.security.trusted_keys import TrustedKeyRegistry


def test_trusted_key_resolves():
    key = Ed25519PrivateKey.generate().public_key()

    registry = TrustedKeyRegistry({"test-key-001": key})

    assert registry.resolve("test-key-001") is key


def test_unknown_key_rejected():
    key = Ed25519PrivateKey.generate().public_key()

    registry = TrustedKeyRegistry({"test-key-001": key})

    with pytest.raises(AuthorizationRejected):
        registry.resolve("attacker-key")


def test_empty_registry_rejected():
    with pytest.raises(ValueError):
        TrustedKeyRegistry({})


def test_invalid_key_identifier_rejected():
    key = Ed25519PrivateKey.generate().public_key()

    with pytest.raises(ValueError):
        TrustedKeyRegistry({"": key})


def test_invalid_public_key_rejected():
    with pytest.raises(ValueError):
        TrustedKeyRegistry({"test-key-001": "not-a-public-key"})


def test_multiple_trusted_keys():
    first = Ed25519PrivateKey.generate().public_key()
    second = Ed25519PrivateKey.generate().public_key()

    registry = TrustedKeyRegistry({
        "test-key-001": first,
        "test-key-002": second,
    })

    assert registry.resolve("test-key-001") is first
    assert registry.resolve("test-key-002") is second
