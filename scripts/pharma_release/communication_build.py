"""Reviewed exact canonical ingredient/article context and curated coverage."""
from collections import Counter
import re

from .communication_sources import URLS, SOURCE_NAME, validate_evidence
from .ids import qualified_id
from .identity import digest_rows
from .sources import canonical_json, SourceError

POLICY_VERSION = '1.0.0'
RULE_VERSION = 'phase4b-reviewed-exact-ingredient-article-v1'
SCOPE = 'Generic ingredient-level FDA communication context only; not product-, NDC-, formulation-, strength-, dose-, or indication-specific applicability.'
COVERAGE = 'CURATED_PARTIAL'
EMPTY_MESSAGE = 'No verified safety communication is linked in this release. Communication coverage is curated and not comprehensive.'
LINKED_MESSAGE = 'FDA safety communication available in this curated release.'
LIMITATIONS = [
    'Three curated preserved FDA safety communications; discovery and linkage are not comprehensive.',
    SCOPE,
    'A missing edge does not establish that FDA never issued a communication, found no safety issue, or that an ingredient is safe or has no warnings.',
    'Communication statements must be attributed to FDA in their article context; linkage only means the article discusses the ingredient.',
]
IDENTITIES = {
    'semaglutide': 'ingredient:aceb6dacee359207f1939f8b',
    'tirzepatide': 'ingredient:ab9c2b4259f284e8218f79aa',
    'gabapentin': 'ingredient:c29f34d9df2eb152bd25c16c',
    'pregabalin': 'ingredient:cb074fa079561b337c4942b1',
    'montelukast': 'ingredient:be6e5a076a5b88bacfaa1163',
    'gabapentin enacarbil': 'ingredient:0917f059fbabcfa1c76b5ad5',
    'montelukast alcohol': 'ingredient:fa67228eee612fa59c38dced',
    'montelukast sodium': 'ingredient:f2c0831752eafe057c140a71',
}
ACCEPTED = ((0, 'semaglutide', 1), (0, 'tirzepatide', 1), (1, 'gabapentin', 3), (1, 'pregabalin', 3), (2, 'montelukast', 72))
REJECTED = (
    ('gabapentin enacarbil', 1, 'Brand mention "Horizant" is not sufficient for ingredient identity inference.'),
    ('montelukast alcohol', 2, 'No editorial scope and no exact article support.'),
    ('montelukast sodium', 2, 'Configured name exists, but preserved article body lacks exact source-text support; no salt inference allowed.'),
)
PROJECTION_TABLES = ('safety_communications', 'drug_communications', 'coverage')


def exact_matches(text, name):
    # Case-insensitive whole ingredient term; no stemming, spelling, salt or brand expansion.
    return list(re.finditer(r'(?<!\w)' + re.escape(name) + r'(?!\w)', text, re.IGNORECASE))


def article_rows(rows, config, source_id):
    by_url = {row['source_url']: row for row in rows}
    projected = []
    for definition in config['communications']:
        row = by_url[definition['url']]
        projected.append({
            'communication_id': qualified_id('communication', SOURCE_NAME, row['source_record_id']),
            'source_id': source_id,
            **{field: row[field] for field in ('source_record_id', 'title', 'communication_type', 'published_date', 'body_text', 'source_url', 'source_updated_at', 'ingested_at')},
            'configured_names_json': canonical_json(definition['names']), 'editorial_scope': definition['scope'],
        })
    return projected


def project(connection, rows, config, legacy, source_id):
    validate_evidence(rows, config, legacy)
    source = connection.execute('SELECT source_name FROM sources WHERE source_id=?', (source_id,)).fetchone()
    if source != (SOURCE_NAME,):
        raise SourceError('Article source is not registered')
    for name, iid in IDENTITIES.items():
        actual = connection.execute('SELECT canonical_name FROM ingredients WHERE ingredient_id=?', (iid,)).fetchone()
        if actual is None or actual[0].casefold() != name:
            raise SourceError('Exact frozen ingredient identity missing or changed: ' + name)
    articles = article_rows(rows, config, source_id)
    edges = []
    for index, name, expected_count in ACCEPTED:
        article = articles[index]
        matches = exact_matches(article['body_text'], name)
        configured = name in config['communications'][index]['names']
        reviewed = name == 'pregabalin'
        if len(matches) != expected_count or (not configured and not reviewed):
            raise SourceError('Exact source-text/name evidence absent or changed: ' + name)
        title_match = bool(exact_matches(article['title'], name))
        if reviewed and not title_match:
            raise SourceError('Reviewed pregabalin correction requires explicit title evidence')
        match = matches[0]
        evidence = {'exact_term': article['body_text'][match.start():match.end()],
                    'body_occurrences': len(matches), 'first_body_character_span': [match.start(), match.end()],
                    'title_match': title_match}
        basis = {'source': 'preserved_fda_article', 'identity_method': 'EXACT_CANONICAL_INGREDIENT_NAME',
                 'source_text_match': True, 'editorial_scope': 'generic', 'configured_in_source_definition': configured,
                 'manual_review_added': reviewed, 'legacy_link_reused': False, 'brand_inference_used': False, 'salt_inference_used': False}
        if reviewed:
            basis['manual_review_basis'] = 'Phase 4B release review explicitly approves pregabalin from exact preserved title/body evidence; correction of omission in historical config.'
        edges.append({'ingredient_id': IDENTITIES[name], 'communication_id': article['communication_id'],
                      'applicability_class': 'INGREDIENT_CONTEXT_ONLY', 'configured_name': name,
                      'source_text_evidence': canonical_json(evidence), 'scope_qualifiers': SCOPE,
                      'review_basis_json': canonical_json(basis), 'policy_version': POLICY_VERSION})
    rejected = []
    for name, index, reason in REJECTED:
        article = articles[index]
        count = len(exact_matches(article['body_text'], name))
        if count:
            raise SourceError('Rejected candidate evidence changed; explicit review required: ' + name)
        rejected.append({'ingredient_id': IDENTITIES[name], 'canonical_name': name, 'communication_id': article['communication_id'],
                         'configured_in_source_definition': name in config['communications'][index]['names'],
                         'exact_body_occurrences': count, 'reason': reason})
    counts = Counter(edge['ingredient_id'] for edge in edges)
    coverage = []
    for (iid,) in connection.execute('SELECT ingredient_id FROM ingredients ORDER BY ingredient_id'):
        present = bool(counts[iid])
        coverage.append({'entity_type': 'INGREDIENT', 'entity_id': iid, 'ingredient_id': iid,
                         'domain': 'safety_communications', 'window_key': '', 'state': 'PARTIAL' if present else 'UNKNOWN',
                         'reason_code': 'CURATED_COMMUNICATION_LINK_AVAILABLE' if present else 'NO_VERIFIED_COMMUNICATION_LINK',
                         'scope': COVERAGE + '; INGREDIENT_CONTEXT_ONLY', 'as_of_date': None, 'source_date': None,
                         'measured_count': counts[iid] if present else None, 'unresolved_count': None,
                         'rule_version': RULE_VERSION, 'limitations_json': canonical_json(LIMITATIONS + [LINKED_MESSAGE if present else EMPTY_MESSAGE])})
    return {'safety_communications': articles, 'drug_communications': edges, 'coverage': coverage}, rejected


def put(connection, table, row):
    fields = list(connection.execute(f'PRAGMA table_info({table})'))
    columns = [field[1] for field in fields]
    keys = [field[1] for field in sorted(fields, key=lambda field: field[5]) if field[5]]
    values = [row.get(column) for column in columns]
    old = connection.execute(f"SELECT * FROM {table} WHERE " + ' AND '.join(key + '=?' for key in keys), [row[key] for key in keys]).fetchone()
    if old is None:
        connection.execute(f"INSERT INTO {table} ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})", values)
        return True
    if list(old) != values:
        raise SourceError('Nonidentical communication replay/collision in ' + table)
    return False


def projection_fingerprints(connection):
    result = {}
    for table in PROJECTION_TABLES:
        where = " WHERE domain='safety_communications'" if table == 'coverage' else ''
        result[table] = {'rows': connection.execute(f'SELECT count(*) FROM {table}' + where).fetchone()[0],
                         'sha256_sorted_row_hashes': digest_rows(list(row) for row in connection.execute(f'SELECT * FROM {table}' + where))}
    return result


def populate(connection, rows, config, legacy, source_id):
    projections, rejected = project(connection, rows, config, legacy, source_id)
    inserted = {}
    for table, records in projections.items():
        inserted[table] = sum(put(connection, table, row) for row in records)
        columns = [r[1] for r in connection.execute(f'PRAGMA table_info({table})')]
        expected = {'rows': len(records), 'sha256_sorted_row_hashes': digest_rows([row.get(column) for column in columns] for row in records)}
        actual = projection_fingerprints(connection)[table]
        if actual != expected:
            raise SourceError('Communication projection does not match preserved evidence: ' + table)
    return {'projection': projection_fingerprints(connection), 'inserted': inserted, 'rejected_candidates': rejected}
