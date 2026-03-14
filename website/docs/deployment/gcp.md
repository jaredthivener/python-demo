---
sidebar_position: 3
---

# GCP Deployment

Deploy FastAPI to Google Cloud with zero long-lived credentials using Workload Identity Federation and Application Default Credentials (ADC).

## Choose your target

| | Cloud Run | GKE + Workload Identity | App Engine |
|---|---|---|---|
| **Cost at idle** | $0 (scale to zero) | ~$100+/month (node pool) | ~$0 (F1 free tier) |
| **Cold start?** | Yes (mitigable with min-instances) | No | Yes |
| **IAM auth** | Service account binding | Workload Identity | Service account |
| **Container support** | Native | Native | Custom runtime |
| **Custom networking** | VPC connector | Full VPC | Limited |
| **Best for** | Serverless containers | Microservices / complex routing | Simple web apps |

---

## Option A — Cloud Run (recommended)

Cloud Run is the simplest GCP deployment: push a container, get a URL. Each revision runs with a bound Google Cloud service account — no key files needed.

### Build and push to Artifact Registry

```bash
# Enable APIs
gcloud services enable run.googleapis.com artifactregistry.googleapis.com

# Create registry
gcloud artifacts repositories create fastapi-repo \
  --repository-format=docker \
  --location=us-central1

# Build and push
gcloud auth configure-docker us-central1-docker.pkg.dev

docker build -t fastapi-books .
docker tag fastapi-books:latest \
  us-central1-docker.pkg.dev/my-project/fastapi-repo/fastapi-books:latest
docker push us-central1-docker.pkg.dev/my-project/fastapi-repo/fastapi-books:latest
```

### Create a dedicated service account

```bash
# Create service account for the Cloud Run service
gcloud iam service-accounts create fastapi-books-sa \
  --display-name "FastAPI Books Service"

# Grant it access to Secret Manager
gcloud projects add-iam-policy-binding my-project \
  --member "serviceAccount:fastapi-books-sa@my-project.iam.gserviceaccount.com" \
  --role "roles/secretmanager.secretAccessor"

# Grant access to Cloud SQL (example)
gcloud projects add-iam-policy-binding my-project \
  --member "serviceAccount:fastapi-books-sa@my-project.iam.gserviceaccount.com" \
  --role "roles/cloudsql.client"
```

### Deploy

```bash
gcloud run deploy fastapi-books \
  --image us-central1-docker.pkg.dev/my-project/fastapi-repo/fastapi-books:latest \
  --region us-central1 \
  --service-account fastapi-books-sa@my-project.iam.gserviceaccount.com \
  --set-env-vars GCP_PROJECT=my-project \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 10
```

The `--service-account` flag binds the IAM service account to the Cloud Run revision. **No keyfile, no environment variable credentials.**

### Access GCP services from FastAPI without credentials

Application Default Credentials (ADC) automatically picks up the Cloud Run service account:

```python
from google.cloud import secretmanager
import os

def get_secret(secret_id: str) -> str:
    """Fetch a secret from Secret Manager using ADC (no credentials needed)."""
    client = secretmanager.SecretManagerServiceClient()  # ADC resolves automatically
    project = os.environ["GCP_PROJECT"]
    name = f"projects/{project}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("utf-8")
```

---

## Option B — GKE with Workload Identity

GKE Workload Identity maps a Kubernetes service account to a Google Cloud service account, giving each pod its own IAM identity — no node-level credentials.

### Enable Workload Identity on the cluster

```bash
gcloud container clusters create fastapi-cluster \
  --workload-pool=my-project.svc.id.goog \
  --region us-central1

# Or enable on an existing cluster
gcloud container clusters update fastapi-cluster \
  --workload-pool=my-project.svc.id.goog \
  --region us-central1
```

### Create the IAM binding

```bash
# Create Google Cloud service account
gcloud iam service-accounts create fastapi-gke-sa \
  --display-name "FastAPI GKE Service Account"

# Grant permissions to the Google Cloud SA
gcloud projects add-iam-policy-binding my-project \
  --member "serviceAccount:fastapi-gke-sa@my-project.iam.gserviceaccount.com" \
  --role "roles/secretmanager.secretAccessor"

# Allow the Kubernetes SA to impersonate the Google Cloud SA
gcloud iam service-accounts add-iam-policy-binding fastapi-gke-sa@my-project.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:my-project.svc.id.goog[default/fastapi-sa]"
```

### Kubernetes manifests

```yaml
# service-account.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: fastapi-sa
  namespace: default
  annotations:
    iam.gke.io/gcp-service-account: fastapi-gke-sa@my-project.iam.gserviceaccount.com
---
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-books
spec:
  template:
    spec:
      serviceAccountName: fastapi-sa   # <-- Workload Identity annotation lives here
      containers:
        - name: fastapi
          image: us-central1-docker.pkg.dev/my-project/fastapi-repo/fastapi-books:latest
          ports:
            - containerPort: 8000
          env:
            - name: GCP_PROJECT
              value: "my-project"
```

ADC inside the pod automatically uses the Workload Identity token — your Python code is identical to the Cloud Run example above.

---

## Option C — App Engine

App Engine Standard uses the default App Engine service account bound to your app. Useful for simple APIs that don't need custom networking.

```yaml
# app.yaml
runtime: python313
entrypoint: uvicorn demo.main:app --host 0.0.0.0 --port $PORT

env_variables:
  GCP_PROJECT: "my-project"
```

```bash
gcloud app deploy
```

Grant the App Engine default service account the roles it needs:

```bash
gcloud projects add-iam-policy-binding my-project \
  --member "serviceAccount:my-project@appspot.gserviceaccount.com" \
  --role "roles/secretmanager.secretAccessor"
```

---

## Reading GCP secrets in FastAPI

```python
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from google.cloud import secretmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    client = secretmanager.SecretManagerServiceClient()
    project = os.environ["GCP_PROJECT"]

    def _get(name: str) -> str:
        n = f"projects/{project}/secrets/{name}/versions/latest"
        return client.access_secret_version(request={"name": n}).payload.data.decode()

    app.state.jwt_secret = _get("jwt-signing-key")
    app.state.db_password = _get("db-password")
    yield

app = FastAPI(lifespan=lifespan)
```

No key files, no `GOOGLE_APPLICATION_CREDENTIALS` env var — ADC resolves the bound service account automatically on Cloud Run, GKE, and App Engine.

---

## Next steps

- [Cloud IAM / Workload Identity](../auth/managed-identity.md) — how the credential chain works across clouds
- [AWS Deployment](./aws.md) — Lambda + IRSA
- [Azure Functions](./azure-functions.md) — Azure equivalent
