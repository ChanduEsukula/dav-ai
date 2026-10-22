"""Exact local pg_restore TOC extraction; SQL is parsed, never executed."""
from collections import Counter
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from .sources import SourceError

PARENT_PATH = 'data/releases/dav_ai_pharma_v1/phase4a-ae-2026-10-06/pharma.sqlite'
PARENT_SHA256 = 'f7e798c8219f09a3281dd717dc931043d360de8ff6ec708ace577c870db99741'
DUMP_PATH = 'data/pharma_recovery/davai_recovery.dump'
CONFIG_PATH = 'backend/app/config/safety_communications.json'
SOURCE_NAME = 'fda_drug_safety_communications'
OBJECTS = {
    'safety_communications': '4158; 0 20816 TABLE DATA pharma safety_communications chanduesukula',
    'drug_safety_communication_links': '4162; 0 20897 TABLE DATA pharma drug_safety_communication_links chanduesukula',
}
COLUMNS = ('id', 'title', 'communication_type', 'published_date', 'body_text', 'source', 'source_record_id', 'source_url', 'source_updated_at', 'ingested_at', 'ingestion_run_id', 'raw_json')
LINK_COLUMNS = ('drug_id', 'safety_communication_id', 'match_method', 'matched_value')
URLS = (
    'https://www.fda.gov/drugs/drug-safety-communications/fda-requests-removal-suicidal-behavior-and-ideation-warning-glucagon-peptide-1-receptor-agonist-glp',
    'https://www.fda.gov/safety/medical-product-safety-information/neurontin-gralise-horizant-gabapentin-and-lyrica-lyrica-cr-pregabalin-drug-safety-communication',
    'https://www.fda.gov/drugs/drug-safety-communications/fda-requires-boxed-warning-about-serious-mental-health-side-effects-asthma-and-allergy-drug',
)
EXPECTED_CONFIG = {'communications': [
    {'url': URLS[0], 'names': ['semaglutide', 'tirzepatide'], 'scope': 'generic'},
    {'url': URLS[1], 'names': ['gabapentin'], 'scope': 'generic'},
    {'url': URLS[2], 'names': ['montelukast', 'montelukast sodium', 'Singulair'], 'scope': 'generic'},
]}
RECORD_IDS = ('4e25b9dd-ad27-4b2d-a80a-d023475836a7', '7ca463a7-620e-4f12-ad6d-c36934e808e0', 'a54d8f19-be8d-4a84-b64f-f27aabe69d3c')
TITLES = (
    'FDA Requests Removal of Suicidal Behavior and Ideation Warning from Glucagon-Like Peptide-1 Receptor Agonist (GLP-1 RA) Medications',
    'Neurontin, Gralise, Horizant (gabapentin) and Lyrica, Lyrica CR (pregabalin): Drug Safety Communication - Serious Breathing Problems',
    'FDA requires Boxed Warning about serious mental health side effects for asthma and allergy drug montelukast (Singulair); advises restricting use for allergic rhinitis',
)
DATES = ('2026-01-13', None, '2020-03-04')


def copy_value(value):
    if value == r'\N':
        return None
    escapes = {'b': '\b', 'f': '\f', 'n': '\n', 'r': '\r', 't': '\t', 'v': '\v', '\\': '\\'}
    def replace(match):
        token = match[1]
        if token[0] in '01234567':
            return chr(int(token, 8))
        if token.startswith('x') and len(token) > 1:
            return chr(int(token[1:], 16))
        return escapes.get(token, token)
    trailing = len(value) - len(value.rstrip('\\'))
    if trailing % 2:
        raise SourceError('Truncated COPY escape')
    return re.sub(r'\\([0-7]{1,3}|x[0-9a-fA-F]{1,2}|.)', replace, value)


def parse_copy(sql, table, columns):
    header = f"COPY pharma.{table} ({', '.join(columns)}) FROM stdin;"
    lines = sql.splitlines()
    if lines.count(header) != 1 or sum(line.startswith('COPY ') for line in lines) != 1:
        raise SourceError('Unexpected COPY table/columns/block count: ' + table)
    start = lines.index(header) + 1
    rows = []
    for line in lines[start:]:
        if line == r'\.':
            return rows
        fields = line.split('\t')
        if len(fields) != len(columns):
            raise SourceError('Unexpected COPY field count: ' + table)
        rows.append(dict(zip(columns, map(copy_value, fields))))
    raise SourceError('Unterminated COPY block: ' + table)


def extract_dump(dump, executable=None):
    executable = executable or shutil.which('pg_restore')
    if not executable:
        raise SourceError('Local pg_restore executable required; no PostgreSQL server is needed')
    def command(args):
        result = subprocess.run([executable, *args], capture_output=True, text=True, encoding='utf-8')
        if result.returncode:
            raise SourceError('Local pg_restore extraction failed: ' + result.stderr)
        return result.stdout
    toc = command(['--list', str(dump)]).splitlines()
    for entry in OBJECTS.values():
        if toc.count(entry) != 1:
            raise SourceError('Missing or changed exact dump TOC object: ' + entry)
    outputs = {}
    with tempfile.TemporaryDirectory(prefix='dav-phase4b-toc-') as temporary:
        for table, entry in OBJECTS.items():
            selected = Path(temporary) / (table + '.list')
            selected.write_text(entry + '\n')
            sql = command(['--data-only', '--no-owner', '--no-privileges', '--use-list', str(selected), '--file=-', str(dump)])
            outputs[table] = parse_copy(sql, table, COLUMNS if table == 'safety_communications' else LINK_COLUMNS)
    return outputs['safety_communications'], outputs['drug_safety_communication_links'], {
        'method': 'pg_restore exact --use-list TABLE DATA objects to stdout; parse COPY without executing SQL',
        'objects': OBJECTS, 'pg_restore_version': command(['--version']).strip(),
        'network_used': False, 'postgresql_server_used': False,
    }


def validate_evidence(rows, config, legacy):
    if config != EXPECTED_CONFIG:
        raise SourceError('Configured metadata differs from preserved source definition')
    if len(rows) != 3 or {r['source_url'] for r in rows} != set(URLS):
        raise SourceError('Expected exactly 3 preserved configured article URLs')
    by_url = {r['source_url']: r for r in rows}
    for i, url in enumerate(URLS):
        row = by_url[url]
        if (row['id'], row['title'], row['published_date'], row['source'], row['source_record_id'], row['communication_type']) != (
                RECORD_IDS[i], TITLES[i], DATES[i], SOURCE_NAME, url, 'FDA pharmaceutical safety communication'):
            raise SourceError('Unexpected preserved article identity/metadata: ' + url)
        if not row['body_text'] or not row['body_text'].strip():
            raise SourceError('Required preserved article body missing')
        try:
            raw = json.loads(row['raw_json'])
        except (TypeError, ValueError) as error:
            raise SourceError('Missing/malformed preserved source metadata') from error
        if not isinstance(raw, dict):
            raise SourceError('Unexpected preserved metadata shape')
        definition = EXPECTED_CONFIG['communications'][i]
        # Historical capture serialized "generic context"; editorial config uses
        # "generic". Pin both independently and preserve the raw capture verbatim.
        if raw.get('scope') != 'generic context' or raw.get('configured_names') != definition['names']:
            raise SourceError('Preserved article metadata differs from configured source definition')
    counts = Counter((r['safety_communication_id'], r['match_method'], r['matched_value']) for r in legacy)
    expected = {(RECORD_IDS[0], 'name', 'semaglutide'): 142, (RECORD_IDS[0], 'name', 'tirzepatide'): 3, (RECORD_IDS[1], 'name', 'gabapentin'): 3}
    if len(legacy) != 148 or len({(r['drug_id'], r['safety_communication_id']) for r in legacy}) != 148 or counts != expected:
        raise SourceError('Unexpected historical link audit; no legacy links may be migrated')
    return {'preserved_communication_rows': len(rows), 'historical_legacy_product_links': len(legacy),
            'legacy_link_breakdown': [{'source_postgresql_id': sid, 'match_method': method, 'matched_value': name, 'count': count}
                                    for (sid, method, name), count in sorted(counts.items())], 'legacy_links_migrated': 0}
