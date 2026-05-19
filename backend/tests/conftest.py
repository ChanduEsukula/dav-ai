"""Shared pytest configuration.

Backend tests should not read from or write to the real DATABASE_URL by default.
Individual tests that need to validate database configuration should monkeypatch
DATABASE_URL explicitly inside that test.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def isolate_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent tests from using the developer's real configured database."""

    monkeypatch.delenv("DATABASE_URL", raising=False)