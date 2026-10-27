"""Read-only discovery summaries. Brand aliases are search scope, never identity equivalence."""
from contextlib import closing
import json

from app.db.pharma.release_connection import connect_release
from app.db.pharma.release_repository import FrozenPharmaReleaseRepository, _normalize_name
from app.services.pharma.evidence import release_metadata

MAX_PRODUCTS = 100


def medication_overview(query: str):
    repo = FrozenPharmaReleaseRepository()
    normalized = _normalize_name(query)
    with closing(connect_release()) as con:
        # Stored brand-base aliases may include XR. Each original product and
        # formulation remains distinct; ingredient search is a different scope.
        rows = con.execute("""
            SELECT DISTINCT p.* FROM products p JOIN search_names sn ON sn.product_id=p.product_id
            WHERE sn.entity_type='PRODUCT' AND sn.normalized_name=?
              AND sn.name_role IN ('BRAND','BRAND_BASE') AND p.eligibility_mode='NORMAL_CONSUMER'
            ORDER BY p.product_id LIMIT ?
        """, (normalized, MAX_PRODUCTS + 1)).fetchall()
        scope = 'stored_brand_alias_matches'
        if rows:
            products = [repo._project_product(con, row) for row in rows[:MAX_PRODUCTS]]
            truncated = len(rows) > MAX_PRODUCTS
        else:
            # Preserve established identifier / ingredient / prefix discovery.
            matches = repo.search(query, limit=MAX_PRODUCTS + 1)
            products, truncated = matches[:MAX_PRODUCTS], len(matches) > MAX_PRODUCTS
            scope = 'bounded_catalog_search_matches'
        ids = [product['id'] for product in products]
        product_by_id = {product['id']: product for product in products}
        label_ids, label_links, label_products, ingredients = set(), 0, 0, {}
        recalls = {}
        for product in products:
            admitted = repo._consumer_labels(con, product['id'])
            label_ids.update(row['label_id'] for row in admitted)
            label_links += len(admitted)
            label_products += bool(admitted)
            # Only admitted recall links. No ingredient-name inference and no
            # name matching of recalling firms to labelers.
            eligible = {row[0] for row in con.execute("""
                SELECT recall_id FROM product_recalls WHERE product_id=?
                  AND consumer_eligible=1 AND json_array_length(conflicts_json)=0
            """, (product['id'],))}
            for row in repo._recalls(con, product['id'])['records']:
                if row['id'] not in eligible:
                    continue
                item = recalls.setdefault(row['id'], {
                    key: row[key] for key in ['id', 'recall_number', 'product_description', 'reason_for_recall',
                        'classification', 'reported_status', 'recalling_firm', 'recall_initiation_date',
                        'report_date', 'source_record_id', 'source_url']})
                item.setdefault('product_links', []).append({
                    'product_id': product['id'], 'product_ndcs': product['product_ndcs'],
                    **{key: row[key] for key in ['lot_scope', 'lot_information', 'applicability_class', 'match_method', 'matched_value']}})
            for row in con.execute("""SELECT i.ingredient_id,i.canonical_name FROM product_ingredients pi
                    JOIN ingredients i ON i.ingredient_id=pi.ingredient_id WHERE pi.product_id=?""", (product['id'],)):
                ingredients[row['ingredient_id']] = row['canonical_name']
        reporting = []
        for ingredient_id, name in sorted(ingredients.items()):
            row = con.execute('SELECT * FROM ae_summary WHERE ingredient_id=?', (ingredient_id,)).fetchone()
            source = con.execute('SELECT source_name,source_url,export_date FROM sources WHERE source_id=?', (row['source_id'],)).fetchone() if row else None
            reporting.append({
                'ingredient_id': ingredient_id, 'ingredient_name': name,
                'report_count': row['report_count'] if row else None,
                'count_unit': row['count_unit'] if row else None,
                'window_start': row['window_start'] if row else None, 'window_end': row['window_end'] if row else None,
                'source': dict(source) if source else None,
                'coverage': repo._ingredient_coverage(con, ingredient_id, 'ae_analytics'),
                'reactions': [dict(r) for r in con.execute('SELECT reaction,co_report_activity,rank FROM ae_top_reactions WHERE ingredient_id=? ORDER BY rank,reaction LIMIT 5', (ingredient_id,))] if row else [],
            })
        # Formulation IDs are sealed identifiers, not inferred name equivalence.
        families = {}
        for product in products:
            key = product['formulation_id'] or product['id']
            families.setdefault(key, []).append(product['id'])
        return {
            'query': query, 'match_scope': scope, 'matched_product_count': len(ids), 'truncated': truncated,
            'products': products, 'formulations': [{'formulation_id': product_by_id[value[0]]['formulation_id'], 'product_ids': value} for value in families.values()],
            'labels': {'distinct_admitted_records': len(label_ids), 'product_label_links': label_links, 'products_with_labels': label_products},
            'recalls': {'distinct_linked_records': len(recalls), 'product_recall_links': sum(len(row['product_links']) for row in recalls.values()),
                'records': sorted(recalls.values(), key=lambda row: (row['recall_initiation_date'] or '', row['id']), reverse=True)},
            'ingredients': reporting, 'release': release_metadata(),
            'limitations': [
                'Discovery overview only. Select and confirm an exact product before product-scoped research.',
                'Counts describe returned matching eligible products in this frozen release, not complete brand or ingredient history.',
                'Stored brand-base aliases can include extended-release forms. Products, formulations and labelers remain separate.',
                'Recall records are deduplicated by sealed recall_id, not summed across NDCs. A record is not necessarily a unique FDA recall event.',
                'Historical links do not establish current status or applicability to every package or lot. No linked records is not evidence of no recalls.',
                'FAERS ingredients are listed once by sealed ingredient_id. Never sum ingredients into a product total; associations do not establish causation, incidence or individual risk.',
                'Label documents are deduplicated only after the existing consumer-admission checks. Missing label evidence does not mean no warnings exist.',
            ],
        }


def data_inventory():
    """Definitions accompany every metric; corpus counts are not consumer coverage."""
    with closing(connect_release()) as con:
        manifest = dict(con.execute('SELECT * FROM release_manifest').fetchone())
        counts = json.loads(manifest['table_counts_json'])
        normal = con.execute("SELECT count(*) FROM products WHERE eligibility_mode='NORMAL_CONSUMER'").fetchone()[0]
        def metric(key, label, value, definition, source, window):
            return dict(key=key, label=label, value=value, definition=definition, source=source, window=window)
        metrics = [
            metric('labels', 'Stored label documents', counts['labels'], 'Rows in labels, including retained context/withheld documents. Not all are admitted exact-product evidence.', 'release_manifest.table_counts_json.labels', 'Label export '+manifest['label_export_date']+'; document dates vary'),
            metric('products', 'Searchable product records', normal, "products rows with eligibility_mode=NORMAL_CONSUMER; NDC strengths and labelers stay separate.", 'products.eligibility_mode', 'NDC observation '+manifest['ndc_observation_date']),
            metric('recalls', 'Stored recall records', counts['recalls'], 'Rows in recalls. Includes records without consumer product links; not a count of recall events or all FDA recalls.', 'release_manifest.table_counts_json.recalls', 'Historical dates vary; source vintage shown below'),
            metric('analytics', 'Ingredients with analytics', counts['ae_summary'], 'One ae_summary row per ingredient_id. This counts analytical rows, not reports, patients or side effects.', 'release_manifest.table_counts_json.ae_summary', manifest['window_start']+' to '+manifest['window_end']),
        ]
        identifier_counts = {row[0]: row[1] for row in con.execute('SELECT identifier_type,count(DISTINCT value) FROM product_identifiers GROUP BY identifier_type')}
        for key, label in [('PRODUCT_NDC','Distinct product NDCs'), ('PACKAGE_NDC','Distinct package NDCs')]:
            if key in identifier_counts:
                metrics.append(metric(key.lower(), label, identifier_counts[key], 'Distinct preserved identifier values across runtime products, including regulatory-only records; not equivalent medication counts.', "product_identifiers WHERE identifier_type='"+key+"'", 'NDC observation '+manifest['ndc_observation_date']))
        return {'release': release_metadata(), 'metrics': metrics,
            'limitations': ['Manifest counts describe the sealed runtime corpus, not comprehensive FDA coverage or clinical completeness.',
                'Dates and scopes differ by dataset. FAERS activity, ingredient-report associations and patient counts are different units.',
                'No brand-wide FAERS or product safety score is inferred. Publication authorization remains false.']}
