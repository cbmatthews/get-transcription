#!/usr/bin/env bash
# Provision Azure resources (Bicep) and deploy the backend and frontend.
#
# Usage:
#   az login
#   ./scripts/deploy.sh                 # infra + backend + frontend
#   ./scripts/deploy.sh --skip-infra    # code only
#
# Config (env vars, all optional):
#   PRISM_SUBSCRIPTION  subscription name or ID (default: current az account)
#   PRISM_RG            resource group           (default: rg-prism)
#   PRISM_LOCATION      region                   (default: eastus2)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RG="${PRISM_RG:-rg-prism}"
LOCATION="${PRISM_LOCATION:-eastus2}"
SKIP_INFRA=false
SKIP_BACKEND=false
SKIP_FRONTEND=false

for arg in "$@"; do
  case "$arg" in
    --skip-infra) SKIP_INFRA=true ;;
    --skip-backend) SKIP_BACKEND=true ;;
    --skip-frontend) SKIP_FRONTEND=true ;;
    -h|--help) sed -n '2,14p' "$0"; exit 0 ;;
    *) echo "Unknown option: $arg" >&2; exit 2 ;;
  esac
done

step() { printf '\n\033[1;35m==> %s\033[0m\n' "$*"; }
need() { command -v "$1" >/dev/null || { echo "Missing required tool: $1 ($2)" >&2; exit 1; }; }

need az "https://learn.microsoft.com/cli/azure/install-azure-cli"
need node "https://nodejs.org (v20+)"
need npm "comes with Node.js"
need python3 "https://www.python.org (3.10+)"
need zip "your package manager"

if [[ -n "${PRISM_SUBSCRIPTION:-}" ]]; then
  az account set --subscription "$PRISM_SUBSCRIPTION"
fi
az account show --query "{subscription:name, user:user.name}" -o table

# ---------------------------------------------------------------- infra
if [[ "$SKIP_INFRA" == false ]]; then
  step "Registering resource providers (no-op if already registered)"
  for ns in Microsoft.Web Microsoft.Storage Microsoft.KeyVault Microsoft.Insights \
            Microsoft.OperationalInsights Microsoft.ManagedIdentity; do
    az provider register --namespace "$ns" --wait -o none
  done

  step "Resource group $RG ($LOCATION)"
  az group create -n "$RG" -l "$LOCATION" -o none

  DEPLOYER_ID="$(az ad signed-in-user show --query id -o tsv 2>/dev/null || true)"
  if [[ -z "$DEPLOYER_ID" ]]; then
    echo "Couldn't read your user object ID; you'll need to grant yourself Storage Blob Data Contributor manually." >&2
  fi

  step "Deploying Bicep (first run takes ~5 minutes)"
  az deployment group create \
    -g "$RG" -n prism-main \
    -f "$ROOT/infra/main.bicep" \
    -p "$ROOT/infra/main.bicepparam" \
    -p deployerPrincipalId="$DEPLOYER_ID" \
    -o none
fi

out() { az deployment group show -g "$RG" -n prism-main --query "properties.outputs.$1.value" -o tsv; }
SWA_NAME="$(out staticWebAppName)"
SWA_HOST="$(out staticWebAppHostname)"
FUNC_NAME="$(out functionAppName)"
FUNC_ID="$(out functionAppId)"
STORAGE="$(out storageAccountName)"
DEPLOY_CONTAINER="$(out deploymentContainer)"
PACKAGE_BLOB="$(out packageBlobName)"

# ---------------------------------------------------------------- backend
if [[ "$SKIP_BACKEND" == false ]]; then
  step "Building backend package"
  BUILD="$ROOT/.build/backend"
  rm -rf "$BUILD" && mkdir -p "$BUILD"
  (cd "$ROOT/backend" && tar --exclude-from=.funcignore --exclude='*.pyc' -cf - .) | (cd "$BUILD" && tar -xf -)
  # Linux Consumption runs Python 3.12 on x86_64: fetch matching wheels whatever OS you're on.
  python3 -m pip install -q -r "$ROOT/backend/requirements.txt" \
    --target "$BUILD/.python_packages/lib/site-packages" \
    --platform manylinux2014_x86_64 --platform manylinux_2_17_x86_64 --platform manylinux_2_28_x86_64 \
    --python-version 3.12 --implementation cp --only-binary=:all: --upgrade
  GIT_SHA="$(git -C "$ROOT" rev-parse HEAD 2>/dev/null || echo unknown)"
  printf '{"version":"0.1.0","gitSha":"%s","builtAt":"%s"}\n' "$GIT_SHA" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$BUILD/build_info.json"
  rm -f "$ROOT/.build/backend.zip"
  (cd "$BUILD" && zip -qr "$ROOT/.build/backend.zip" .)

  step "Uploading package to $STORAGE/$DEPLOY_CONTAINER/$PACKAGE_BLOB"
  # New role assignments can take a few minutes to apply; retry.
  for attempt in 1 2 3 4 5 6; do
    if az storage blob upload --auth-mode login --account-name "$STORAGE" \
        -c "$DEPLOY_CONTAINER" -n "$PACKAGE_BLOB" -f "$ROOT/.build/backend.zip" --overwrite -o none 2>/dev/null; then
      break
    fi
    [[ $attempt == 6 ]] && { echo "Upload failed. Check you have Storage Blob Data Contributor on $STORAGE." >&2; exit 1; }
    echo "  upload not permitted yet (role assignment propagating); retrying in 30s…"
    sleep 30
  done

  step "Restarting $FUNC_NAME and syncing triggers"
  az functionapp restart -g "$RG" -n "$FUNC_NAME" -o none
  az rest --method post --url "https://management.azure.com${FUNC_ID}/syncfunctiontriggers?api-version=2023-12-01" -o none || true
fi

# ---------------------------------------------------------------- frontend
if [[ "$SKIP_FRONTEND" == false ]]; then
  step "Building frontend"
  (cd "$ROOT/frontend" && npm ci --no-audit --no-fund && npm run build)

  step "Deploying frontend to $SWA_NAME"
  TOKEN="$(az staticwebapp secrets list -g "$RG" -n "$SWA_NAME" --query properties.apiKey -o tsv)"
  npx --yes @azure/static-web-apps-cli@2.1.0 deploy "$ROOT/frontend/dist" \
    --deployment-token "$TOKEN" --env production
fi

step "Done"
cat <<EOF
App:          https://$SWA_HOST
Function App: $FUNC_NAME (only reachable through the Static Web App)

First time? Invite your Microsoft account so it gets the 'owner' role:
  ./scripts/invite-owner.sh you@outlook.com
EOF
