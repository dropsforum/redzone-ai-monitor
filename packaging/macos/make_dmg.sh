#!/bin/zsh
set -euo pipefail
APP="dist/DROPS Red Zone Monitoring POC.app"
DMG="DROPS-POC-macos-arm64.dmg"
[[ -d "$APP" ]] || { echo "App not found: $APP"; exit 1; }
hdiutil create -volname DROPS-POC -srcfolder "$APP" -ov -format UDZO "$DMG"

