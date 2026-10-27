"""Research-only counts, as-of guards, and explicit retrospective exploration.

Current snapshots cannot reconstruct historical public availability. Strict exports
are blocked until multiple archived vintages support temporal evaluation.
"""
from datetime import date, datetime
import json
import inspect
from pathlib import Path
import time

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
from app.research.bulk import file_digest, fingerprint, now, atomic_json
from app.research.identity import IdentityIndex, snapshot, records


def quote(value):return "'"+str(value).replace("'","''")+"'"


def normalize_mentions(root, paths=None, index=None):
    root=Path(root);index=index or IdentityIndex.load(root)
    mapping_hash=json.loads((root/'identity/summary.json').read_text())['mapping_hash']
    source=snapshot(root,'event');out=root/'normalized'/mapping_hash/source.name;out.mkdir(parents=True,exist_ok=True)
    schema=pa.schema([('report_uid',pa.string()),('drug_index',pa.int32()),('ingredient_ids',pa.list_(pa.string())),
                     ('resolution',pa.string()),('mapping_observed_at',pa.string())])
    destinations=[]
    selected = paths if paths is not None else sorted(source.glob('files/quarter=*/*/drugs.parquet'))
    for path in selected:
        if path.parent.name.endswith('.partial') or not (path.parent/'receipt.json').exists():
            continue
        dest=out/(path.parent.name+'.parquet');receipt=dest.with_suffix('.json')
        destinations.append(dest)
        signature=file_digest(path)
        source_rows=pq.ParquetFile(path).metadata.num_rows
        if receipt.exists() and dest.exists():
            saved=json.loads(receipt.read_text())
            if (saved['input_hash']==signature and saved['output_hash']==file_digest(dest)
                and pq.ParquetFile(dest).metadata.num_rows==source_rows):continue
        partial=dest.with_suffix('.partial')
        with pq.ParquetWriter(partial,schema,compression='zstd') as writer:
            # Dose/indication/route text is preserved in source Parquet but is not
            # consulted by this exact-identity resolver. Avoid materializing it.
            columns=['report_uid','drug_index','medicinalproduct','rxcui','product_ndc',
                     'package_ndc','substance_name','generic_name','brand_name']
            for batch in pq.ParquetFile(path).iter_batches(batch_size=2000,columns=columns):
                normalized=[]
                for row in batch.to_pylist():
                    ids,reason=index.resolve(row)
                    normalized.append({'report_uid':row['report_uid'],'drug_index':row['drug_index'],
                        'ingredient_ids':ids,'resolution':reason,'mapping_observed_at':index.mapping['observed_at']})
                writer.write_table(pa.Table.from_pylist(normalized,schema=schema))
        output_rows=pq.ParquetFile(partial).metadata.num_rows
        if output_rows!=source_rows:raise ValueError('Normalization row count does not match source mentions')
        partial.replace(dest)
        atomic_json(receipt,{'input_hash':signature,'output_hash':file_digest(dest),
                            'source_rows':source_rows,'normalized_rows':output_rows})
    return destinations


def export_context(root):
    """Current official regulatory snapshots; never backdate their availability."""
    from app.db.pharma.connection import connect
    root=Path(root);out=root/'context';out.mkdir(exist_ok=True)
    index=IdentityIndex.load(root)
    schema=pa.schema([(k,pa.string()) for k in ['kind','source_id','ingredient_id','source_date','available_at','classification']]+
                     [('boxed_warning_present',pa.bool_()),('warning_section_present',pa.bool_())])
    rows=[];counts={'labels_total':0,'labels_resolved':0,'recalls_total':0,'recalls_resolved':0}
    def append(kind,sid,dt,observed,mention,**extra):
        counts[kind+'_total']+=1
        ids,_=index.resolve(mention)
        if ids:counts[kind+'_resolved']+=1
        available=max(str(observed),index.mapping['observed_at'])[:10]
        for identifier in ids:
            rows.append(dict(kind=kind,source_id=sid,ingredient_id=identifier,source_date=str(dt)[:10] if dt else None,
                             available_at=available,classification=None,boxed_warning_present=None,warning_section_present=None,**extra))
    with pq.ParquetWriter(out/'regulatory.parquet',schema,compression='zstd') as writer:
        with connect() as conn,conn.cursor(name='research_label_context') as cursor:
            cursor.itersize=500
            cursor.execute("""SELECT source_record_id,effective_date,ingested_at,
                raw_json->'openfda' AS identity,
                nullif(trim(boxed_warning),'') IS NOT NULL AS boxed,
                nullif(trim(warnings_and_precautions),'') IS NOT NULL AS warning
                FROM pharma.drug_labels ORDER BY source_record_id""")
            for row in cursor:
                # Availability is the actual observed snapshot, not the effective date.
                mention=row['identity'] or {}
                counts['labels_total']+=1
                ids,_=index.resolve(mention)
                if ids:counts['labels_resolved']+=1
                for identifier in ids:
                    rows.append({'kind':'labels','source_id':row['source_record_id'],'ingredient_id':identifier,
                        'source_date':str(row['effective_date']) if row['effective_date'] else None,
                        'available_at':max(row['ingested_at'].date().isoformat(),index.mapping['observed_at'][:10]),
                        'boxed_warning_present':row['boxed'],'warning_section_present':row['warning'],'classification':None})
                if len(rows)>=1000:
                    writer.write_table(pa.Table.from_pylist(rows,schema=schema));rows=[]
        for row in records(root,'enforcement'):
            from app.research.bulk import source_date
            raw=json.loads(row['raw_json']);ids,_=index.resolve(raw.get('openfda') or {})
            counts['recalls_total']+=1
            if ids:counts['recalls_resolved']+=1
            for identifier in ids:
                rows.append({'kind':'recalls','source_id':row['source_id'],'ingredient_id':identifier,
                    'source_date':source_date(raw.get('report_date')),
                    'available_at':max(row['observed_at'][:10],index.mapping['observed_at'][:10]),
                    'classification':raw.get('classification'),'boxed_warning_present':None,'warning_section_present':None})
            if len(rows)>=1000:
                writer.write_table(pa.Table.from_pylist(rows,schema=schema));rows=[]
        if rows:writer.write_table(pa.Table.from_pylist(rows,schema=schema))
    (out/'summary.json').write_text(json.dumps(counts,indent=2));return counts


def available_context(rows,ingredient,cutoff,kind):
    """NULL is unknown coverage, not absence. Used by tests and documentation examples."""
    valid=[r for r in rows if r['ingredient_id']==ingredient and r['kind']==kind
           and r.get('available_at') and r['available_at']<=cutoff
           and r.get('source_date') and r['source_date']<=cutoff]
    return valid or None


def eligible_asof(report,cutoff,mapping_observed_at):
    return bool(report.get('observed_at') and report['observed_at'][:10]<=cutoff
                and mapping_observed_at[:10]<=cutoff and report.get('last_received')
                and report['last_received']<=cutoff)


def connect_analytics(root):
    conn=duckdb.connect(str(Path(root)/'analysis.duckdb'))
    conn.execute("SET memory_limit='2GB'")
    conn.execute("SET max_temp_directory_size='20GB'")
    conn.execute('SET threads=1')
    conn.execute('SET preserve_insertion_order=false')
    conn.execute('SET temp_directory='+quote(Path(root)/'duckdb_tmp'))
    return conn


def rows(conn,query):
    result=conn.execute(query)
    return [dict(zip([d[0] for d in result.description],row)) for row in result.fetchall()]


def temporal_coverage(conn,unit):
    """Receipt-date coverage; source archive quarter is separate provenance."""
    if unit not in ('year','quarter'):
        raise ValueError('Unsupported coverage period')
    period=f"date_trunc('{unit}',CAST(last_received AS DATE))::DATE"
    return rows(conn,f'''WITH raw AS (
        SELECT {period} period,count(*) raw_reports,count(DISTINCT case_id) source_cases
        FROM raw_reports WHERE last_received IS NOT NULL GROUP BY period),
        selected AS (SELECT {period} period,count(*) selected_cases,
            count(*) FILTER(WHERE first_received>last_received) contradictory_date_cases
            FROM latest_reports WHERE last_received IS NOT NULL GROUP BY period),
        ingredients AS (SELECT {period} period,count(DISTINCT ingredient_id) canonical_ingredients
            FROM latest_reports JOIN report_ingredients USING(report_uid)
            WHERE last_received IS NOT NULL AND (first_received IS NULL OR last_received>=first_received)
            GROUP BY period),
        reactions AS (SELECT {period} period,count(DISTINCT reaction) reactions
            FROM latest_reports JOIN report_reactions USING(report_uid)
            WHERE last_received IS NOT NULL AND (first_received IS NULL OR last_received>=first_received)
            GROUP BY period),
        pairs AS (SELECT date_trunc('{unit}',period)::DATE period,
            count(DISTINCT (ingredient_id,reaction)) drug_reaction_pairs,
            sum(report_count) co_report_incidences FROM monthly GROUP BY 1)
        SELECT raw.*,coalesce(selected_cases,0) selected_cases,
            coalesce(contradictory_date_cases,0) contradictory_date_cases,
            coalesce(canonical_ingredients,0) canonical_ingredients,
            coalesce(reactions,0) reactions,coalesce(drug_reaction_pairs,0) drug_reaction_pairs,
            coalesce(co_report_incidences,0) co_report_incidences
        FROM raw LEFT JOIN selected USING(period) LEFT JOIN ingredients USING(period)
        LEFT JOIN reactions USING(period) LEFT JOIN pairs USING(period) ORDER BY period''')


def select_latest_keys(conn,buckets=16):
    """Keep every exported identifier's versions together in bounded ranking shards."""
    if type(buckets) is not int or buckets<1:raise ValueError('Invalid ranking bucket count')
    conn.execute('''CREATE OR REPLACE TABLE latest_report_keys AS
        SELECT filename,file_row_number FROM raw_reports WHERE FALSE''')
    for bucket in range(buckets):
        # Hashing only routes identifiers; it never changes their grouping or
        # ordering, and collisions merely put different identifiers in one shard.
        predicate=f'hash(case_id)%{buckets}={bucket}'
        conn.execute(f'''INSERT INTO latest_report_keys
            WITH ranked AS (SELECT case_id,version,filename,file_row_number,
                row_number() OVER(PARTITION BY case_id ORDER BY version DESC NULLS LAST,
                last_received DESC NULLS LAST,source_hash,source_url,filename,file_row_number) AS rn
                FROM raw_reports WHERE {predicate})
            SELECT r.filename,r.file_row_number FROM ranked r
            JOIN (SELECT * FROM version_audit WHERE {predicate}) v
                ON r.case_id=v.case_id AND r.version IS NOT DISTINCT FROM v.version
            JOIN (SELECT * FROM case_audit WHERE {predicate}) a ON r.case_id=a.case_id
            WHERE rn=1 AND v.distinct_payloads=1
              AND (a.unknown_versions=0 OR a.payloads=1)''')


def selection_signature(root,inputs):
    return fingerprint({'snapshot':snapshot(root,'event').name,'duckdb_version':duckdb.__version__,
        'selector':inspect.getsource(select_latest_keys),
        'reports':{p.parent.name:json.loads((p.parent/'receipt.json').read_text())['outputs']['reports.parquet'] for p in inputs}})


def selection_table_checks(conn):
    # Constant-memory aggregate checks detect changed analytical tables. These
    # are DuckDB row-hash checks, not substitutes for source artifact SHA-256.
    return {table:rows(conn,f'''SELECT count(*) row_count,bit_xor(hash(t)) row_hash_xor,
                    sum(hash(t)::HUGEINT)::VARCHAR row_hash_sum FROM {table} t''')[0]
            for table in ('version_audit','case_audit','latest_report_keys','latest_reports')}


def select_resolved_drugs(conn,buckets=16):
    query='''SELECT DISTINCT d.report_uid,d.drug_index,d.role,unnest(n.ingredient_ids) AS ingredient_id,
        n.mapping_observed_at FROM {drugs} d JOIN {normalized} n USING(report_uid,drug_index)
        JOIN {reports} r USING(report_uid)'''
    conn.execute('CREATE OR REPLACE TABLE resolved_drugs AS '+query.format(
        drugs='(SELECT * FROM raw_drugs WHERE FALSE)',normalized='normalized',reports='latest_reports'))
    for bucket in range(buckets):
        predicate=f'hash(report_uid)%{buckets}={bucket}'
        conn.execute('INSERT INTO resolved_drugs '+query.format(
            drugs=f'(SELECT report_uid,drug_index,role FROM raw_drugs WHERE {predicate})',
            normalized=f'(SELECT * FROM normalized WHERE {predicate} AND len(ingredient_ids)>0)',
            reports=f'(SELECT report_uid FROM latest_reports WHERE {predicate})'))


def prepare(root,*,resume_selection=False,resume_drugs=False):
    root=Path(root)
    if resume_drugs and not resume_selection:raise ValueError('Drug checkpoint reuse requires selection checkpoint reuse')
    source=snapshot(root,'event')
    inputs=sorted(p for p in source.glob('files/quarter=*/*/drugs.parquet')
                  if not p.parent.name.endswith('.partial') and (p.parent/'receipt.json').exists())
    if resume_selection:
        mapping=json.loads((root/'identity/summary.json').read_text())['mapping_hash']
        normalized=[root/'normalized'/mapping/source.name/(p.parent.name+'.parquet') for p in inputs]
        if not all(p.exists() and p.with_suffix('.json').exists() for p in normalized):
            raise ValueError('Existing normalization checkpoint is incomplete; no automatic rebuild on analytical resume')
    else:normalized=normalize_mentions(root,inputs)
    conn=connect_analytics(root)
    for table in ['reports','drugs','reactions']:
        files='['+','.join(quote(p.parent/(table+'.parquet')) for p in inputs)+']'
        positions=',filename=true,file_row_number=true' if table=='reports' else ''
        conn.execute(f'CREATE OR REPLACE VIEW raw_{table} AS SELECT * FROM read_parquet({files}, hive_partitioning=false{positions})')
    files='['+','.join(quote(p) for p in normalized)+']'
    conn.execute('CREATE OR REPLACE VIEW normalized AS SELECT * FROM read_parquet('+files+')')
    checkpoint=root/'analysis-selected-checkpoint.json'
    signature=selection_signature(root,inputs)
    if resume_selection:
        saved=json.loads(checkpoint.read_text())
        if saved['signature']!=signature or saved['tables']!=selection_table_checks(conn):
            raise ValueError('Selected-report checkpoint does not match inputs, selector or durable tables')
    else:
        conn.execute('''CREATE OR REPLACE TABLE version_audit AS
            SELECT case_id,version,count(DISTINCT source_hash) AS distinct_payloads,count(*) AS rows
            FROM raw_reports GROUP BY case_id,version''')
        conn.execute('''CREATE OR REPLACE TABLE case_audit AS
            SELECT case_id,sum(distinct_payloads) payloads,
                coalesce(sum(rows) FILTER(WHERE version IS NULL),0) unknown_versions
            FROM version_audit GROUP BY case_id''')
        # Rank narrow file-row references; preserve the completed stage for safe
        # reuse if a later, independent analytical query needs repair.
        select_latest_keys(conn)
        conn.execute('''CREATE OR REPLACE TABLE latest_reports AS
            SELECT r.* EXCLUDE(filename,file_row_number) FROM raw_reports r
            JOIN latest_report_keys k USING(filename,file_row_number)''')
        atomic_json(checkpoint,{'created_at':now(),'signature':signature,'tables':selection_table_checks(conn)})
    from app.research.shards import verify_drug_checkpoint,materialize_reactions,materialize_monthly
    if resume_drugs:verify_drug_checkpoint(conn,root)
    else:select_resolved_drugs(conn)
    materialize_reactions(conn,root)
    conn.execute('''CREATE OR REPLACE TABLE report_ingredients AS
        SELECT report_uid,ingredient_id,bool_or(role='1') AS suspect,bool_or(role='2') AS concomitant,
        bool_or(role='3') AS interacting,max(mapping_observed_at) AS mapping_observed_at
        FROM resolved_drugs GROUP BY report_uid,ingredient_id''')
    conn.execute('''CREATE OR REPLACE TABLE mention_counts AS SELECT report_uid,count(DISTINCT drug_index) AS co_drugs
        FROM raw_drugs GROUP BY report_uid''')
    materialize_monthly(conn,root)
    summary={
        'reports':rows(conn,'''SELECT count(*) raw_rows,count(DISTINCT case_id) unique_source_cases,
            count(DISTINCT report_uid) distinct_payload_versions,
            count(*)-count(DISTINCT report_uid) exact_duplicate_rows,
            min(first_received) first_receipt_min,max(first_received) first_receipt_max,
            min(last_received) latest_receipt_min,max(last_received) latest_receipt_max,
            count(*) FILTER(WHERE last_received IS NULL) missing_latest_receipt,
            count(*) FILTER(WHERE version IS NULL) missing_numeric_version FROM raw_reports''')[0],
        'versions':rows(conn,'''SELECT count(*) FILTER(WHERE distinct_payloads>1) conflicting_case_versions,
            sum(rows-distinct_payloads) duplicate_rows FROM version_audit''')[0],
        'version_selection':rows(conn,'''SELECT
            count(*) FILTER(WHERE latest.case_id IS NOT NULL) raw_rows_in_selected_cases,
            count(DISTINCT raw.report_uid) FILTER(WHERE latest.case_id IS NOT NULL) payloads_in_selected_cases,
            count(DISTINCT raw.report_uid) FILTER(WHERE latest.case_id IS NOT NULL)
                -count(DISTINCT latest.case_id) superseded_distinct_payloads,
            count(*) FILTER(WHERE latest.case_id IS NULL) raw_rows_in_ambiguous_cases
            FROM raw_reports raw LEFT JOIN latest_reports latest ON raw.case_id=latest.case_id''')[0],
        'latest_cases':conn.execute('SELECT count(*) FROM latest_reports').fetchone()[0],
        'selected_missing_version_cases':conn.execute('SELECT count(*) FROM latest_reports WHERE version IS NULL').fetchone()[0],
        'excluded_ambiguous_cases':conn.execute('SELECT count(DISTINCT case_id) FROM raw_reports WHERE case_id NOT IN (SELECT case_id FROM latest_reports)').fetchone()[0],
        'inconsistent_receipt_date_cases':conn.execute('SELECT count(*) FROM latest_reports WHERE first_received>last_received').fetchone()[0],
        'normalization':rows(conn,'SELECT resolution,count(*) mentions FROM normalized GROUP BY resolution ORDER BY mentions DESC'),
        'drug_roles':rows(conn,'SELECT role,count(*) mentions FROM raw_drugs GROUP BY role ORDER BY mentions DESC'),
        'seriousness':rows(conn,'SELECT serious,count(*) cases FROM latest_reports GROUP BY serious'),
        'reactions':rows(conn,'''SELECT count(DISTINCT normalized_term) unique_terms,
            count(*) FILTER(WHERE normalized_term IS NULL) missing_terms,
            count(DISTINCT meddra_version) supplied_meddra_versions FROM raw_reactions''')[0],
        'top_reactions':rows(conn,'SELECT reaction,count(*) reports FROM report_reactions GROUP BY reaction ORDER BY reports DESC,reaction LIMIT 25'),
        'rare_reactions':rows(conn,'''SELECT frequency,count(*) terms FROM (SELECT reaction,count(*) frequency FROM report_reactions GROUP BY reaction)
            GROUP BY frequency ORDER BY frequency LIMIT 20'''),
        'year_coverage':rows(conn,"SELECT substring(last_received,1,4) AS year,count(*) AS cases FROM latest_reports GROUP BY year ORDER BY year"),
        'source_partition_coverage':rows(conn,'SELECT partition,count(*) cases FROM latest_reports GROUP BY partition ORDER BY partition'),
        'receipt_year_coverage':temporal_coverage(conn,'year'),
        'receipt_quarter_coverage':temporal_coverage(conn,'quarter'),
        'resolved_ingredients':conn.execute('SELECT count(DISTINCT ingredient_id) FROM resolved_drugs').fetchone()[0],
        'pairs':conn.execute('SELECT count(*) FROM (SELECT DISTINCT ingredient_id,reaction FROM monthly)').fetchone()[0],
        'observed_monthly_rows':conn.execute('SELECT count(*) FROM monthly').fetchone()[0],
        'input_files':len(inputs),'input_file_ids':[p.parent.name for p in inputs],
        'analysis_code_sha256':file_digest(Path(__file__)),
        'created_at':now(),'availability_basis':'Latest-receipt retrospective exploration; not historical public availability.'}
    atomic_json(root/'analysis-summary.json',json.loads(json.dumps(summary,default=str)))
    conn.close();return summary


def diagnose_sparsity(root):
    """Descriptive partial-corpus diagnostics, never pair selection for training."""
    root=Path(root);source=snapshot(root,'event')
    manifest=json.loads((source/'manifest.json').read_text())['results']['drug']['event']
    analysis=json.loads((root/'analysis-summary.json').read_text())
    input_ids=set(analysis['input_file_ids'])
    complete=[]
    by_quarter={}
    for part in manifest['partitions']:
        quarter=part['file'].split('/')[-2]
        by_quarter.setdefault(quarter,[]).append(fingerprint(part['file'])[:24])
    # A missing quarter stops contiguous coverage. all_other has no invented date.
    for quarter,ids in sorted(by_quarter.items()):
        if len(quarter)!=6 or quarter[4]!='q':continue
        if not set(ids)<=input_ids:break
        complete.append(quarter)
    if not complete:raise ValueError('No complete contiguous source quarters to describe')
    q=complete[-1];year=int(q[:4]);month=int(q[-1])*3+1
    end=date(year+1,1,1) if month==13 else date(year,month,1)
    first=complete[0];start=date(int(first[:4]),3*(int(first[-1])-1)+1,1)
    c=connect_analytics(root)
    c.execute(f"CREATE OR REPLACE TEMP VIEW diagnostic_monthly AS SELECT * FROM monthly WHERE period>={quote(start)}::DATE AND period<{quote(end)}::DATE")
    distributions=[]
    for unit,multiplier in [('month',1),('quarter',3)]:
        distributions.extend(rows(c,f'''WITH bins AS (
            SELECT ingredient_id,reaction,date_trunc('{unit}',period) period,sum(report_count) reports
            FROM diagnostic_monthly GROUP BY ALL),
            pairs AS (SELECT ingredient_id,reaction,count(*) active_bins,
                date_diff('month',min(period),{quote(end)}::DATE)/{multiplier} possible_bins
                FROM bins GROUP BY ingredient_id,reaction)
            SELECT '{unit}' unit,(SELECT count(*) FROM bins) observed_rows,
                (SELECT quantile_cont(reports,[0.5,0.9,0.99]) FROM bins) reports_per_observed_bin_quantiles,
                count(*) pairs,sum(possible_bins) possible_pair_bins,
                sum(active_bins)/nullif(sum(possible_bins),0) occupied_fraction,
                median(active_bins/possible_bins) median_pair_occupied_fraction FROM pairs'''))
    threshold_rows=[]
    for threshold in [1,3,5,10,20]:
        threshold_rows.extend(rows(c,f'''WITH pairs AS (
            SELECT ingredient_id,reaction,sum(report_count) reports,count(*) temporal_rows
            FROM diagnostic_monthly GROUP BY ingredient_id,reaction)
            SELECT {threshold} minimum_reports,count(*) FILTER(WHERE reports>={threshold}) retained_pairs,
                coalesce(sum(reports) FILTER(WHERE reports>={threshold}),0) retained_pair_report_incidences,
                coalesce(sum(temporal_rows) FILTER(WHERE reports>={threshold}),0) retained_observed_monthly_rows,
                100.0*sum(reports) FILTER(WHERE reports>={threshold})/nullif(sum(reports),0) evidence_retained_percent
            FROM pairs'''))
    result={'input_files':analysis['input_files'],'complete_source_quarters':complete,
            'diagnostic_start':str(start),'diagnostic_end_exclusive':str(end),
            'frequency_comparison':distributions,'threshold_analysis':threshold_rows,
            'decision':'Pending full coverage and training-window-only analysis; diagnostics are not eligibility rules.',
            'count_unit':'Unique source case × ingredient × reaction incidences; not distinct patients or corpus-wide reports.',
            'availability':'Retrospective current snapshot only; no verified historical public availability.'}
    atomic=root/'sparsity-diagnostics.json';atomic.write_text(json.dumps(result,indent=2,default=str))
    c.close();return result


def build_features(root,export_dir='data/ml',max_dense_rows=5_000_000,*,exploratory=False):
    root=Path(root)
    # Never interpret unprocessed partitions as zero reporting or export a stale
    # analysis after ingestion has advanced. Receipts, not summary.json, are truth.
    source=snapshot(root,'event')
    manifest=json.loads((source/'manifest.json').read_text())['results']['drug']['event']
    completed={json.loads(p.read_text())['url'] for p in source.glob('files/quarter=*/*/receipt.json')
               if not p.parent.name.endswith('.partial')}
    if completed!={p['file'] for p in manifest['partitions']}:
        raise ValueError('Incomplete event snapshot: unprocessed periods must not become zero counts')
    analysis=json.loads((root/'analysis-summary.json').read_text())
    if analysis['input_files']!=len(completed):
        raise ValueError('Stale analysis: run prepare after completing ingestion')
    if not exploratory:
        raise ValueError('Historical availability is unverified: no training export is supported by this snapshot. '
                         'Exploratory diagnostics require explicit opt-in and are not training data.')
    out=Path(export_dir);out.mkdir(parents=True,exist_ok=True);c=connect_analytics(root)
    coverage=c.execute('SELECT min(period),max(period),count(DISTINCT period) FROM monthly').fetchone()
    if coverage[0] is None:raise ValueError('No valid dated co-reporting pairs')
    start,end,active_months=coverage
    months=(end.year-start.year)*12+end.month-start.month+1
    if months<18:raise ValueError('Insufficient retrospective coverage even for exploratory temporal partitions')
    val=c.execute("SELECT (?::DATE + (? * INTERVAL '1 month'))::DATE",[start,int(months*.6)]).fetchone()[0]
    test=c.execute("SELECT (?::DATE + (? * INTERVAL '1 month'))::DATE",[start,int(months*.8)]).fetchone()[0]
    # Diagnostic support thresholds are estimated from the proposed older training
    # window only. Eligibility at each cutoff is separately cumulative and causal.
    analysis=[]
    for threshold in [1,3,5,10,20]:
        result=rows(c,f'''WITH p AS (SELECT ingredient_id,reaction,sum(report_count) total,count(*) active,
                min(period) AS first_period FROM monthly WHERE period<{quote(val)}::DATE GROUP BY ingredient_id,reaction)
            SELECT {threshold} minimum_observations,count(*) FILTER(WHERE total>={threshold}) retained_pairs,
                coalesce(sum(total) FILTER(WHERE total>={threshold}),0) retained_pair_report_count,
                count(*) FILTER(WHERE total>={threshold} AND active>=3) history_eligible_pairs,
                coalesce(sum(date_diff('month',first_period,{quote(end)}::DATE)+1) FILTER(WHERE total>={threshold} AND active>=3),0) estimated_dense_rows
            FROM p''')[0]
        analysis.append(result)
    feasible=[r for r in analysis if 0<r['estimated_dense_rows']<=max_dense_rows]
    if not feasible:
        raise ValueError('No tested support threshold fits the declared local row budget')
    chosen=min(feasible,key=lambda r:r['minimum_observations']);threshold=chosen['minimum_observations']
    # Entry is the first cutoff with observed support/history. Freeze the ingredient
    # pair cohort at the proposed training boundary to avoid test-period selection.
    c.execute(f'''CREATE OR REPLACE TABLE pair_entry AS WITH history AS (
        SELECT *,sum(report_count) OVER w cumulative,count(*) OVER w active
        FROM monthly WINDOW w AS(PARTITION BY ingredient_id,reaction ORDER BY period ROWS UNBOUNDED PRECEDING))
        SELECT ingredient_id,reaction,min(period) entry_period FROM history
        WHERE cumulative>={threshold} AND active>=3 AND period<{quote(val)}::DATE GROUP BY ingredient_id,reaction''')
    c.execute(f'''CREATE OR REPLACE TABLE dense AS SELECT e.ingredient_id,e.reaction,t.period::DATE AS period,
        (t.period + INTERVAL '1 month' - INTERVAL '1 day')::DATE AS cutoff,
        coalesce(m.report_count,0)::BIGINT AS report_count,
        coalesce(m.serious_count,0)::BIGINT AS serious_count,
        coalesce(m.serious_known_count,0)::BIGINT AS serious_known_count,
        coalesce(m.suspect_count,0)::BIGINT AS suspect_count,
        coalesce(m.concomitant_count,0)::BIGINT AS concomitant_count,
        coalesce(m.interacting_count,0)::BIGINT AS interacting_count,
        coalesce(m.hospitalization_count,0)::BIGINT AS hospitalization_count,
        coalesce(m.death_report_count,0)::BIGINT AS death_report_count,
        coalesce(m.disability_count,0)::BIGINT AS disability_count,
        coalesce(m.life_threatening_count,0)::BIGINT AS life_threatening_count,
        m.mean_co_reported_drugs,
        date_diff('month',p.first_period,t.period)::INTEGER AS months_since_first_report,
        coalesce(p.pre_entry_reports,0)::BIGINT AS pre_entry_reports
        FROM pair_entry e
        JOIN (SELECT e.ingredient_id,e.reaction,min(m.period) first_period,
            sum(m.report_count) FILTER(WHERE m.period<e.entry_period) pre_entry_reports
            FROM pair_entry e JOIN monthly m USING(ingredient_id,reaction) GROUP BY e.ingredient_id,e.reaction) p USING(ingredient_id,reaction)
        CROSS JOIN LATERAL generate_series(e.entry_period,{quote(end)}::DATE,INTERVAL '1 month') t(period)
        LEFT JOIN monthly m ON m.ingredient_id=e.ingredient_id AND m.reaction=e.reaction AND m.period=t.period''')
    # Historical lag windows use the complete observed history, including months
    # before eligibility; count missing months as zero, not unknown clinical events.
    c.execute(f'''CREATE OR REPLACE TABLE feature_history AS SELECT e.ingredient_id,e.reaction,t.period::DATE period,
        coalesce(m.report_count,0)::BIGINT report_count
        FROM pair_entry e JOIN (SELECT ingredient_id,reaction,min(period) first_period FROM monthly GROUP BY ingredient_id,reaction) p USING(ingredient_id,reaction)
        CROSS JOIN LATERAL generate_series(p.first_period,{quote(end)}::DATE,INTERVAL '1 month') t(period)
        LEFT JOIN monthly m ON m.ingredient_id=e.ingredient_id AND m.reaction=e.reaction AND m.period=t.period''')
    c.execute('''CREATE OR REPLACE TABLE rolled AS SELECT *,
        lag(report_count) OVER w AS reports_previous_1_period,
        sum(report_count) OVER(PARTITION BY ingredient_id,reaction ORDER BY period ROWS BETWEEN 3 PRECEDING AND 1 PRECEDING) AS reports_previous_3_periods,
        sum(report_count) OVER(PARTITION BY ingredient_id,reaction ORDER BY period ROWS BETWEEN 6 PRECEDING AND 1 PRECEDING) AS reports_previous_6_periods,
        sum(report_count) OVER(PARTITION BY ingredient_id,reaction ORDER BY period ROWS BETWEEN 12 PRECEDING AND 1 PRECEDING) AS reports_previous_12_periods,
        avg(report_count) OVER(PARTITION BY ingredient_id,reaction ORDER BY period ROWS BETWEEN 11 PRECEDING AND CURRENT ROW) AS rolling_mean_12,
        stddev_pop(report_count) OVER(PARTITION BY ingredient_id,reaction ORDER BY period ROWS BETWEEN 11 PRECEDING AND CURRENT ROW) AS rolling_std_12,
        lag(report_count,3) OVER w AS lag3,lag(report_count,2) OVER w AS lag2,
        sum(report_count) OVER(PARTITION BY ingredient_id,reaction ORDER BY period ROWS UNBOUNDED PRECEDING) AS cumulative_reports_to_date,
        lead(report_count) OVER w AS next_period_count,
        sum(report_count) OVER(PARTITION BY ingredient_id,reaction ORDER BY period ROWS BETWEEN 1 FOLLOWING AND 3 FOLLOWING) AS future_count_3,
        sum(report_count) OVER(PARTITION BY ingredient_id,reaction ORDER BY period ROWS BETWEEN 1 FOLLOWING AND 6 FOLLOWING) AS future_count_6
        FROM feature_history WINDOW w AS(PARTITION BY ingredient_id,reaction ORDER BY period)''')
    context=root/'context/regulatory.parquet'
    c.execute('CREATE OR REPLACE VIEW regulatory AS SELECT * FROM read_parquet('+quote(context)+')')
    c.execute('''CREATE OR REPLACE TABLE context_months AS SELECT d.ingredient_id,d.cutoff,
        count(DISTINCT r.source_id) FILTER(WHERE r.kind='labels') AS eligible_labels,
        bool_or(r.boxed_warning_present) FILTER(WHERE r.kind='labels') AS boxed_warning_present,
        bool_or(r.warning_section_present) FILTER(WHERE r.kind='labels') AS warning_section_present,
        count(DISTINCT r.source_id) FILTER(WHERE r.kind='recalls' AND CAST(r.source_date AS DATE)>d.cutoff-INTERVAL '3 months') AS recall_count_previous_3m,
        count(DISTINCT r.source_id) FILTER(WHERE r.kind='recalls' AND CAST(r.source_date AS DATE)>d.cutoff-INTERVAL '6 months') AS recall_count_previous_6m,
        count(DISTINCT r.source_id) FILTER(WHERE r.kind='recalls' AND CAST(r.source_date AS DATE)>d.cutoff-INTERVAL '12 months') AS recall_count_previous_12m,
        max(CAST(r.source_date AS DATE)) FILTER(WHERE r.kind='recalls') AS last_recall,
        count(DISTINCT r.source_id) FILTER(WHERE r.kind='recalls') AS known_recall_records
        FROM (SELECT DISTINCT ingredient_id,cutoff FROM dense) d LEFT JOIN regulatory r
        ON r.ingredient_id=d.ingredient_id AND CAST(r.available_at AS DATE)<=d.cutoff AND CAST(r.source_date AS DATE)<=d.cutoff
        GROUP BY d.ingredient_id,d.cutoff''')
    c.execute(f'''CREATE OR REPLACE TABLE features AS SELECT d.* EXCLUDE(pre_entry_reports),
        d.report_count AS unique_case_count,
        NULL::BIGINT AS primary_suspect_count,NULL::BIGINT AS secondary_suspect_count,
        r.reports_previous_1_period,r.reports_previous_3_periods,r.reports_previous_6_periods,r.reports_previous_12_periods,
        r.rolling_mean_12,r.rolling_std_12,r.cumulative_reports_to_date,
        (d.report_count-r.reports_previous_1_period)::DOUBLE / nullif(r.reports_previous_1_period,0) AS growth_1_period,
        (d.report_count-r.lag3)::DOUBLE / nullif(r.lag3,0) AS growth_3_period,
        d.report_count-2*r.reports_previous_1_period+r.lag2 AS acceleration,
        d.serious_count::DOUBLE/nullif(d.serious_known_count,0) AS serious_fraction,
        d.suspect_count::DOUBLE/nullif(d.report_count,0) AS suspect_fraction,
        d.hospitalization_count::DOUBLE/nullif(d.report_count,0) AS reported_hospitalization_flag_fraction,
        CASE WHEN x.eligible_labels>0 THEN true ELSE NULL END AS label_available,
        x.boxed_warning_present,x.warning_section_present,
        CASE WHEN x.known_recall_records>0 THEN x.recall_count_previous_3m ELSE NULL END AS recall_count_previous_3m,
        CASE WHEN x.known_recall_records>0 THEN x.recall_count_previous_6m ELSE NULL END AS recall_count_previous_6m,
        CASE WHEN x.known_recall_records>0 THEN x.recall_count_previous_12m ELSE NULL END AS recall_count_previous_12m,
        date_diff('day',x.last_recall,d.cutoff) AS days_since_last_recall,
        CASE WHEN d.period+INTERVAL '1 month'<={quote(end)}::DATE THEN r.next_period_count END AS next_period_count,
        CASE WHEN d.period+INTERVAL '3 months'<={quote(end)}::DATE THEN r.future_count_3 END AS future_count_3,
        CASE WHEN d.period+INTERVAL '6 months'<={quote(end)}::DATE THEN r.future_count_6 END AS future_count_6,
        false AS historical_availability_verified,
        CASE WHEN d.period<{quote(val)}::DATE THEN 'train' WHEN d.period<{quote(test)}::DATE THEN 'validation' ELSE 'test' END AS exploratory_split
        FROM dense d JOIN rolled r USING(ingredient_id,reaction,period) JOIN context_months x USING(ingredient_id,cutoff)''')
    distributions=[]
    for horizon,target in [(1,'next_period_count'),(3,'future_count_3'),(6,'future_count_6')]:
        # Fixed candidate criteria, not chosen by model performance. Require an
        # increase over baseline and distinguish onset from an ongoing growth state.
        query=f'''SELECT {horizon} horizon_months,count(*) evaluable_rows,
            count(*) FILTER(WHERE {target}>=greatest(5,2*rolling_mean_12*{horizon})) growth_positives,
            count(*) FILTER(WHERE {target}>=greatest(5,rolling_mean_12*{horizon}+3*sqrt({horizon})*greatest(rolling_std_12,1))) surge_positives,
            avg({target}) mean_future_count,var_pop({target}) variance_future_count,
            quantile_cont({target},[0.5,0.9,0.99]) quantiles,
            count(*) FILTER(WHERE {target}=0) zero_future_rows
            FROM features WHERE {target} IS NOT NULL'''
        distributions.extend(rows(c,query))
    c.execute('''CREATE OR REPLACE TABLE candidate_targets AS SELECT ingredient_id,reaction,period,
        next_period_count,future_count_3,future_count_6,ln(1+next_period_count) AS log1p_next_count,
        CASE WHEN future_count_3 IS NOT NULL THEN future_count_3>=greatest(5,2*rolling_mean_12*3) END AS candidate_growth_3m,
        CASE WHEN future_count_3 IS NOT NULL THEN future_count_3>=greatest(5,rolling_mean_12*3+3*sqrt(3)*greatest(rolling_std_12,1)) END AS candidate_surge_3m
        FROM features''')
    c.execute('COPY (SELECT * FROM features ORDER BY ingredient_id,reaction,period) TO '+quote(out/'exploratory_features.parquet')+" (FORMAT PARQUET,COMPRESSION ZSTD)")
    c.execute('COPY (SELECT * FROM candidate_targets ORDER BY ingredient_id,reaction,period) TO '+quote(out/'candidate_targets.parquet')+" (FORMAT PARQUET,COMPRESSION ZSTD)")
    # Strict exports contain no fabricated historical availability or invented targets.
    # Empty partition files have a usable schema, but MUST NOT be advertised trainable.
    target_columns=['next_period_count','future_count_3','future_count_6','exploratory_split']
    exclusion=','.join(target_columns)
    for split in ['train','validation','test']:
        c.execute('COPY (SELECT * EXCLUDE('+exclusion+') FROM features WHERE historical_availability_verified) TO '+quote(out/(split+'.parquet'))+' (FORMAT PARQUET,COMPRESSION ZSTD)')
    columns=rows(c,'DESCRIBE features')
    stats=rows(c,'''SELECT count(*) AS rows,count(*) FILTER(WHERE report_count=0) zero_months,
        count(DISTINCT ingredient_id) ingredients,count(DISTINCT reaction) reactions,
        count(*) FILTER(WHERE label_available) label_joined_rows,
        count(*) FILTER(WHERE recall_count_previous_12m IS NOT NULL) recall_known_rows FROM features''')[0]
    metadata={'created_at':now(),'training_ready':False,'reason':'Only a current snapshot is available; historical public availability cannot be reconstructed.',
        'exploratory_only':True,'threshold_analysis_training_window':analysis,'selected_initial_support':threshold,
        'threshold_rationale':'Lowest tested support fitting the declared dense-row budget with at least three active historical months; cohort frozen before validation.',
        'dense_row_budget':max_dense_rows,'coverage_start':str(start),'coverage_end':str(end),'active_months':active_months,
        'proposed_validation_start':str(val),'proposed_test_start':str(test),
        'split_requirement':'Future target window must finish before the next split boundary; six-month maximum embargo. Strict training exports blocked.',
        'feature_stats':stats,'candidate_distributions':distributions,
        'canonical_mapping_observed_at':IdentityIndex.load(root).mapping['observed_at'],
        'input_event_snapshot':str(snapshot(root,'event')),
        'exports':{p.name:{'bytes':p.stat().st_size,'sha256':file_digest(p)} for p in out.glob('*.parquet')}}
    (out/'dataset_metadata.json').write_text(json.dumps(metadata,indent=2,default=str))
    (out/'feature_schema.json').write_text(json.dumps({'features':columns,'target_columns':target_columns[:3],
        'interpretation':'Co-reporting counts; no causality, incidence, or individual clinical risk.',
        'normalization':'Exact ingredient mapping; MedDRA source terms case/whitespace only. No LLM.'},indent=2,default=str))
    c.close();return metadata
