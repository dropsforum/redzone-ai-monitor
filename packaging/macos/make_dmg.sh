#!/bin/zsh
set -euo pipefail
APP="dist/DROPS Red Zone Monitoring.app"
DMG="DROPS-Red-Zone-Monitoring-macos-arm64.dmg"
[[ -d "$APP" ]] || { echo "App not found: $APP"; exit 1; }
hdiutil create -volname DROPS-Red-Zone-Monitoring -srcfolder "$APP" -ov -format UDZO "$DMG"

