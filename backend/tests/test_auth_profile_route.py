"""Tests for Phase 1 auth and profile foundation."""

from fastapi.testclient import TestClient

from app.db.user_repository import user_repository
from app.main import app


client = TestClient(app)


def setup_function() -> None:
    user_repository.clear()


def _signup_user(
    *,
    full_name: str = "Alex Rivera",
    email: str = "alex@example.com",
    password: str = "safe-demo-password-123",
) -> dict:
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "full_name": full_name,
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 201
    return response.json()


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_signup_creates_user_and_returns_bearer_token() -> None:
    data = _signup_user(email="Alex.Rivera@Example.com")

    assert data["access_token"]
    assert data["token_type"] == "bearer"
    assert data["user"]["id"]
    assert data["user"]["full_name"] == "Alex Rivera"
    assert data["user"]["email"] == "alex.rivera@example.com"
    assert data["user"]["created_at"]
    assert data["user"]["updated_at"]


def test_signup_rejects_duplicate_email() -> None:
    _signup_user(email="Casey.PublicSafety@example.com")

    response = client.post(
        "/api/v1/auth/signup",
        json={
            "full_name": "Casey Public Safety",
            "email": "casey.publicsafety@example.com",
            "password": "another-safe-demo-password-123",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "A user already exists for this email."


def test_login_returns_token_for_valid_credentials() -> None:
    _signup_user(
        full_name="Jordan Lee",
        email="jordan@example.com",
        password="correct-demo-password-123",
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "JORDAN@example.com",
            "password": "correct-demo-password-123",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["access_token"]
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "jordan@example.com"


def test_login_rejects_invalid_credentials() -> None:
    _signup_user(
        email="invalid-login@example.com",
        password="correct-demo-password-123",
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "invalid-login@example.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_me_returns_authenticated_user() -> None:
    signup_data = _signup_user(
        full_name="Morgan Chen",
        email="morgan@example.com",
    )

    response = client.get(
        "/api/v1/auth/me",
        headers=_auth_headers(signup_data["access_token"]),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Morgan Chen"
    assert data["email"] == "morgan@example.com"


def test_me_requires_bearer_token() -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required."


def test_get_profile_returns_default_profile() -> None:
    signup_data = _signup_user(email="profile-default@example.com")

    response = client.get(
        "/api/v1/profile",
        headers=_auth_headers(signup_data["access_token"]),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == signup_data["user"]["id"]
    assert data["role"] is None
    assert data["state"] is None
    assert data["zip_code"] is None
    assert data["alert_interests"] == []
    assert data["alert_frequency"] is None
    assert data["report_style"] == "simple"


def test_update_profile_persists_preferences() -> None:
    signup_data = _signup_user(email="profile-update@example.com")
    headers = _auth_headers(signup_data["access_token"])

    update_response = client.put(
        "/api/v1/profile",
        headers=headers,
        json={
            "role": "consumer",
            "state": "mn",
            "zip_code": "55401",
            "alert_interests": [
                " insulin pump ",
                "CPAP",
                "insulin pump",
                "glucose meter",
            ],
            "alert_frequency": "weekly",
            "report_style": "technical",
        },
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["user_id"] == signup_data["user"]["id"]
    assert updated["role"] == "consumer"
    assert updated["state"] == "MN"
    assert updated["zip_code"] == "55401"
    assert updated["alert_interests"] == [
        "insulin pump",
        "CPAP",
        "glucose meter",
    ]
    assert updated["alert_frequency"] == "weekly"
    assert updated["report_style"] == "technical"

    get_response = client.get("/api/v1/profile", headers=headers)

    assert get_response.status_code == 200
    assert get_response.json()["alert_interests"] == [
        "insulin pump",
        "CPAP",
        "glucose meter",
    ]
