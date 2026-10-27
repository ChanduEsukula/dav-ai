"""Check fail-closed capture authentication without network or real corpus data."""
import base64
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import zipfile

import pytest

SCRIPT = Path(__file__).resolve().parents[3] / 'scripts/verify_fda_historical_capture.py'
spec = importlib.util.spec_from_file_location('historical_capture', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def run_capture(tmp_path, monkeypatch, *, encoded=True, bad_digest=False, bad_timestamp=False):
    body = io.BytesIO()
    with zipfile.ZipFile(body, 'w') as archive:
        archive.writestr('README.txt', 'Synthetic provenance fixture')
    decoded = body.getvalue()
    raw = gzip.compress(decoded, mtime=0) if encoded else decoded
    digest = base64.b32encode(hashlib.sha1(raw).digest()).decode().rstrip('=')
    index = tmp_path / 'index.json'
    index.write_text(json.dumps([
        ['timestamp', 'original', 'statuscode', 'mimetype', 'digest', 'length'],
        ['20250206033534', 'https://fis.fda.gov/content/Exports/faers_ascii_2024Q4.zip',
         '200', 'application/zip', 'WRONG' if bad_digest else digest, str(len(raw))]]))

    class Response:
        status_code = 200
        url = 'https://web.archive.org/web/20250206033534id_/https://fis.fda.gov/content/Exports/faers_ascii_2024Q4.zip'
        headers = {'memento-datetime': 'wrong' if bad_timestamp else 'Thu, 06 Feb 2025 03:35:34 GMT'}
        if encoded:
            headers['content-encoding'] = 'gzip'

        def __enter__(self): return self
        def __exit__(self, *args): return False
        def iter_raw(self):
            for i in range(0, len(raw), 13): yield raw[i:i + 13]

    monkeypatch.setattr(module.httpx, 'stream', lambda *args, **kwargs: Response())
    monkeypatch.setattr(module.shutil, 'disk_usage', lambda path: type('Disk', (), {'free': 100 * 1024**3})())
    evidence, output = tmp_path / 'evidence', tmp_path / 'output'
    monkeypatch.setattr(sys, 'argv', ['capture', '--index', str(index), '--evidence', str(evidence), '--output', str(output)])
    return decoded, evidence, output


@pytest.mark.parametrize('encoded', [False, True])
def test_raw_payload_digest_authenticates_decoded_zip(tmp_path, monkeypatch, encoded):
    decoded, evidence, output = run_capture(tmp_path, monkeypatch, encoded=encoded)
    module.main()
    receipt = json.loads(next(evidence.glob('*receipt.json')).read_text())
    assert receipt['passed'] and receipt['all_member_crc_passed']
    assert receipt['decoded_sha256'] == hashlib.sha256(decoded).hexdigest()
    assert next(output.glob('*.zip')).read_bytes() == decoded
    assert receipt['usable_for_temporal_training'] == 'UNKNOWN'


@pytest.mark.parametrize('failure', ['digest', 'timestamp'])
def test_bad_provenance_never_promotes_payload(tmp_path, monkeypatch, failure):
    _, evidence, output = run_capture(tmp_path, monkeypatch, bad_digest=failure == 'digest', bad_timestamp=failure == 'timestamp')
    with pytest.raises(ValueError): module.main()
    receipt = json.loads(next(evidence.glob('*receipt.json')).read_text())
    assert receipt['passed'] is False
    assert receipt['historical_source_bytes_available'] == 'UNKNOWN'
    assert not list(output.glob('*.zip'))
