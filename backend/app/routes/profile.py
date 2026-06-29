from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.db.user_repository import UserProfileRecord, UserRepositoryError, user_repository
from app.schemas.profile import UserProfile, UserProfileUpdate
from app.services.auth_context import AuthenticatedUser, get_current_user


router = APIRouter(prefix="/api/v1/profile", tags=["profile"])


def _profile_response(profile: UserProfileRecord) -> UserProfile:
    return UserProfile(
        user_id=profile.user_id,
        role=profile.role,
        state=profile.state,
        zip_code=profile.zip_code,
        alert_interests=profile.alert_interests,
        alert_frequency=profile.alert_frequency,
        report_style=profile.report_style,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.get("", response_model=UserProfile)
def get_profile(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> UserProfile:
    try:
        profile = user_repository.get_or_create_profile(current_user.id)
    except UserRepositoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User profile persistence is unavailable.",
        ) from exc

    return _profile_response(profile)


@router.put("", response_model=UserProfile)
def update_profile(
    payload: UserProfileUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> UserProfile:
    try:
        profile = user_repository.upsert_profile(
            user_id=current_user.id,
            role=payload.role,
            state=payload.state,
            zip_code=payload.zip_code,
            alert_interests=payload.alert_interests,
            alert_frequency=payload.alert_frequency,
            report_style=payload.report_style,
        )
    except UserRepositoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User profile persistence is unavailable.",
        ) from exc

    return _profile_response(profile)
