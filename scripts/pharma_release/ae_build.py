"""Compact SQLite serving rows, coverage-only product links, exact replay."""
from collections import Counter, defaultdict
import hashlib

from .ae_derive import FLAGS, LIMITATIONS, RULE_VERSION, WINDOW_START, WINDOW_END, WINDOW_KEY, stream_rows
from .schema_ae import AE_TABLES
from .sources import canonical_json, SourceError

PROJECTION_TABLES = (*AE_TABLES, "coverage")


class AEWriter:
    def __init__(self, connection):
        self.connection = connection
        self.columns = {table: [field[1] for field in connection.execute(f"PRAGMA table_info({table})")] for table in PROJECTION_TABLES}
        self.keys = {table: [field[1] for field in sorted(connection.execute(f"PRAGMA table_info({table})"), key=lambda field: field[5]) if field[5]] for table in PROJECTION_TABLES}
        self.hashes = {table: [] for table in PROJECTION_TABLES}; self.inserted = Counter(); self.replayed = Counter()

    def put(self, table, row):
        columns = self.columns[table]; keys = self.keys[table]; values = [row.get(column) for column in columns]
        old = self.connection.execute(f"SELECT {','.join(columns)} FROM {table} WHERE " + " AND ".join(column + "=?" for column in keys), [row[column] for column in keys]).fetchone()
        if old is None:
            self.connection.execute(f"INSERT INTO {table} ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})", values)
            self.inserted[table] += 1
        elif list(old) != values:
            raise SourceError("Nonidentical AE replay/collision in " + table)
        else:
            self.replayed[table] += 1
        self.hashes[table].append(hashlib.sha256(canonical_json(values).encode()).digest())

    def report(self):
        return {table: {"projected_rows": len(self.hashes[table]), "inserted": self.inserted[table], "identical_replays": self.replayed[table],
            "sha256_sorted_row_hashes": hashlib.sha256(b"".join(sorted(self.hashes[table]))).hexdigest()} for table in PROJECTION_TABLES}


def populate_ae(connection, research, source_id):
    writer = AEWriter(connection)
    for row in stream_rows(research, "SELECT s.*,p.reaction_term_count,p.co_report_activity FROM ae_report_summary s JOIN ae_pair_stats p USING(ingredient_id) ORDER BY ingredient_id"):
        row.update({"window_start": WINDOW_START, "window_end": WINDOW_END, "count_unit": "deduplicated ingredient-report associations",
            "date_basis": "parsed latest-receipt month", "limitations_json": canonical_json(LIMITATIONS), "source_id": source_id})
        writer.put("ae_summary", row)
    for row in stream_rows(research, "SELECT * FROM ae_report_monthly ORDER BY ingredient_id,period"):
        row["period"] = row["period"].isoformat(); row["source_id"] = source_id
        writer.put("ae_monthly", row)
    for row in stream_rows(research, "SELECT * FROM ae_ranked_reactions ORDER BY ingredient_id,rank"):
        row.update({"window_start": WINDOW_START, "window_end": WINDOW_END, "source_id": source_id})
        writer.put("ae_top_reactions", row)
    populate_coverage(connection, writer)
    return {"projection": writer.report()}


def coverage_row(entity_type, identifier, state, reason, measured_count, limitations):
    return {"entity_type": entity_type, "entity_id": identifier, entity_type.lower() + "_id": identifier,
        "domain": "ae_analytics", "window_key": WINDOW_KEY, "state": state, "reason_code": reason,
        "scope": "DEDUPLICATED_INGREDIENT_REPORT_ANALYTICS" if entity_type == "INGREDIENT" else "COMPONENT_ANALYTICS_AVAILABILITY_ONLY; NOT_PRODUCT_REPORT_COUNTS",
        "as_of_date": "2026-09-26", "source_date": "2026-09-23", "measured_count": measured_count,
        "unresolved_count": None, "rule_version": RULE_VERSION, "limitations_json": canonical_json(LIMITATIONS + limitations)}


def populate_coverage(connection, writer):
    available = {row[0] for row in connection.execute("SELECT ingredient_id FROM ae_summary")}
    for (iid,) in connection.execute("SELECT ingredient_id FROM ingredients ORDER BY ingredient_id"):
        present = iid in available
        writer.put("coverage", coverage_row("INGREDIENT", iid, "READY" if present else "UNKNOWN",
            "SCOPED_INGREDIENT_ANALYTICS_AVAILABLE" if present else "NO_STORED_SCOPED_ANALYTICS", 1 if present else None,
            [] if present else ["AE analytics are unavailable for this ingredient in this release."]))
    membership = defaultdict(set)
    for pid, iid in connection.execute("SELECT product_id,ingredient_id FROM product_ingredients"):
        membership[pid].add(iid)
    for pid, complete in connection.execute("SELECT product_id,ingredient_set_complete FROM products ORDER BY product_id"):
        total = len(membership[pid]); covered = len(membership[pid] & available)
        state = "READY" if complete and total and covered == total else "PARTIAL" if covered else "UNKNOWN"
        reason = "ALL_COMPONENT_ANALYTICS_AVAILABLE" if state == "READY" else "PARTIAL_COMPONENT_ANALYTICS_AVAILABLE" if covered else "NO_STORED_COMPONENT_ANALYTICS"
        notes = ["This coverage count measures available ingredient components, never AE reports for the product."]
        if not covered: notes.append("AE analytics are unavailable for this product in this release.")
        if total != covered and covered: notes.append("Some components have no stored AE analytics; component report counts are never added into a combination total.")
        if not complete: notes.append("Frozen product ingredient identity is incomplete.")
        writer.put("coverage", coverage_row("PRODUCT", pid, state, reason, covered if covered else None, notes))


def product_coverage(connection):
    active = {row[0] for row in connection.execute("SELECT ingredient_id FROM ae_summary")}
    membership = defaultdict(set)
    for pid, iid in connection.execute("SELECT product_id,ingredient_id FROM product_ingredients"): membership[pid].add(iid)
    counts = Counter()
    for pid, combination in connection.execute("SELECT product_id,is_combination FROM products WHERE consumer_classification='NORMAL_CONSUMER_HUMAN_PRODUCT'"):
        members = membership[pid]; covered = len(members & active); total = len(members)
        counts["total"] += 1; counts["any_covered" if covered else "uncovered"] += 1
        kind = "combination" if combination else "single"
        counts[kind + "_total"] += 1; counts[kind + "_covered"] += int(covered > 0)
        if combination:
            counts["combination_fully_covered"] += int(bool(total) and covered == total)
            counts["combination_partially_covered"] += int(0 < covered < total)
    result = dict(counts)
    result["coverage_percent"] = 100 * counts["any_covered"] / counts["total"] if counts["total"] else None
    result["single_coverage_percent"] = 100 * counts["single_covered"] / counts["single_total"] if counts["single_total"] else None
    result["semantics"] = "Component ingredient analytics availability; no product-level AE report counts or summation across components."
    return result
