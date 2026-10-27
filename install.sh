#!/usr/bin/env bash
# Launch the Linux TUI installer
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"
if command -v python3 >/dev/null 2>&1; then
  exec python3 install_linux.py
elif command -v python >/dev/null 2>&1; then
  exec python install_linux.py
else
  echo "Python 3 is required."
  exit 1
fi
