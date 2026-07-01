from uuid import uuid4

import pytest

from app.services.auth_tokens import AuthTokenError, create_auth_token, verify_auth_token


def test_demo_auth_secret_is_allowed_for_local_development(monkeypatch):
    monkeypatch.delenv("AUTH_SECRET_KEY", raising=False)
    monkeypatch.delenv("DAVAI_ENV", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("PYTHON_ENV", raising=False)
    monkeypatch.delenv("RENDER", raising=False)

    user_id = uuid4()
    token = create_auth_token(user_id=user_id, email="demo@example.com")

    payload = verify_auth_token(token)

    assert payload.user_id == user_id
    assert payload.email == "demo@example.com"


def test_missing_auth_secret_fails_closed_in_deployed_environment(monkeypatch):
    monkeypatch.delenv("AUTH_SECRET_KEY", raising=False)
    monkeypatch.setenv("DAVAI_ENV", "production")

    with pytest.raises(AuthTokenError, match="AUTH_SECRET_KEY must be configured"):
        create_auth_token(user_id=uuid4(), email="demo@example.com")
