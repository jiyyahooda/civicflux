#!/usr/bin/env bash
set -euo pipefail
export PYTHONUTF8=1
cd "$(dirname "$0")/.."
if [ ! -x .venv/bin/python ] || [ ! -f frontend/dist/index.html ]; then
  echo 'First run: installing this device environment and building the website.'
  bash scripts/setup_mac.sh
fi
.venv/bin/python scripts/local_config.py
.venv/bin/python scripts/check_runtime.py --configured
echo 'Open http://127.0.0.1:8001 | Admin ID: admin | Password: 001'
exec .venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8001
