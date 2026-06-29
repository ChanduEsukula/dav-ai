from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.db.user_repository import UserRecord, UserRepositoryError, user_repository
from app.schemas.auth import AuthLoginRequest, AuthResponse, AuthSignupRequest, AuthUser
from app.services.auth_context import AuthenticatedUser, get_current_user
from app.services.auth_passwords import PasswordHashError, hash_password, verify_password
from app.services.auth_tokens import create_auth_token


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _auth_user(user: UserRecord) -> AuthUser:
    return AuthUser(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def _auth_response(user: UserRecord) -> AuthResponse:
    return AuthResponse(
        access_token=create_auth_token(user_id=user.id, email=user.email),
        user=_auth_user(user),
    )


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: AuthSignupRequest) -> AuthResponse:
    try:
        password_hash = hash_password(payload.password)
        user = user_repository.create_user(
            full_name=payload.full_name,
            email=payload.email,
            password_hash=password_hash,
        )
        user_repository.create_default_profile(user.id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except UserRepositoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User persistence is unavailable.",
        ) from exc

    return _auth_response(user)


@router.post("/login", response_model=AuthResponse)
def login(payload: AuthLoginRequest) -> AuthResponse:
    try:
        user = user_repository.get_user_by_email(payload.email)
        password_matches = (
            verify_password(payload.password, user.password_hash)
            if user is not None
            else False
        )
    except (PasswordHashError, UserRepositoryError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is temporarily unavailable.",
        ) from exc

    if user is None or not password_matches:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    return _auth_response(user)


@router.get("/me", response_model=AuthUser)
def me(current_user: AuthenticatedUser = Depends(get_current_user)) -> AuthUser:
    user = user_repository.get_user_by_id(current_user.id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
        )
    return _auth_user(user)
