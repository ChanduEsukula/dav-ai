import pytest

from app.db.user_repository import UserRepository, UserRepositoryError


def test_user_repository_uses_memory_mode_locally_without_database(monkeypatch):
    repo = UserRepository()
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DAVAI_ENV", raising=False)

    user = repo.create_user(
        full_name="Demo User",
        email="demo@example.com",
        password_hash="hashed-password",
    )

    assert repo.get_user_by_email("demo@example.com") == user


def test_user_repository_requires_database_in_deployed_environment(monkeypatch):
    repo = UserRepository()
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DAVAI_ENV", "production")

    with pytest.raises(UserRepositoryError, match="DATABASE_URL"):
        repo.get_user_by_email("demo@example.com")
