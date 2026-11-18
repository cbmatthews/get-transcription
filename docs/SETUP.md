# Prism — setup and deployment

This covers M0 (Foundation): one resource group with a Static Web App, a Function App, Storage and Key Vault. Sign-in is limited to your Microsoft account.

## What gets created

All resources go in one resource group (`rg-prism`, region `eastus2`) and are defined in `infra/`.

| Resource | Purpose | Cost |
|---|---|---|
| Static Web App (Standard) | Hosts the React app, handles Microsoft sign-in, proxies `/api` to the Function App | ~$9/month |
| Function App (Linux Consumption, Python 3.12) | Job API and Durable Functions | Free grant, then cents |
| Storage account | Containers `uploads`, `audio`, `jobs` and `deployments`, plus Functions host state. Shared keys are disabled. | Cents |
| Key Vault (RBAC) | Secrets that can't use managed identity (e.g. the Notion token in M5) | Cents |
| User-assigned managed identity | The Function App uses it to reach Storage and Key Vault. There are no keys in app settings. | Free |
| Log Analytics + App Insights | Logs, capped at 1 GB/day | Free tier |

**Why Standard SWA:** linking a separate Function App as the `/api` backend requires the Standard plan. Durable Functions, managed identity and Key Vault need a separate Function App rather than SWA's built-in managed functions. **Why Linux Consumption:** it is the plan Microsoft documents for SWA linked backends. Flex Consumption isn't listed yet. The code is the same on either plan, so moving to Flex later (Linux Consumption retires in September 2028) only changes the infrastructure.

## How sign-in is locked to you

1. The SWA's built-in Microsoft provider (`/.auth/login/aad`) lets any Microsoft account sign in. The GitHub provider is disabled.
2. `frontend/public/staticwebapp.config.json` requires the custom role **`owner`** on every route, including `/api/*`. Signed-out visitors are redirected to Microsoft sign-in. Signed-in accounts without the role get a 403 page.
3. The `owner` role is granted only by invitation (`scripts/invite-owner.sh`) to your email address.
4. The backend checks for `owner` again on every request (`backend/prism/auth.py`).
5. Linking the Function App to the SWA turns on App Service authentication for it, so calls straight to `*.azurewebsites.net` are rejected.

## One-time prerequisites

1. **Activate the Visual Studio Azure credit** with your *personal* Microsoft account: [my.visualstudio.com](https://my.visualstudio.com) → Benefits → Azure monthly credit → Activate. This creates a subscription named something like "Visual Studio Enterprise Subscription". Keep it separate from any work tenant.
2. **Install tools:**
   - [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli) 2.60+ (includes Bicep)
   - Node.js 20+ and Python 3.10+ (the script downloads Python 3.12 Linux wheels, whatever your local version)
   - `zip`
3. **Sign in:**
   ```bash
   az login                      # use your personal Microsoft account
   az account list -o table      # find the Visual Studio subscription
   export PRISM_SUBSCRIPTION="<subscription name or id>"
   ```

## Deploy

```bash
./scripts/deploy.sh
```

The script:
- registers resource providers
- creates `rg-prism`
- deploys `infra/main.bicep`
- builds the backend zip, uploads it to Blob Storage and restarts the Function App
- builds the frontend and deploys it to the Static Web App

The first run takes about 5–8 minutes. Re-run any time; it's idempotent. Useful flags: `--skip-infra`, `--skip-backend`, `--skip-frontend`. You can override the defaults with `PRISM_RG` and `PRISM_LOCATION`.

Then grant your account the `owner` role:

```bash
./scripts/invite-owner.sh you@outlook.com
```

Open the printed link in a private browser window and sign in with that exact account.

## M0 test checklist

- [ ] **Sign-in:** open `https://<app>.azurestaticapps.net` in a private window. You're sent to Microsoft sign-in, then land on Prism with your email in the header.
- [ ] **System check:** every row is green: *Sign-in reaches API*, *Blob Storage*, *Key Vault*, *Providers*. The footer shows the backend git SHA.
- [ ] **Durable check:** press **Run Durable check**. Within about 30 seconds it shows `Completed, output "pong"`. The first run after a deploy can take longer while the app cold-starts.
- [ ] **Other accounts are blocked:** in another private window, sign in with a different Microsoft account. You see "This account can't use Prism".
- [ ] **API is locked:** `curl -i https://<app>.azurestaticapps.net/api/health` returns a 302 redirect to login. `curl -i https://<func>.azurewebsites.net/api/health` returns 401 or 403.
- [ ] **Portal:** the Storage account has `uploads`, `audio`, `jobs` and `deployments` containers. Key Vault has the secret `prism-healthcheck`. All resources are in `rg-prism`.
- [ ] **Cost:** Cost Management → Budgets. Optionally add a $30/month budget alert on the resource group.

## Troubleshooting

- **Health shows Storage/Key Vault failing right after the first deploy:** role assignments can take up to about 10 minutes to apply. Wait, then press **Re-run**.
- **`/api/*` returns 404 or 5xx right after deploy:** the Function App is cold-starting or still loading the package. Wait a minute. Logs: portal → Function App → Log stream, or App Insights → Failures.
- **Invite link says the role is already assigned, or you need a new link:** run `invite-owner.sh` again. To list roles: `az staticwebapp users list -g rg-prism -n <swa-name>`.
- **Stuck in a sign-in loop:** clear cookies for the `azurestaticapps.net` site, or use a private window.

## Local development

You need [Azure Functions Core Tools v4](https://learn.microsoft.com/azure/azure-functions/functions-run-local), [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite) and the [SWA CLI](https://azure.github.io/static-web-apps-cli/) (`npm i -g @azure/static-web-apps-cli azurite`).

```bash
# 1. Storage emulator
azurite --silent --location .azurite &

# 2. Backend
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp local.settings.example.json local.settings.json
func start                         # http://localhost:7071

# 3. Frontend
cd frontend && npm install && npm run dev   # http://localhost:5173

# 4. SWA emulator (auth + /api proxy) from the repo root
swa start prism                    # open http://localhost:4280
```

The SWA emulator shows a fake sign-in form. Enter any username and add `owner` under **User's roles**. Locally, the Key Vault check passes as "Not configured", and the health check creates the `uploads`, `audio` and `jobs` containers in Azurite on first run.

Tests:
```bash
cd backend && pytest -q && ruff check .
cd frontend && npm test && npm run build
```
