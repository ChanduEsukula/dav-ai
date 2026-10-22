"""Build a deterministic source-only review candidate, without touching Git or datasets."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
PREFIXES = ('backend/', 'frontend/', 'scripts/', '.github/', 'docs/simplification/', 'docs/hardening/', 'docs/staging-artifacts/', 'ops/')
FILES = {'.dockerignore', '.gitignore', 'README.md', 'alembic.ini', 'docker-compose.yml', 'docker-compose.staging.yml',
         'docs/architecture/PHARMACEUTICAL_EXPLORER.md'}
DENIED_SUFFIXES = {'.sqlite', '.db', '.dump', '.zip', '.parquet', '.gz', '.png', '.log'}


def contents():
    paths = subprocess.check_output(['git','ls-files','-c','-o','--exclude-standard','-z'],cwd=ROOT).decode().split('\0')
    result = {}
    for name in sorted(set(paths)):
        if not name or (name not in FILES and not name.startswith(PREFIXES)):
            continue
        if name.startswith('docs/staging-artifacts/verification/') or name == 'docs/staging-artifacts/REPORT.md':
            continue
        if name.startswith('docs/hardening/verification/') or name in {'docs/hardening/candidate.json', 'docs/hardening/RELEASE_CANDIDATE_REPORT.md'}:
            continue
        path = ROOT / name
        if not path.is_file() or path.suffix in DENIED_SUFFIXES:
            continue
        if path.is_symlink() or (path.name.startswith('.env') and path.name != '.env.example'):
            raise ValueError('Private configuration or symlink cannot enter candidate: '+name)
        if path.stat().st_size > 2_000_000:
            raise ValueError('Unexpected large source file: '+name)
        content = path.read_bytes()
        if re.search(rb'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY|(?:sk-proj-|AKIA)[A-Za-z0-9]{16}',content):
            raise ValueError('Potential secret in candidate: '+name)
        result[name] = content
    return result


def build(output):
    output = Path(output).resolve()
    if output.exists():
        raise ValueError('Do not overwrite an existing candidate')
    files = contents()
    manifest = {'format':'dav-ai-source-candidate-v1', 'publication_authorized':False,
                'base_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),
                'files':{name:hashlib.sha256(data).hexdigest() for name,data in files.items()},
                'external_artifacts':'Frozen SQLite and research datasets excluded. Required release gate must fail if the sealed artifact is absent; source-only tests do not qualify staging.'}
    files['CANDIDATE_MANIFEST.json'] = json.dumps(manifest,sort_keys=True,indent=2).encode()+b'\n'
    with output.open('xb') as raw:
        with gzip.GzipFile(fileobj=raw,mode='wb',filename='',mtime=0) as compressed:
            with tarfile.open(fileobj=compressed,mode='w',format=tarfile.USTAR_FORMAT) as archive:
                for name,data in sorted(files.items()):
                    info=tarfile.TarInfo(name);info.size=len(data);info.mode=0o644
                    archive.addfile(info,io.BytesIO(data))
    # Reopen and verify all bytes after packaging.
    with tarfile.open(output,'r:gz') as archive:
        for name,data in files.items():
            if archive.extractfile(name).read()!=data:raise ValueError('Candidate verification failed')
    return {'path':str(output),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'source_files':len(manifest['files'])}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(build(args.output),sort_keys=True,indent=2))
