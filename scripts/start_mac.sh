#!/usr/bin/env bash
set -euo pipefail
export PYTHONUTF8=1
cd "$(dirname "$0")/.."
if [ ! -x .venv/bin/python ] || [ ! -f frontend/dist/index.html ]; then
  echo 'First run: installing this device environment and building the website.'
  bash scripts/setup_mac.sh
else
  (cd frontend && corepack pnpm install --frozen-lockfile && corepack pnpm build)
fi
.venv/bin/python scripts/local_config.py
.venv/bin/python scripts/check_runtime.py --configured
exec .venv/bin/python scripts/launch_app.py "$@"
