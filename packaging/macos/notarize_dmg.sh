#!/bin/zsh
set -euo pipefail

DMG="${1:-DROPS-Red-Zone-Monitoring-macos-arm64.dmg}"
PROFILE="${APPLE_NOTARY_PROFILE:-}"

[[ -f "$DMG" ]] || { echo "DMG not found: $DMG"; exit 1; }

if [[ -n "$PROFILE" ]]; then
  xcrun notarytool submit "$DMG" --keychain-profile "$PROFILE" --wait
else
  : "${APPLE_ID:?Set APPLE_ID or APPLE_NOTARY_PROFILE}"
  : "${APPLE_TEAM_ID:?Set APPLE_TEAM_ID or APPLE_NOTARY_PROFILE}"
  : "${APPLE_APP_SPECIFIC_PASSWORD:?Set APPLE_APP_SPECIFIC_PASSWORD or APPLE_NOTARY_PROFILE}"
  xcrun notarytool submit "$DMG" \
    --apple-id "$APPLE_ID" \
    --team-id "$APPLE_TEAM_ID" \
    --password "$APPLE_APP_SPECIFIC_PASSWORD" \
    --wait
fi

xcrun stapler staple "$DMG"
spctl -a -t open --context context:primary-signature -v "$DMG"
echo "Notarized and stapled: $DMG"
