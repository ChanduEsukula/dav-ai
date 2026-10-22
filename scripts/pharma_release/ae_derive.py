"""Offline SQL derivations: report outcomes and reaction activity stay separate."""
from .sources import SourceError

RULE_VERSION = "phase4a-exact-ingredient-report-dedup-202001-202606-top50-v1"
WINDOW_START = "2020-01-01"
WINDOW_END = "2026-06-30"
WINDOW_EXCLUSIVE_END = "2026-07-01"
WINDOW_KEY = WINDOW_START + "/" + WINDOW_END
FLAGS = {"serious_report_count": "serious", "serious_known_report_count": None, "death_report_count": "death",
    "hospitalization_report_count": "hospitalization", "disability_report_count": "disability", "life_threatening_report_count": "life_threatening",
    "suspect_report_count": "suspect", "concomitant_report_count": "concomitant", "interacting_report_count": "interacting"}
LIMITATIONS = ["Descriptive FAERS-derived ingredient co-reporting associations; not patient counts.",
    "A report can contain multiple drugs, ingredients and reactions; ingredient totals cannot be summed into globally unique report counts or product totals.",
    "Outcome counts describe reports marked serious or containing the specified outcome flag.",
    "This is a current normalized/revised research snapshot filtered by parsed receipt dates; it does not recreate the public data at historical cutoffs.",
    "Exact frozen ingredient IDs retain separate salt, hydrate and solvate identities; unresolved source mentions and reporting completeness are not measured.",
    "Reaction co_report_activity is distinct from deduplicated report_count; each report may contribute to multiple reaction terms.",
    "Only observed ingredient-month rows are stored; an absent bin is not an observed zero."]

ACTIVE_SQL = "SELECT DISTINCT ingredient_id FROM monthly WHERE period>=DATE '2020-01-01' AND period<=DATE '2026-06-01'"
WINDOW_REPORTS_SQL = """SELECT report_uid,case_id,serious,death,hospitalization,disability,life_threatening,
    TRY_CAST(first_received AS DATE) first_date,TRY_CAST(last_received AS DATE) last_date
    FROM latest_reports WHERE TRY_CAST(last_received AS DATE)>=DATE '2020-01-01'
    AND TRY_CAST(last_received AS DATE)<DATE '2026-07-01'
    AND TRY_CAST(first_received AS DATE) IS NOT NULL
    AND TRY_CAST(first_received AS DATE)<=TRY_CAST(last_received AS DATE)"""
ELIGIBLE_SQL = """WITH ir AS (SELECT ri.report_uid,ri.ingredient_id,
    bool_or(ri.suspect) suspect,bool_or(ri.concomitant) concomitant,bool_or(ri.interacting) interacting
    FROM report_ingredients ri JOIN ae_active a USING(ingredient_id) JOIN ae_window_reports lr USING(report_uid)
    GROUP BY ri.report_uid,ri.ingredient_id)
    SELECT ir.*,lr.* EXCLUDE(report_uid) FROM ir JOIN ae_window_reports lr USING(report_uid)"""
COUNTS_SQL = "count(*)::BIGINT report_count," + ",".join(
    "count(*) FILTER(WHERE " + ("serious IS NOT NULL" if flag is None else flag) + ")::BIGINT " + name for name, flag in FLAGS.items())
SUMMARY_SQL = "SELECT ingredient_id," + COUNTS_SQL + ",count(DISTINCT case_id)::BIGINT unique_case_count,count(DISTINCT date_trunc('month',last_date))::BIGINT active_month_count FROM ae_eligible GROUP BY ingredient_id"
MONTHLY_SQL = "SELECT ingredient_id,date_trunc('month',last_date)::DATE period," + COUNTS_SQL + " FROM ae_eligible GROUP BY ingredient_id,period"
PAIR_STATS_SQL = """SELECT ingredient_id,count(DISTINCT reaction)::BIGINT reaction_term_count,
    sum(report_count)::BIGINT co_report_activity FROM monthly
    WHERE period>=DATE '2020-01-01' AND period<=DATE '2026-06-01' GROUP BY ingredient_id"""
TOP_SQL = """WITH pairs AS (SELECT ingredient_id,reaction,sum(report_count)::BIGINT co_report_activity,
    count(DISTINCT period)::BIGINT active_months FROM monthly
    WHERE period>=DATE '2020-01-01' AND period<=DATE '2026-06-01' GROUP BY ingredient_id,reaction),
    ranked AS (SELECT *,row_number() OVER(PARTITION BY ingredient_id ORDER BY co_report_activity DESC,reaction ASC) rank FROM pairs)
    SELECT * FROM ranked WHERE rank<=50"""
TEMPORAL_SQL = """SELECT count(*) latest_report_rows,
    count(*) FILTER(WHERE TRY_CAST(first_received AS DATE) IS NULL) first_unparseable_or_missing,
    count(*) FILTER(WHERE TRY_CAST(last_received AS DATE) IS NULL) last_unparseable_or_missing,
    count(*) FILTER(WHERE TRY_CAST(first_received AS DATE)>TRY_CAST(last_received AS DATE)) contradictory_chronology,
    count(*) FILTER(WHERE TRY_CAST(last_received AS DATE)>=DATE '2020-01-01' AND TRY_CAST(last_received AS DATE)<DATE '2026-07-01') last_receipt_in_window,
    count(*) FILTER(WHERE TRY_CAST(last_received AS DATE)>=DATE '2020-01-01' AND TRY_CAST(last_received AS DATE)<DATE '2026-07-01'
        AND (TRY_CAST(first_received AS DATE) IS NULL OR TRY_CAST(first_received AS DATE)>TRY_CAST(last_received AS DATE))) in_window_temporal_exclusions
    FROM latest_reports"""


def one_dict(connection, sql):
    cursor = connection.execute(sql)
    return dict(zip([field[0] for field in cursor.description], cursor.fetchone()))


def derive(connection, frozen_ingredient_ids):
    for table in ("ae_active", "ae_window_reports", "ae_eligible", "ae_report_summary", "ae_report_monthly", "ae_pair_stats", "ae_ranked_reactions"):
        connection.execute("DROP TABLE IF EXISTS temp.main." + table)
    connection.execute("CREATE TEMP TABLE ae_active AS " + ACTIVE_SQL)
    active = {row[0] for row in connection.execute("SELECT ingredient_id FROM ae_active").fetchall()}
    missing = sorted(active - set(frozen_ingredient_ids))
    if missing: raise SourceError("AE ingredient IDs absent from frozen release: " + repr(missing[:10]))
    connection.execute("CREATE TEMP TABLE ae_window_reports AS " + WINDOW_REPORTS_SQL)
    shape = one_dict(connection, "SELECT count(*) row_count,count(DISTINCT report_uid) unique_report_uids,count(*) FILTER(WHERE report_uid IS NULL OR trim(report_uid)='') missing_report_uids FROM ae_window_reports")
    if shape["row_count"] != shape["unique_report_uids"] or shape["missing_report_uids"]:
        raise SourceError("Selected latest report identities are missing/duplicated; do not choose a replacement")
    invalid = connection.execute("""SELECT count(*) FROM monthly WHERE period>=DATE '2020-01-01' AND period<=DATE '2026-06-01'
        AND (reaction IS NULL OR trim(reaction)='' OR report_count IS NULL OR report_count<=0)""").fetchone()[0]
    if invalid: raise SourceError("Invalid reaction co-reporting aggregate")
    for table, sql in (("ae_eligible", ELIGIBLE_SQL), ("ae_report_summary", SUMMARY_SQL), ("ae_report_monthly", MONTHLY_SQL),
        ("ae_pair_stats", PAIR_STATS_SQL), ("ae_ranked_reactions", TOP_SQL)):
        connection.execute("CREATE TEMP TABLE " + table + " AS " + sql)
        if table == "ae_eligible":
            connection.execute("DROP TABLE temp.main.ae_window_reports")
        print("Derived " + table, flush=True)
    extra = connection.execute("""SELECT ingredient_id,period::VARCHAR FROM ae_report_monthly EXCEPT
        SELECT DISTINCT ingredient_id,period::VARCHAR FROM monthly WHERE period>=DATE '2020-01-01' AND period<=DATE '2026-06-01' ORDER BY ingredient_id,2""").fetchall()
    old_only = connection.execute("""SELECT DISTINCT ingredient_id,period::VARCHAR FROM monthly WHERE period>=DATE '2020-01-01' AND period<=DATE '2026-06-01'
        EXCEPT SELECT ingredient_id,period::VARCHAR FROM ae_report_monthly ORDER BY ingredient_id,2""").fetchall()
    extra_details = []
    for iid, period in extra:
        cursor = connection.execute("""SELECT count(*) ingredient_report_associations,
            count(*) FILTER(WHERE EXISTS(SELECT 1 FROM report_reactions x WHERE x.report_uid=e.report_uid)) associations_with_normalized_reaction
            FROM ae_eligible e WHERE e.ingredient_id=? AND date_trunc('month',e.last_date)::DATE=?::DATE""", [iid, period])
        n, with_reaction = cursor.fetchone()
        extra_details.append({"ingredient_id": iid, "period": period, "eligible_ingredient_report_associations": n,
            "associations_with_normalized_reaction": with_reaction, "associations_without_normalized_reaction": n - with_reaction})
    return {"identity": {"release_ingredients": len(frozen_ingredient_ids), "ae_active_ingredients": len(active), "overlap": len(active), "absent": len(missing)},
        "temporal_quality": one_dict(connection, TEMPORAL_SQL), "eligible_report_shape": shape,
        "eligible_ingredient_report_associations": connection.execute("SELECT count(*) FROM ae_eligible").fetchone()[0],
        "monthly_reconciliation": {"reaction_aggregate_ingredient_month_rows": connection.execute("SELECT count(*) FROM (SELECT DISTINCT ingredient_id,period FROM monthly WHERE period>=DATE '2020-01-01' AND period<=DATE '2026-06-01')").fetchone()[0],
            "report_derived_ingredient_month_rows": connection.execute("SELECT count(*) FROM ae_report_monthly").fetchone()[0],
            "report_only_rows": extra, "reaction_aggregate_only_rows": old_only, "extra_row_details": extra_details,
            "basis": "Report-derived months include eligible ingredient/report associations without a reaction-granular monthly row. No report_reactions requirement is added."}}


def stream_rows(connection, sql):
    cursor = connection.execute(sql); names = [field[0] for field in cursor.description]
    while True:
        batch = cursor.fetchmany(1000)
        if not batch: return
        for row in batch:
            yield dict(zip(names, row))
