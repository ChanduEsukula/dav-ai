"""Catalog plan regressions: fixed VM budgets, not machine-speed assertions."""
from contextlib import closing
import sqlite3

import pytest

from app.db.pharma import release_repository as repository
from app.db.pharma.release_connection import connect_release
from backend.tests.pharma_release.test_phase3_labels import db
from backend.tests.security.test_production_activation import grant  # Synthetic test-only signer.


@pytest.mark.parametrize('prefix,upper', [('xanax','xanay'), ('a%','a&'),
    ('a_','a`'), ('a\\','a]'), ('é','ê'), ('a\U0010ffff','b'), ('\U0010ffff',None)])
def test_prefix_bound_preserves_literal_and_unicode_prefixes(prefix,upper):
    assert repository._prefix_end(prefix)==upper


@pytest.mark.release_artifact
@pytest.mark.parametrize('limit,offset', [(20,0),(3,2)])
@pytest.mark.parametrize('query', ['Xanax','alprazolam','0009-0029','999999999999','xan%', 'xan_', 'xan\\', 'é'])
def test_search_uses_bounded_index_work_and_preserves_legacy_results(query,limit,offset,monkeypatch):
    with closing(connect_release()) as con:
        statements=[]
        class Connection:
            def execute(self,sql,args=()):
                statements.append((sql,args))
                return con.execute(sql,args)
            def close(self):pass
        monkeypatch.setattr(repository,'connect_release',lambda:Connection())
        # A warm search must not need millions of VM instructions. The prior
        # product-first joins exceed this budget on the same immutable artifact.
        ticks=0
        def budget():
            nonlocal ticks
            ticks+=1
            return ticks>2000
        con.set_progress_handler(budget,1000)
        result=repository.FrozenPharmaReleaseRepository().search(query,limit=limit,offset=offset)
        con.set_progress_handler(None,0)
        optimized_ids=[p['id'] for p in result]
        # Replay exactly the pre-fix discovery SQL against the same connection,
        # preserving discovery priority, deduplication, ordering and pagination.
        original_ids=[]
        for sql,args in statements:
            if 'SELECT DISTINCT' not in sql:continue
            if 'identifiers_lookup' in sql:
                sql=sql.replace(' INDEXED BY identifiers_lookup','').replace('CROSS JOIN','JOIN')
                sql=sql.replace("pi.identifier_type IN ('PRODUCT_NDC', 'PACKAGE_NDC', 'RXCUI')\n                  AND ",'')
            elif 'product_ingredients_reverse' in sql:
                sql=sql.replace('FROM ingredients i\n                CROSS JOIN product_ingredients pi INDEXED BY product_ingredients_reverse\n                  ON pi.ingredient_id = i.ingredient_id', 'FROM product_ingredients pi JOIN ingredients i ON i.ingredient_id=pi.ingredient_id').replace('CROSS JOIN','JOIN')
            elif 'INDEXED BY names_lookup' in sql:
                sql=sql.replace(' INDEXED BY names_lookup','').replace('sn.entity_id','sn.product_id').replace('CROSS JOIN','JOIN')
                sql=sql.replace('sn.normalized_name >= ?\n                      AND sn.normalized_name < ?','sn.product_id IS NOT NULL')
                args=args[2:]
            for row in con.execute(sql,args):
                if row['product_id'] not in original_ids:original_ids.append(row['product_id'])
        assert optimized_ids==original_ids[offset:offset+limit]
        if query=='Xanax':assert len(result)==min(limit,9-offset)


@pytest.mark.release_artifact
def test_signed_public_http_catalog_stays_within_query_budget(grant):
    from fastapi.testclient import TestClient
    from app.main import app
    app.middleware_stack=None
    try:
        with TestClient(app) as client:
            for path in ('/api/drugs/search?q=Xanax','/api/medications/overview?q=Xanax'):
                response=client.get(path)
                assert response.status_code==200
                value=response.json()
                assert value.get('count',value.get('matched_product_count'))==9
            assert client.get('/ready').status_code==200
            assert client.post('/api/local/research/sessions',json={}).status_code==403
            assert client.post('/api/v1/reports/pharmaceutical',json={}).status_code==403
    finally:app.middleware_stack=None


@pytest.mark.parametrize('query,alias', [
    ('literal%','literal%medicine'), ('literal_','literal_medicine'),
    ('literal\\','literal\\medicine'), ('é','éclair'), ('\U0010ffff','\U0010ffffmedicine'),
])
def test_prefix_bounds_keep_real_literal_and_unicode_matches(db,monkeypatch,query,alias):
    from contextlib import nullcontext
    db.row_factory=sqlite3.Row
    db.execute('''INSERT INTO search_names
        (entity_type,entity_id,product_id,name_role,normalized_name,original_names_json,source_id)
        VALUES ('PRODUCT','oz','oz','BRAND',?,'[]','ndc-source')''',(alias,))
    monkeypatch.setattr(repository,'connect_release',lambda:db)
    monkeypatch.setattr(repository,'closing',nullcontext)
    assert [row['id'] for row in repository.FrozenPharmaReleaseRepository().search(query)]==['oz']


@pytest.mark.release_artifact
def test_brand_overview_avoids_product_first_scan(monkeypatch):
    from app.services.pharma import medication_overview as service
    def bounded_connection():
        con=connect_release()
        ticks=0
        def budget():
            nonlocal ticks
            ticks+=1
            return ticks>500
        con.set_progress_handler(budget,1000)
        return con
    monkeypatch.setattr(service,'connect_release',bounded_connection)
    result=service.medication_overview('Xanax')
    assert result['matched_product_count']==9
    assert result['recalls']['distinct_linked_records']==2
    assert result['labels']['distinct_admitted_records']==1
    assert len(result['ingredients'])==1
