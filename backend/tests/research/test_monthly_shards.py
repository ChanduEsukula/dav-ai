import json
from pathlib import Path

import pytest

from app.research.analysis import connect_analytics
from app.research.shards import materialize_monthly


MONTHLY_SQL = """
SELECT
    d.ingredient_id,
    x.reaction,
    date_trunc('month',CAST(r.last_received AS DATE))::DATE AS period,
    count(*)::BIGINT AS report_count,
    count(DISTINCT r.case_id)::BIGINT AS unique_case_count,
    count(*) FILTER(WHERE serious)::BIGINT AS serious_count,
    count(*) FILTER(WHERE serious IS NOT NULL)::BIGINT AS serious_known_count,
    count(*) FILTER(WHERE death)::BIGINT AS death_report_count,
    count(*) FILTER(WHERE hospitalization)::BIGINT AS hospitalization_count,
    count(*) FILTER(WHERE disability)::BIGINT AS disability_count,
    count(*) FILTER(WHERE life_threatening)::BIGINT AS life_threatening_count,
    count(*) FILTER(WHERE suspect)::BIGINT AS suspect_count,
    count(*) FILTER(WHERE concomitant)::BIGINT AS concomitant_count,
    count(*) FILTER(WHERE interacting)::BIGINT AS interacting_count,
    avg(c.co_drugs)::DOUBLE AS mean_co_reported_drugs
FROM latest_reports r
JOIN report_ingredients d USING(report_uid)
JOIN report_reactions x USING(report_uid)
JOIN mention_counts c USING(report_uid)
WHERE r.last_received IS NOT NULL
  AND (r.first_received IS NULL OR r.last_received>=r.first_received)
GROUP BY d.ingredient_id,x.reaction,period
"""


def seed(conn, root: Path):
    conn.execute("""
        CREATE TABLE latest_reports(
            report_uid VARCHAR,
            case_id VARCHAR,
            first_received VARCHAR,
            last_received VARCHAR,
            serious BOOLEAN,
            death BOOLEAN,
            hospitalization BOOLEAN,
            disability BOOLEAN,
            life_threatening BOOLEAN
        )
    """)

    conn.execute("""
        INSERT INTO latest_reports VALUES
        ('r1','c1','2020-01-01','2020-01-10',true,false,true,false,false),
        ('r2','c2','2020-01-01','2020-01-20',true,true,false,false,true),
        ('r3','c3','2020-02-01','2020-02-10',false,false,false,false,false),
        ('r4','c4','2020-03-10','2020-02-10',true,false,true,false,false),
        ('r5','c5',NULL,'2020-02-15',NULL,false,false,true,false)
    """)

    conn.execute("""
        CREATE TABLE report_ingredients(
            report_uid VARCHAR,
            ingredient_id VARCHAR,
            suspect BOOLEAN,
            concomitant BOOLEAN,
            interacting BOOLEAN,
            mapping_observed_at VARCHAR
        )
    """)

    conn.execute("""
        INSERT INTO report_ingredients VALUES
        ('r1','drug-a',true,false,false,NULL),
        ('r2','drug-a',false,true,false,NULL),
        ('r3','drug-a',true,false,false,NULL),
        ('r3','drug-b',false,false,true,NULL),
        ('r4','drug-a',true,false,false,NULL),
        ('r5','drug-b',true,false,false,NULL)
    """)

    conn.execute("""
        CREATE TABLE report_reactions(
            report_uid VARCHAR,
            reaction VARCHAR
        )
    """)

    conn.execute("""
        INSERT INTO report_reactions VALUES
        ('r1','reaction-x'),
        ('r1','reaction-y'),
        ('r2','reaction-x'),
        ('r3','reaction-x'),
        ('r3','reaction-z'),
        ('r4','reaction-x'),
        ('r5','reaction-z')
    """)

    conn.execute("""
        CREATE TABLE mention_counts(
            report_uid VARCHAR,
            co_drugs BIGINT
        )
    """)

    conn.execute("""
        INSERT INTO mention_counts VALUES
        ('r1',1),('r2',2),('r3',3),('r4',1),('r5',2)
    """)

    # materialize_monthly only needs a valid selected-checkpoint signature
    # for this isolated synthetic test.
    (root / "analysis-selected-checkpoint.json").write_text(
        json.dumps({"signature": "synthetic-monthly-test"})
    )


def result_rows(conn):
    return set(conn.execute("""
        SELECT *
        FROM monthly
    """).fetchall())


@pytest.mark.parametrize("buckets", [1, 3, 7])
def test_monthly_shards_equal_monolithic_sql(tmp_path, buckets):
    root = tmp_path / f"monthly-{buckets}"
    root.mkdir()

    with connect_analytics(root) as conn:
        seed(conn, root)

        conn.execute(
            "CREATE TABLE monthly_oracle AS " + MONTHLY_SQL
        )
        oracle = set(
            conn.execute("SELECT * FROM monthly_oracle").fetchall()
        )

        manifest = materialize_monthly(
            conn,
            root,
            buckets=buckets,
        )

        assert manifest["complete"]
        assert manifest["union_integrity_passed"]
        assert result_rows(conn) == oracle

        # The partition key contains ingredient_id, so no final aggregation
        # key may appear in more than one shard.
        assert conn.execute("""
            SELECT count(*)
            FROM (
                SELECT ingredient_id,reaction,period,count(*) n
                FROM monthly
                GROUP BY ingredient_id,reaction,period
                HAVING count(*) > 1
            )
        """).fetchone()[0] == 0

        shard_dir = root / "analysis-shards" / "monthly"
        before = {
            p.name: p.stat().st_mtime_ns
            for p in shard_dir.glob("shard-*")
        }

        # A second call must reuse committed shards rather than rewrite them.
        again = materialize_monthly(
            conn,
            root,
            buckets=buckets,
        )

        assert again["complete"]
        assert before == {
            p.name: p.stat().st_mtime_ns
            for p in shard_dir.glob("shard-*")
        }


def test_monthly_shards_reject_corruption(tmp_path):
    root = tmp_path / "monthly-corrupt"
    root.mkdir()

    with connect_analytics(root) as conn:
        seed(conn, root)

        materialize_monthly(conn, root, buckets=3)

        shard_dir = root / "analysis-shards" / "monthly"
        damaged = next(shard_dir.glob("shard-*.parquet"))
        damaged.write_bytes(b"corrupt fixture")

        with pytest.raises(ValueError, match="checkpoint mismatch"):
            materialize_monthly(conn, root, buckets=3)
