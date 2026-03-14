---
sidebar_position: 2
---

# Azure Functions

Deploy FastAPI as a serverless Azure Function using the **Python v2 programming model** — a single-file, decorator-based approach that requires no `function.json` files.

## When to choose Functions

- Spiky or infrequent traffic — pay $0 at idle (Consumption plan)
- Event-driven triggers: HTTP, Service Bus, Event Hub, Timer
- Zero infrastructure management
- Cold start latency is acceptable (typically 1–3 s; mitigable with Premium plan or Always On)

## Architecture

```
Client → Azure API Management (optional) → HTTP Trigger → AsgiFunctionApp → FastAPI
```

`AsgiFunctionApp` is an official Azure Functions wrapper that bridges the Functions runtime to any ASGI app — no custom handler or subprocess required.

## Install

```bash
uv add "azure-functions>=1.17.0" azure-monitor-opentelemetry
```

## Project structure

```
fastapi-func/
├── function_app.py     ← Functions entry point (Python v2)
├── host.json
├── local.settings.json
└── demo/               ← your FastAPI app
```

## `function_app.py`

```python
# function_app.py
import azure.functions as func
from demo.main import app as fastapi_app

# AsgiFunctionApp wraps the FastAPI ASGI app for the Functions runtime
app = func.AsgiFunctionApp(app=fastapi_app, http_auth_level=func.AuthLevel.ANONYMOUS)
```

That's the entire glue layer. No `function.json`, no subprocess, no custom handler config.

## `host.json`

```json
{
  "version": "2.0",
  "extensionBundle": {
    "id": "Microsoft.Azure.Functions.ExtensionBundle",
    "version": "[4.*, 5.0.0)"
  }
}
```

## `local.settings.json`

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "APPLICATIONINSIGHTS_CONNECTION_STRING": ""
  }
}
```

## Observability with Azure Monitor

Azure Monitor OpenTelemetry is Azure's unified OTel distro — it configures distributed tracing, structured logging, and metrics in a single call:

```python
# demo/main.py (or a dedicated telemetry module)
import os
from azure.monitor.opentelemetry import configure_azure_monitor

# Call before the FastAPI app is created
if conn_str := os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING"):
    configure_azure_monitor(connection_string=conn_str)
```

This sends traces, logs, and metrics to Application Insights automatically — the equivalent of AWS Lambda Powertools + X-Ray rolled into one package.

## Secrets from Key Vault

Use Managed Identity + `DefaultAzureCredential` to fetch secrets without any credentials in code:

```python
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    vault_url = os.environ["KEY_VAULT_URL"]  # e.g. https://myvault.vault.azure.net/
    client = SecretClient(vault_url=vault_url, credential=DefaultAzureCredential())
    app.state.jwt_secret = client.get_secret("jwt-signing-key").value
    app.state.db_password = client.get_secret("db-password").value
    yield


app = FastAPI(lifespan=lifespan)
```

## Enable Managed Identity

```bash
# Create the Function App
az functionapp create \
  --name my-fastapi-func \
  --resource-group my-rg \
  --consumption-plan-location eastus \
  --runtime python \
  --runtime-version 3.13 \
  --functions-version 4 \
  --assign-identity [system]

# Grant Key Vault Secrets User to the system-assigned identity
az role assignment create \
  --assignee $(az functionapp identity show \
      --name my-fastapi-func --resource-group my-rg --query principalId -o tsv) \
  --role "Key Vault Secrets User" \
  --scope /subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.KeyVault/vaults/<vault>
```

## Deploy

```bash
func azure functionapp publish my-fastapi-func --python
```

## Mitigating cold starts

Use the **Premium (EP1)** plan with pre-warmed instances for latency-sensitive APIs:

```bash
az functionapp plan create \
  --name my-fastapi-plan \
  --resource-group my-rg \
  --sku EP1 \
  --is-linux true

az functionapp update \
  --name my-fastapi-func \
  --resource-group my-rg \
  --set alwaysOn=true
```

## Next steps

- [App Service](./app-service.md) — always-on container with deployment slots
- [AKS](./aks.md) — Kubernetes with Workload Identity
- [Cloud IAM / Workload Identity](../auth/managed-identity.md) — how the credential chain works across clouds
