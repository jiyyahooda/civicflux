#!/usr/bin/env bash
set -euo pipefail
export PYTHONUTF8=1
cd "$(dirname "$0")/.."
case "${1:-}" in
 backend)
  [ -x .venv/bin/python ] || { echo 'Run bash scripts/setup_mac.sh first.' >&2; exit 1; }
  .venv/bin/python scripts/check_runtime.py --configured
  exec .venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8001 ;;
 frontend)
  [ -d frontend/node_modules ] || { echo 'Run setup first.' >&2; exit 1; }
  cd frontend; exec corepack pnpm dev ;;
 *) echo 'Usage: bash scripts/run_mac.sh backend|frontend' >&2; exit 2 ;;
esac
