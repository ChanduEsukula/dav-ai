import asyncio
from copy import deepcopy
import json
import os
from uuid import uuid4

import httpx
import psycopg
import pytest

from app.db.pharma.drug_repository import DrugRepository
from app.db.pharma.ingestion_run_repository import IngestionRunRepository
from app.db.pharma.safety_repository import SafetyRepository
from app.services.pharma.ndc_ingestion import normalize_ndc_record, SOURCE
from app.services.pharma.safety_ingestion import ingest_safety, SafetyFDAClient
from app.services.pharma.safety_records import normalize_record, SOURCES
from app.services.pharma.safety_matching import CatalogIndex, match_mentions
from app.services.pharma.communications_ingestion import ingest_communications, FDAArticleParser, official_url, CommunicationClient


@pytest.fixture
def drug(pharma_db, ndc_record):
    run = IngestionRunRepository().start(SOURCE, {})
    return DrugRepository().upsert(normalize_ndc_record(ndc_record, run))[0]


@pytest.fixture
def label():
    return {'id': 'label-document-1', 'set_id': 'label-family-1', 'version': '1', 'effective_time': '20240101',
            'boxed_warning': ['Source warning'], 'warnings': ['Source precaution'], 'contraindications': ['Source contraindication'],
            'openfda': {'product_ndc': ['12345-6789'], 'generic_name': ['Example Ingredient']}}


@pytest.fixture
def recall():
    return {'recall_number': 'D-TEST-2025', 'event_id': 'event-test', 'report_date': '20250202',
            'recall_initiation_date': '20250201', 'product_description': 'Example product',
            'reason_for_recall': 'Source reason', 'status': 'Ongoing', 'classification': 'Class II',
            'code_info': 'Lot TEST', 'openfda': {'product_ndc': ['12345-6789']}}


@pytest.fixture
def event():
    return {'safetyreportid': 'report-1', 'safetyreportversion': '2', 'receivedate': '20250301',
            'receiptdate': '20250401', 'serious': '1', 'seriousnesshospitalization': '1',
            'patient': {'drug': [{'medicinalproduct': 'Example Brand', 'drugcharacterization': '1',
                                 'openfda': {'rxcui': ['1234567']}}],
                        'reaction': [{'reactionmeddrapt': 'NAUSEA'}, {'reactionmeddrapt': 'NAUSEA'}]}}


class Source:
    def __init__(self, records, total=None):
        self.records = records
        self.total = total or len(records)
    async def fetch(self, kind, query, limit):
        return deepcopy(self.records), {'available': self.total, 'fetched': len(self.records), 'truncated': self.total > len(self.records)}


def ingest(kind, records, total=None):
    return asyncio.run(ingest_safety(kind, limit=5, start='2024-01-01', end='2025-12-31', client=Source(records, total)))


@pytest.mark.parametrize('kind,fixture', [('labels', 'label'), ('recalls', 'recall'), ('adverse_events', 'event')])
def test_ingestion_linking_idempotency_and_provenance(drug, request, kind, fixture):
    raw = request.getfixturevalue(fixture)
    first = ingest(kind, [raw])
    second = ingest(kind, [raw])
    assert first['counts']['inserted'] == 1 and first['counts']['unresolved'] == 0
    assert second['counts']['inserted'] == 0 and second['counts']['updated'] == 1
    section = SafetyRepository().section(kind, drug['id'])
    assert len(section['records']) == 1
    record = section['records'][0]
    assert record['source'] == SOURCES[kind][0]
    assert record['source_updated_at'] is None and record['ingested_at']
    assert record['source_url'].startswith('https://api.fda.gov/')
    assert section['coverage']['last_attempt']['status'] == 'succeeded'
    if kind == 'recalls':
        assert record['reported_status'] == 'Ongoing' and 'status' not in record
    if kind == 'adverse_events':
        assert record['reported_drugs'][0]['drugcharacterization'] == '1'
        assert record['reactions'] == ['NAUSEA']


def test_label_versions_latest_and_unresolved(drug, label):
    newer = deepcopy(label)
    newer.update(id='label-document-2', version='2', effective_time='20250601')
    unresolved = deepcopy(label)
    unresolved.update(id='unresolved', openfda={'product_ndc': ['99999-1111'], 'generic_name': ['Example Ingredient']})
    result = ingest('labels', [label, newer, unresolved])
    assert result['counts']['unresolved'] == 1
    section = SafetyRepository().safety(drug['id'])['labels']
    assert len(section['records']) == 2
    assert section['latest_records'][0]['label_version'] == '2'
    assert section['records'][0]['drug_interactions'] is None
    with psycopg.connect(os.environ['DATABASE_URL']) as conn:
        assert conn.execute('SELECT count(*) FROM pharma.drug_labels').fetchone()[0] == 3


def test_report_dedup_and_older_version_never_replaces(drug, ndc_record, event):
    run = IngestionRunRepository().start(SOURCE, {})
    other = deepcopy(ndc_record)
    other.update(product_id='second-product', product_ndc='54321-1111', generic_name='Second Ingredient')
    other['openfda'] = {'rxcui': ['7654321']}
    second = DrugRepository().upsert(normalize_ndc_record(other, run))[0]
    event['patient']['drug'].append({'medicinalproduct': 'Second Ingredient', 'drugcharacterization': '2', 'openfda': {'rxcui': ['7654321']}})
    result = ingest('adverse_events', [event], total=900)
    assert result['counts']['fetched'] == 2 and result['counts']['inserted'] == 1
    for d in (drug, second):
        summary = SafetyRepository().safety(d['id'])['adverse_events']['summary']
        assert summary['stored_report_count'] == 1 and summary['serious_report_count'] == 1
        assert summary['top_reported_reactions'][0]['report_count'] == 1
    older = deepcopy(event)
    older['safetyreportversion'] = '1'
    older['patient']['reaction'] = []
    result = ingest('adverse_events', [older])
    assert result['older_versions_ignored'] == 1
    assert SafetyRepository().section('adverse_events', drug['id'])['records'][0]['report_version'] == '2'
    assert SafetyRepository().section('adverse_events', second['id'])['records']


def test_updated_record_replaces_links_atomically(drug, label):
    ingest('labels', [label])
    label['openfda'] = {'product_ndc': ['00000-0000'], 'generic_name': ['Example Ingredient']}
    ingest('labels', [label])
    assert not SafetyRepository().section('labels', drug['id'])['records']


def test_failure_keeps_usable_data_and_coverage(drug, label):
    ingest('labels', [label])
    class Broken:
        async def fetch(self, *args): raise httpx.ConnectError('no network')
    result = asyncio.run(ingest_safety('labels', client=Broken()))
    assert result['status'] == 'failed'
    section = SafetyRepository().section('labels', drug['id'])
    assert len(section['records']) == 1
    assert section['coverage']['last_attempt']['status'] == 'failed'
    assert section['coverage']['last_ingested_at']


def test_communication_ingestion_and_html_extraction(drug, tmp_path):
    html = '''<html><head><meta property="article:published_time" content="2025-06-01"><meta property="article:modified_time" content="2025-06-02T12:00:00Z"></head>
    <body><nav>Ignore navigation</nav><main><h1>Official example communication</h1><p>Example Ingredient is discussed in this official test communication. The content is sufficiently long to represent the article body rather than a navigation or error page.</p><script>ignore script</script></main></body></html>'''
    url = 'https://www.fda.gov/drugs/test-communication'
    path = tmp_path / 'communications.json'
    path.write_text(json.dumps({'communications': [{'url': url, 'names': ['Example Ingredient'], 'scope': 'generic'}]}))
    class Client:
        async def fetch(self, url): return html, url
    first = asyncio.run(ingest_communications(config=path, client=Client()))
    second = asyncio.run(ingest_communications(config=path, client=Client()))
    assert first['counts']['inserted'] == 1 and second['counts']['updated'] == 1
    row = SafetyRepository().section('communications', drug['id'])['records'][0]
    assert str(row['published_date']) == '2025-06-01'
    assert row['source_updated_at'] and row['source_url'] == url
    assert 'Ignore navigation' not in row['body_text'] and 'ignore script' not in row['body_text']
    class Broken:
        async def fetch(self, url): raise httpx.ConnectError('offline')
    assert asyncio.run(ingest_communications(config=path, client=Broken()))['status'] == 'failed'
    assert len(SafetyRepository().section('communications', drug['id'])['records']) == 1


def test_ingestion_repository_and_timeline_offline(drug, label, recall, event, monkeypatch):
    ingest('labels', [label]); ingest('recalls', [recall]); ingest('adverse_events', [event], total=1234)
    def forbidden(*args, **kwargs): raise AssertionError('No upstream reads')
    monkeypatch.setattr(httpx.AsyncClient, 'get', forbidden)
    data = SafetyRepository().safety(drug['id'])
    assert data['recalls']['records'][0]['reported_status'] == 'Ongoing'
    assert data['adverse_events']['summary']['stored_report_count'] == 1
    coverage = data['adverse_events']['coverage']
    assert coverage['truncated'] and coverage['stored_record_count'] == 1
    assert coverage['last_attempt']['parameters']['sample_window']['start'] == '2024-01-01'
    assert list(coverage['last_attempt']['coverage'].values())[0]['available'] == 1234
    assert 'No records in Dav AI' in data['communications']['coverage']['empty_message']
    timeline = SafetyRepository().timeline(drug['id'])
    assert [e['date'] for e in timeline] == sorted([e['date'] for e in timeline], reverse=True)
    assert timeline[0]['date_type'] == 'received_date'
    assert 'not the adverse-event occurrence date' in timeline[0]['summary']


def test_link_foreign_key_rolls_back_record(drug, label):
    run = IngestionRunRepository().start(SOURCES['labels'][0], {})
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        SafetyRepository().upsert('labels', normalize_record('labels', label, run), [(uuid4(), 'ndc', '123')])
    import os
    with psycopg.connect(os.environ['DATABASE_URL']) as conn:
        assert conn.execute('SELECT count(*) FROM pharma.drug_labels').fetchone()[0] == 0


@pytest.mark.parametrize('url', ['http://www.fda.gov/drugs/a', 'https://www.fda.gov.evil.example/drugs/a', 'https://127.0.0.1/drugs/a', 'https://user@www.fda.gov/drugs/a'])
def test_communication_url_allowlist(url):
    with pytest.raises(ValueError): official_url(url)


def test_no_name_fallback_for_conflicting_identifier(drug):
    assert match_mentions(CatalogIndex([drug]), 'labels', {'openfda': {'product_ndc': ['00000-0000'], 'generic_name': ['Example Ingredient']}}) == []


def test_fda_client_window_and_source_total():
    seen = []
    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={'results': [{'safetyreportid': '1'}], 'meta': {'results': {'total': 90}, 'last_updated': '2025-01-01'}})
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            return await SafetyFDAClient(http).fetch('adverse_events', 'receivedate:[20240101 TO 20251231]', 1)
    rows, coverage = asyncio.run(run())
    assert len(rows) == 1 and coverage['available'] == 90 and coverage['truncated']
    assert seen[0].url.params['sort'] == 'receivedate:desc'


def test_redirect_allowlist_checked_before_next_request():
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(302, headers={'location': 'https://evil.example/drugs/a'})
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            await CommunicationClient(http).fetch('https://www.fda.gov/drugs/a')
    with pytest.raises(ValueError): asyncio.run(run())
    assert len(calls) == 1


def test_failed_refresh_does_not_claim_untruncated_coverage(drug, label):
    ingest('labels', [label], total=200)
    class Broken:
        async def fetch(self, *args): raise httpx.ConnectError('offline')
    asyncio.run(ingest_safety('labels', client=Broken()))
    coverage = SafetyRepository().section('labels', drug['id'])['coverage']
    assert coverage['truncated'] is None
    assert coverage['query_status'] == 'failed'
    assert coverage['stored_record_count'] == 1


def test_offline_sections_are_stored_reads(drug, label, monkeypatch):
    ingest('labels', [label])
    def forbidden(*args, **kwargs): raise AssertionError('Upstream access forbidden')
    monkeypatch.setattr(httpx.AsyncClient, 'request', forbidden)
    monkeypatch.setattr(httpx.HTTPTransport, 'handle_request', forbidden)
    for section in SOURCES:
        result = SafetyRepository().section(section, drug['id'])
        assert 'coverage' in result


def test_matching_ambiguity_and_order_independence(drug):
    other = dict(drug, id=uuid4(), product_ndcs=['54321-1111'], package_ndcs=[])
    for catalog in ([drug, other], [other, drug]):
        index = CatalogIndex(catalog)
        assert match_mentions(index, 'labels', {'openfda': {'generic_name': ['Example Ingredient']}}) == []
        assert match_mentions(index, 'labels', {'openfda': {'rxcui': ['1234567']}}) == []
        links = match_mentions(index, 'labels', {'openfda': {'product_ndc': ['54321-1111', '12345-6789']}})
        reverse = match_mentions(index, 'labels', {'openfda': {'product_ndc': ['12345-6789', '54321-1111']}})
        assert links == reverse and len(links) == 2
        assert match_mentions(index, 'labels', {'openfda': {'product_ndc': ['12345-6789'], 'rxcui': ['999']}}) == []


def test_cross_query_versions_choose_newest_independent_of_order(drug, ndc_record, event):
    run = IngestionRunRepository().start(SOURCE, {})
    other = deepcopy(ndc_record)
    other.update(product_id='second', product_ndc='54321-1111', generic_name='Second Ingredient')
    DrugRepository().upsert(normalize_ndc_record(other, run))
    older = deepcopy(event)
    older['safetyreportversion'] = '1'
    older['patient']['reaction'] = []
    class Overlapping:
        def __init__(self, records): self.records = iter(records)
        async def fetch(self, *args):
            return [next(self.records)], {'available': 1, 'fetched': 1, 'truncated': False}
    for versions in ([event, older], [older, event]):
        result = asyncio.run(ingest_safety('adverse_events', client=Overlapping(versions)))
        assert result['counts']['fetched'] == 2
        with psycopg.connect(os.environ['DATABASE_URL']) as conn:
            rows = conn.execute('SELECT report_version, reactions FROM pharma.adverse_events').fetchall()
        assert rows == [('2', ['NAUSEA'])]
