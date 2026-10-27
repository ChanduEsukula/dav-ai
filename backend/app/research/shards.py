"""Durable analytical shards, separate from immutable source/normalization files."""
import inspect
import json
from pathlib import Path
import resource
import shutil
import sys
import time

import duckdb
import pyarrow.parquet as pq

from app.research.analysis import (connect_analytics,quote,rows,select_resolved_drugs,
                                   selection_table_checks)
from app.research.bulk import atomic_json,file_digest,fingerprint,now
from app.research.identity import snapshot


def table_check(conn,relation):
    return rows(conn,f'''SELECT count(*) row_count,bit_xor(hash(t)) row_hash_xor,
        sum(hash(t)::HUGEINT)::VARCHAR row_hash_sum FROM {relation} t''')[0]


def checkpoint_resolved_drugs(root,*,buckets=16,origin_log=None):
    """Checkpoint an already completed drug join; never rerun that join here."""
    root=Path(root);out=root/'analysis-shards/resolved_drugs';out.mkdir(parents=True,exist_ok=True)
    if type(buckets) is not int or buckets<1:raise ValueError('Invalid shard count')
    selected=json.loads((root/'analysis-selected-checkpoint.json').read_text())
    mapping=json.loads((root/'identity/summary.json').read_text())['mapping_hash']
    conn=connect_analytics(root)
    try:
        if selection_table_checks(conn)!=selected['tables']:
            raise ValueError('Selection checkpoint changed; refusing drug checkpoint')
        source=table_check(conn,'resolved_drugs')
        signature=fingerprint({'selected':selected,'mapping':mapping,'source_table':source,
            'buckets':buckets,'duckdb_version':duckdb.__version__,'join_logic':inspect.getsource(select_resolved_drugs)})
        timings=[]
        if origin_log is not None:
            events=[json.loads(line) for line in Path(origin_log).read_text().splitlines() if line.startswith('{')]
            starts=[e for e in events if e.get('query_start','').startswith('INSERT INTO resolved_drugs')]
            ends=[e for e in events if e.get('query','').startswith('INSERT INTO resolved_drugs')]
            if len(starts)!=buckets or len(ends)!=buckets:raise ValueError('Incomplete originating drug-join log')
            timings=[{'started_at':a['at'],'completed_at':b['at'],'seconds':b['query_seconds']} for a,b in zip(starts,ends)]
        manifest={'signature':signature,'buckets':buckets,'source_table':source,'complete':False,
                  'selected_checkpoint_signature':selected['signature'],'mapping_hash':mapping,
                  'partition_expression':f'hash(report_uid)%{buckets}',
                  'duckdb_version':duckdb.__version__,'completed_shard_ids':[],'shards':[]}
        for bucket in range(buckets):
            started=time.monotonic();path=out/f'shard-{bucket:03d}.parquet';receipt=path.with_suffix('.json')
            if receipt.exists():
                saved=json.loads(receipt.read_text())
                if (saved['signature']!=signature or saved['shard_id']!=bucket or not saved['complete']
                    or not path.exists() or file_digest(path)!=saved['sha256']
                    or pq.ParquetFile(path).metadata.num_rows!=saved['output']['row_count']):
                    raise ValueError('Analytical drug shard checkpoint mismatch: '+str(receipt))
            else:
                if path.exists():raise ValueError('Drug shard output lacks receipt: '+str(path))
                if shutil.disk_usage(root).free<40*1024**3:raise ValueError('Research disk reserve reached')
                partial=path.with_suffix('.partial')
                if partial.exists():raise ValueError('Inspect unfinished drug shard staging before retry: '+str(partial))
                predicate=f'hash(report_uid)%{buckets}={bucket}'
                output=table_check(conn,f'(SELECT * FROM resolved_drugs WHERE {predicate})')
                input_references=table_check(conn,f'(SELECT case_id,report_uid FROM latest_reports WHERE {predicate})')
                # All original normalized rows correspond one-to-one with raw
                # drug mentions. DISTINCT removes duplicate exported payloads,
                # while drug_index preserves repeated mentions within a report.
                conn.execute(f'''CREATE OR REPLACE TEMP TABLE shard_selected_mentions AS
                    SELECT n.report_uid,n.drug_index,len(n.ingredient_ids) ingredient_count,n.resolution
                    FROM (SELECT * FROM normalized WHERE {predicate}) n
                    JOIN (SELECT report_uid FROM latest_reports WHERE {predicate}) r USING(report_uid)''')
                stats=rows(conn,f'''WITH unique_mentions AS (SELECT DISTINCT * FROM shard_selected_mentions)
                    SELECT (SELECT count(*) FROM normalized WHERE {predicate}) input_normalized_rows,
                        (SELECT count(*) FROM latest_reports WHERE {predicate}) input_selected_reports,
                        (SELECT count(*) FROM shard_selected_mentions) selected_source_mention_rows,
                        count(*) selected_unique_mentions,count(DISTINCT (report_uid,drug_index)) unique_mention_keys,
                        count(*) FILTER(WHERE ingredient_count>0) resolved_mentions,
                        count(*) FILTER(WHERE ingredient_count=0) unresolved_mentions,
                        count(*) FILTER(WHERE ingredient_count>1) combination_mentions,
                        count(DISTINCT report_uid) selected_reports_with_drugs,
                        count(DISTINCT report_uid) FILTER(WHERE ingredient_count>0) selected_reports_with_resolved_drugs,
                        coalesce(sum(ingredient_count),0)::BIGINT expected_ingredient_links
                    FROM unique_mentions''')[0]
                if stats['selected_unique_mentions']!=stats['unique_mention_keys']:
                    raise ValueError('Conflicting normalized results for one selected mention')
                if stats['expected_ingredient_links']!=output['row_count']:
                    raise ValueError('Resolved drug output lost or duplicated ingredient links')
                if conn.execute(f'''SELECT count(*)-count(DISTINCT
                    (report_uid,drug_index,role,ingredient_id,mapping_observed_at))
                    FROM resolved_drugs WHERE {predicate}''').fetchone()[0]:
                    raise ValueError('Duplicate resolved drug rows in shard')
                conn.execute(f"COPY (SELECT * FROM resolved_drugs WHERE {predicate}) TO {quote(partial)} (FORMAT PARQUET,COMPRESSION ZSTD)")
                if pq.ParquetFile(partial).metadata.num_rows!=output['row_count']:
                    raise ValueError('Drug shard Parquet row mismatch')
                check=table_check(conn,f'read_parquet({quote(partial)})')
                if check!=output:raise ValueError('Drug shard Parquet content mismatch')
                partial.replace(path)
                saved={'signature':signature,'shard_id':bucket,'shard_number':bucket+1,'complete':True,
                       'output':output,'stats':stats,'sha256':file_digest(path),
                       'input_selected_references':input_references,
                       'original_join':timings[bucket] if timings else None,
                       'original_join_peak_memory':None,'original_join_peak_spill':None,
                       'resource_note':'Original per-shard peaks were not sampled; attempt resource log is process-wide.',
                       'checkpointed_at':now(),'checkpoint_seconds':round(time.monotonic()-started,3),
                       'checkpoint_process_peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),
                       'errors':[]}
                atomic_json(receipt,saved)
            manifest['completed_shard_ids'].append(bucket)
            manifest['shards'].append(saved)
            manifest['updated_at']=now();manifest['next_shard_id']=bucket+1 if bucket+1<buckets else None
            atomic_json(out/'manifest.json',manifest)
            print(json.dumps({'drug_checkpoint_shard':bucket,'rows':saved['output']['row_count'],'completed':len(manifest['shards'])}),flush=True)
        expected_files={f'shard-{i:03d}{suffix}' for i in range(buckets) for suffix in ('.json','.parquet')}|{'manifest.json'}
        if any(p.name not in expected_files for p in out.iterdir()):raise ValueError('Unexpected drug shard artifact')
        row_count=sum(s['output']['row_count'] for s in manifest['shards']);xor=0
        for shard in manifest['shards']:xor^=shard['output']['row_hash_xor'] or 0
        checksum_sum=sum(int(s['output']['row_hash_sum'] or 0) for s in manifest['shards'])
        if (row_count!=source['row_count'] or xor!=(source['row_hash_xor'] or 0)
            or checksum_sum!=int(source['row_hash_sum'] or 0)):
            raise ValueError('Drug shard union does not match completed source table')
        manifest['totals']={k:sum(s['stats'][k] for s in manifest['shards']) for k in manifest['shards'][0]['stats']}
        manifest.update(complete=True,union_integrity_passed=True,updated_at=now())
        atomic_json(out/'manifest.json',manifest)
        return manifest
    finally:conn.close()


def verify_drug_checkpoint(conn,root):
    root=Path(root);out=root/'analysis-shards/resolved_drugs'
    manifest=json.loads((out/'manifest.json').read_text())
    if not manifest['complete'] or not manifest['union_integrity_passed']:
        raise ValueError('Drug shard union is incomplete')
    if manifest['completed_shard_ids']!=list(range(manifest['buckets'])):
        raise ValueError('Missing, duplicate or unexpected drug shard IDs')
    for saved in manifest['shards']:
        path=out/f"shard-{saved['shard_id']:03d}.parquet"
        if file_digest(path)!=saved['sha256'] or pq.ParquetFile(path).metadata.num_rows!=saved['output']['row_count']:
            raise ValueError('Drug shard checksum or row count mismatch')
    if table_check(conn,'resolved_drugs')!=manifest['source_table']:
        raise ValueError('Completed resolved-drug table differs from its shard checkpoint')
    return manifest


def materialize_reactions(conn,root,*,buckets=16):
    """Resume independently committed reaction shards for the same selected reports."""
    root=Path(root);out=root/'analysis-shards/report_reactions';out.mkdir(parents=True,exist_ok=True)
    if type(buckets) is not int or buckets<1:raise ValueError('Invalid reaction shard count')
    selected=json.loads((root/'analysis-selected-checkpoint.json').read_text())
    source=snapshot(root,'event')
    signature=fingerprint({'selected':selected,'buckets':buckets,'duckdb_version':duckdb.__version__,
        'semantics':'selected report_uid, distinct existing nonempty normalized_term; reaction-v1',
        'reaction_inputs':{p.parent.name:json.loads(p.read_text())['outputs']['reactions.parquet']
            for p in source.glob('files/quarter=*/*/receipt.json') if not p.parent.name.endswith('.partial')}})
    manifest={'signature':signature,'buckets':buckets,'complete':False,'completed_shard_ids':[],
              'selected_checkpoint_signature':selected['signature'],'shards':[],
              'term_semantics':'Existing source normalized_term only; no external MedDRA or medical mapping'}
    try:
        for bucket in range(buckets):
            manifest.update(current_shard_id=bucket,current_error=None,updated_at=now())
            atomic_json(out/'manifest.json',manifest)
            path=out/f'shard-{bucket:03d}.parquet';receipt=path.with_suffix('.json')
            if receipt.exists():
                saved=json.loads(receipt.read_text())
                if (saved['signature']!=signature or saved['shard_id']!=bucket or not saved['complete']
                    or not path.exists() or file_digest(path)!=saved['sha256']
                    or pq.ParquetFile(path).metadata.num_rows!=saved['output']['row_count']):
                    raise ValueError('Reaction shard checkpoint mismatch')
            else:
                if path.exists():raise ValueError('Reaction output lacks its receipt')
                partial=path.with_suffix('.partial')
                if partial.exists():raise ValueError('Inspect unfinished reaction shard staging before retry')
                if shutil.disk_usage(root).free<40*1024**3:raise ValueError('Research disk reserve reached')
                started=time.monotonic();started_at=now();predicate=f'hash(report_uid)%{buckets}={bucket}'
                conn.execute(f'''CREATE OR REPLACE TEMP TABLE shard_selected_reactions AS
                    SELECT x.report_uid,x.reaction_index,x.normalized_term AS reaction
                    FROM (SELECT report_uid,reaction_index,normalized_term FROM raw_reactions WHERE {predicate}) x
                    JOIN (SELECT report_uid FROM latest_reports WHERE {predicate}) r USING(report_uid)''')
                stats=rows(conn,f'''WITH mentions AS (SELECT DISTINCT * FROM shard_selected_reactions)
                    SELECT (SELECT count(*) FROM raw_reactions WHERE {predicate}) input_source_reaction_rows,
                        (SELECT count(*) FROM latest_reports WHERE {predicate}) input_selected_reports,
                        (SELECT count(*) FROM shard_selected_reactions) selected_source_reaction_rows,
                        count(*) selected_unique_reaction_mentions,
                        count(*) FILTER(WHERE nullif(reaction,'') IS NOT NULL) usable_reaction_mentions,
                        count(*) FILTER(WHERE nullif(reaction,'') IS NULL) invalid_or_empty_reaction_mentions,
                        count(DISTINCT report_uid) selected_reports_with_reaction_mentions,
                        count(DISTINCT report_uid) FILTER(WHERE nullif(reaction,'') IS NOT NULL) selected_reports_with_usable_reactions
                    FROM mentions''')[0]
                conn.execute('''CREATE OR REPLACE TEMP TABLE shard_report_reactions AS
                    SELECT DISTINCT report_uid,reaction FROM shard_selected_reactions WHERE nullif(reaction,'') IS NOT NULL''')
                output=table_check(conn,'shard_report_reactions')
                conn.execute(f"COPY shard_report_reactions TO {quote(partial)} (FORMAT PARQUET,COMPRESSION ZSTD)")
                if (pq.ParquetFile(partial).metadata.num_rows!=output['row_count']
                    or table_check(conn,f'read_parquet({quote(partial)})')!=output):
                    raise ValueError('Reaction shard Parquet verification failed')
                partial.replace(path)
                saved={'signature':signature,'shard_id':bucket,'complete':True,'output':output,'stats':stats,
                       'sha256':file_digest(path),'started_at':started_at,'completed_at':now(),
                       'seconds':round(time.monotonic()-started,3),'errors':[],
                       'process_peak_rss_bytes_after':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),
                       'resource_scope':'Process high-water RSS, not an isolated per-query peak; DuckDB limits remain 2GB/20GB.'}
                atomic_json(receipt,saved)
            manifest['completed_shard_ids'].append(bucket);manifest['shards'].append(saved)
            manifest.update(updated_at=now(),next_shard_id=bucket+1 if bucket+1<buckets else None)
            atomic_json(out/'manifest.json',manifest)
            print(json.dumps({'reaction_shard':bucket,'rows':saved['output']['row_count'],'completed':len(manifest['shards'])}),flush=True)
        expected={f'shard-{i:03d}{suffix}' for i in range(buckets) for suffix in ('.json','.parquet')}|{'manifest.json'}
        if any(p.name not in expected for p in out.iterdir()):raise ValueError('Unexpected reaction shard artifact')
        check={'row_count':sum(s['output']['row_count'] for s in manifest['shards']),
               'row_hash_xor':0,'row_hash_sum':str(sum(int(s['output']['row_hash_sum'] or 0) for s in manifest['shards']))}
        for saved in manifest['shards']:check['row_hash_xor']^=saved['output']['row_hash_xor'] or 0
        exists=conn.execute("SELECT count(*) FROM information_schema.tables WHERE table_name='report_reactions'").fetchone()[0]
        current=table_check(conn,'report_reactions') if exists else None
        if current!=check:
            paths='['+','.join(quote(out/f'shard-{i:03d}.parquet') for i in range(buckets))+']'
            conn.execute('CREATE OR REPLACE TABLE report_reactions AS SELECT * FROM read_parquet('+paths+')')
        actual=table_check(conn,'report_reactions')
        if actual['row_count']!=check['row_count'] or (actual['row_hash_xor'] or 0)!=check['row_hash_xor'] or int(actual['row_hash_sum'] or 0)!=int(check['row_hash_sum']):
            raise ValueError('Reaction union integrity failed')
        manifest['totals']={k:sum(s['stats'][k] for s in manifest['shards']) for k in manifest['shards'][0]['stats']}
        manifest.update(complete=True,union_integrity_passed=True,output=actual,current_shard_id=None,current_error=None,updated_at=now())
        atomic_json(out/'manifest.json',manifest)
        return manifest
    except Exception as exc:
        manifest.update(current_error=type(exc).__name__+': '+str(exc),updated_at=now())
        atomic_json(out/'manifest.json',manifest)
        raise

def materialize_monthly(conn,root,*,buckets=32):
    """Build the drug-reaction-month aggregation in durable bounded shards."""
    root=Path(root)
    out=root/'analysis-shards/monthly'
    out.mkdir(parents=True,exist_ok=True)

    if type(buckets) is not int or buckets<1:
        raise ValueError('Invalid monthly shard count')

    selected=json.loads((root/'analysis-selected-checkpoint.json').read_text())

    inputs={
        'latest_reports':table_check(conn,'latest_reports'),
        'report_ingredients':table_check(conn,'report_ingredients'),
        'report_reactions':table_check(conn,'report_reactions'),
        'mention_counts':table_check(conn,'mention_counts'),
    }

    signature=fingerprint({
        'selected_checkpoint_signature':selected['signature'],
        'inputs':inputs,
        'buckets':buckets,
        'duckdb_version':duckdb.__version__,
        'partition_expression':f'hash(ingredient_id)%{buckets}',
        'semantics':'drug-reaction-month-v1; exact existing monthly aggregation semantics',
    })

    manifest={
        'signature':signature,
        'buckets':buckets,
        'complete':False,
        'completed_shard_ids':[],
        'shards':[],
        'inputs':inputs,
        'partition_expression':f'hash(ingredient_id)%{buckets}',
    }

    try:
        for bucket in range(buckets):
            manifest.update(
                current_shard_id=bucket,
                current_error=None,
                updated_at=now(),
            )
            atomic_json(out/'manifest.json',manifest)

            path=out/f'shard-{bucket:03d}.parquet'
            receipt=path.with_suffix('.json')

            if receipt.exists():
                saved=json.loads(receipt.read_text())

                if (
                    saved['signature']!=signature
                    or saved['shard_id']!=bucket
                    or not saved['complete']
                    or not path.exists()
                    or file_digest(path)!=saved['sha256']
                    or pq.ParquetFile(path).metadata.num_rows!=saved['output']['row_count']
                ):
                    raise ValueError(
                        'Monthly shard checkpoint mismatch: '+str(receipt)
                    )

            else:
                if path.exists():
                    raise ValueError(
                        'Monthly shard output lacks receipt: '+str(path)
                    )

                partial=path.with_suffix('.partial')

                if partial.exists():
                    raise ValueError(
                        'Inspect unfinished monthly shard staging before retry: '
                        +str(partial)
                    )

                if shutil.disk_usage(root).free<40*1024**3:
                    raise ValueError('Research disk reserve reached')

                started=time.monotonic()
                started_at=now()

                predicate=f'hash(d.ingredient_id)%{buckets}={bucket}'

                conn.execute(f'''CREATE OR REPLACE TEMP TABLE shard_monthly AS
                    SELECT
                        d.ingredient_id,
                        x.reaction,
                        date_trunc('month',CAST(r.last_received AS DATE))::DATE AS period,
                        count(*)::BIGINT AS report_count,
                        count(DISTINCT r.case_id)::BIGINT AS unique_case_count,
                        count(*) FILTER(WHERE serious)::BIGINT AS serious_count,
                        count(*) FILTER(WHERE serious IS NOT NULL)::BIGINT AS serious_known_count,
                        count(*) FILTER(WHERE death)::BIGINT AS death_report_count,
                        count(*) FILTER(WHERE hospitalization)::BIGINT AS hospitalization_count,
                        count(*) FILTER(WHERE disability)::BIGINT AS disability_count,
                        count(*) FILTER(WHERE life_threatening)::BIGINT AS life_threatening_count,
                        count(*) FILTER(WHERE suspect)::BIGINT AS suspect_count,
                        count(*) FILTER(WHERE concomitant)::BIGINT AS concomitant_count,
                        count(*) FILTER(WHERE interacting)::BIGINT AS interacting_count,
                        avg(c.co_drugs)::DOUBLE AS mean_co_reported_drugs
                    FROM latest_reports r
                    JOIN report_ingredients d USING(report_uid)
                    JOIN report_reactions x USING(report_uid)
                    JOIN mention_counts c USING(report_uid)
                    WHERE
                        r.last_received IS NOT NULL
                        AND (r.first_received IS NULL OR r.last_received>=r.first_received)
                        AND {predicate}
                    GROUP BY d.ingredient_id,x.reaction,period''')

                duplicate_groups=conn.execute('''SELECT count(*) FROM (
                    SELECT ingredient_id,reaction,period,count(*) n
                    FROM shard_monthly
                    GROUP BY ingredient_id,reaction,period
                    HAVING count(*)>1
                )''').fetchone()[0]

                if duplicate_groups:
                    raise ValueError(
                        'Monthly shard contains duplicate aggregation keys'
                    )

                output=table_check(conn,'shard_monthly')

                conn.execute(
                    f"COPY shard_monthly TO {quote(partial)} "
                    "(FORMAT PARQUET,COMPRESSION ZSTD)"
                )

                if pq.ParquetFile(partial).metadata.num_rows!=output['row_count']:
                    raise ValueError('Monthly shard Parquet row mismatch')

                if table_check(
                    conn,
                    f'read_parquet({quote(partial)})'
                )!=output:
                    raise ValueError(
                        'Monthly shard Parquet content mismatch'
                    )

                partial.replace(path)

                saved={
                    'signature':signature,
                    'shard_id':bucket,
                    'complete':True,
                    'output':output,
                    'sha256':file_digest(path),
                    'started_at':started_at,
                    'completed_at':now(),
                    'seconds':round(time.monotonic()-started,3),
                    'errors':[],
                    'process_peak_rss_bytes_after':
                        resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                        *(1 if sys.platform=='darwin' else 1024),
                    'resource_scope':
                        'Process high-water RSS; DuckDB limits remain 2GB/20GB.',
                }

                atomic_json(receipt,saved)

            manifest['completed_shard_ids'].append(bucket)
            manifest['shards'].append(saved)
            manifest.update(
                updated_at=now(),
                next_shard_id=bucket+1 if bucket+1<buckets else None,
            )
            atomic_json(out/'manifest.json',manifest)

            print(json.dumps({
                'monthly_shard':bucket,
                'rows':saved['output']['row_count'],
                'completed':len(manifest['shards']),
            }),flush=True)

        expected={
            f'shard-{i:03d}{suffix}'
            for i in range(buckets)
            for suffix in ('.json','.parquet')
        }|{'manifest.json'}

        if any(p.name not in expected for p in out.iterdir()):
            raise ValueError('Unexpected monthly shard artifact')

        check={
            'row_count':sum(
                s['output']['row_count']
                for s in manifest['shards']
            ),
            'row_hash_xor':0,
            'row_hash_sum':str(sum(
                int(s['output']['row_hash_sum'] or 0)
                for s in manifest['shards']
            )),
        }

        for saved in manifest['shards']:
            check['row_hash_xor']^=saved['output']['row_hash_xor'] or 0

        paths='['+','.join(
            quote(out/f'shard-{i:03d}.parquet')
            for i in range(buckets)
        )+']'

        conn.execute(
            'CREATE OR REPLACE TABLE monthly AS '
            'SELECT * FROM read_parquet('+paths+')'
        )

        actual=table_check(conn,'monthly')

        if (
            actual['row_count']!=check['row_count']
            or (actual['row_hash_xor'] or 0)!=check['row_hash_xor']
            or int(actual['row_hash_sum'] or 0)!=int(check['row_hash_sum'])
        ):
            raise ValueError('Monthly shard union integrity failed')

        duplicate_groups=conn.execute('''SELECT count(*) FROM (
            SELECT ingredient_id,reaction,period,count(*) n
            FROM monthly
            GROUP BY ingredient_id,reaction,period
            HAVING count(*)>1
        )''').fetchone()[0]

        if duplicate_groups:
            raise ValueError(
                'Monthly union contains duplicate aggregation keys'
            )

        manifest.update(
            complete=True,
            union_integrity_passed=True,
            output=actual,
            current_shard_id=None,
            current_error=None,
            updated_at=now(),
        )

        atomic_json(out/'manifest.json',manifest)
        return manifest

    except Exception as exc:
        manifest.update(
            current_error=type(exc).__name__+': '+str(exc),
            updated_at=now(),
        )
        atomic_json(out/'manifest.json',manifest)
        raise
