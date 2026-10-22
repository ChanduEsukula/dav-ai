"""Phase 1 structural gates. Semantic ingestion gates belong to later phases."""
from .schema import TABLES


def validate_structure(connection):
    errors = []
    tables = {r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if tables != set(TABLES):
        errors.append({"gate": "exact_19_tables", "actual": sorted(tables)})
    if connection.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
        errors.append({"gate": "foreign_keys_enabled"})
    fk_errors = connection.execute("PRAGMA foreign_key_check").fetchall()
    if fk_errors:
        errors.append({"gate": "foreign_keys", "violations": fk_errors})
    integrity = [r[0] for r in connection.execute("PRAGMA integrity_check").fetchall()]
    if integrity != ["ok"]:
        errors.append({"gate": "integrity_check", "actual": integrity})
    counts = {}
    columns = {}
    for name in sorted(tables & set(TABLES)):
        fields = connection.execute(f'PRAGMA table_info("{name}")').fetchall()
        columns[name] = [{"name": r[1], "type": r[2], "not_null": bool(r[3]), "primary_key_position": r[5]} for r in fields]
        if not any(r[5] for r in fields):
            errors.append({"gate": "explicit_primary_key", "table": name})
        counts[name] = connection.execute(f'SELECT count(*) FROM "{name}"').fetchone()[0]
    return {"passed": not errors, "errors": errors, "table_count": len(tables), "table_counts": counts,
            "columns": columns, "integrity_check": integrity, "foreign_key_violations": fk_errors,
            "scope": "PHASE1_STRUCTURAL_ONLY; semantic release publication not yet validated"}
