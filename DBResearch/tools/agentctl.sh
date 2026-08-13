#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if command -v python3 >/dev/null 2>&1; then
  exec python3 "$SCRIPT_DIR/agentctl.py" "$@"
fi
if command -v python >/dev/null 2>&1; then
  exec python "$SCRIPT_DIR/agentctl.py" "$@"
fi
echo "ERROR Python was not found. The Markdown harness still works, but agentctl requires Python 3.10 or newer." >&2
exit 127
