"""Exercise harness setup in a subprocess: its audit hooks must not enter pytest."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("origins, expected", [
    (None, ["http://127.0.0.1:15173"]),
    ("https://restricted.example", ["https://restricted.example"]),
    ("", []),
])
def test_offline_harness_scopes_cors_and_preserves_explicit_restrictions(tmp_path, origins, expected):
    environment = dict(os.environ, PYTHONPATH=str(ROOT / "backend"), PORT="18000", DAVAI_ENV="staging",
                       PHARMA_OFFLINE_LOG=str(tmp_path / "outbound.log"))
    environment.pop("ALLOWED_ORIGINS", None)
    if origins is not None:
        environment["ALLOWED_ORIGINS"] = origins
    # Replace only the listener; exercise the script's real __main__ initialization,
    # app configuration and the hosted gate without opening SQLite or a network port.
    code = '''
import json, runpy, sys, types

def inspect(application, **kwargs):
    from app.main import get_allowed_origins
    from app.db.pharma.release_connection import connect_release, PharmaceuticalReleaseUnavailable
    try:
        connect_release()
    except PharmaceuticalReleaseUnavailable:
        denied = True
    else:
        denied = False
    print(json.dumps(dict(origins=get_allowed_origins(), denied=denied, **kwargs)))

sys.modules['uvicorn'] = types.SimpleNamespace(run=inspect)
runpy.run_path('scripts/pharma_offline_server.py', run_name='__main__')
'''
    result = subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=environment,
                            capture_output=True, text=True, check=True, timeout=15)
    config = json.loads(result.stdout)
    assert config["origins"] == expected
    assert config["host"] == "127.0.0.1"
    assert config["port"] == 18000
    assert config["access_log"] is False
    assert config["denied"] is True


def test_application_default_cors_does_not_admit_test_origin(monkeypatch):
    from app.main import get_allowed_origins
    monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
    assert get_allowed_origins() == ["http://localhost:5173", "http://127.0.0.1:5173"]
