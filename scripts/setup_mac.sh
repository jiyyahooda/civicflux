#!/usr/bin/env bash
set -euo pipefail
export PYTHONUTF8=1
trap 'echo "Setup failed. Review the error above and README troubleshooting." >&2' ERR
cd "$(dirname "$0")/.."
command -v brew >/dev/null || { echo 'Install Homebrew from https://brew.sh first.' >&2; exit 1; }
command -v python3.13 >/dev/null || { echo 'Install native Python 3.13 first.' >&2; exit 1; }
command -v node >/dev/null || { echo 'Install Node.js 24 first.' >&2; exit 1; }
command -v corepack >/dev/null || { echo 'Install Corepack: npm install -g corepack' >&2; exit 1; }
node -e 'if(Number(process.versions.node.split(".")[0]) < 24) process.exit(1)'
brew list --versions libomp >/dev/null 2>&1 || brew install libomp
if [ ! -d .venv ]; then python3.13 -m venv .venv; fi
[ -x .venv/bin/python ] || { echo 'Transferred or broken .venv: rename it, then rerun setup.' >&2; exit 1; }
.venv/bin/python -c 'import sys,platform; assert sys.version_info[:2] == (3,13); assert platform.system() == "Darwin"'
.venv/bin/python -m pip install -r requirements-test.txt
.venv/bin/python -m pip check
.venv/bin/python scripts/check_runtime.py
.venv/bin/python scripts/local_config.py
(cd frontend && corepack pnpm install --frozen-lockfile && corepack pnpm build)
echo 'Ready. In separate terminals: bash scripts/run_mac.sh backend and bash scripts/run_mac.sh frontend'
