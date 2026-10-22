"""Narrow child-only enum extension; frozen parent tables are never migrated."""
from .sources import SourceError

SCHEMA_VERSION = "dav-ai-pharma-sqlite-v1.phase2-identity1.phase3b-recalls1"


def extend_recall_method(connection):
    if connection.execute("SELECT count(*) FROM product_recalls").fetchone()[0]:
        raise SourceError("Enum extension requires the empty Phase 3A recall edge table")
    sql = connection.execute("SELECT sql FROM sqlite_master WHERE name='product_recalls' AND type='table'").fetchone()[0]
    if "'EXACT_PRODUCT_NDC'" in sql or sql.count("'EXACT_NDC'") != 1:
        raise SourceError("Unexpected parent recall method constraint")
    indexes = connection.execute("SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='product_recalls' AND sql IS NOT NULL ORDER BY name").fetchall()
    if connection.execute("SELECT count(*) FROM sqlite_master WHERE type='trigger' AND tbl_name='product_recalls'").fetchone()[0]:
        raise SourceError("Unexpected parent recall edge trigger")
    # Rebuild this empty table using its exact DDL, changing only one enum value.
    with connection:
        connection.execute("DROP TABLE product_recalls")
        connection.execute(sql.replace("'EXACT_NDC'", "'EXACT_NDC', 'EXACT_PRODUCT_NDC'"))
        for (index_sql,) in indexes:
            connection.execute(index_sql)
        connection.execute("PRAGMA user_version=3")
    return {"changed_table": "product_recalls", "change": "Add EXACT_PRODUCT_NDC to match_method CHECK; retain all original methods and constraints", "schema_version": SCHEMA_VERSION, "user_version": 3}
