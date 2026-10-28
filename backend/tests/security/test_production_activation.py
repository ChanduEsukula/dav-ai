"""Focused Render demonstration activation tests; all signing keys are ephemeral test fixtures."""
import asyncio
import base64
from contextlib import closing
from datetime import datetime, timedelta, timezone
import hashlib
import json
import sqlite3

import httpx
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient

from app.security import production_authorization as auth
from app.security.validation import AuthorizationRejected
from app.services import public_evidence as boundary
from app.db.pharma import release_connection as release
from scripts import sign_public_evidence_approval as signer

@pytest.fixture
def grant(tmp_path, monkeypatch):
    for key in ('DAVAI_ENV','APP_ENV','ENVIRONMENT','PYTHON_ENV','RENDER','DAV_AI_PHARMA_RELEASE_DB','DAV_AI_PHARMA_ARTIFACT_ROOT'):
        monkeypatch.delenv(key,raising=False)
    key=Ed25519PrivateKey.generate()
    keypath=tmp_path/'synthetic.pem'
    keypath.write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
    keypath.chmod(0o600)
    review=tmp_path/'review.txt';review.write_text('Synthetic test-only operator decision')
    auth.application_digest.cache_clear()
    result=signer.issue(keypath,review,auth.application_digest(),'srv-test','test-approval',tmp_path/'files',1)
    monkeypatch.setattr(auth,'POLICY_FILE',tmp_path/'files/dav-ai-public-policy.json')
    monkeypatch.setattr(auth,'GRANT_FILE',tmp_path/'files/dav-ai-public-approval.json')
    monkeypatch.setenv('DAVAI_ENV','production');monkeypatch.setenv('RENDER','true')
    monkeypatch.setenv('RENDER_SERVICE_ID','srv-test');monkeypatch.setenv('DAV_AI_PUBLIC_KEY_SHA256',result['signing_key_sha256'])
    return key


def rewrite(grant, **changes):
    envelope=json.loads(auth.GRANT_FILE.read_bytes())
    claims=json.loads(base64.b64decode(envelope['payload_base64']))
    claims.update(changes)
    raw=json.dumps(claims).encode()
    auth.GRANT_FILE.write_text(json.dumps({'payload_base64':base64.b64encode(raw).decode(),
                                          'signature_base64':base64.b64encode(grant.sign(raw)).decode()}))


def test_signed_operator_grant_accepts_only_current_scope(grant):
    assert auth.require_production_authorization().approval_id=='test-approval'
    assert all(operation.startswith('GET ') for operation in auth.READ_OPERATIONS)
    assert 'POST /api/v1/reports/pharmaceutical' not in auth.READ_OPERATIONS

@pytest.mark.parametrize('change',[
 {'database_sha256':'f'*64},{'application_sha256':'0'*64},{'review_bundle_sha256':'1'*64},
 {'deployment_id':'srv-other'},{'audience':'private'},{'purpose':'private-staging'},
 {'operations':list(auth.READ_OPERATIONS)+['POST /api/local/research/sessions']},
 {'operations':list(auth.READ_OPERATIONS)+['POST /api/v1/reports/pharmaceutical']},
 {'expires_at':'2020-01-01T00:00:00Z'},
 {'expires_at':(datetime.now(timezone.utc)+timedelta(days=2)).isoformat()},
])
def test_even_authentically_signed_wrong_grant_denies(grant,change):
    rewrite(grant,**change)
    with pytest.raises(AuthorizationRejected): auth.require_production_authorization()

@pytest.mark.parametrize('name,value', [('DAV_AI_PUBLIC_KEY_SHA256','0'*64),('RENDER_SERVICE_ID','srv-other'),
 ('DAVAI_ENV','staging'),('RENDER','false'),('APP_ENV','preview'),('PYTHON_ENV','local')])
def test_wrong_operator_pin_or_environment_denies(grant,monkeypatch,name,value):
    monkeypatch.setenv(name,value)
    with pytest.raises(AuthorizationRejected): auth.require_production_authorization()


def test_missing_tampered_unsafe_and_symlink_documents_deny(grant,tmp_path):
    original=auth.GRANT_FILE.read_bytes()
    auth.GRANT_FILE.unlink()
    with pytest.raises(AuthorizationRejected): auth.require_production_authorization()
    auth.GRANT_FILE.write_bytes(original.replace(b'payload_base64',b'changed_base64'))
    with pytest.raises(AuthorizationRejected): auth.require_production_authorization()
    auth.GRANT_FILE.write_bytes(original)
    auth.GRANT_FILE.chmod(0o666)
    with pytest.raises(AuthorizationRejected): auth.require_production_authorization()
    auth.GRANT_FILE.chmod(0o600)
    target=tmp_path/'saved';target.write_bytes(original)
    auth.GRANT_FILE.unlink();auth.GRANT_FILE.symlink_to(target)
    with pytest.raises(AuthorizationRejected): auth.require_production_authorization()


def test_forged_signature_denies(grant):
    envelope=json.loads(auth.GRANT_FILE.read_bytes())
    envelope['signature_base64']=base64.b64encode(b'x'*64).decode()
    auth.GRANT_FILE.write_text(json.dumps(envelope))
    with pytest.raises(AuthorizationRejected): auth.require_production_authorization()


def test_real_readonly_connection_uses_gate_and_interrupts_expired_queries(grant,tmp_path,monkeypatch):
    path=tmp_path/'synthetic.sqlite'
    with closing(sqlite3.connect(path)) as con:
        for table in release.REQUIRED_TABLES-{'release_manifest'}: con.execute(f'CREATE TABLE {table}(fixture TEXT)')
        con.execute('CREATE TABLE release_manifest(release_id,contract_id,policy_version,build_version)')
        con.execute('INSERT INTO release_manifest VALUES(?,?,?,?)',(auth.RELEASE_ID,'dav-ai-pharma-release-v1','1.0.0','test'))
        con.execute('PRAGMA user_version=4');con.commit()
    path.chmod(0o444)
    sha=hashlib.sha256(path.read_bytes()).hexdigest()
    monkeypatch.setattr(release,'EXPECTED_SHA256',sha);monkeypatch.setattr(release,'EXPECTED_BYTES',path.stat().st_size)
    monkeypatch.setenv('DAV_AI_PHARMA_RELEASE_DB',str(path))
    rewrite(grant,database_sha256=sha)
    with closing(release.connect_release()) as con:
        assert con.execute('PRAGMA query_only').fetchone()[0]==1
        with pytest.raises(sqlite3.OperationalError): con.execute('CREATE TABLE forbidden(x)')
    token=boundary.QUERY_DEADLINE.set(0)
    try:
        # Use a nonzero expired monotonic deadline (0 is the no-request fallback).
        boundary.QUERY_DEADLINE.set(0.001)
        with closing(release.connect_release()) as con:
            with pytest.raises(sqlite3.OperationalError,match='interrupted'):
                con.execute('WITH RECURSIVE t(n) AS (SELECT 1 UNION ALL SELECT n+1 FROM t WHERE n<1000000) SELECT sum(n) FROM t').fetchone()
    finally: boundary.QUERY_DEADLINE.reset(token)
    path.chmod(0o644)
    with pytest.raises(release.PharmaceuticalReleaseUnavailable): release.connect_release()


def run_requests(inner, paths, monkeypatch=None):
    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=boundary.PublicEvidenceMiddleware(inner)),base_url='https://demo.test') as client:
            return [await client.request(method,path) for method,path in paths]
    return asyncio.run(scenario())

async def data(scope,receive,send):
    from starlette.responses import JSONResponse
    await JSONResponse({'source_id':'source:data/pharma_recovery/private.dump','source_url':'https://api.fda.gov/drug/event.json','data':'valid'})(scope,receive,send)


def test_public_read_succeeds_and_internal_acquisition_id_is_opaque(grant):
    response=run_requests(data,[('GET','/api/drugs/search?q=Xanax')])[0]
    assert response.status_code==200 and response.json()['data']=='valid'
    assert response.json()['source_id'].startswith('source:') and 'pharma_recovery' not in response.text
    assert response.headers['cache-control']=='no-store'
    assert response.json()['source_url']=='https://api.fda.gov/drug/event.json'

@pytest.mark.parametrize('method,path', [('POST','/api/local/research/sessions'),('POST','/api/v1/reports/pharmaceutical'),
 ('GET','/api/drugs/id/safety/communications'),('GET','/api/drugs/id/safety'),('GET','/api/drugs/id/timeline'),('GET','/docs')])
def test_unapproved_routes_stay_denied_with_valid_grant(grant,method,path):
    assert run_requests(data,[(method,path)])[0].status_code==403

@pytest.mark.parametrize('path',['/api/drugs/search?q=x','/api/drugs/search?q=xx&limit=21',
 '/api/drugs/search?q=xx&offset=1001','/api/drugs/search?q=xx&q=yy'])
def test_queries_are_bounded(grant,path):
    assert run_requests(data,[('GET',path)])[0].status_code in {400,422}


def test_global_burst_limit_and_live_removal(grant):
    responses=run_requests(data,[('GET','/api/drugs/search?q=Xanax')]*11)
    assert [r.status_code for r in responses[:10]]==[200]*10
    assert responses[10].status_code==429 and responses[10].headers['retry-after']=='5'
    async def remove(scope,receive,send):
        auth.GRANT_FILE.unlink()
        await data(scope,receive,send)
    response=run_requests(remove,[('GET','/api/drugs/search?q=Xanax')])[0]
    assert response.status_code==503 and 'valid' not in response.text


def test_errors_response_size_and_deadline_are_safe(grant,monkeypatch):
    async def broken(scope,receive,send): raise RuntimeError('private exception content')
    response=run_requests(broken,[('GET','/api/drugs/search?q=Xanax')])[0]
    assert response.status_code==503 and 'private' not in response.text
    monkeypatch.setattr(boundary,'MAX_RESPONSE_BYTES',10)
    assert run_requests(data,[('GET','/api/drugs/search?q=Xanax')])[0].status_code==503
    monkeypatch.setattr(boundary,'MAX_RESPONSE_BYTES',2048)
    async def late(scope,receive,send):
        boundary.QUERY_DEADLINE.set(0.001)
        await data(scope,receive,send)
    assert run_requests(late,[('GET','/api/drugs/search?q=Xanax')])[0].status_code==503


def test_two_reads_and_one_overview_admission_are_nonblocking(grant):
    async def slow(scope,receive,send):
        await asyncio.sleep(.03)
        await data(scope,receive,send)
    async def scenario(path,count):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=boundary.PublicEvidenceMiddleware(slow)),base_url='https://demo.test') as client:
            return [r.status_code for r in await asyncio.gather(*[client.get(path) for _ in range(count)])]
    assert sorted(asyncio.run(scenario('/api/drugs/search?q=Xanax',3)))==[200,200,429]
    assert sorted(asyncio.run(scenario('/api/medications/overview?q=Xanax',2)))==[200,429]


@pytest.mark.release_artifact
def test_signed_render_scope_serves_the_pinned_artifact_without_research_or_pdf(grant):
    from app.main import app
    app.middleware_stack=None
    try:
        with TestClient(app) as client:
            assert client.get('/ready').status_code==200
            result=client.get('/api/medications/overview?q=Xanax')
            assert result.status_code==200
            value=result.json()
            assert value['matched_product_count']==9 and value['recalls']['distinct_linked_records']==2
            assert value['release']['publication_authorized'] is False
            assert 'pharma_recovery' not in result.text
            product=value['products'][0]['id']
            assert client.get(f'/api/drugs/{product}/evidence').status_code==200
            assert client.get(f'/api/drugs/{product}/safety/labels').status_code==200
            assert client.post('/api/v1/reports/pharmaceutical',json={}).status_code==403
            assert client.post('/api/local/research/sessions',json={}).status_code==403
    finally: app.middleware_stack=None


def test_denial_is_private_cors_safe_and_liveness_is_not_permission(grant,monkeypatch):
    monkeypatch.setenv('ALLOWED_ORIGINS','https://approved.example')
    auth.GRANT_FILE.unlink()
    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=boundary.PublicEvidenceMiddleware(data)),base_url='https://demo.test') as client:
            response=await client.get('/api/drugs/search?q=Xanax',headers={'Origin':'https://approved.example'})
            assert response.status_code==503
            assert response.headers['access-control-allow-origin']=='https://approved.example'
            assert response.headers['cache-control']=='no-store'
            assert (await client.get('/health')).status_code==200
    asyncio.run(scenario())


def render_secret_layout(root, *, generation_link=True):
    """Render/Kubernetes projected-volume layout; no real secret files are used."""
    directory=root/'..2026_10_28_01_02_03.123456789' if generation_link else root/'..data'
    directory.mkdir(mode=0o755)
    for filename in ('dav-ai-public-policy.json','dav-ai-public-approval.json'):
        (root/filename).rename(directory/filename)
        (root/filename).symlink_to('..data/'+filename)
    if generation_link: (root/'..data').symlink_to(directory.name)
    return directory


@pytest.mark.parametrize('generation_link',[False,True])
def test_render_projected_secret_layout_preserves_signed_authorization(grant,generation_link):
    render_secret_layout(auth.POLICY_FILE.parent,generation_link=generation_link)
    assert auth.require_production_authorization().approval_id=='test-approval'


@pytest.mark.parametrize('target',[
    '/etc/passwd','../outside.json','..data/../dav-ai-public-policy.json',
    './..data/dav-ai-public-policy.json','..data/dav-ai-public-approval.json',
    '..other/dav-ai-public-policy.json',
])
def test_unexpected_leaf_symlink_targets_fail_closed(grant,target):
    render_secret_layout(auth.POLICY_FILE.parent)
    auth.POLICY_FILE.unlink();auth.POLICY_FILE.symlink_to(target)
    with pytest.raises(AuthorizationRejected): auth.require_production_authorization()


@pytest.mark.parametrize('target',['/tmp','../outside','./..generation','..','..data','..generation/nested'])
def test_unexpected_data_symlink_targets_fail_closed(grant,target):
    root=auth.POLICY_FILE.parent
    render_secret_layout(root)
    (root/'..data').unlink();(root/'..data').symlink_to(target)
    with pytest.raises(AuthorizationRejected): auth.require_production_authorization()


@pytest.mark.parametrize('unsafe',['root','generation','file','generation_symlink','file_symlink','directory','fifo','missing'])
def test_render_targets_require_safe_regular_files_and_real_directories(grant,tmp_path,unsafe):
    root=auth.POLICY_FILE.parent
    generation=render_secret_layout(root)
    target=generation/auth.POLICY_FILE.name
    if unsafe=='root': root.chmod(0o777)
    elif unsafe=='generation': generation.chmod(0o777)
    elif unsafe=='file': target.chmod(0o666)
    elif unsafe=='generation_symlink':
        saved=root/'..saved';generation.rename(saved);generation.symlink_to(saved.name)
    elif unsafe=='file_symlink':
        saved=generation/'saved.json';target.rename(saved);target.symlink_to(saved.name)
    elif unsafe=='directory': target.unlink();target.mkdir()
    elif unsafe=='fifo':
        import os
        target.unlink();os.mkfifo(target)
    elif unsafe=='missing': target.unlink()
    with pytest.raises(AuthorizationRejected): auth.require_production_authorization()


def test_root_symlink_and_explicit_path_traversal_are_rejected(grant,tmp_path):
    render_secret_layout(auth.POLICY_FILE.parent)
    alias=tmp_path/'alias';alias.symlink_to(auth.POLICY_FILE.parent,target_is_directory=True)
    with pytest.raises(AuthorizationRejected): auth.operator_document(alias/auth.POLICY_FILE.name)
    with pytest.raises(AuthorizationRejected):
        auth.operator_document(auth.POLICY_FILE.parent/'..'/'files'/auth.POLICY_FILE.name)


@pytest.mark.parametrize('change',['data_link','leaf_link','generation_directory','final_file_before_open'])
def test_render_target_changes_during_open_are_rejected(grant,monkeypatch,change):
    import os
    root=auth.POLICY_FILE.parent
    generation=render_secret_layout(root)
    replacement=root/'..replacement'
    replacement.mkdir()
    for filename in ('dav-ai-public-policy.json','dav-ai-public-approval.json'):
        (replacement/filename).write_bytes((generation/filename).read_bytes())
    actual_open=os.open
    mutated=[]
    def racing_open(path,flags,*args,**kwargs):
        if path==auth.POLICY_FILE.name and kwargs.get('dir_fd') is not None and not mutated:
            mutated.append(True)
            if change=='data_link':
                pending=root/'..pending';pending.symlink_to(replacement.name);os.replace(pending,root/'..data')
            elif change=='leaf_link':
                auth.POLICY_FILE.unlink();auth.POLICY_FILE.symlink_to('..data/'+auth.GRANT_FILE.name)
            elif change=='generation_directory':
                generation.rename(root/'..old');replacement.rename(generation)
            else:
                pending=generation/'replacement.json';pending.write_bytes((generation/path).read_bytes())
                os.replace(pending,generation/path)
        return actual_open(path,flags,*args,**kwargs)
    monkeypatch.setattr(os,'open',racing_open)
    with pytest.raises(AuthorizationRejected): auth.operator_document(auth.POLICY_FILE)
    assert mutated


@pytest.mark.parametrize('change',['contents','permissions','replace_file','data_link'])
def test_render_target_changes_during_read_are_rejected(grant,monkeypatch,change):
    import os
    from contextlib import contextmanager
    root=auth.POLICY_FILE.parent
    generation=render_secret_layout(root)
    target=generation/auth.POLICY_FILE.name
    replacement=root/'..replacement';replacement.mkdir()
    for filename in ('dav-ai-public-policy.json','dav-ai-public-approval.json'):
        (replacement/filename).write_bytes((generation/filename).read_bytes())
    actual_fdopen=os.fdopen
    @contextmanager
    def racing_fdopen(fd,*args,**kwargs):
        with actual_fdopen(fd,*args,**kwargs) as stream:
            class Reader:
                def fileno(self): return stream.fileno()
                def read(self,*args):
                    value=stream.read(*args)
                    if change=='contents': target.write_bytes(target.read_bytes()+b' ')
                    elif change=='permissions': target.chmod(0o666)
                    elif change=='replace_file':
                        pending=generation/'new.json';pending.write_bytes(target.read_bytes());os.replace(pending,target)
                    else:
                        pending=root/'..pending';pending.symlink_to(replacement.name);os.replace(pending,root/'..data')
                    return value
            yield Reader()
    monkeypatch.setattr(os,'fdopen',racing_fdopen)
    with pytest.raises(AuthorizationRejected): auth.operator_document(auth.POLICY_FILE)


def test_render_secret_bytes_retain_parser_bounds(grant):
    generation=render_secret_layout(auth.POLICY_FILE.parent)
    target=generation/auth.POLICY_FILE.name
    for raw in (b'{"duplicate":1,"duplicate":2}', b' '*16385):
        target.write_bytes(raw)
        with pytest.raises(AuthorizationRejected): auth.operator_document(auth.POLICY_FILE)


@pytest.mark.parametrize('failure',['signature','code_digest','service_id','expiration','key_pin','production_mode'])
def test_render_layout_does_not_weaken_existing_authorization(grant,monkeypatch,failure):
    render_secret_layout(auth.POLICY_FILE.parent)
    if failure=='signature':
        envelope=json.loads(auth.GRANT_FILE.read_bytes())
        envelope['signature_base64']=base64.b64encode(b'x'*64).decode()
        auth.GRANT_FILE.write_text(json.dumps(envelope))
    elif failure=='code_digest': rewrite(grant,application_sha256='0'*64)
    elif failure=='service_id': monkeypatch.setenv('RENDER_SERVICE_ID','srv-other')
    elif failure=='expiration': rewrite(grant,expires_at='2020-01-01T00:00:00Z')
    elif failure=='key_pin': monkeypatch.setenv('DAV_AI_PUBLIC_KEY_SHA256','0'*64)
    else: monkeypatch.setenv('DAVAI_ENV','staging')
    with pytest.raises(AuthorizationRejected): auth.require_production_authorization()


@pytest.fixture
def annual_grant(grant,tmp_path,monkeypatch):
    """Use only the existing synthetic fixture key; never an operator approval."""
    output=tmp_path/'annual-files'
    receipt=signer.issue(tmp_path/'synthetic.pem',tmp_path/'review.txt',auth.application_digest(),
                         'srv-test','test-annual-approval',output,8760)
    monkeypatch.setattr(auth,'POLICY_FILE',output/'dav-ai-public-policy.json')
    monkeypatch.setattr(auth,'GRANT_FILE',output/'dav-ai-public-approval.json')
    return grant,receipt


def annual_window():
    envelope=json.loads(auth.GRANT_FILE.read_bytes())
    claims=json.loads(base64.b64decode(envelope['payload_base64']))
    return datetime.fromisoformat(claims['issued_at']),datetime.fromisoformat(claims['expires_at'])


def test_365_day_grant_and_policy_cover_the_entire_year(annual_grant):
    issued,expires=annual_window()
    policy=json.loads(auth.POLICY_FILE.read_bytes())
    assert expires-issued==timedelta(days=365)
    assert datetime.fromisoformat(policy['not_before'])==issued
    assert datetime.fromisoformat(policy['not_after'])==expires
    assert annual_grant[1]['expires_at']==policy['not_after']
    for now in (issued,issued+timedelta(days=180),expires-timedelta(microseconds=1)):
        assert auth.require_production_authorization(now=now).approval_id=='test-annual-approval'


@pytest.mark.parametrize('hours',[0,8761])
def test_signer_rejects_out_of_range_lifetime_before_reading_key(tmp_path,hours):
    with pytest.raises(ValueError,match='1–8760'):
        signer.issue(tmp_path/'no-key',tmp_path/'no-review','a'*64,'srv-test','test',tmp_path/'unused',hours)
    assert not (tmp_path/'unused').exists()


def test_authentically_signed_over_year_grant_denies_even_with_longer_key_window(annual_grant):
    key,_=annual_grant
    issued,_=annual_window()
    policy=json.loads(auth.POLICY_FILE.read_bytes())
    policy['not_after']=(issued+timedelta(days=366)).isoformat()
    auth.POLICY_FILE.write_text(json.dumps(policy))
    rewrite(key,expires_at=(issued+timedelta(days=365,seconds=1)).isoformat())
    with pytest.raises(AuthorizationRejected) as error:
        auth.require_production_authorization(now=issued)
    assert 'validity window' in str(error.value.__cause__)


@pytest.mark.parametrize('offset',[timedelta(0),timedelta(seconds=1)])
def test_annual_approval_denies_at_and_after_expiry(annual_grant,offset):
    _,expires=annual_window()
    with pytest.raises(AuthorizationRejected):auth.require_production_authorization(now=expires+offset)


@pytest.mark.parametrize('field',['not_before','not_after'])
def test_annual_approval_must_fit_inside_signing_key_window(annual_grant,field):
    issued,expires=annual_window()
    policy=json.loads(auth.POLICY_FILE.read_bytes())
    policy[field]=(issued+timedelta(seconds=1) if field=='not_before' else expires-timedelta(seconds=1)).isoformat()
    auth.POLICY_FILE.write_text(json.dumps(policy))
    with pytest.raises(AuthorizationRejected) as error:
        auth.require_production_authorization(now=issued+timedelta(days=180))
    assert 'signing key validity interval' in str(error.value.__cause__)


@pytest.mark.parametrize('failure',['signature','service'])
def test_annual_grant_preserves_signature_and_deployment_binding(annual_grant,monkeypatch,failure):
    if failure=='signature':
        envelope=json.loads(auth.GRANT_FILE.read_bytes())
        envelope['signature_base64']=base64.b64encode(b'x'*64).decode()
        auth.GRANT_FILE.write_text(json.dumps(envelope))
    else:monkeypatch.setenv('RENDER_SERVICE_ID','srv-other')
    issued,_=annual_window()
    with pytest.raises(AuthorizationRejected):auth.require_production_authorization(now=issued)


@pytest.mark.parametrize('generation_link',[False,True])
def test_annual_grant_preserves_render_projected_files(annual_grant,generation_link):
    issued,expires=annual_window()
    render_secret_layout(auth.POLICY_FILE.parent,generation_link=generation_link)
    assert auth.require_production_authorization(now=expires-timedelta(seconds=1)).approval_id=='test-annual-approval'
