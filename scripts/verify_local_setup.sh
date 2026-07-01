#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "== DavAI local setup verification =="

echo
echo "Checking required files..."
required_files=(
  "README.md"
  "alembic.ini"
  "backend/requirements.txt"
  "backend/.env.example"
  "frontend/package.json"
  "frontend/package-lock.json"
  "frontend/.env.example"
  "docker-compose.yml"
)

for file in "${required_files[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "Missing required file: $file"
    exit 1
  fi
  echo "OK: $file"
done

echo
echo "Checking Python..."
python3 --version
python3 - <<'PY'
import importlib.util
import sys

required = ["fastapi", "pydantic", "sqlalchemy", "alembic", "pytest"]
missing = [name for name in required if importlib.util.find_spec(name) is None]

if missing:
    print("Missing Python packages:", ", ".join(missing))
    print("Run: python3 -m pip install -r backend/requirements.txt")
    sys.exit(1)

print("OK: required Python packages import")
PY

echo
echo "Checking backend import path..."
PYTHONPATH=backend python3 - <<'PY'
from app.main import app

print("OK: FastAPI app imports")
print(f"OK: app title = {app.title}")
PY

echo
echo "Checking Alembic configuration..."
python3 -m alembic --version
python3 -m alembic heads

echo
echo "Checking Node..."
node --version
npm --version
node - <<'NODE'
const major = Number.parseInt(process.versions.node.split('.')[0], 10)

if (major !== 24) {
  console.warn(`Warning: CI uses Node 24, but local Node is ${process.version}.`)
  console.warn('Frontend checks may still pass locally, but use Node 24 for CI parity.')
} else {
  console.log('OK: Node major version matches CI')
}
NODE

echo
echo "Checking frontend package scripts..."
node - <<'NODE'
const pkg = require('./frontend/package.json')
const required = ['dev', 'build', 'lint', 'test', 'test:e2e']
const missing = required.filter((script) => !pkg.scripts || !pkg.scripts[script])

if (missing.length) {
  console.error(`Missing frontend scripts: ${missing.join(', ')}`)
  process.exit(1)
}

console.log('OK: frontend scripts present')
NODE

echo
echo "Checking frontend dependencies..."
if [[ ! -d "frontend/node_modules" ]]; then
  echo "Missing frontend/node_modules"
  echo "Run: cd frontend && npm ci"
  exit 1
fi
echo "OK: frontend/node_modules exists"

echo
echo "Local setup verification passed."
