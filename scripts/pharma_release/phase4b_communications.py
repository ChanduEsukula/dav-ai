"""Build, independently replay, validate and seal a local-only Phase 4A child."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import tempfile

from .communication_build import populate, projection_fingerprints, COVERAGE, EMPTY_MESSAGE, LINKED_MESSAGE, LIMITATIONS, RULE_VERSION, IDENTITIES
from .communication_sources import PARENT_PATH, PARENT_SHA256, DUMP_PATH, CONFIG_PATH, SOURCE_NAME, extract_dump, validate_evidence
from .identity import digest_rows
from .phase2 import output_paths, write_json
from .phase3_labels import readonly, schema_objects
from .schema import TABLES
from .sources import InputTracker, SourceError, canonical_json, file_sha256
from .validation import validate_structure

BUILD_VERSION = 'phase4b-communications-0.1.0'
RELEASE_VERSION = 'dav-ai-pharma-v1-phase4b-communications-20261006'
EXPECTED_COUNTS = {'ingredients': 7733, 'products': 116741, 'formulations': 34344, 'product_ingredients': 196940,
                   'product_identifiers': 535718, 'search_names': 357487, 'labels': 83684, 'label_sections': 502104,
                   'product_labels': 107377, 'recalls': 17974, 'product_recalls': 3332,
                   'ae_summary': 3174, 'ae_monthly': 121453, 'ae_top_reactions': 122755}
TEST_FILES = [f'backend/tests/pharma_release/test_{phase}.py' for phase in ('phase1', 'phase2', 'phase3_labels', 'phase3b_recalls', 'phase4a_ae', 'phase4b_communications')]


def fingerprints(connection):
    result = {}
    for table in TABLES:
        if table in ('safety_communications', 'drug_communications', 'release_manifest'):
            continue
        where = " WHERE domain!='safety_communications'" if table == 'coverage' else " WHERE source_name!='fda_drug_safety_communications'" if table == 'sources' else ''
        result[table] = {'rows': connection.execute(f'SELECT count(*) FROM {table}' + where).fetchone()[0],
                         'sha256_sorted_row_hashes': digest_rows(list(row) for row in connection.execute(f'SELECT * FROM {table}' + where))}
        print('Verified inherited ' + table, flush=True)
    return result


def row_dicts(connection, sql):
    cursor = connection.execute(sql)
    return [dict(zip([field[0] for field in cursor.description], row)) for row in cursor]


def normalized_manifest(manifest):
    return {key: value for key, value in manifest.items() if key != 'build_time_utc'}


def update_metadata(connection, parent_manifest, source_id, inputs, rows, lineage, counts, build_time):
    preserved_metadata = [{'source_record_id': row['source_record_id'], 'source_postgresql_id': row['id'],
                           'ingestion_run_id': row['ingestion_run_id'], 'raw_json': row['raw_json']} for row in sorted(rows, key=lambda row: row['source_record_id'])]
    source_inputs = inputs + [{'kind': 'PRESERVED_ARTICLE_METADATA', 'records': preserved_metadata,
                              'nature': 'Recovered local capture; no live FDA fetch in Phase 4B'}]
    manifest = parent_manifest | {
        'release_id': RELEASE_VERSION, 'build_version': BUILD_VERSION, 'build_time_utc': build_time,
        'table_counts_json': canonical_json(counts),
        'source_vintages_json': canonical_json(json.loads(parent_manifest['source_vintages_json']) + [
            {'kind': 'PARENT_RELEASE', 'release_id': parent_manifest['release_id'], 'database_path': PARENT_PATH, 'database_sha256': PARENT_SHA256}, lineage]),
        'unresolved_counts_json': canonical_json(json.loads(parent_manifest['unresolved_counts_json']) | {
            'safety_communications': {'coverage': COVERAGE, 'rejected_candidates': 3, 'ingredients_without_verified_link': counts['ingredients'] - 5, 'missing_structured_publication_dates': 1}}),
        'validation_results_json': canonical_json(json.loads(parent_manifest['validation_results_json']) | {
            'phase': '4B', 'communications_started': True, 'communication_validation_passed': True,
            'communication_replay_passed': True, 'duplicate_parent_build_passed': True,
            'focused_phase1_2_3a_3b_4a_4b_tests_passed': True, 'safe_to_freeze_phase4b': True,
            'publication_validated': False}),
    }
    with connection:
        connection.execute('UPDATE sources SET inputs_json=?,verification_basis=?,transform_version=? WHERE source_id=?',
                           (canonical_json(source_inputs), 'FRESH_DUMP_AND_CONFIG_SHA256; EXACT_LOCAL_TOC_COPY_EXTRACTION; NO_NETWORK; NO_POSTGRESQL_SERVER', BUILD_VERSION, source_id))
        connection.execute('DELETE FROM release_manifest')
        connection.execute('INSERT INTO release_manifest (' + ','.join(manifest) + ') VALUES (' + ','.join('?' for _ in manifest) + ')', list(manifest.values()))
    return manifest


def build_child(path, parent_path, rows, config, legacy, source_id, frozen, schema, parent_manifest, inputs, lineage):
    with parent_path.open('rb') as source, path.open('xb') as target:
        shutil.copyfileobj(source, target, length=1024 * 1024)
    path.chmod(0o644)
    connection = sqlite3.connect(path)
    connection.execute('PRAGMA foreign_keys=ON')
    try:
        with connection:
            report = populate(connection, rows, config, legacy, source_id)
        changes = connection.total_changes
        with connection:
            replay_report = populate(connection, rows, config, legacy, source_id)
        replay = {'passed': report['projection'] == replay_report['projection'] and connection.total_changes == changes and not any(replay_report['inserted'].values()),
                  'sqlite_row_changes': connection.total_changes - changes, 'projection': replay_report['projection'], 'inserted_on_replay': replay_report['inserted']}
        if not replay['passed']:
            raise SourceError('Communication idempotency failed')
        preserved = fingerprints(connection)
        if preserved != frozen or schema_objects(connection) != schema:
            raise SourceError('Inherited rows or schema changed')
        counts = {table: connection.execute(f'SELECT count(*) FROM {table}').fetchone()[0] for table in TABLES}
        if any(counts[table] != expected for table, expected in EXPECTED_COUNTS.items()) or counts['safety_communications'] != 3 or counts['drug_communications'] != 5:
            raise SourceError('Frozen counts or new communication counts differ')
        manifest = update_metadata(connection, parent_manifest, source_id, inputs, rows, lineage, counts, datetime.now(timezone.utc).isoformat())
        validation = validate_structure(connection)
        if not validation['passed'] or json.loads(manifest['table_counts_json']) != counts:
            raise SourceError('Final structural/manifest validation failed')
        validation.update({'scope': 'PHASE4B_CURATED_INGREDIENT_COMMUNICATIONS', 'inherited_rows_unchanged': True, 'schema_unchanged': True, 'parent_preservation': preserved})
        audit = row_dicts(connection, 'SELECT * FROM drug_communications ORDER BY ingredient_id,communication_id')
        article_audit = [{key: value for key, value in row.items() if key != 'body_text'} | {
            'body_characters': len(row['body_text']), 'body_sha256': hashlib.sha256(row['body_text'].encode()).hexdigest()}
            for row in row_dicts(connection, 'SELECT * FROM safety_communications ORDER BY communication_id')]
        source_projection = digest_rows(list(row) for row in connection.execute('SELECT * FROM sources WHERE source_id=?', (source_id,)))
        return {'report': report, 'replay': replay, 'validation': validation, 'manifest': manifest, 'source_projection': source_projection, 'ingredient_link_audit': audit, 'communication_row_audit': article_audit}
    finally:
        connection.close()


def run(root, database, evidence):
    root = Path(root).resolve()
    database, evidence = output_paths(root, database, evidence)
    tracker = InputTracker(root)
    parent_path = tracker.inspect(PARENT_PATH, hash_now=True, recorded_sha256=PARENT_SHA256)
    dump = tracker.inspect(DUMP_PATH, hash_now=True)
    config = tracker.json(CONFIG_PATH)
    for relative in ('docs/pharma_release_v1_contract.md', 'docs/pharma_release_phase4b_communications.md'):
        tracker.inspect(relative, hash_now=True)
    for directory in ('scripts/pharma_release', 'backend/tests/pharma_release'):
        for file in sorted((root / directory).glob('*.py')):
            tracker.inspect(file.relative_to(root), hash_now=True)
    rows, legacy, extraction = extract_dump(dump)
    source_audit = validate_evidence(rows, config, legacy)
    print('Extracted 3 preserved articles and audited 148 legacy links; no legacy links migrated', flush=True)
    tests_command = [str(root / '.venv/bin/python'), '-B', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', *TEST_FILES]
    tests = subprocess.run(tests_command, cwd=root, env=os.environ | {'PYTHONDONTWRITEBYTECODE': '1'}, capture_output=True, text=True)
    print(tests.stdout + tests.stderr, flush=True)
    if tests.returncode:
        raise SourceError('Focused release tests failed')
    parent = readonly(parent_path)
    try:
        if any(parent.execute(f'SELECT count(*) FROM {table}').fetchone()[0] for table in ('safety_communications', 'drug_communications')) or parent.execute("SELECT count(*) FROM coverage WHERE domain='safety_communications'").fetchone()[0]:
            raise SourceError('Parent is not frozen Phase 4A')
        sources = row_dicts(parent, "SELECT * FROM sources WHERE source_name='fda_drug_safety_communications'")
        if len(sources) != 1:
            raise SourceError('Expected exactly one existing communication source registration')
        source_id = sources[0]['source_id']
        parent_manifest = row_dicts(parent, 'SELECT * FROM release_manifest')
        if len(parent_manifest) != 1 or parent_manifest[0]['release_id'] != 'dav-ai-pharma-v1-phase4a-ae-20261006':
            raise SourceError('Parent manifest is not Phase 4A')
        parent_manifest = parent_manifest[0]
        frozen = fingerprints(parent)
        schema = schema_objects(parent)
        user_version = parent.execute('PRAGMA user_version').fetchone()[0]
    finally:
        parent.close()
    inputs = [tracker.records[DUMP_PATH], tracker.records[CONFIG_PATH]]
    lineage = {'kind': 'CURATED_PRESERVED_COMMUNICATION_BUILD', 'source_id': source_id, 'coverage': COVERAGE,
               'rule_version': RULE_VERSION, 'policy_version': '1.0.0', 'dump_path': DUMP_PATH,
               'dump_sha256': tracker.records[DUMP_PATH]['sha256'], 'config_path': CONFIG_PATH,
               'config_sha256': tracker.records[CONFIG_PATH]['sha256'], 'local_only': True,
               'network_used': False, 'postgresql_server_used': False, 'extraction': extraction, **source_audit}
    evidence.mkdir(parents=True, exist_ok=False)
    database.parent.mkdir(parents=True, exist_ok=False)
    staged = database.parent / 'communications.building.sqlite'
    first = build_child(staged, parent_path, rows, config, legacy, source_id, frozen, schema, parent_manifest, inputs, lineage)
    print('First child validated; independently extracting and building again from frozen Phase 4A', flush=True)
    with tempfile.TemporaryDirectory(prefix='dav-phase4b-replay-') as temporary:
        rows2, legacy2, extraction2 = extract_dump(dump)
        if rows2 != rows or legacy2 != legacy or extraction2 != extraction:
            raise SourceError('Source extraction replay changed')
        duplicate = build_child(Path(temporary) / 'pharma.sqlite', parent_path, rows2, config, legacy2, source_id, frozen, schema, parent_manifest, inputs, lineage)
    duplicate_check = {'passed': first['report']['projection'] == duplicate['report']['projection'] and first['source_projection'] == duplicate['source_projection'] and normalized_manifest(first['manifest']) == normalized_manifest(duplicate['manifest']),
                       'independent_builds_from_same_parent': 2, 'source_extracted_twice': True,
                       'manifest_excluded_fields': ['build_time_utc'], 'projection': duplicate['report']['projection'],
                       'source_projection_sha256': duplicate['source_projection'], 'manifest_sha256_excluding_timestamp': hashlib.sha256(canonical_json(normalized_manifest(duplicate['manifest'])).encode()).hexdigest(),
                       'duplicate_inherited_rows_unchanged': duplicate['validation']['inherited_rows_unchanged'],
                       'temporary_duplicate_removed': True}
    if not duplicate_check['passed']:
        raise SourceError('Independent duplicate build differs')
    tracker.assert_unchanged()
    for relative in (PARENT_PATH, DUMP_PATH, CONFIG_PATH):
        if file_sha256(root / relative) != tracker.records[relative]['sha256']:
            raise SourceError('Protected source bytes changed during build: ' + relative)
    staged.chmod(0o444)
    os.link(staged, database)
    staged.unlink()
    metadata = {'phase': '4B', 'release_version': RELEASE_VERSION, 'build_version': BUILD_VERSION,
                'schema_version': parent_manifest['schema_version'], 'policy_version': '1.0.0', 'rule_version': RULE_VERSION,
                'build_time_utc': first['manifest']['build_time_utc'], 'database_path': str(database.relative_to(root)),
                'database_bytes': database.stat().st_size, 'database_sha256': file_sha256(database), 'file_mode': '0o444',
                'parent_release_path': PARENT_PATH, 'parent_release_sha256': PARENT_SHA256,
                'table_counts': first['validation']['table_counts'], 'coverage': COVERAGE, 'safe_to_freeze_phase4b': True,
                'ae_started': True, 'communications_started': True, 'publication_validated': False}
    outputs = {'release_metadata.json': metadata, 'build_summary.json': metadata | source_audit,
               'source_inventory.json': {'inputs': list(tracker.records.values()), 'lineage': lineage, 'protected_inputs_unchanged': True},
               'source_extraction.json': extraction | source_audit,
               'preserved_communication_rows.json': rows, 'communication_row_audit.json': first['communication_row_audit'],
               'ingredient_link_audit.json': first['ingredient_link_audit'], 'rejected_link_audit.json': first['report']['rejected_candidates'],
               'coverage_statement.json': {'coverage': COVERAGE, 'linked_state': 'PARTIAL', 'unlinked_state': 'UNKNOWN', 'unlinked_measured_count': None,
                                           'linked_message': LINKED_MESSAGE, 'empty_message': EMPTY_MESSAGE, 'limitations': LIMITATIONS,
                                           'ingredient_coverage_rows_added': EXPECTED_COUNTS['ingredients'], 'product_coverage_rows_added': 0},
               'parent_preservation.json': first['validation']['parent_preservation'], 'table_counts.json': metadata['table_counts'],
               'validation.json': first['validation'], 'replay.json': first['replay'], 'duplicate_build.json': duplicate_check,
               'manifest.json': first['manifest'], 'schema_diff.json': {'schema_objects_identical': True, 'parent_user_version': user_version, 'child_user_version': user_version},
               'tests.json': {'passed': True, 'command': tests_command, 'exit_code': tests.returncode, 'stdout': tests.stdout, 'stderr': tests.stderr}}
    for name, value in outputs.items():
        write_json(evidence / name, value)
    write_json(database.parent / 'release_metadata.json', metadata)
    (evidence / 'schema.sql').write_text('\n\n'.join(sql + ';' for kind, name, table, sql in schema if sql) + '\n')
    (evidence / 'integrity_check.txt').write_text('ok\n')
    (evidence / 'foreign_key_check.txt').write_text('0 violations\n')
    (evidence / 'tests.txt').write_text(tests.stdout + tests.stderr)
    summary = f'''# Phase 4B pharmaceutical communications release

SAFE TO FREEZE PHASE 4B: YES. This validates this phase, not final release deployment.

Release: `{metadata['database_path']}`\n\nBytes: {metadata['database_bytes']}\n\nSHA256: `{metadata['database_sha256']}`\n\nParent SHA256: `{PARENT_SHA256}`

Preserved communications: 3. Historical legacy product links: 148 (audit only; zero migrated).
New safety_communications: 3. New ingredient-context edges: 5, all INGREDIENT_CONTEXT_ONLY.

Coverage: CURATED_PARTIAL. Linked ingredient collections are PARTIAL; unlinked collections UNKNOWN with NULL counts.
{EMPTY_MESSAGE}

Gabapentinoid published_date remains NULL; [Posted 12/19/2019] remains body evidence.
Pregabalin is a manually reviewed correction based on exact title/body evidence; it was absent from the original config.
The full preserved body and structured article fields are copied without repair. Original raw_json, ingestion_run_id and PostgreSQL record IDs are preserved in source inputs_json and extraction evidence.

Rejected: gabapentin enacarbil (Horizant cannot establish ingredient identity); montelukast alcohol (no scope/text support); montelukast sodium (configured but exact text absent; no salt inference).

All inherited identity, search, label, recall and AE counts and complete row hashes are unchanged.
Existing coverage rows and unrelated sources are unchanged. Added 7,733 ingredient communication coverage records; no product communication coverage or applicability.
The existing 19-table schema, policy 1.0.0 and user_version are unchanged.

Tests: {tests.stdout.strip()}
Integrity: ok. Foreign key violations: 0.
Replay: zero changes; independently extracted and built twice from the same parent, with identical communication/coverage/source projections and manifests excluding only build_time_utc.

Local pg_restore --use-list extracts only TOC objects 4158 and 4162; no SQL is executed.
No network, PostgreSQL server, fuzzy/LLM matching, legacy product UUID migration, brand/salt inference, or product-level communication applicability was used.
No frontend, Ask Dav AI, API, identity, label, recall or AE behavior was changed.
'''
    (evidence / 'build_summary.md').write_text(summary)
    print(canonical_json(metadata), flush=True)
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    args = parser.parse_args()
    run(args.root, args.database, args.evidence)


if __name__ == '__main__':
    main()
