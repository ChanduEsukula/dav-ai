"""Sticky parent checks; root ownership is simulated in unit metadata only.

Real root:1000 ownership and sticky-bit enforcement are also checked in the
network-isolated diagnostic container as UID/GID 1000:1000. No signing keys here.
"""
import json
import os
from pathlib import Path
import stat

import pytest
from app.security import production_authorization as auth
from app.security.validation import AuthorizationRejected


@pytest.fixture
def projected(tmp_path,monkeypatch):
    root=tmp_path/'secrets';root.mkdir();root.chmod(0o3777)
    generation=root/'..2026_10_28_01_58_47.2003122367';generation.mkdir();generation.chmod(0o2755)
    leaf=root/'dav-ai-public-policy.json'
    target=generation/leaf.name;target.write_text(json.dumps({'test':'public metadata only'}));target.chmod(0o640)
    leaf.symlink_to('..data/'+leaf.name);(root/'..data').symlink_to(generation.name)
    monkeypatch.setattr(auth,'RENDER_SECRET_ROOT',root)
    owners={}
    for path in (root,generation,leaf,root/'..data',target):
        info=path.lstat();owners[(info.st_dev,info.st_ino)]=0
    actual_stat,actual_lstat,actual_fstat=os.stat,os.lstat,os.fstat
    def metadata(info):
        values=list(info);values[stat.ST_UID]=owners.get((info.st_dev,info.st_ino),info.st_uid)
        return os.stat_result(values,{'st_atime_ns':info.st_atime_ns,'st_mtime_ns':info.st_mtime_ns,'st_ctime_ns':info.st_ctime_ns})
    monkeypatch.setattr(os,'stat',lambda *args,**kwargs:metadata(actual_stat(*args,**kwargs)))
    monkeypatch.setattr(os,'lstat',lambda *args,**kwargs:metadata(actual_lstat(*args,**kwargs)))
    monkeypatch.setattr(os,'fstat',lambda *args,**kwargs:metadata(actual_fstat(*args,**kwargs)))
    return root,generation,leaf,target,owners


def test_root_owned_render_sticky_parent_accepts_640_projected_file(projected):
    assert auth.operator_document(projected[2])=={'test':'public metadata only'}

@pytest.mark.parametrize('entry',['root','generation','leaf','data_link','target'])
def test_every_protected_entry_must_be_root_owned(projected,entry):
    root,generation,leaf,target,owners=projected
    path={'root':root,'generation':generation,'leaf':leaf,'data_link':root/'..data','target':target}[entry]
    info=path.lstat();owners[(info.st_dev,info.st_ino)]=1000
    with pytest.raises(AuthorizationRejected): auth.operator_document(leaf)

@pytest.mark.parametrize('entry',['root','generation','target'])
def test_writable_nonsticky_parent_or_writable_payload_remains_rejected(projected,entry):
    root,generation,leaf,target,_=projected
    if entry=='root':root.chmod(0o2777)
    elif entry=='generation':generation.chmod(0o2775)
    else:target.chmod(0o660)
    with pytest.raises(AuthorizationRejected): auth.operator_document(leaf)


def test_sticky_exception_is_limited_to_configured_render_root(projected,monkeypatch):
    monkeypatch.setattr(auth,'RENDER_SECRET_ROOT',Path('/etc/secrets'))
    with pytest.raises(AuthorizationRejected):auth.operator_document(projected[2])


def test_sticky_exception_rejects_traversal_and_unexpected_symlink(projected):
    root,_,leaf,_,owners=projected
    leaf.unlink();leaf.symlink_to('../outside')
    info=leaf.lstat();owners[(info.st_dev,info.st_ino)]=0
    with pytest.raises(AuthorizationRejected): auth.operator_document(leaf)


def test_sticky_parent_target_change_during_read_remains_rejected(projected,monkeypatch):
    from contextlib import contextmanager
    root,generation,leaf,_,_=projected
    fdopen=os.fdopen
    @contextmanager
    def change(fd,*args,**kwargs):
        with fdopen(fd,*args,**kwargs) as stream:
            class Reader:
                def fileno(self):return stream.fileno()
                def read(self,*args):
                    raw=stream.read(*args)
                    leaf.unlink();leaf.symlink_to('..data/not-the-policy.json')
                    return raw
            yield Reader()
    monkeypatch.setattr(os,'fdopen',change)
    with pytest.raises(AuthorizationRejected): auth.operator_document(leaf)


def test_regular_nonsticky_operator_document_still_works(tmp_path):
    path=tmp_path/'dav-ai-public-policy.json'
    path.write_text('{"test":"regular document"}');path.chmod(0o600)
    assert auth.operator_document(path)=={'test':'regular document'}


@pytest.mark.parametrize('raw',[b'{"duplicate":1,"duplicate":2}',b' '*16385])
def test_sticky_parent_keeps_parser_and_size_limits(projected,raw):
    projected[3].write_bytes(raw)
    with pytest.raises(AuthorizationRejected):auth.operator_document(projected[2])
