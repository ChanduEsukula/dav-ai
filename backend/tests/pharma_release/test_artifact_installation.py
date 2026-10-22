"""Managed installation/recovery regressions. Synthetic files only; original release untouched."""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.db.pharma import artifact_store as store
from app.db.pharma import release_connection as release


@pytest.fixture
def artifact(tmp_path, monkeypatch):
    for key in ('DAV_AI_PHARMA_ARTIFACT_ROOT','DAV_AI_PHARMA_RELEASE_DB','DAVAI_ENV','APP_ENV','ENVIRONMENT','PYTHON_ENV','RENDER'):
        monkeypatch.delenv(key, raising=False)
    path=tmp_path/'external.sqlite'
    with closing(sqlite3.connect(path)) as con:
        for name in release.REQUIRED_TABLES - {'release_manifest'}:
            con.execute(f'CREATE TABLE {name} (fixture TEXT)')
        con.execute('CREATE TABLE release_manifest(release_id,contract_id,policy_version,build_version)')
        con.execute('INSERT INTO release_manifest VALUES (?,?,?,?)', (
            'dav-ai-pharma-v1-phase4b-communications-20261006','dav-ai-pharma-release-v1','1.0.0','fixture'))
        con.execute('PRAGMA user_version=4');con.commit()
    path.chmod(0o444)
    monkeypatch.setattr(release,'EXPECTED_BYTES',path.stat().st_size)
    monkeypatch.setattr(release,'EXPECTED_SHA256',hashlib.sha256(path.read_bytes()).hexdigest())
    release._verify_checksum.cache_clear();store.pinned_path.cache_clear()
    yield path, tmp_path/'store'
    store.pinned_path.cache_clear();release._verify_checksum.cache_clear()


def test_install_is_verified_independent_immutable_and_not_activated(artifact):
    source,root=artifact
    before=release.artifact_signature(source)
    result=store.install(source,root,'v1')
    installed=store.installed(root,'v1',reverify=True)
    assert installed.read_bytes()==source.read_bytes() and installed.stat().st_ino!=source.stat().st_ino
    assert release.artifact_signature(source)==before
    assert not installed.stat().st_mode & 0o222
    assert result['activated'] is False and result['verification']['publication_validated'] is False
    assert not (root/'activation.json').exists()
    assert store.inspect(root)['installed']==['v1']
    with pytest.raises(FileExistsError):store.install(source,root,'v1')


def test_two_versions_atomic_activation_rollback_and_idempotency(artifact):
    source,root=artifact
    for version in ('v1','v2'):store.install(source,root,version)
    first=store.activate(root,'v1');assert first['previous'] is None
    assert store.activate(root,'v1')==first
    second=store.activate(root,'v2');assert second['previous']=='v1'
    assert store.activate(root,'v2')==second
    assert store.activate(root,rollback=True)['active']=='v1'
    assert store.activate(root,rollback=True)['active']=='v2'
    assert store.state(root)['publication_authorized'] is False


@pytest.mark.parametrize('version',['../escape','/tmp/x','.','..','', 'x/y'])
def test_version_paths_are_bounded(artifact,version):
    source,root=artifact
    with pytest.raises(ValueError):store.install(source,root,version)
    assert not root.exists()


def test_wrong_checksum_and_missing_source_do_not_publish(artifact,tmp_path):
    source,root=artifact
    store.install(source,root,'good');store.activate(root,'good')
    previous=(root/'activation.json').read_bytes()
    broken=tmp_path/'broken.sqlite';data=bytearray(source.read_bytes());data[-1]^=1;broken.write_bytes(data)
    with pytest.raises(ValueError):store.install(broken,root,'bad')
    with pytest.raises(FileNotFoundError):store.install(tmp_path/'absent',root,'missing')
    assert store.inspect(root)['installed']==['good'] and store.inspect(root)['incomplete']==[]
    assert (root/'activation.json').read_bytes()==previous


@pytest.mark.parametrize('bad', ['schema','tables','release','contract','policy','duplicate_manifest'])
def test_incompatible_artifact_rejected_even_with_matching_test_checksum(artifact,monkeypatch,bad):
    source,root=artifact
    # Adjust only the test checksum to reach each schema contract validation branch.
    source.chmod(0o644)
    with closing(sqlite3.connect(source)) as con:
        if bad=='schema':con.execute('PRAGMA user_version=3')
        elif bad=='tables':con.execute('DROP TABLE formulations')
        elif bad=='release':con.execute("UPDATE release_manifest SET release_id='wrong'")
        elif bad=='contract':con.execute("UPDATE release_manifest SET contract_id='wrong'")
        elif bad=='policy':con.execute("UPDATE release_manifest SET policy_version='wrong'")
        else:con.execute('INSERT INTO release_manifest SELECT * FROM release_manifest')
        con.commit()
    source.chmod(0o444)
    monkeypatch.setattr(release,'EXPECTED_SHA256',hashlib.sha256(source.read_bytes()).hexdigest())
    with pytest.raises(release.PharmaceuticalReleaseUnavailable):store.install(source,root,'bad')
    assert not (root/'releases'/'bad').exists()
    assert store.inspect(root)['incomplete']==[]


def test_failed_atomic_activation_preserves_previous_selection(artifact,monkeypatch):
    source,root=artifact
    for version in ('v1','v2'):store.install(source,root,version)
    store.activate(root,'v1');before=(root/'activation.json').read_bytes()
    def failed(*_):raise OSError('simulated failure before pointer replacement')
    monkeypatch.setattr(store.os,'replace',failed)
    with pytest.raises(OSError):store.activate(root,'v2')
    assert (root/'activation.json').read_bytes()==before
    assert not list(root.glob('.pending-*'))


def test_failed_install_rename_cleans_own_incomplete_copy(artifact,monkeypatch):
    source,root=artifact
    def failed(*_):raise OSError('simulated disk/publish failure')
    monkeypatch.setattr(store.os,'rename',failed)
    with pytest.raises(OSError):store.install(source,root,'bad')
    assert store.inspect(root)['installed']==[] and store.inspect(root)['incomplete']==[]


def test_permission_failure_does_not_activate_or_allow_api_fallback(artifact,monkeypatch):
    source,root=artifact
    store.install(source,root,'v1');store.activate(root,'v1')
    before=(root/'activation.json').read_bytes()
    import builtins
    original=builtins.open
    def denied(path,*args,**kwargs):
        if str(path).endswith('pharma.sqlite'):raise PermissionError('simulated mount permissions')
        return original(path,*args,**kwargs)
    monkeypatch.setattr(builtins,'open',denied)
    with pytest.raises(PermissionError):store.activate(root,'v1')
    assert (root/'activation.json').read_bytes()==before
    monkeypatch.setenv('DAV_AI_PHARMA_ARTIFACT_ROOT',str(root))
    assert TestClient(app).get('/ready').status_code==503


def test_pinning_and_restart_switch_versions(artifact,monkeypatch):
    source,root=artifact
    for version in ('v1','v2'):store.install(source,root,version)
    store.activate(root,'v1');monkeypatch.setenv('DAV_AI_PHARMA_ARTIFACT_ROOT',str(root))
    with TestClient(app) as client:
        assert client.get('/ready').status_code==200
        path1=release.release_database_path()
        store.activate(root,'v2')
        assert release.release_database_path()==path1
        assert client.get('/ready').status_code==200
    store.pinned_path.cache_clear() # Fresh process/startup has an empty selection cache.
    with TestClient(app) as client:
        assert release.release_database_path().parent.name=='v2'
        assert client.get('/ready').status_code==200
    assert store.state(root)['previous']=='v1'


@pytest.mark.parametrize('failure',['missing','corrupt','permissions','conflicting','empty'])
def test_managed_startup_and_readiness_fail_closed(artifact,monkeypatch,failure):
    source,root=artifact
    store.install(source,root,'v1');store.activate(root,'v1')
    monkeypatch.setenv('DAV_AI_PHARMA_ARTIFACT_ROOT',str(root))
    installed=store.installed(root,'v1')
    if failure=='missing':monkeypatch.setenv('DAV_AI_PHARMA_ARTIFACT_ROOT',str(root/'absent'))
    elif failure=='corrupt':
        installed.chmod(0o644);installed.write_bytes(b'corrupt');installed.chmod(0o444)
    elif failure=='permissions':
        installed.chmod(0o644) # Managed mutable mounts are refused even if bytes still match.
    elif failure=='conflicting':monkeypatch.setenv('DAV_AI_PHARMA_RELEASE_DB',str(source))
    else:monkeypatch.setenv('DAV_AI_PHARMA_ARTIFACT_ROOT','')
    client=TestClient(app)
    assert client.get('/health').status_code==200
    assert client.get('/ready').status_code==503
    with pytest.raises(RuntimeError,match='startup refused'):
        with TestClient(app):pass


@pytest.mark.parametrize('environment',['production','staging','preview'])
def test_managed_selection_cannot_authorize_any_pharmaceutical_surface(artifact,monkeypatch,environment):
    source,root=artifact
    store.install(source,root,'v1');store.activate(root,'v1')
    monkeypatch.setenv('DAV_AI_PHARMA_ARTIFACT_ROOT',str(root));monkeypatch.setenv('DAVAI_ENV',environment)
    client=TestClient(app)
    for path in ('/ready','/api/coverage','/api/drugs/search?q=Example','/api/drugs/x',
                 '/api/drugs/x/evidence','/api/drugs/x/safety','/api/drugs/x/safety/recalls',
                 '/api/drugs/x/safety/adverse_events','/api/drugs/x/safety/labels',
                 '/api/drugs/x/safety/communications','/api/drugs/x/timeline'):
        assert client.get(path).status_code==503
    from app.routes import reports
    reports._attempts.clear()
    assert client.post('/api/v1/reports/pharmaceutical',json={'product_id':'x','name':'Synthetic Reader'}).status_code==503
    with pytest.raises(RuntimeError):
        with TestClient(app):pass
    assert store.state(root)['publication_authorized'] is False


def test_symlinks_and_unknown_receipts_fail_closed(artifact,tmp_path):
    source,root=artifact
    store.install(source,root,'v1');store.activate(root,'v1')
    alias=tmp_path/'alias';alias.symlink_to(root,target_is_directory=True)
    with pytest.raises(ValueError):store.activate(alias,'v1')
    receipt=root/'releases'/'v1'/'receipt.json';receipt.chmod(0o644)
    value=json.loads(receipt.read_text());value['verification']['publication_validated']=True
    receipt.write_text(json.dumps(value));receipt.chmod(0o444)
    with pytest.raises(ValueError):store.installed(root,'v1')


def test_crash_recovery_is_explicit_and_never_removes_installed_versions(artifact):
    source,root=artifact
    store.install(source,root,'v1')
    incomplete=root/'releases'/'.install-abcdefgh';incomplete.mkdir();(incomplete/'pharma.sqlite').write_bytes(b'incomplete')
    assert store.inspect(root)['incomplete']==[incomplete.name]
    with pytest.raises(ValueError):store.discard_incomplete(root,'v1')
    store.discard_incomplete(root,incomplete.name)
    assert store.inspect(root)['incomplete']==[] and store.installed(root,'v1').is_file()


def test_corrupt_selection_requires_explicit_verified_recovery(artifact,monkeypatch):
    source,root=artifact
    store.install(source,root,'v1');store.activate(root,'v1')
    pointer=root/'activation.json';pointer.write_text('{broken')
    assert store.inspect(root)['activation_error']=='JSONDecodeError'
    with pytest.raises(ValueError):store.activate(root,'v1')
    monkeypatch.setenv('DAV_AI_PHARMA_ARTIFACT_ROOT',str(root))
    assert TestClient(app).get('/ready').status_code==503
    recovered=store.activate(root,'v1',recover=True)
    assert recovered['active']=='v1' and recovered['previous'] is None
    assert recovered['publication_authorized'] is False
    with pytest.raises(ValueError):store.activate(root,'v1',recover=True)
    with TestClient(app) as client:assert client.get('/ready').status_code==200


def test_missing_selection_does_not_fall_back_and_can_be_restored(artifact,monkeypatch):
    source,root=artifact
    store.install(source,root,'v1')
    monkeypatch.setenv('DAV_AI_PHARMA_ARTIFACT_ROOT',str(root))
    assert TestClient(app).get('/ready').status_code==503
    store.activate(root,'v1',recover=True)
    with TestClient(app) as client:assert client.get('/ready').status_code==200


def test_world_writable_root_is_refused(artifact):
    source,root=artifact
    root.mkdir(mode=0o777);root.chmod(0o777)
    try:
        with pytest.raises(ValueError):store.install(source,root,'v1')
    finally:root.chmod(0o755)


@pytest.mark.parametrize('suffix',['-wal','-shm','-journal'])
def test_sqlite_sidecars_cannot_change_verified_logical_contents(artifact,suffix):
    source,root=artifact
    Path(str(source)+suffix).write_bytes(b'not an immutable standalone release')
    with pytest.raises(release.PharmaceuticalReleaseUnavailable):store.install(source,root,'bad')
    assert not root.exists()


def test_post_replace_sync_error_leaves_valid_state_for_explicit_inspection(artifact,monkeypatch):
    source,root=artifact
    for version in ('v1','v2'):store.install(source,root,version)
    store.activate(root,'v1')
    def failed(_):raise OSError('simulated directory sync failure after atomic replace')
    monkeypatch.setattr(store,'sync_directory',failed)
    with pytest.raises(OSError):store.activate(root,'v2')
    # Operator must inspect after an ambiguous I/O error; no partial JSON or unverified data.
    assert store.state(root)['active']=='v2' and store.state(root)['previous']=='v1'
    assert store.installed(root,'v1').is_file() and store.installed(root,'v2').is_file()


@pytest.mark.parametrize('key,value', [
    ('DAVAI_ENV','stagin'), ('DAVAI_ENV',''), ('APP_ENV','public'),
    ('ENVIRONMENT','Production '), ('PYTHON_ENV','unknown'), ('RENDER','1'),
])
def test_unknown_or_hosted_environment_never_selects_local(artifact,monkeypatch,key,value):
    source,root=artifact
    monkeypatch.setenv('DAV_AI_PHARMA_RELEASE_DB',str(source))
    monkeypatch.setenv('DAVAI_ENV','local')
    monkeypatch.setenv(key,value)
    with pytest.raises(release.PharmaceuticalReleaseUnavailable):release.connect_release()
    assert TestClient(app).get('/ready').status_code==503
    with pytest.raises(RuntimeError):
        with TestClient(app):pass


def test_record_permission_race_is_rejected(tmp_path,monkeypatch):
    path=tmp_path/'record.json';path.write_text('{}')
    original=store.os.open
    def race(target,*args,**kwargs):
        if Path(target)==path:path.chmod(0o666)
        return original(target,*args,**kwargs)
    monkeypatch.setattr(store.os,'open',race)
    with pytest.raises(ValueError,match='changed'):store.read_json(path)


def test_record_replacement_race_is_rejected(tmp_path,monkeypatch):
    path=tmp_path/'record.json';path.write_text('{}')
    replacement=tmp_path/'replacement';replacement.write_text('{}')
    original=store.os.open
    def race(target,*args,**kwargs):
        if Path(target)==path:replacement.replace(path)
        return original(target,*args,**kwargs)
    monkeypatch.setattr(store.os,'open',race)
    with pytest.raises(ValueError,match='changed'):store.read_json(path)


@pytest.mark.parametrize('kind',['symlink','fifo','hardlink','writable'])
def test_unsafe_writer_locks_refused(artifact,tmp_path,kind):
    import os
    source,root=artifact;root.mkdir()
    lock=root/'.lock'
    if kind=='symlink':lock.symlink_to(source)
    elif kind=='fifo':os.mkfifo(lock,0o600)
    elif kind=='hardlink':os.link(source,lock)
    else:lock.write_text('');lock.chmod(0o666)
    before=source.read_bytes()
    with pytest.raises((OSError,ValueError)):store.install(source,root,'v1')
    assert source.read_bytes()==before and not (root/'releases').exists()


def test_concurrent_activation_serializes_and_failed_target_never_promoted(artifact):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    source,root=artifact
    for version in ('v1','v2'):store.install(source,root,version)
    barrier=Barrier(3)
    def activate(version):
        barrier.wait()
        try:return store.activate(root,version)
        except FileNotFoundError:return None
    with ThreadPoolExecutor(max_workers=3) as pool:
        results=list(pool.map(activate,('v1','v2','absent')))
    current=store.state(root)
    assert set((current['active'],current['previous']))=={'v1','v2'}
    assert results[2] is None
    assert store.activate(root,rollback=True)['active']==current['previous']


def test_cached_integrity_does_not_accept_changed_bytes_with_restored_mtime(artifact,monkeypatch):
    import os
    source,root=artifact
    store.install(source,root,'v1');store.activate(root,'v1')
    monkeypatch.setenv('DAV_AI_PHARMA_ARTIFACT_ROOT',str(root))
    with closing(release.connect_release()):pass
    path=store.installed(root,'v1');before=path.stat()
    content=bytearray(path.read_bytes());content[-1]^=1
    path.chmod(0o644);path.write_bytes(content);path.chmod(0o444)
    os.utime(path,ns=(before.st_atime_ns,before.st_mtime_ns))
    with pytest.raises(release.PharmaceuticalReleaseUnavailable):release.connect_release()
    assert TestClient(app).get('/ready').status_code==503
    pointer=(root/'activation.json').read_bytes()
    with pytest.raises(release.PharmaceuticalReleaseUnavailable):store.activate(root,'v1')
    assert (root/'activation.json').read_bytes()==pointer


@pytest.mark.parametrize('component',['releases','version','database','receipt','selection'])
def test_managed_symlinks_are_refused(artifact,tmp_path,component):
    source,root=artifact
    store.install(source,root,'v1');store.activate(root,'v1')
    paths={'releases':root/'releases','version':root/'releases'/'v1',
           'database':root/'releases'/'v1'/'pharma.sqlite',
           'receipt':root/'releases'/'v1'/'receipt.json','selection':root/'activation.json'}
    path=paths[component];target=tmp_path/'moved'
    if component in ('database','receipt'):path.parent.chmod(0o755)
    if component=='version':path.chmod(0o755) # macOS requires writable directory for this move.
    path.rename(target);path.symlink_to(target,target_is_directory=target.is_dir())
    with pytest.raises((ValueError,OSError)):store.activate(root,'v1')


def test_corrupt_rollback_and_recovery_targets_never_promoted(artifact):
    source,root=artifact
    for version in ('v1','v2'):store.install(source,root,version)
    store.activate(root,'v1');store.activate(root,'v2')
    path=store.installed(root,'v1');path.chmod(0o644)
    data=bytearray(path.read_bytes());data[-1]^=1;path.write_bytes(data);path.chmod(0o444)
    before=(root/'activation.json').read_bytes()
    with pytest.raises(release.PharmaceuticalReleaseUnavailable):store.activate(root,rollback=True)
    assert (root/'activation.json').read_bytes()==before
    (root/'activation.json').write_text('{broken')
    with pytest.raises(release.PharmaceuticalReleaseUnavailable):store.activate(root,'v1',recover=True)
    assert (root/'activation.json').read_text()=='{broken'
    assert store.activate(root,'v2',recover=True)['active']=='v2'


@pytest.mark.parametrize('value',[True,0,'false'])
def test_forged_selection_authorization_refused(artifact,value):
    source,root=artifact
    store.install(source,root,'v1');store.activate(root,'v1')
    pointer=root/'activation.json';data=json.loads(pointer.read_text())
    data['publication_authorized']=value;pointer.write_text(json.dumps(data))
    with pytest.raises(ValueError):store.activate(root,'v1')


def test_read_permissions_fail_closed_without_changing_source(artifact,monkeypatch):
    source,root=artifact
    before=release.artifact_signature(source)
    store.install(source,root,'v1');store.activate(root,'v1')
    path=store.installed(root,'v1');path.chmod(0o000)
    monkeypatch.setenv('DAV_AI_PHARMA_ARTIFACT_ROOT',str(root))
    try:
        assert TestClient(app).get('/ready').status_code==503
        with pytest.raises(RuntimeError):
            with TestClient(app):pass
    finally:path.chmod(0o444)
    assert release.artifact_signature(source)==before
