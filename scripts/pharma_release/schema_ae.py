"""Child-only report-deduplicated AE schema and bounded top-50 ranking."""
from .schema import identity, json_column, table
from .sources import SourceError

SCHEMA_VERSION = "dav-ai-pharma-sqlite-v1.phase2-identity1.phase3b-recalls1.phase4a-ae1"
AE_TABLES = ("ae_summary", "ae_monthly", "ae_top_reactions")
OUTCOME_COLUMNS = ("serious_report_count", "serious_known_report_count", "death_report_count", "hospitalization_report_count",
    "disability_report_count", "life_threatening_report_count", "suspect_report_count", "concomitant_report_count", "interacting_report_count")


def ae_schema_statements():
    ingredient = identity("ingredient_id", "ingredients(ingredient_id)")
    source = identity("source_id", "sources(source_id)")
    window = ["window_start TEXT NOT NULL CHECK(window_start='2020-01-01')", "window_end TEXT NOT NULL CHECK(window_end='2026-06-30')"]
    counts = ["report_count INTEGER NOT NULL CHECK(report_count>0)",
        *[f"{name} INTEGER NOT NULL CHECK({name} BETWEEN 0 AND report_count)" + (" CHECK(serious_report_count<=serious_known_report_count)" if name == "serious_report_count" else "") for name in OUTCOME_COLUMNS]]
    return [table("ae_summary", [ingredient, *window, *counts,
        "unique_case_count INTEGER NOT NULL CHECK(unique_case_count BETWEEN 0 AND report_count)",
        "active_month_count INTEGER NOT NULL CHECK(active_month_count BETWEEN 1 AND 78)",
        "reaction_term_count INTEGER NOT NULL CHECK(reaction_term_count>0)",
        "co_report_activity INTEGER NOT NULL CHECK(co_report_activity>0)",
        "count_unit TEXT NOT NULL CHECK(count_unit='deduplicated ingredient-report associations')",
        "date_basis TEXT NOT NULL CHECK(date_basis='parsed latest-receipt month')", json_column("limitations_json", "array"), source,
        "PRIMARY KEY(ingredient_id,window_start,window_end)"]),
        table("ae_monthly", [ingredient,
            "period TEXT NOT NULL CHECK(period BETWEEN '2020-01-01' AND '2026-06-01' AND strftime('%Y-%m-%d',period) IS NOT NULL AND strftime('%Y-%m-%d',period)=period AND substr(period,9,2)='01')",
            *counts, source, "PRIMARY KEY(ingredient_id,period)"]),
        table("ae_top_reactions", [ingredient, *window,
            "reaction TEXT NOT NULL CHECK(length(trim(reaction))>0)",
            "co_report_activity INTEGER NOT NULL CHECK(co_report_activity>0)",
            "active_months INTEGER NOT NULL CHECK(active_months BETWEEN 1 AND 78)",
            "rank INTEGER NOT NULL CHECK(rank BETWEEN 1 AND 50)", source,
            "PRIMARY KEY(ingredient_id,window_start,window_end,reaction)", "UNIQUE(ingredient_id,window_start,window_end,rank)"])]


def extend_ae_schema(connection):
    for name in AE_TABLES:
        if connection.execute(f"SELECT count(*) FROM {name}").fetchone()[0]:
            raise SourceError("AE schema extension requires empty Phase 3B AE tables")
        if connection.execute("SELECT count(*) FROM sqlite_master WHERE tbl_name=? AND type IN ('trigger','index') AND sql IS NOT NULL", (name,)).fetchone()[0]:
            raise SourceError("Unexpected parent AE secondary index/trigger")
    with connection:
        for name in AE_TABLES: connection.execute(f"DROP TABLE {name}")
        for statement in ae_schema_statements(): connection.execute(statement)
        connection.execute("PRAGMA user_version=4")
    return {"schema_version": SCHEMA_VERSION, "user_version": 4, "changed_tables": list(AE_TABLES),
        "changes": ["Summary and monthly use deduplicated report-level counts and reported outcome flags", "Summary retains separately named reaction co_report_activity diagnostic", "Top reactions use co_report_activity and rank cap 50"],
        "ddl_statements": ae_schema_statements()}
