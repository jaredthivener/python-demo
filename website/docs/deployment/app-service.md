---
sidebar_position: 4
---

# Azure App Service

The simplest path to a production FastAPI app on Azure — git push or ZIP deploy, TLS included, Managed Identity with one toggle.

## When to choose App Service

- Steady, predictable traffic (not spiky)
- You want PaaS simplicity without managing Kubernetes
- Zero-downtime deployments with deployment slots (blue/green)
- Built-in TLS, custom domains, and autoscaling without extra config
- Team prefers `az webapp deploy` over YAML manifests

## Create the App Service

```bash
# Create a resource group and App Service plan (Linux, B2 = 2 vCPU / 3.5 GB)
az group create --name my-rg --location eastus

az appservice plan create \
  --name my-plan \
  --resource-group my-rg \
  --is-linux \
  --sku B2

# Create the web app (Python 3.13)
az webapp create \
  --name my-fastapi-app \
  --resource-group my-rg \
  --plan my-plan \
  --runtime "PYTHON:3.13"
```

## Enable Managed Identity

```bash
az webapp identity assign \
  --name my-fastapi-app \
  --resource-group my-rg

# Capture the principal ID for RBAC assignments
PRINCIPAL_ID=$(az webapp identity show \
  --name my-fastapi-app \
  --resource-group my-rg \
  --query principalId -o tsv)
```

## Grant Key Vault access

```bash
az role assignment create \
  --assignee-object-id "$PRINCIPAL_ID" \
  --assignee-principal-type ServicePrincipal \
  --role "Key Vault Secrets User" \
  --scope /subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.KeyVault/vaults/<vault>
```

## Configure app settings

```bash
# No secrets here — only non-sensitive config
az webapp config appsettings set \
  --name my-fastapi-app \
  --resource-group my-rg \
  --settings \
    AZURE_KEYVAULT_URL="https://myvault.vault.azure.net/" \
    APPLICATIONINSIGHTS_CONNECTION_STRING="<your-connection-string>" \
    WEBSITES_PORT=8000
```

## Observability with Azure Monitor

Install Azure Monitor OpenTelemetry — covers distributed tracing, structured logging, and metrics in one package:

```bash
uv add azure-monitor-opentelemetry
```

Call `configure_azure_monitor` once at startup, before the FastAPI app is instantiated:

```python
import os
from azure.monitor.opentelemetry import configure_azure_monitor

if conn_str := os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING"):
    configure_azure_monitor(connection_string=conn_str)
```

After this, every HTTP request is traced automatically and all `logging` output is forwarded to Application Insights Logs.

## Secrets from Key Vault

```python
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    client = SecretClient(
        vault_url=os.environ["AZURE_KEYVAULT_URL"],
        credential=DefaultAzureCredential(),  # resolves Managed Identity automatically
    )
    app.state.jwt_secret = client.get_secret("jwt-signing-key").value
    app.state.db_password = client.get_secret("db-password").value
    yield


app = FastAPI(lifespan=lifespan)
```

## Startup command

```bash
az webapp config set \
  --name my-fastapi-app \
  --resource-group my-rg \
  --startup-file "uvicorn demo.main:app --host 0.0.0.0 --port 8000 --workers 4"
```

## Deploy

### Option A: ZIP deploy (simplest)

```bash
# Package the app (excluding dev files)
zip -r app.zip . \
  --exclude ".git/*" \
  --exclude ".venv/*" \
  --exclude "website/*" \
  --exclude "*.pyc" \
  --exclude "__pycache__/*"

az webapp deploy \
  --name my-fastapi-app \
  --resource-group my-rg \
  --src-path app.zip \
  --type zip
```

### Option B: Container deploy (recommended for production)

```bash
# Push to ACR
az acr build --registry myacr --image fastapi-books:latest .

# Configure the web app to pull from ACR with MI
az webapp config container set \
  --name my-fastapi-app \
  --resource-group my-rg \
  --container-image-name myacr.azurecr.io/fastapi-books:latest \
  --container-registry-url https://myacr.azurecr.io

# Grant AcrPull so App Service can pull images without credentials
az role assignment create \
  --assignee-object-id "$PRINCIPAL_ID" \
  --assignee-principal-type ServicePrincipal \
  --role AcrPull \
  --scope /subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.ContainerRegistry/registries/myacr
```

## Zero-downtime deploys with slots

```bash
# Create a staging slot
az webapp deployment slot create \
  --name my-fastapi-app \
  --resource-group my-rg \
  --slot staging

# Deploy to staging first
az webapp deploy \
  --name my-fastapi-app \
  --resource-group my-rg \
  --slot staging \
  --src-path app.zip \
  --type zip

# Swap staging → production (zero downtime)
az webapp deployment slot swap \
  --name my-fastapi-app \
  --resource-group my-rg \
  --slot staging \
  --target-slot production
```

## Autoscaling

```bash
az monitor autoscale create \
  --resource-group my-rg \
  --resource my-plan \
  --resource-type Microsoft.Web/serverfarms \
  --name autoscale-policy \
  --min-count 2 \
  --max-count 10 \
  --count 2

az monitor autoscale rule create \
  --resource-group my-rg \
  --autoscale-name autoscale-policy \
  --condition "CpuPercentage > 70 avg 5m" \
  --scale out 2
```

## Health check

App Service can use your `/health` endpoint to take unhealthy instances out of rotation automatically:

```bash
az webapp config set \
  --name my-fastapi-app \
  --resource-group my-rg \
  --generic-configurations '{"healthCheckPath": "/health"}'
```
