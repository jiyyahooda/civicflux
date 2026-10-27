#!/usr/bin/env bash
cd "$(dirname "$0")"
bash scripts/start_mac.sh
result=$?
if [ "$result" -ne 0 ]; then
  read -r -p 'Startup failed. Read the error above. Press Enter to close.'
fi
exit "$result"
