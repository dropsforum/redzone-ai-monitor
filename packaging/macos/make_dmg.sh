#!/bin/zsh
set -euo pipefail
APP="${APP_PATH:-/tmp/redzone-mac-sign/DROPS Red Zone Monitoring.app}"
DMG="DROPS-Red-Zone-Monitoring-macos-arm64.dmg"
IDENTITY="${MACOS_CODESIGN_IDENTITY:-Developer ID Application: DrillingVR Pte Ltd (P86GW426XK)}"

if [[ ! -d "$APP" ]]; then
  APP="dist/DROPS Red Zone Monitoring.app"
fi

[[ -d "$APP" ]] || { echo "App not found: $APP"; exit 1; }
hdiutil create -volname DROPS-Red-Zone-Monitoring -srcfolder "$APP" -ov -format UDZO "$DMG"

if security find-identity -v -p codesigning | grep -Fq "$IDENTITY"; then
  codesign --force --sign "$IDENTITY" "$DMG"
  codesign --verify --verbose=2 "$DMG"
fi

echo "Created: $DMG"
