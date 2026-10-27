"""Atomic source upserts and links; all safety reads come from PostgreSQL."""
from collections import Counter
from contextlib import nullcontext
from psycopg import sql
from psycopg.types.json import Jsonb
from app.db.pharma.connection import connect
from app.services.pharma.safety_records import TABLES, SOURCES

JSON_FIELDS = {'raw_json', 'reported_drugs', 'seriousness_details'}


class SafetyRepository:
    def upsert(self, kind, record, links, *, connection=None):
        table, link_table, key, _ = TABLES[kind]
        fields = list(record)
        updates = sql.SQL(', ').join(sql.SQL('{}=EXCLUDED.{}').format(sql.Identifier(f), sql.Identifier(f))
                                     for f in fields if f not in ('source', 'source_record_id'))
        # Latest report version wins even if overlapping source queries return older revisions.
        condition = sql.SQL('')
        if kind == 'adverse_events':
            condition = sql.SQL(""" WHERE
                CASE WHEN EXCLUDED.report_version ~ '^[0-9]+$' THEN EXCLUDED.report_version::numeric ELSE -1 END
                >= CASE WHEN adverse_events.report_version ~ '^[0-9]+$' THEN adverse_events.report_version::numeric ELSE -1 END
            """)
        query = sql.SQL('''INSERT INTO pharma.{} ({}) VALUES ({})
            ON CONFLICT (source, source_record_id) DO UPDATE SET {}, ingested_at=now() {}
            RETURNING id, (xmax=0) AS inserted''').format(
                sql.Identifier(table), sql.SQL(', ').join(map(sql.Identifier, fields)),
                sql.SQL(', ').join(sql.Placeholder() for _ in fields), updates, condition)
        with (nullcontext(connection) if connection is not None else connect()) as conn:
            row = conn.execute(query, [Jsonb(record[f]) if f in JSON_FIELDS else record[f] for f in fields]).fetchone()
            if row is None:
                return 'unchanged'
            conn.execute(sql.SQL('DELETE FROM pharma.{} WHERE {}=%s').format(sql.Identifier(link_table), sql.Identifier(key)), (row['id'],))
            for drug_id, method, value in links:
                conn.execute(sql.SQL('INSERT INTO pharma.{} (drug_id, {}, match_method, matched_value) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING').format(
                    sql.Identifier(link_table), sql.Identifier(key)), (drug_id, row['id'], method, value))
            return 'inserted' if row['inserted'] else 'updated'

    def catalog(self):
        with connect() as conn:
            return conn.execute('SELECT * FROM pharma.drugs ORDER BY normalized_generic_name, id').fetchall()

    def section(self, kind, drug_id):
        table, links, key, date_key = TABLES[kind]
        with connect() as conn:
            rows = conn.execute(sql.SQL('''SELECT r.* FROM pharma.{} r JOIN pharma.{} l ON l.{}=r.id
                WHERE l.drug_id=%s ORDER BY r.{} DESC NULLS LAST, r.id''').format(
                    sql.Identifier(table), sql.Identifier(links), sql.Identifier(key), sql.Identifier(date_key)), (drug_id,)).fetchall()
            attempt = conn.execute('''SELECT id, status, started_at, finished_at, parameters, coverage, error_summary
                FROM pharma.ingestion_runs WHERE source=%s AND parameters->'drug_ids' @> %s
                ORDER BY started_at DESC LIMIT 1''', (SOURCES[kind][0], Jsonb([str(drug_id)]))).fetchone()
        latest_ingested = max((r['ingested_at'] for r in rows), default=None)
        coverage = {'source': SOURCES[kind][0], 'stored_record_count': len(rows),
                    'last_ingested_at': latest_ingested, 'last_attempt': attempt,
                    'empty_message': "No records in Dav AI's stored dataset. This does not establish that no such records exist.",
                    'bounded': True, 'scope': 'Stored records linked deterministically to this catalog product; unresolved records are excluded.'}
        if attempt:
            relevant = {k: v for k, v in attempt['coverage'].items() if str(drug_id) in v.get('drug_ids', [])}
            attempt['coverage'] = relevant
            if attempt['parameters'].get('mode') == 'bulk':
                coverage['retrieval_mode'] = 'bulk'
                complete = relevant.get('bulk', {}).get('truncated') is False
                coverage['bounded'] = not complete
                coverage['scope'] = ('Official bulk label snapshot coverage; only deterministic catalog links are displayed. '
                    'Snapshot completeness does not establish complete historical label coverage.')
            coverage['truncated'] = (True if any(v.get('truncated') is True for v in relevant.values())
                else False if relevant and all(v.get('status') == 'succeeded' and v.get('truncated') is False for v in relevant.values())
                else None)
            coverage['query_status'] = ('not_configured' if not relevant else
                'failed' if all(v.get('status') == 'failed' for v in relevant.values()) else
                'partial' if any(v.get('status') != 'succeeded' for v in relevant.values()) else 'succeeded')
        else:
            coverage['truncated'] = None
            coverage['query_status'] = 'not_attempted'
        for r in rows:
            r.pop('raw_json', None)
        return {'records': rows, 'coverage': coverage}

    def safety(self, drug_id):
        sections = {kind: self.section(kind, drug_id) for kind in TABLES}
        events = sections['adverse_events']['records']
        reactions = Counter(reaction for r in events for reaction in set(r['reactions']))
        sections['adverse_events']['summary'] = {
            'stored_report_count': len(events), 'serious_report_count': sum(r['serious'] is True for r in events),
            'top_reported_reactions': [{'reaction': name, 'report_count': count} for name, count in reactions.most_common(10)],
            'limitation': 'Counts describe the accumulated bounded stored sample, not total FAERS reports or incidence. Co-reported drugs and reactions do not establish causation.',
        }
        # Latest per set; missing set IDs remain independent, legitimate label records.
        latest = {}
        for record in sections['labels']['records']:
            family = record['label_set_id'] or str(record['id'])
            def rank(row):
                v = row['label_version'] or ''
                return (int(v) if v.isdigit() else -1, str(row['effective_date'] or ''))
            if family not in latest or rank(record) > rank(latest[family]):
                latest[family] = record
        sections['labels']['latest_records'] = list(latest.values())
        return sections

    def timeline(self, drug_id, sections=None):
        entries = []
        for kind in TABLES:
            for record in (sections[kind] if sections is not None else self.section(kind, drug_id))['records']:
                date_key = TABLES[kind][3]
                when = record[date_key]
                if not when:
                    continue
                if kind == 'adverse_events':
                    title, summary = 'Adverse-event report received', 'FDA report receipt date; not the adverse-event occurrence date.'
                elif kind == 'recalls':
                    title, summary = record['product_description'], record['reason_for_recall']
                elif kind == 'labels':
                    title, summary = record['title'], 'Label effective date; version ' + (record['label_version'] or 'not supplied')
                else:
                    title, summary = record['title'], record['body_text'][:350]
                entries.append(dict(event_type=kind, date=when, date_type=date_key, title=title,
                                    summary=summary, source_url=record['source_url'], source=record['source'], record_id=record['id'],
                                    ingested_at=record['ingested_at'], source_updated_at=record['source_updated_at']))
        return sorted(entries, key=lambda e: (e['date'], e['event_type'], str(e['record_id'])), reverse=True)
