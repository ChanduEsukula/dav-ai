"""Scientific guardrails for native release continuity diagnostics."""
import importlib.util
from pathlib import Path
import sqlite3

SCRIPT=Path(__file__).resolve().parents[3]/'scripts/audit_fda_native_continuity.py'
spec=importlib.util.spec_from_file_location('native_continuity',SCRIPT)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def database(rows,deleted=()):
    c=sqlite3.connect(':memory:')
    c.execute('CREATE TABLE demo(release,pid,cid,ver_raw,ver_num,init_raw,fda_raw,init_date,fda_date,row_hash)')
    c.execute('CREATE TABLE deletions(release,cid)')
    c.executemany('INSERT INTO demo VALUES(?,?,?,?,?,?,?,?,?,?)',rows)
    c.executemany('INSERT INTO deletions VALUES(?,?)',deleted)
    return c


def row(release,cid,version,date='2024-09-01',fingerprint='unchanged'):
    return (release,cid+str(version),cid,str(version),version,'20240101',date.replace('-',''),'2024-01-01',date,fingerprint)


def test_nonappearance_is_separate_from_explicit_deletion():
    c=database([row('a','1',1),row('a','2',1),row('b','3',1)],[('b','2')])
    t=module.transition(c,'a','b')
    assert t['caseid']['earlier_only_keys']==2
    assert t['deletion_evidence']['earlier_absent_and_explicitly_listed']==1
    assert t['deletion_evidence']['earlier_absent_not_listed_deleted']==1


def test_version_change_and_backward_date_are_observed_without_repair():
    c=database([row('a','1',1,'2024-09-01'),row('b','1',2,'2024-08-01')])
    t=module.transition(c,'a','b')
    assert t['caseid']['persistent_keys']==1
    assert t['primaryid']['persistent_keys']==0
    assert t['case_versions']['higher_version']==1
    assert t['case_versions']['latest_receipt_moved_backward']==1
    assert c.execute("SELECT fda_date FROM demo WHERE release='b'").fetchone()[0]=='2024-08-01'


def test_ambiguous_case_is_not_silently_selected():
    c=database([row('a','1',1),row('a','1',2),row('b','1',3)])
    t=module.transition(c,'a','b')
    assert t['case_versions']['ambiguous_comparison']==1
    assert t['case_versions']['higher_version']==0
    assert c.execute('SELECT count(*) FROM demo').fetchone()[0]==3


def test_partial_or_malformed_dates_remain_unknown():
    assert module.parse_date('20240230')==(None,'unparseable_or_partial')
    assert module.parse_date('2024')==(None,'unparseable_or_partial')
    assert module.parse_date('')==(None,'missing')
    assert module.parse_date('20240229')==('2024-02-29','valid_calendar')
