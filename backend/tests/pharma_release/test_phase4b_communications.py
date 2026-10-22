"""Offline exact evidence, reviewed scope, fail-closed extraction and replay gates."""
from copy import deepcopy
import json
from pathlib import Path
import socket
import sqlite3
import subprocess

import pytest

from backend.tests.pharma_release.test_phase4a_ae import db as ae_db, research, seed, build as build_ae
from backend.tests.pharma_release.test_phase3b_recalls import db as frozen_db, record, build as build_recalls
from backend.tests.pharma_release.test_phase3_labels import db as identity_db, insert, raw_label, build as build_labels
from scripts.pharma_release.communication_sources import (
    COLUMNS, LINK_COLUMNS, OBJECTS, SOURCE_NAME, URLS, TITLES, RECORD_IDS, DATES, EXPECTED_CONFIG,
    copy_value, parse_copy, extract_dump, validate_evidence,
)
from scripts.pharma_release.communication_build import populate, IDENTITIES, ACCEPTED, COVERAGE, EMPTY_MESSAGE, exact_matches
from scripts.pharma_release.phase4b_communications import fingerprints, normalized_manifest
from scripts.pharma_release.identity import digest_rows
from scripts.pharma_release.ids import decode_id
from scripts.pharma_release.sources import SourceError
from scripts.pharma_release.validation import validate_structure


@pytest.fixture
def evidence():
    rows = []
    bodies = ['semaglutide tirzepatide\nFDA article context.',
              TITLES[1] + '\n[Posted 12/19/2019]\ngabapentin pregabalin gabapentin pregabalin Horizant Lyrica',
              'montelukast ' * 72 + 'Singulair']
    for i in range(3):
        metadata = json.dumps({'html': 'preserved local HTML', 'scope': 'generic context', 'configured_names': EXPECTED_CONFIG['communications'][i]['names']})
        rows.append(dict(zip(COLUMNS, (RECORD_IDS[i], TITLES[i], 'FDA pharmaceutical safety communication', DATES[i], bodies[i], SOURCE_NAME, URLS[i], URLS[i], None, '2026-09-26 09:44:12-05', 'preserved-run', metadata))))
    legacy = [{'drug_id': 'legacy-product-' + str(i), 'safety_communication_id': RECORD_IDS[0] if i < 145 else RECORD_IDS[1], 'match_method': 'name', 'matched_value': 'semaglutide' if i < 142 else 'tirzepatide' if i < 145 else 'gabapentin'} for i in range(148)]
    return rows, deepcopy(EXPECTED_CONFIG), legacy


@pytest.fixture
def db(ae_db):
    insert(ae_db, 'sources', {'source_id': 'communication-source', 'source_name': SOURCE_NAME, 'capture_id': 'preserved-fixture', 'source_kind': 'CAPTURE', 'verification_basis': 'fixture', 'inputs_json': '[]'})
    for name, iid in IDENTITIES.items():
        insert(ae_db, 'ingredients', {'ingredient_id': iid, 'canonical_name': name.upper(), 'identity_rule': 'exact fixture', 'observed_at': '2026-09-26', 'source_id': 'ndc-source'})
    ae_db.commit()
    return ae_db


def build(db, evidence):
    with db:
        return populate(db, *evidence, 'communication-source')


def test_exact_counts_bodies_metadata_and_null_date(db, evidence):
    build(db, evidence)
    assert db.execute('SELECT count(*) FROM safety_communications').fetchone() == (3,)
    assert db.execute('SELECT count(*) FROM drug_communications').fetchone() == (5,)
    for row in evidence[0]:
        actual = db.execute('SELECT title,communication_type,published_date,body_text,source_url,source_record_id,source_updated_at,ingested_at FROM safety_communications WHERE source_record_id=?', (row['source_record_id'],)).fetchone()
        assert actual == tuple(row[key] for key in ('title', 'communication_type', 'published_date', 'body_text', 'source_url', 'source_record_id', 'source_updated_at', 'ingested_at'))
    assert db.execute('SELECT published_date FROM safety_communications WHERE source_record_id=?', (URLS[1],)).fetchone() == (None,)
    assert '[Posted 12/19/2019]' in evidence[0][1]['body_text']


@pytest.mark.parametrize('index,name,count', ACCEPTED)
def test_accepted_exact_edges(db, evidence, index, name, count):
    build(db, evidence)
    row = db.execute('SELECT d.applicability_class,d.source_text_evidence,d.review_basis_json,d.scope_qualifiers,c.source_record_id FROM drug_communications d JOIN safety_communications c USING(communication_id) WHERE ingredient_id=?', (IDENTITIES[name],)).fetchone()
    assert row[0] == 'INGREDIENT_CONTEXT_ONLY' and row[4] == URLS[index]
    term = json.loads(row[1]); basis = json.loads(row[2])
    assert term['exact_term'].casefold() == name and term['body_occurrences'] == count
    a, b = term['first_body_character_span']
    assert evidence[0][index]['body_text'][a:b] == term['exact_term']
    assert basis['source_text_match'] and not basis['legacy_link_reused']
    assert not basis['brand_inference_used'] and not basis['salt_inference_used']
    assert basis['configured_in_source_definition'] == (name != 'pregabalin')
    assert basis['manual_review_added'] == (name == 'pregabalin')
    assert 'not product-' in row[3]


@pytest.mark.parametrize('name', ['gabapentin enacarbil', 'montelukast alcohol', 'montelukast sodium'])
def test_rejected_candidates(db, evidence, name):
    result = build(db, evidence)
    assert not db.execute('SELECT 1 FROM drug_communications WHERE ingredient_id=?', (IDENTITIES[name],)).fetchone()
    assert next(row for row in result['rejected_candidates'] if row['canonical_name'] == name)['exact_body_occurrences'] == 0


def test_links_have_existing_ingredients_and_sources_only(db, evidence):
    build(db, evidence)
    assert db.execute('SELECT count(*) FROM drug_communications d JOIN ingredients i USING(ingredient_id)').fetchone() == (5,)
    assert db.execute('SELECT count(*) FROM safety_communications c JOIN sources s USING(source_id)').fetchone() == (3,)
    assert db.execute('SELECT DISTINCT applicability_class,policy_version FROM drug_communications').fetchall() == [('INGREDIENT_CONTEXT_ONLY', '1.0.0')]
    assert db.execute('PRAGMA foreign_key_check').fetchall() == []
    assert db.execute('PRAGMA integrity_check').fetchall() == [('ok',)]
    assert validate_structure(db)['passed']


def test_no_legacy_product_uuid_or_new_product_table(db, evidence):
    schema = db.execute('SELECT type,name,sql FROM sqlite_master ORDER BY type,name').fetchall()
    build(db, evidence)
    assert schema == db.execute('SELECT type,name,sql FROM sqlite_master ORDER BY type,name').fetchall()
    assert len(db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()) == 19
    assert not any('legacy-product' in str(row) for row in db.execute('SELECT * FROM drug_communications'))
    for (cid,) in db.execute('SELECT communication_id FROM safety_communications'):
        assert decode_id(cid)[0:2] == ('communication', SOURCE_NAME)
        assert decode_id(cid)[2] in URLS and cid not in RECORD_IDS


def test_coverage_unknown_is_not_absence(db, evidence):
    build(db, evidence)
    for name in IDENTITIES:
        state, measured, scope, notes = db.execute("SELECT state,measured_count,scope,limitations_json FROM coverage WHERE entity_id=? AND domain='safety_communications'", (IDENTITIES[name],)).fetchone()
        linked = name in {name for _, name, _ in ACCEPTED}
        assert (state, measured) == (('PARTIAL', 1) if linked else ('UNKNOWN', None))
        assert COVERAGE in scope
        if not linked:
            assert EMPTY_MESSAGE in json.loads(notes)
    assert db.execute("SELECT count(*) FROM coverage WHERE domain='safety_communications' AND entity_type='PRODUCT'").fetchone() == (0,)


def test_real_prior_identity_label_recall_ae_rows_unchanged(db, research, evidence):
    build_labels(db, [raw_label(ndcs=['0001-101'])]); build_recalls(db, [record()])
    seed(research); build_ae(db, research)
    before = fingerprints(db)
    build(db, evidence)
    assert before == fingerprints(db)


def test_replay_and_duplicate_projection(db, evidence):
    first = build(db, evidence); changes = db.total_changes
    second = build(db, evidence)
    assert first['projection'] == second['projection'] and db.total_changes == changes
    assert not any(second['inserted'].values())
    duplicate = sqlite3.connect(':memory:'); db.backup(duplicate); duplicate.execute('PRAGMA foreign_keys=ON')
    duplicate.execute("DELETE FROM coverage WHERE domain='safety_communications'")
    duplicate.execute('DELETE FROM drug_communications'); duplicate.execute('DELETE FROM safety_communications'); duplicate.commit()
    assert first['projection'] == build(duplicate, evidence)['projection']
    duplicate.close()


def test_nonidentical_replay_rejected(db, evidence):
    build(db, evidence)
    evidence[0][0]['body_text'] += '\nchanged captured text'
    with pytest.raises(SourceError, match='Nonidentical'):
        build(db, evidence)


@pytest.mark.parametrize('mutation', ['row_count', 'url', 'source', 'config', 'raw_scope', 'raw_names', 'empty_body', 'term_absent', 'title_review', 'legacy_count', 'identity', 'rejected_term'])
def test_fail_closed(db, evidence, mutation):
    rows, config, legacy = evidence
    if mutation == 'row_count': rows.pop()
    if mutation == 'url': rows[0]['source_url'] = 'unexpected'
    if mutation == 'source': rows[0]['source'] = 'unexpected'
    if mutation == 'config': config['communications'][1]['names'].append('pregabalin')
    if mutation in ('raw_scope', 'raw_names'):
        metadata = json.loads(rows[0]['raw_json'])
        metadata['scope' if mutation == 'raw_scope' else 'configured_names'] = 'changed'
        rows[0]['raw_json'] = json.dumps(metadata)
    if mutation == 'empty_body': rows[0]['body_text'] = ''
    if mutation == 'term_absent': rows[0]['body_text'] = 'tirzepatide only'
    if mutation == 'title_review': rows[1]['title'] = 'Gabapentinoids'
    if mutation == 'legacy_count': legacy.pop()
    if mutation == 'identity': db.execute('DELETE FROM ingredients WHERE ingredient_id=?', (IDENTITIES['pregabalin'],)); db.commit()
    if mutation == 'rejected_term': rows[2]['body_text'] += ' montelukast sodium'
    with pytest.raises(SourceError): build(db, evidence)
    assert db.execute('SELECT count(*) FROM safety_communications').fetchone() == (0,)


def test_whole_exact_terms_no_fuzzy_brand_or_salt_expansion():
    assert len(exact_matches('semaglutide semaglutides xsemaglutide SEMAGLUTIDE', 'semaglutide')) == 2
    assert not exact_matches('Horizant gabapentin', 'gabapentin enacarbil')
    assert not exact_matches('Singulair montelukast', 'montelukast sodium')


@pytest.mark.parametrize('raw,expected', [(r'\N', None), (r'literal\\N', r'literal\N'), (r'a\nb\tc\\d', 'a\nb\tc\\d'), (r'\141\x62', 'ab'), ('é', 'é'), ('end\\\\', 'end\\')])
def test_copy_decoder(raw, expected):
    assert copy_value(raw) == expected


def copy_sql(table, columns, records):
    def escape(value):
        return r'\N' if value is None else str(value).replace('\\', '\\\\').replace('\n', r'\n').replace('\t', r'\t').replace('\r', r'\r')
    return f"COPY pharma.{table} ({', '.join(columns)}) FROM stdin;\n" + '\n'.join('\t'.join(escape(row[field]) for field in columns) for row in records) + '\n\\.\n'


def test_parse_copy_preserves_escaped_body_and_raw_json(evidence):
    rows, _, _ = evidence
    rows[0]['body_text'] += '\n\\literal\ttab\rcarriage é'
    assert parse_copy(copy_sql('safety_communications', COLUMNS, rows), 'safety_communications', COLUMNS) == rows


@pytest.mark.parametrize('sql', ['COPY pharma.other (id) FROM stdin;\n1\n\\.\n', 'COPY pharma.test (id) FROM stdin;\na\tb\n\\.\n', 'COPY pharma.test (id) FROM stdin;\na\n', 'COPY pharma.test (id) FROM stdin;\na\n\\.\nCOPY pharma.test (id) FROM stdin;\nb\n\\.\n'])
def test_copy_unexpected_blocks_fail(sql):
    with pytest.raises(SourceError): parse_copy(sql, 'test', ('id',))


def test_extraction_no_network_or_server_and_only_exact_objects(monkeypatch, tmp_path, evidence):
    def forbidden(*args, **kwargs):
        raise AssertionError('Network forbidden in Phase 4B')
    monkeypatch.setattr(socket, 'socket', forbidden)
    monkeypatch.setattr(socket, 'create_connection', forbidden)
    calls = []
    def local_restore(command, **kwargs):
        calls.append(command)
        assert command[0] == 'pg_restore' and not any(arg in command for arg in ('-d', '--dbname'))
        if '--list' in command: result = '\n'.join(OBJECTS.values())
        elif '--version' in command: result = 'pg_restore local fixture'
        else:
            selected = Path(command[command.index('--use-list') + 1]).read_text().strip()
            assert selected in OBJECTS.values()
            table = next(table for table, object_id in OBJECTS.items() if object_id == selected)
            result = copy_sql(table, COLUMNS if table == 'safety_communications' else LINK_COLUMNS, evidence[0] if table == 'safety_communications' else evidence[2])
        return subprocess.CompletedProcess(command, 0, result, '')
    monkeypatch.setattr(subprocess, 'run', local_restore)
    rows, links, method = extract_dump(tmp_path / 'local.dump', executable='pg_restore')
    assert (rows, links) == (evidence[0], evidence[2])
    assert not method['network_used'] and not method['postgresql_server_used']
    assert len(calls) == 4


def test_changed_toc_fails_before_extract(monkeypatch, tmp_path):
    monkeypatch.setattr(subprocess, 'run', lambda command, **kwargs: subprocess.CompletedProcess(command, 0, 'unexpected object', ''))
    with pytest.raises(SourceError, match='exact dump TOC'):
        extract_dump(tmp_path / 'local.dump', executable='pg_restore')


def test_manifest_only_build_timestamp_may_differ():
    assert normalized_manifest({'build_time_utc': 'a', 'table_counts_json': 'fixed'}) == normalized_manifest({'build_time_utc': 'b', 'table_counts_json': 'fixed'})
    assert normalized_manifest({'table_counts_json': 'fixed'}) != normalized_manifest({'table_counts_json': 'changed'})
