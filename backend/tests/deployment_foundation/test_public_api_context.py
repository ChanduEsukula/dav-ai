"""Test the actual source-only Docker allowlist, without opening the real artifact."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]


def test_source_only_context_imports_all_public_routes_but_never_research(tmp_path):
    paths = {line[1:] for line in (ROOT / '.dockerignore').read_text().splitlines()
             if line.startswith('!') and line.endswith('.py')}
    for name in paths:
        source = ROOT / name
        destination = tmp_path / Path(name).relative_to('backend')
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    assert not (tmp_path / 'app/local_research').exists()
    assert not (tmp_path / 'app/agent').exists()
    assert (tmp_path / 'app/security/production_authorization.py').exists()
    code = '''
import sys, json
sys.path.insert(0, sys.argv[1])
from app.main import app
assert not any(name in sys.modules for name in ('sqlalchemy','faiss','app.local_research.api','app.agent.workflow'))
paths = app.openapi()['paths']
assert '/api/medications/overview' in paths
assert '/api/coverage/inventory' in paths
assert '/api/v1/reports/pharmaceutical' in paths
assert not any('research' in path or 'sessions' in path for path in paths)
print(json.dumps({'routes': len(paths), 'public_context_import': 'passed'}))
'''
    result = subprocess.run([sys.executable, '-I', '-c', code, str(tmp_path)],
                            env={**os.environ, 'DAVAI_ENV': 'production'}, cwd=tmp_path,
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['public_context_import'] == 'passed'


def test_every_unignored_directory_reexcludes_children_before_file_allowlist():
    # Docker !directory/ also unignores descendants. Explicitly re-deny children
    # before the exact file exceptions, so research/backups cannot enter COPY.
    lines=(ROOT/'.dockerignore').read_text().splitlines()
    for index,line in enumerate(lines):
        if line.startswith('!') and line.endswith('/'):
            assert lines[index+1]==line[1:]+'*'
