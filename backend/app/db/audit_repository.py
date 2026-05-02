from typing import Any

from app.db.database import is_database_configured


def save_audit_event(audit_event: dict[str, Any]) -> dict[str, str]:
    if not is_database_configured():
        return {
            "status": "skipped",
            "reason": "database_not_configured",
        }

    return {
        "status": "not_implemented",
        "reason": "database_configured_but_repository_not_implemented",
    }