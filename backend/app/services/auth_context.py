from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Header, HTTPException, status

from app.db.user_repository import UserRepositoryError, user_repository
from app.services.auth_tokens import AuthTokenError, verify_auth_token


@dataclass(frozen=True)
class AuthenticatedUser:
    id: UUID
    full_name: str
    email: str


def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> AuthenticatedUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = verify_auth_token(token)
        user = user_repository.get_user_by_id(payload.user_id)
    except (AuthTokenError, UserRepositoryError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
        ) from None

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
        )

    return AuthenticatedUser(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
    )
