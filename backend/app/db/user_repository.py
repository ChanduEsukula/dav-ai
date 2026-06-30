"""Repository for portfolio-demo users and profiles."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.db.database import get_database_url


logger = logging.getLogger("dav_ai.user_repository")


class UserRepositoryError(RuntimeError):
    """Raised when user persistence is unavailable."""


@dataclass(frozen=True)
class UserRecord:
    id: UUID
    full_name: str
    email: str
    password_hash: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class UserProfileRecord:
    user_id: UUID
    role: str | None
    state: str | None
    zip_code: str | None
    alert_interests: list[str]
    alert_frequency: str | None
    report_style: str | None
    created_at: datetime
    updated_at: datetime


def normalize_email(email: str) -> str:
    """Normalize email addresses for duplicate checks and login."""

    return email.strip().lower()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UserRepository:
    """User/profile repository with database persistence and local memory mode."""

    def __init__(self) -> None:
        self._users: dict[UUID, UserRecord] = {}
        self._email_index: dict[str, UUID] = {}
        self._profiles: dict[UUID, UserProfileRecord] = {}

    def _database_url(self) -> str | None:
        return get_database_url()

    def _row_to_user(self, row) -> UserRecord:
        return UserRecord(
            id=row["id"],
            full_name=row["full_name"],
            email=row["email"],
            password_hash=row["password_hash"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _row_to_profile(self, row) -> UserProfileRecord:
        raw_interests = row["alert_interests"] or []
        alert_interests = [
            str(value)
            for value in raw_interests
            if str(value).strip()
        ] if isinstance(raw_interests, list) else []

        return UserProfileRecord(
            user_id=row["user_id"],
            role=row["role"],
            state=row["state"],
            zip_code=row["zip_code"],
            alert_interests=alert_interests,
            alert_frequency=row["alert_frequency"],
            report_style=row["report_style"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def create_user(
        self,
        *,
        full_name: str,
        email: str,
        password_hash: str,
    ) -> UserRecord:
        normalized_email = normalize_email(email)
        existing = self.get_user_by_email(normalized_email)
        if existing is not None:
            raise ValueError("A user already exists for this email.")

        now = _utc_now()
        user = UserRecord(
            id=uuid4(),
            full_name=full_name.strip(),
            email=normalized_email,
            password_hash=password_hash,
            created_at=now,
            updated_at=now,
        )

        database_url = self._database_url()
        if not database_url:
            self._users[user.id] = user
            self._email_index[user.email] = user.id
            return user

        try:
            with psycopg.connect(database_url, row_factory=dict_row) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        insert into users (
                            id,
                            full_name,
                            email,
                            password_hash,
                            created_at,
                            updated_at
                        )
                        values (
                            %(id)s,
                            %(full_name)s,
                            %(email)s,
                            %(password_hash)s,
                            %(created_at)s,
                            %(updated_at)s
                        )
                        """,
                        {
                            "id": user.id,
                            "full_name": user.full_name,
                            "email": user.email,
                            "password_hash": user.password_hash,
                            "created_at": user.created_at,
                            "updated_at": user.updated_at,
                        },
                    )
            return user
        except Exception as exc:
            logger.exception("user_create_failed")
            raise UserRepositoryError("Unable to create user.") from exc

    def get_user_by_email(self, email: str) -> UserRecord | None:
        normalized_email = normalize_email(email)
        database_url = self._database_url()
        if not database_url:
            user_id = self._email_index.get(normalized_email)
            return self._users.get(user_id) if user_id else None

        try:
            with psycopg.connect(database_url, row_factory=dict_row) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        select
                            id,
                            full_name,
                            email,
                            password_hash,
                            created_at,
                            updated_at
                        from users
                        where email = %(email)s
                        """,
                        {"email": normalized_email},
                    )
                    row = cursor.fetchone()
            return self._row_to_user(row) if row else None
        except Exception as exc:
            logger.exception("user_get_by_email_failed")
            raise UserRepositoryError("Unable to read user.") from exc

    def get_user_by_id(self, user_id: UUID) -> UserRecord | None:
        database_url = self._database_url()
        if not database_url:
            return self._users.get(user_id)

        try:
            with psycopg.connect(database_url, row_factory=dict_row) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        select
                            id,
                            full_name,
                            email,
                            password_hash,
                            created_at,
                            updated_at
                        from users
                        where id = %(id)s
                        """,
                        {"id": user_id},
                    )
                    row = cursor.fetchone()
            return self._row_to_user(row) if row else None
        except Exception as exc:
            logger.exception("user_get_by_id_failed")
            raise UserRepositoryError("Unable to read user.") from exc

    def create_default_profile(self, user_id: UUID) -> UserProfileRecord:
        return self.upsert_profile(
            user_id=user_id,
            role=None,
            state=None,
            zip_code=None,
            alert_interests=[],
            alert_frequency=None,
            report_style="simple",
        )

    def get_profile(self, user_id: UUID) -> UserProfileRecord | None:
        database_url = self._database_url()
        if not database_url:
            return self._profiles.get(user_id)

        try:
            with psycopg.connect(database_url, row_factory=dict_row) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        select
                            user_id,
                            role,
                            state,
                            zip_code,
                            alert_interests,
                            alert_frequency,
                            report_style,
                            created_at,
                            updated_at
                        from user_profiles
                        where user_id = %(user_id)s
                        """,
                        {"user_id": user_id},
                    )
                    row = cursor.fetchone()
            return self._row_to_profile(row) if row else None
        except Exception as exc:
            logger.exception("user_profile_get_failed")
            raise UserRepositoryError("Unable to read user profile.") from exc

    def get_or_create_profile(self, user_id: UUID) -> UserProfileRecord:
        profile = self.get_profile(user_id)
        if profile is not None:
            return profile
        return self.create_default_profile(user_id)

    def upsert_profile(
        self,
        *,
        user_id: UUID,
        role: str | None,
        state: str | None,
        zip_code: str | None,
        alert_interests: list[str],
        alert_frequency: str | None,
        report_style: str | None,
    ) -> UserProfileRecord:
        now = _utc_now()
        existing = self.get_profile(user_id)
        created_at = existing.created_at if existing else now
        clean_interests = [
            interest.strip()
            for interest in alert_interests
            if interest.strip()
        ][:12]
        profile = UserProfileRecord(
            user_id=user_id,
            role=role,
            state=state,
            zip_code=zip_code,
            alert_interests=clean_interests,
            alert_frequency=alert_frequency,
            report_style=report_style,
            created_at=created_at,
            updated_at=now,
        )

        database_url = self._database_url()
        if not database_url:
            self._profiles[user_id] = profile
            return profile

        try:
            with psycopg.connect(database_url, row_factory=dict_row) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        insert into user_profiles (
                            user_id,
                            role,
                            state,
                            zip_code,
                            alert_interests,
                            alert_frequency,
                            report_style,
                            created_at,
                            updated_at
                        )
                        values (
                            %(user_id)s,
                            %(role)s,
                            %(state)s,
                            %(zip_code)s,
                            %(alert_interests)s,
                            %(alert_frequency)s,
                            %(report_style)s,
                            %(created_at)s,
                            %(updated_at)s
                        )
                        on conflict (user_id) do update set
                            role = excluded.role,
                            state = excluded.state,
                            zip_code = excluded.zip_code,
                            alert_interests = excluded.alert_interests,
                            alert_frequency = excluded.alert_frequency,
                            report_style = excluded.report_style,
                            updated_at = excluded.updated_at
                        """,
                        {
                            "user_id": profile.user_id,
                            "role": profile.role,
                            "state": profile.state,
                            "zip_code": profile.zip_code,
                            "alert_interests": Jsonb(profile.alert_interests),
                            "alert_frequency": profile.alert_frequency,
                            "report_style": profile.report_style,
                            "created_at": profile.created_at,
                            "updated_at": profile.updated_at,
                        },
                    )
            return profile
        except Exception as exc:
            logger.exception("user_profile_upsert_failed")
            raise UserRepositoryError("Unable to save user profile.") from exc

    def clear(self) -> None:
        """Clear local in-memory state. Used by tests."""

        self._users.clear()
        self._email_index.clear()
        self._profiles.clear()


user_repository = UserRepository()
