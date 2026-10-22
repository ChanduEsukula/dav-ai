"""Exact SQLite lookups return all candidate identities in deterministic order."""
from .eligibility import normalize_name
from .ids import require_identifier


def lookup_name(connection, value, role):
    if role not in {"BRAND", "GENERIC", "INGREDIENT", "BRAND_BASE"}:
        raise ValueError("Unsupported source name role")
    name = normalize_name(value)
    if not name:
        return []
    if role == "INGREDIENT":
        sql = """SELECT DISTINCT p.product_id FROM search_names n
                 JOIN product_ingredients pi ON pi.ingredient_id=n.ingredient_id
                 JOIN products p ON p.product_id=pi.product_id
                 WHERE n.name_role='INGREDIENT' AND n.normalized_name=? ORDER BY p.product_id"""
        args = (name,)
    else:
        sql = """SELECT product_id FROM search_names WHERE entity_type='PRODUCT'
                 AND name_role=? AND normalized_name=? ORDER BY product_id"""
        args = (role, name)
    return [r[0] for r in connection.execute(sql, args)]


def lookup_identifier(connection, kind, value):
    if kind not in {"PRODUCT_NDC", "PACKAGE_NDC", "RXCUI"}:
        raise ValueError("Unsupported identifier type")
    require_identifier(value)
    return [r[0] for r in connection.execute(
        "SELECT product_id FROM product_identifiers WHERE identifier_type=? AND value=? ORDER BY product_id", (kind, value))]


def candidate_details(connection, product_id):
    cursor = connection.execute("SELECT * FROM products WHERE product_id=?", (product_id,))
    result = dict(zip([c[0] for c in cursor.description], cursor.fetchone()))
    result["ingredient_ids"] = [r[0] for r in connection.execute(
        "SELECT ingredient_id FROM product_ingredients WHERE product_id=? ORDER BY ingredient_id", (product_id,))]
    result["identifiers"] = {kind: [r[0] for r in connection.execute(
        "SELECT value FROM product_identifiers WHERE product_id=? AND identifier_type=? ORDER BY value", (product_id, kind))]
        for kind in ("PRODUCT_NDC", "PACKAGE_NDC", "RXCUI")}
    result["search_names"] = [dict(zip(("role", "normalized", "originals_json"), r)) for r in connection.execute(
        "SELECT name_role,normalized_name,original_names_json FROM search_names WHERE product_id=? ORDER BY name_role,normalized_name", (product_id,))]
    fid = result["formulation_id"]
    cursor = connection.execute("SELECT * FROM formulations WHERE formulation_id=?", (fid,))
    row = cursor.fetchone()
    result["formulation"] = dict(zip([c[0] for c in cursor.description], row)) if row else None
    cursor = connection.execute("SELECT state,reason_code,measured_count,unresolved_count FROM coverage WHERE entity_type='PRODUCT' AND entity_id=? AND domain='identity' AND window_key=''", (product_id,))
    row = cursor.fetchone()
    result["identity_coverage"] = dict(zip([c[0] for c in cursor.description], row)) if row else None
    return result
