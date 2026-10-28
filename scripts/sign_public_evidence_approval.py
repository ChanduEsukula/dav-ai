"""Offline operator tool. Reads an existing private key; never generates or uploads one.

Writes only new policy/grant files in an operator-chosen private output directory.
No activation, Render API calls, environment edits or database operations.
"""
import argparse
import base64
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from app.security.production_authorization import READ_OPERATIONS, RELEASE_ID
from app.db.pharma.release_connection import EXPECTED_SHA256
from app.security.publication_candidate import PURPOSE


def issue(private_key_path, review_path, application_sha256, deployment_id, approval_id, output, hours=24):
    if not 1<=hours<=24: raise ValueError('Grant lifetime must be 1–24 hours')
    if len(application_sha256)!=64 or any(c not in '0123456789abcdef' for c in application_sha256):
        raise ValueError('Use the digest from the exact built runtime image')
    if not deployment_id or not approval_id: raise ValueError('Explicit service and approval identity required')
    keypath=Path(private_key_path)
    if keypath.is_symlink() or keypath.stat().st_mode & 0o077:
        raise ValueError('Private key must be an operator-only regular file')
    key=serialization.load_pem_private_key(keypath.read_bytes(),password=None)
    if not isinstance(key,Ed25519PrivateKey): raise ValueError('Ed25519 private key required')
    public=key.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
    now=datetime.now(timezone.utc).replace(microsecond=0)
    policy={'key_id':'operator-demo-v1','public_key_base64':base64.b64encode(public).decode(),
            'deployment_id':deployment_id,'review_bundle_sha256':hashlib.sha256(Path(review_path).read_bytes()).hexdigest(),
            'not_before':now.isoformat(),'not_after':(now+timedelta(hours=hours)).isoformat()}
    claims={'purpose':PURPOSE,'approval_id':approval_id,'key_id':policy['key_id'],'release_id':RELEASE_ID,
            'database_sha256':EXPECTED_SHA256,'deployment_id':deployment_id,'application_sha256':application_sha256,
            'review_bundle_sha256':policy['review_bundle_sha256'],'environment':'production','audience':'public',
            'operations':list(READ_OPERATIONS),'issued_at':now.isoformat(),'expires_at':policy['not_after']}
    payload=json.dumps(claims,sort_keys=True,separators=(',',':')).encode()
    grant={'payload_base64':base64.b64encode(payload).decode(),'signature_base64':base64.b64encode(key.sign(payload)).decode()}
    output=Path(output)
    output.mkdir(mode=0o700,parents=True,exist_ok=False)
    for name,value in [('dav-ai-public-policy.json',policy),('dav-ai-public-approval.json',grant)]:
        fd=os.open(output/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'w') as stream: json.dump(value,stream,indent=2);stream.write('\n')
    return {'signing_key_sha256':hashlib.sha256(public).hexdigest(),
            'approval_payload_sha256':hashlib.sha256(payload).hexdigest(),'expires_at':policy['not_after'],
            'activated':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--private-key',required=True)
    parser.add_argument('--review-bundle',required=True)
    parser.add_argument('--application-sha256',required=True)
    parser.add_argument('--render-service-id',required=True)
    parser.add_argument('--approval-id',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--hours',type=int,default=24)
    args=parser.parse_args()
    print(json.dumps(issue(args.private_key,args.review_bundle,args.application_sha256,
        args.render_service_id,args.approval_id,args.output,args.hours),indent=2))
