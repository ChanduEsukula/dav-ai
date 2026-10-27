from psycopg import sql
from psycopg.types.json import Jsonb
from app.db.pharma.connection import connect
from app.services.pharma.normalization import normalize_name, normalize_ndc, normalize_rxcui

FIELDS = (
    'generic_name', 'normalized_generic_name', 'brand_names', 'normalized_names',
    'active_ingredients', 'strength', 'dosage_form', 'routes', 'manufacturers',
    'rxcui', 'product_ndcs', 'package_ndcs', 'source', 'source_record_id',
    'source_url', 'source_updated_at', 'ingestion_run_id', 'raw_json',
)


class DrugRepository:
    def upsert(self, drug: dict):
        """Source product identity is durable; refresh never merges by a bare name."""
        values = [Jsonb(drug[f]) if f == 'raw_json' else drug[f] for f in FIELDS]
        updates = sql.SQL(', ').join(
            sql.SQL('{}=EXCLUDED.{}').format(sql.Identifier(f), sql.Identifier(f))
            for f in FIELDS if f not in ('source', 'source_record_id')
        )
        query = sql.SQL('''INSERT INTO pharma.drugs ({}) VALUES ({})
            ON CONFLICT (source, source_record_id) DO UPDATE SET {}, ingested_at=now()
            RETURNING *, (xmax = 0) AS inserted''').format(
                sql.SQL(', ').join(map(sql.Identifier, FIELDS)),
                sql.SQL(', ').join(sql.Placeholder() for _ in FIELDS), updates)
        with connect() as conn:
            row = conn.execute(query, values).fetchone()
            inserted = row.pop('inserted')
            return row, 'inserted' if inserted else 'updated'

    def find_by_id(self, drug_id):
        with connect() as conn:
            return conn.execute('SELECT * FROM pharma.drugs WHERE id=%s', (drug_id,)).fetchone()

    def _find(self, predicate, params):
        with connect() as conn:
            return conn.execute('SELECT * FROM pharma.drugs WHERE ' + predicate +
                                ' ORDER BY generic_name, id', params).fetchall()

    def find_by_normalized_name(self, name):
        return self._find('normalized_names @> ARRAY[%s]::text[]', (normalize_name(name),))

    def find_by_rxcui(self, rxcui):
        value = normalize_rxcui(rxcui)
        return self._find('rxcui=%s', (value,)) if value else []

    def find_by_ndc(self, ndc):
        value = normalize_ndc(ndc)
        return self._find('(product_ndcs @> ARRAY[%s]::text[] OR package_ndcs @> ARRAY[%s]::text[])',
                          (value, value)) if value else []

    def search(self, query: str, *, limit=20, offset=0):
        normalized = normalize_name(query)
        # LIKE metacharacters are user text, not search syntax.
        pattern = '%' + normalized.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'
        with connect() as conn:
            return conn.execute('''SELECT * FROM pharma.drugs WHERE
                rxcui=%s OR product_ndcs @> ARRAY[%s]::text[] OR package_ndcs @> ARRAY[%s]::text[]
                OR EXISTS (SELECT 1 FROM unnest(normalized_names) n WHERE n LIKE %s)
                ORDER BY (normalized_generic_name=%s) DESC, normalized_generic_name, id
                LIMIT %s OFFSET %s''',
                (normalize_rxcui(query), normalize_ndc(query), normalize_ndc(query), pattern,
                 normalized, max(1, min(limit, 100)), max(0, offset))).fetchall()

    def list_overviews(self, *, limit=20, offset=0):
        with connect() as conn:
            return conn.execute('SELECT * FROM pharma.drugs ORDER BY normalized_generic_name, id LIMIT %s OFFSET %s',
                                (max(1, min(limit, 100)), max(0, offset))).fetchall()
