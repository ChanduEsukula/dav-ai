from app.db.database import get_database_url, is_database_configured


def test_get_database_url_returns_none_when_missing(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    assert get_database_url() is None
    assert is_database_configured() is False


def test_get_database_url_returns_value_when_configured(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://user:password@localhost:5432/medsignal",
    )

    assert (
        get_database_url()
        == "postgresql+psycopg://user:password@localhost:5432/medsignal"
    )
    assert is_database_configured() is True


def test_get_database_url_treats_empty_string_as_missing(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "   ")

    assert get_database_url() is None
    assert is_database_configured() is False