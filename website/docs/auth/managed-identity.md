---
sidebar_position: 3
---

# Cloud IAM / Workload Identity

Pattern 2 — your app authenticates to cloud services using a **platform-assigned identity**, with no long-lived credentials stored anywhere.

## The pattern is the same on every cloud

Every major cloud provides a metadata endpoint that issues short-lived tokens for the attached identity:

```
Your FastAPI app  →  Platform metadata endpoint  →  Cloud IAM
                  ←  Short-lived token (auto-refreshed)
                  →  Cloud service (DB, secrets, queues) with token
```

The token is issued based on the identity assigned to your compute resource. **No password or key file is ever needed.**

---

## AWS — IAM Roles (Lambda / ECS / IRSA)

### Enable the role

**Lambda:** Assign an execution role when creating the function.

**ECS Fargate:** Set `taskRoleArn` in your task definition.

**EKS (IRSA):** Annotate a Kubernetes service account:
```bash
eksctl create iamserviceaccount \
  --name fastapi-sa \
  --namespace default \
  --cluster my-cluster \
  --attach-policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite \
  --approve
```

### Access AWS services without credentials

`boto3` resolves the IAM role automatically via the instance metadata endpoint:

```python
import boto3
import json
from functools import lru_cache

@lru_cache
def get_secret(secret_name: str) -> dict:
    """No credentials needed — Lambda/ECS/IRSA role is resolved automatically."""
    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response["SecretString"])
```

### Credential chain (`boto3`)

| Order | Source | When active |
|---|---|---|
| 1 | `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` env vars | CI/CD |
| 2 | `~/.aws/credentials` | Local development |
| 3 | AWS CLI profile | Local development |
| 4 | ECS task role / Lambda execution role / IRSA token | **Production** |

---

## GCP — Workload Identity / ADC

### Enable the identity

**Cloud Run:** Pass `--service-account` when deploying:
```bash
gcloud run deploy fastapi-books \
  --service-account fastapi-sa@my-project.iam.gserviceaccount.com \
  ...
```

**GKE Workload Identity:** Annotate the Kubernetes service account and bind it to a Google Cloud service account:
```bash
gcloud iam service-accounts add-iam-policy-binding fastapi-gke-sa@my-project.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:my-project.svc.id.goog[default/fastapi-sa]"
```

**App Engine / Cloud Functions:** The default service account is automatically bound.

### Access GCP services without credentials

Application Default Credentials (ADC) resolves the bound service account:

```python
from google.cloud import secretmanager
import os

def get_secret(secret_id: str) -> str:
    """ADC resolves the Cloud Run / GKE / App Engine identity automatically."""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{os.environ['GCP_PROJECT']}/secrets/{secret_id}/versions/latest"
    return client.access_secret_version(request={"name": name}).payload.data.decode()
```

### ADC credential chain

| Order | Source | When active |
|---|---|---|
| 1 | `GOOGLE_APPLICATION_CREDENTIALS` env var | CI/CD / service account key |
| 2 | `gcloud auth application-default login` | Local development |
| 3 | Cloud Run / GKE Workload Identity / App Engine metadata | **Production** |

---

## Azure — Managed Identity

### Enable Managed Identity

**Portal:** Resource → Identity → System assigned → **On** → Save

**Azure CLI:**
```bash
# App Service or Function App
az webapp identity assign --name my-app --resource-group my-rg

# Container App
az containerapp identity assign --name my-app --resource-group my-rg --system-assigned
```

### Pattern 2a — Azure SQL with token auth

```python
import struct
import pyodbc
from azure.identity import DefaultAzureCredential

def get_sql_connection() -> pyodbc.Connection:
    credential = DefaultAzureCredential()
    token = credential.get_token("https://database.windows.net/.default").token
    token_bytes = token.encode("utf-16-le")
    token_struct = struct.pack(f"<I{len(token_bytes)}s", len(token_bytes), token_bytes)
    conn_str = (
        "Driver={ODBC Driver 18 for SQL Server};"
        f"Server=tcp:{SQL_SERVER}.database.windows.net,1433;"
        f"Database={SQL_DATABASE};"
        "Encrypt=yes;TrustServerCertificate=no;"
    )
    return pyodbc.connect(conn_str, attrs_before={1256: token_struct})
```

**Azure side:** grant the Managed Identity the `db_datareader` / `db_datawriter` SQL role:
```sql
CREATE USER [my-app] FROM EXTERNAL PROVIDER;
ALTER ROLE db_datareader ADD MEMBER [my-app];
ALTER ROLE db_datawriter ADD MEMBER [my-app];
```

### Pattern 2b — Key Vault for secrets

```python
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from fastapi import FastAPI

VAULT_URL = os.environ["AZURE_KEYVAULT_URL"]

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    credential = DefaultAzureCredential()
    client = SecretClient(VAULT_URL, credential)
    app.state.jwt_secret = client.get_secret("jwt-signing-key").value
    app.state.db_password = client.get_secret("sql-password").value
    yield

app = FastAPI(lifespan=lifespan)
```

Grant the Managed Identity the `Key Vault Secrets User` RBAC role:
```bash
az role assignment create \
  --assignee <principal-id-of-your-mi> \
  --role "Key Vault Secrets User" \
  --scope /subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.KeyVault/vaults/<vault>
```

### Install dependencies

```bash
uv add azure-identity azure-keyvault-secrets
```

### `DefaultAzureCredential` chain

| Order | Source | When active |
|---|---|---|
| 1 | `AZURE_CLIENT_ID` + `AZURE_CLIENT_SECRET` env vars | CI/CD service principals |
| 2 | Azure CLI (`az login`) | Local development |
| 3 | VS Code credential | Local development |
| 4 | Managed Identity (IMDS) | **Production — Azure compute** |

---

## Local development, across all clouds

| Cloud | Local credential command | SDK |
|---|---|---|
| AWS | `aws configure` or AWS SSO login | `boto3` |
| GCP | `gcloud auth application-default login` | `google-auth` |
| Azure | `az login` | `azure-identity` |

You write the same production code — the credential source resolves automatically based on environment.

---

## Next steps

- [AWS Deployment](../deployment/aws.md) — Lambda + ECS + IRSA
- [GCP Deployment](../deployment/gcp.md) — Cloud Run + GKE Workload Identity
- [Azure Functions](../deployment/azure-functions.md) — Azure serverless

ALTER ROLE db_datawriter ADD MEMBER [my-app];
```

## Pattern 2b — Key Vault for secrets

Fetch secrets at app startup using the `lifespan` context manager so they're loaded once and available throughout the app's lifetime.

```python
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from fastapi import FastAPI

VAULT_URL = os.environ["AZURE_KEYVAULT_URL"]  # e.g. https://myvault.vault.azure.net/

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    credential = DefaultAzureCredential()
    client = SecretClient(VAULT_URL, credential)
    # Load secrets once at startup — no per-request overhead
    app.state.jwt_secret = client.get_secret("jwt-signing-key").value
    app.state.db_password = client.get_secret("sql-password").value
    yield
    # Cleanup if needed

app = FastAPI(lifespan=lifespan)
```

**Azure side:** grant your Managed Identity the `Key Vault Secrets User` RBAC role:
```bash
az role assignment create \
  --assignee <principal-id-of-your-mi> \
  --role "Key Vault Secrets User" \
  --scope /subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.KeyVault/vaults/<vault>
```

## Install dependencies

```bash
uv add azure-identity azure-keyvault-secrets
```

## `DefaultAzureCredential` chain

`DefaultAzureCredential` tries credential sources in order, making local development seamless:

| Order | Source | When active |
|---|---|---|
| 1 | `AZURE_CLIENT_ID` + `AZURE_CLIENT_SECRET` env vars | CI/CD service principals |
| 2 | Azure CLI (`az login`) | Local development |
| 3 | VS Code credential | Local development |
| 4 | Managed Identity (IMDS) | **Production — Azure compute** |

You write the same code in dev and prod — the credential source changes automatically.

## Local development

For local dev, run `az login` and set `AZURE_KEYVAULT_URL`:
```bash
az login
export AZURE_KEYVAULT_URL=https://myvault.vault.azure.net/
uv run uvicorn demo.main:app --reload
```

`DefaultAzureCredential` will use your CLI session to fetch Key Vault secrets exactly as it would in production.
