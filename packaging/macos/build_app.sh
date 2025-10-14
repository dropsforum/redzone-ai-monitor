#!/bin/zsh
set -euo pipefail
python3 -m pip install --quiet pyinstaller
pyinstaller packaging/macos/pyinstaller.spec

