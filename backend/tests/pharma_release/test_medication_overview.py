"""Discovery scope/deduplication with real in-memory schema; no external services."""
from contextlib import nullcontext
import sqlite3
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.pharma import medication_overview as service
from app.db.pharma import release_repository
from backend.tests.pharma_release.test_phase3b_recalls import db, build, record
from backend.tests.pharma_release.test_phase3_labels import db as identity_db, insert, raw_label, build as label_build


@pytest.fixture
def discovery(db, monkeypatch):
    for pid in ['oz', 'weg', 'ry']:
        insert(db, 'search_names', dict(entity_type='PRODUCT', entity_id=pid, product_id=pid,
            name_role='BRAND_BASE', normalized_name='family', original_names_json='["Family"]', source_id='ndc-source'))
    db.commit()
    monkeypatch.setattr(service, 'connect_release', lambda: db)
    monkeypatch.setattr(service, 'closing', nullcontext)
    monkeypatch.setattr(release_repository, 'connect_release', lambda: db)
    monkeypatch.setattr(release_repository, 'closing', nullcontext)
    monkeypatch.setattr(service, 'release_metadata', lambda: {'release_id': 'synthetic', 'publication_authorized': False})
    yield db


def prepare(connection):
    connection.row_factory = sqlite3.Row


def test_duplicate_recall_links_are_one_record_and_unrelated_products_are_excluded(discovery):
    build(discovery, [record('NDC 0001-101 and NDC 0001-102', number='R-1'),
        record('NDC 0001-101', number='R-2'), record('NDC 0002-101', number='UNRELATED')])
    prepare(discovery)
    result = service.medication_overview('Family')
    assert result['matched_product_count'] == 3
    assert result['recalls']['distinct_linked_records'] == 2
    assert result['recalls']['product_recall_links'] == 3
    assert {row['recall_number'] for row in result['recalls']['records']} == {'R-1', 'R-2'}
    # R-1 and R-2 deliberately share FDA event_id: these are distinct records, not events.
    linked = next(row for row in result['recalls']['records'] if row['recall_number'] == 'R-1')
    assert len(linked['product_links']) == 2
    assert linked['reason_for_recall'] == '  Exact source reason.\nSecond line  '
    assert linked['product_links'][0]['lot_scope']


def test_shared_labels_and_ingredients_are_not_summed_across_products(discovery):
    label_build(discovery, [raw_label('shared', ndcs=['0001-101', '0001-102'])])
    prepare(discovery)
    result = service.medication_overview('Family')
    assert result['labels']['distinct_admitted_records'] == 1
    assert result['labels']['product_label_links'] == 2
    assert len(result['ingredients']) == 1
    assert result['ingredients'][0]['report_count'] is None
    assert result['ingredients'][0]['reactions'] == []
    assert len(result['formulations']) == 2  # oral and injected formulations stay distinct


def test_withheld_labels_are_not_promoted_into_medication_counts(discovery):
    label_build(discovery, [raw_label('withheld', ndcs=['0001-101'])])
    discovery.execute('UPDATE product_labels SET consumer_eligible=0')
    prepare(discovery)
    result = service.medication_overview('family')
    assert result['labels']['distinct_admitted_records'] == 0
    assert result['labels']['products_with_labels'] == 0


def test_bounded_overview_declares_truncation(discovery, monkeypatch):
    monkeypatch.setattr(service, 'MAX_PRODUCTS', 1)
    prepare(discovery)
    result = service.medication_overview('family')
    assert result['truncated'] and result['matched_product_count'] == 1
    assert len(result['products']) == 1


@pytest.mark.parametrize('query', ['', ' ', 'x' * 201])
def test_invalid_discovery_query_is_rejected_before_read(query, monkeypatch):
    monkeypatch.setattr('app.routes.medications.medication_overview', lambda _: pytest.fail('No database read'))
    response = TestClient(app).get('/api/medications/overview', params={'q': query})
    assert response.status_code == 422


@pytest.mark.parametrize('env', ['staging', 'production', 'preview'])
def test_new_read_endpoints_keep_hosted_denial(env, monkeypatch):
    monkeypatch.setenv('DAVAI_ENV', env)
    client = TestClient(app)
    assert client.get('/api/medications/overview?q=Xanax').status_code == 503
    assert client.get('/api/coverage/inventory').status_code == 503


@pytest.mark.release_artifact
def test_real_xanax_discovery_and_inventory_preserve_scope():
    result = service.medication_overview('Xanax')
    assert result['matched_product_count'] == 9
    assert result['recalls']['distinct_linked_records'] == 2
    assert len({row['id'] for row in result['recalls']['records']}) == 2
    assert result['labels']['distinct_admitted_records'] == 1
    assert result['labels']['product_label_links'] == 4
    assert len(result['ingredients']) == 1 and result['ingredients'][0]['ingredient_name'] == 'alprazolam'
    assert result['ingredients'][0]['report_count'] == 18
    assert any('XR' in name for product in result['products'] for name in product['brand_names'])
    inventory = service.data_inventory()
    metrics = {metric['key']: metric['value'] for metric in inventory['metrics']}
    assert metrics['labels'] == 83684 and metrics['recalls'] == 17974
    assert inventory['release']['publication_authorized'] is False
