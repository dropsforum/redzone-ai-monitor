#!/bin/zsh
set -euo pipefail

APP_NAME="Exposure Zone Monitoring"
APP_PATH="dist/${APP_NAME}.app"
SIGNED_APP_DIR="${SIGNED_APP_DIR:-/tmp/redzone-mac-sign}"
SIGNED_APP_PATH="${SIGNED_APP_PATH:-${SIGNED_APP_DIR}/${APP_NAME}.app}"
IDENTITY="${MACOS_CODESIGN_IDENTITY:-}"
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

echo "Using Python: $PYTHON_BIN"
echo "Using build venv: $VENV_DIR"
if [[ ! -d "$VENV_DIR" ]]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r requirements_ai.txt

# Release bundles omit checkpoints. The app verifies and caches them on first use.

if [[ "${MACOS_REUSE_DIST:-0}" == "1" && -d "$APP_PATH" ]]; then
  echo "Reusing existing PyInstaller app at $APP_PATH"
else
  rm -rf "$APP_PATH" "build/pyinstaller" || true
  python -m PyInstaller packaging/macos/pyinstaller.spec --clean --noconfirm
fi

find "$APP_PATH" -name ".DS_Store" -delete

rm -rf "$SIGNED_APP_PATH"
mkdir -p "$SIGNED_APP_DIR"
ditto --norsrc --noextattr "$APP_PATH" "$SIGNED_APP_PATH"
find "$SIGNED_APP_PATH" -name ".DS_Store" -delete
codesign --remove-signature "$SIGNED_APP_PATH" 2>/dev/null || true

if [[ -n "$IDENTITY" ]] && security find-identity -v -p codesigning | grep -Fq "$IDENTITY"; then
  echo "Signing $SIGNED_APP_PATH with $IDENTITY"
  codesign \
    --force \
    --deep \
    --options runtime \
    --entitlements packaging/macos/Entitlements.plist \
    --sign "$IDENTITY" \
    "$SIGNED_APP_PATH"
  codesign --verify --deep --strict --verbose=2 "$SIGNED_APP_PATH"
else
  echo "Warning: signing identity not configured or not found."
  echo "Set MACOS_CODESIGN_IDENTITY to sign the app."
  echo "Built unsigned app at $APP_PATH"
  echo "Clean unsigned staging copy: $SIGNED_APP_PATH"
fi

echo "Built: $APP_PATH"
echo "Signed/staged: $SIGNED_APP_PATH"
