#!/bin/zsh
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-}"
VENV_DIR="${MACOS_BUILD_VENV:-/tmp/redzone-mac-venv}"

if [[ -z "$PYTHON_BIN" ]]; then
  for candidate in \
    "$HOME/.local/bin/python3.11" \
    "/opt/homebrew/bin/python3.11" \
    "/opt/homebrew/bin/python3" \
    "/usr/bin/python3"; do
    if [[ -x "$candidate" ]]; then
      PYTHON_BIN="$candidate"
      break
    fi
  done
fi

if [[ -z "$PYTHON_BIN" ]]; then
  echo "No usable Python 3 interpreter found. Set PYTHON_BIN=/path/to/python3."
  exit 1
fi

if [[ ! -d "$VENV_DIR" ]]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r requirements_ai.txt
python run_ai_app.py "$@"
