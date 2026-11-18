#!/usr/bin/env bash
# Grant your personal Microsoft account the 'owner' role on the Static Web App.
# Every route requires that role, so this is what limits Prism to you.
#
# Usage: ./scripts/invite-owner.sh you@outlook.com
# Open the printed link in a private window and sign in with that exact account.
set -euo pipefail

EMAIL="${1:?Usage: $0 you@outlook.com}"
RG="${PRISM_RG:-rg-prism}"

out() { az deployment group show -g "$RG" -n prism-main --query "properties.outputs.$1.value" -o tsv; }
SWA_NAME="$(out staticWebAppName)"
SWA_HOST="$(out staticWebAppHostname)"

URL="$(az staticwebapp users invite \
  -g "$RG" -n "$SWA_NAME" \
  --authentication-provider aad \
  --user-details "$EMAIL" \
  --roles owner \
  --domain "$SWA_HOST" \
  --invitation-expiration-in-hours 24 \
  --query invitationUrl -o tsv)"

echo "Invitation for $EMAIL (valid 24h):"
echo "  $URL"
echo
echo "Open it, sign in with $EMAIL, then visit https://$SWA_HOST"
echo "To review or remove roles later: az staticwebapp users list -g $RG -n $SWA_NAME"
