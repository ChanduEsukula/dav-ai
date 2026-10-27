"""Small live progress report; use audit_research for checksum verification."""
import argparse
import fcntl
import json
from pathlib import Path
import shutil
import time

from app.research.bulk import atomic_json, now
from app.research.identity import snapshot


def size(paths):
    total=0
    for path in paths:
        try:
            if path.is_file():total+=path.stat().st_size
        except FileNotFoundError:
            pass # A disposable cache/staging file may finish during live inspection.
    return total


def status(root):
    root=Path(root);source=snapshot(root,'event')
    receipts=[json.loads(p.read_text()) for p in source.glob('files/quarter=*/*/receipt.json')
              if not p.parent.name.endswith('.partial')]
    manifest=json.loads((source/'manifest.json').read_text())['results']['drug']['event']
    done={r['url'] for r in receipts}
    pending=[p['file'] for p in sorted(manifest['partitions'],key=lambda p:p['file']) if p['file'] not in done]
    mapping=json.loads((root/'identity/summary.json').read_text())['mapping_hash']
    normalized=root/'normalized'/mapping/source.name
    summary=json.loads((root/'analysis-summary.json').read_text()) if (root/'analysis-summary.json').exists() else {}
    progress=json.loads((source/'progress.json').read_text()) if (source/'progress.json').exists() else {}
    phase_path=root/'phase-status.json'
    phase=json.loads(phase_path.read_text()) if phase_path.exists() else {}
    stages={}
    for name in ('resolved_drugs','report_reactions'):
        checkpoint=root/'analysis-shards'/name/'manifest.json'
        if checkpoint.exists():
            saved=json.loads(checkpoint.read_text())
            stages[name]={k:saved.get(k) for k in ('complete','buckets','completed_shard_ids','next_shard_id','current_error')}
    return {'checked_at':now(),'dataset_key':source.name,'files_complete':len(receipts),
        'files_total':len(manifest['partitions']),'files_remaining':len(pending),
        'raw_reports':sum(r['records'] for r in receipts),
        'quarantined_records':sum(r['quarantined'] for r in receipts),
        'current_error':progress.get('error'),
        'stop_reason':progress.get('stop_reason'),
        'last_completed':max(receipts,key=lambda r:r['completed_at'])['url'] if receipts else None,
        'next_file':pending[0] if pending else None,
        'normalization_receipts':len(list(normalized.glob('*.json'))),
        'aggregation_input_files':summary.get('input_files'),
        'incomplete_source_staging':len(list(source.glob('files/quarter=*/*.partial'))),
        'free_bytes':shutil.disk_usage(root).free,
        'retained_zip_bytes':size(root.rglob('*.zip')),
        'event_parquet_bytes':sum(r['parquet_bytes'] for r in receipts),
        'normalized_bytes':size((root/'normalized').rglob('*')),
        'duckdb_bytes':size([root/'analysis.duckdb',root/'analysis.duckdb.wal']),
        'spill_bytes':size((root/'duckdb_tmp').rglob('*')),
        'research_storage_bytes':size(root.rglob('*')),
        'pipeline_active':active(root),
        'research_phase':phase.get('research_phase','ingestion'),
        'audit_state':phase.get('audit_state','Full-corpus audit pending'),
        'replay_state':phase.get('replay_state','Completed-corpus replay pending'),
        'historical_availability_state':phase.get('historical_availability_state','Unverified'),
        'target_analysis_state':phase.get('target_analysis_state','Expanded feasibility study pending; no primary target selected'),
        'ml_export_state':phase.get('ml_export_state','Blocked; no certified training export'),
        'next_action':phase.get('next_action','Complete pinned ingestion and normalization'),
        'aggregation_state':phase.get('aggregation_state','See aggregation input count and attempt logs'),
        'last_aggregation_error':phase.get('last_aggregation_error'),
        'analytical_shard_checkpoints':stages,
        'counts_basis':'Committed receipts; this live view does not rerun output checksum verification.'}


def active(root):
    with (Path(root)/'pipeline.lock').open('r') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return True
        return False


def write_document(path,root,result,running):
    source=snapshot(root,'event')
    progress=json.loads((source/'progress.json').read_text()) if (source/'progress.json').exists() else {}
    verification_path=Path('docs/evidence/research-continuation-2026-09-26/verification.json')
    verification=json.loads(verification_path.read_text()) if verification_path.exists() else {}
    g=1024**3
    if result['files_remaining']==0:
        commands='''Ingestion, normalization, full audit and actual replay are complete. Do not
rerun them without evidence of invalidation. Validate analytical checkpoints first.
The exact next action is recorded above and in `data/research/phase-status.json`.

Current checkpoint publication command (safely reuses completed shard receipts):

```sh
PYTHONPATH=backend .venv/bin/python -m app.jobs.checkpoint_drug_join --origin-log docs/evidence/research-continuation-2026-09-26/full-aggregation-attempt-3.log
```

After the drug checkpoint is complete and semantic tests pass, analytical resume:

```sh
PYTHONPATH=backend .venv/bin/python scripts/run_full_research_analysis.py --attempt 4 --resume-drugs
```
Do not start either command concurrently with an active analytical process.'''
    else:
        commands='''```sh
PYTHONPATH=backend .venv/bin/python -m app.jobs.ingest_research event --resume --normalize --discard-archives --min-free-gb 40 --max-seconds 3600
```
After ingestion completes, perform full audit and completed-corpus replay before aggregation.'''
    payload=f'''# Continuation status — active research pipeline

Updated {result['checked_at']} from durable receipts. Ingestion is **{'running' if running else 'stopped at a checkpoint'}**.
This is not a completed ML dataset. No model trained, no deployment performed.

## Exact current state

- Pinned snapshot: `{result['dataset_key']}`.
- FDA files complete: **{result['files_complete']:,} / {result['files_total']:,}**.
- Remaining source files: **{result['files_remaining']:,}**.
- Raw reports: **{result['raw_reports']:,}**.
- Quarantined event records: **{result['quarantined_records']:,}**.
- Last completed source file: `{result['last_completed']}`.
- Next source file: `{result['next_file']}`.
- Completed normalization receipts: **{result['normalization_receipts']:,}**.
- Aggregation covers **{result['aggregation_input_files']} files** of the {result['files_total']} pinned files.
- Incomplete source staging directories: {result['incomplete_source_staging']} (normal while a file is active).
- Current pipeline error: `{json.dumps(progress.get('error'))}`.
- Recorded stop reason: `{progress.get('stop_reason')}`.

## Research phase and next action

- Current phase: {result['research_phase']}.
- Full audit: {result['audit_state']}.
- Completed replay: {result['replay_state']}.
- Historical availability: {result['historical_availability_state']}.
- Target analysis: {result['target_analysis_state']}.
- ML export: {result['ml_export_state']}.
- Next action: {result['next_action']}.
- Aggregation state: {result['aggregation_state']}.
- Last aggregation error: {result['last_aggregation_error']}.
- Durable analytical shard checkpoints: `{json.dumps(result['analytical_shard_checkpoints'])}`.

The first unfinished phase may be normalization of the last committed source
file. The resume command repairs missing normalization checkpoints before fetching
the next source file; valid normalization outputs are reused. Per-file receipts,
not a stale aggregate summary, are authoritative. Use `audit_research` for a fresh
full checksum/Parquet row-count audit. The 312-file audit and corrected aggregation
are preserved in `docs/evidence/research-continuation-2026-09-26/`.

## Resources

| Measurement | GiB |
|---|---:|
| Available disk | {result['free_bytes']/g:.2f} |
| Total research storage | {result['research_storage_bytes']/g:.2f} |
| Retained research ZIPs | {result['retained_zip_bytes']/g:.2f} |
| Completed event Parquet | {result['event_parquet_bytes']/g:.2f} |
| Normalized output | {result['normalized_bytes']/g:.2f} |
| DuckDB plus WAL | {result['duckdb_bytes']/g:.2f} |
| Temporary spill | {result['spill_bytes']/g:.2f} |

The protected PostgreSQL backup is 2,213,621,015 bytes and its saved SHA-256 was
verified. Do not delete it or any verified partitions/manifests/receipts.
Ingestion maintains a 40 GiB reserve plus next-file allowance. JSON is streamed,
not expanded to temporary disk. DuckDB uses one thread, 2 GB working memory and
a 20 GB spill ceiling; Python/Arrow allocations are additional.

## Exact commands

From `/Users/chanduesukula/dav-ai`, after the current process releases its lock:

{commands}

Live state: `PYTHONPATH=backend .venv/bin/python -m app.jobs.research_status`.
Do not launch a second ingester while the lock is held. Manifest-change protection
must remain enabled. Do not restart label imports, identity construction or the
completed source/normalization partitions.

## Analytical issues and readiness

Missing numeric versions no longer discard otherwise unambiguous source cases.
The 312-file aggregation selected 3,543,317 of 3,545,093 source cases; 1,776 cases
were ambiguous. Ranking full report rows first exceeded 2 GB. Narrow file-row
ranking succeeded in 77.23 seconds using the same limit; logs are preserved.

That analysis found **2,717,932 selected reports with contradictory receipt-date
chronology** under FDA's definitions. Raw archive inspection confirmed the issue.
Do not swap or invent dates. Temporal aggregates exclude those cases and retain
the original source records. This is a major selection/coverage limitation.

Current snapshots do not establish historical public availability of report
revisions or mappings. Cutoff-enforced label and recall joins both yielded zero
eligible rows in the 312-file analysis; unknown is not absence. Strict training
exports remain blocked, and incomplete periods must not become zero counts.
Period/support choice, final target prevalence, chronological splits and nonempty
Colab exports are unfinished. Preserve these limitations even after ingestion finishes.

## Tests, documents and next work

Verification logs and `verification.json` are in
`docs/evidence/research-continuation-2026-09-26/`; they record the exact tested state.
Backend: {verification.get('backend',{}).get('passed','not recorded')} passed;
frontend: {verification.get('frontend',{}).get('passed','not recorded')} passed;
production build exit code: {verification.get('production_build',{}).get('exit_code','not recorded')}.
See [DATASET_REPORT.md](DATASET_REPORT.md),
[TARGET_DEFINITION_ANALYSIS.md](TARGET_DEFINITION_ANALYSIS.md),
[COLAB_HANDOFF.md](COLAB_HANDOFF.md), [MODEL_PLAN.md](MODEL_PLAN.md), and
[deployment preparation](../DEPLOYMENT_PLAN.md).
Date and legacy identifier limitations are documented in [SOURCE_SEMANTICS.md](SOURCE_SEMANTICS.md).

Finish ingestion/normalization, verify the full corpus and actual replay reuse,
then refresh the bounded aggregation and review
date validity and availability before finalizing ML exports. No PyTorch training,
production deployment, or résumé writing is authorized in this phase.

The user has authorized investigation of dated official FDA quarterly production
archives as a separate supplementary source **after full pinned-corpus completion,
verification and corrected aggregation**. Preserve the pinned corpus and mark
unproven availability UNKNOWN. Do not repeatedly rebuild aggregation during ingestion.
After historical-source review, complete the expanded target feasibility study
before selecting any primary ML problem. Compare reporting growth/surge, serious
surge, persistence, abnormal periods and conditionally supported recall, shortage,
utilization/spending or multi-source targets. Assess authoritative public-source
availability, keys, coverage, leakage, costs and value before large external
downloads. No earlier preference for surge onset is a binding target decision.
Future hybrid RAG is documentation-only in this phase and follows trained-model
integration. Deployment must target $0 recurring cost, with only domain spending
allowed; the application database already measures 7.86 GiB before vectors/models.
Keep the Docker exclusions and the frontend asynchronous loading assertion fix.
'''
    temporary=path.with_suffix('.tmp');temporary.write_text(payload);temporary.replace(path)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path('data/research'))
    parser.add_argument('--output',type=Path)
    parser.add_argument('--document',type=Path)
    parser.add_argument('--watch',action='store_true',help='Update every 30 seconds until ingestion releases its lock')
    args=parser.parse_args()
    while True:
        result=status(args.root);running=active(args.root)
        if args.output:
            args.output.parent.mkdir(parents=True,exist_ok=True);atomic_json(args.output,result)
        if args.document:write_document(args.document,args.root,result,running)
        print(json.dumps(result,indent=2),flush=True)
        if not args.watch or not running:break
        time.sleep(30)


if __name__=='__main__':main()
