#!/usr/bin/env bash
# Ensure requirements are installed, then launch the simulator.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"

if [[ ! -x "$ROOT_DIR/install.sh" ]]; then
    chmod +x "$ROOT_DIR/install.sh"
fi

"$ROOT_DIR/install.sh"

cd "$ROOT_DIR"
export PYTHONPATH="$ROOT_DIR/src"
exec "$VENV_DIR/bin/python" -m src.main
