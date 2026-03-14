---
sidebar_position: 1
---

# Cloud Run

Cloud Run is the simplest GCP deployment: push a container, get a URL. Each revision runs with a bound Google Cloud service account — no key files needed.

## When to choose Cloud Run

- Serverless containers that scale to zero — $0 at idle
- Simple HTTP APIs without complex networking requirements
- You want zero infrastructure management
- Cold starts are acceptable (mitigable with `--min-instances`)

## Build and push to Artifact Registry

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

## Create a dedicated service account

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

## Deploy

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

## Observability

Install the GCP observability packages:

```bash
uv add google-cloud-logging opentelemetry-sdk opentelemetry-exporter-gcp-trace
```

### Structured logging

Send JSON-structured logs directly to Cloud Logging:

```python
import google.cloud.logging

# Call once at startup — routes stdlib logging to Cloud Logging
google.cloud.logging.Client().setup_logging()
```

After this, standard `logging.getLogger()` calls emit structured JSON visible in the **Logs Explorer** and queryable with Log Analytics.

### Distributed tracing (X-Ray equivalent on GCP)

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter

provider = TracerProvider()
provider.add_span_processor(BatchSpanProcessor(CloudTraceSpanExporter()))
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)
```

Add `roles/cloudtrace.agent` to the service account to allow writing traces.

## Secrets with caching

Fetch secrets once on cold start via the lifespan and store on `app.state`. Call `access_secret_version` only when needed — Cloud Run instances persist between requests:

```python
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator
from google.cloud import secretmanager
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    client = secretmanager.SecretManagerServiceClient()  # ADC picks up bound SA
    project = os.environ["GCP_PROJECT"]

    def _get(name: str) -> str:
        path = f"projects/{project}/secrets/{name}/versions/latest"
        return client.access_secret_version(request={"name": path}).payload.data.decode()

    app.state.jwt_secret = _get("jwt-signing-key")
    app.state.db_password = _get("db-password")
    yield


app = FastAPI(lifespan=lifespan)
```

No keyfiles, no `GOOGLE_APPLICATION_CREDENTIALS` — ADC resolves the bound service account automatically.

## Next steps

- [GKE](./gcp-gke.md) — Kubernetes with Workload Identity
- [App Engine](./gcp-app-engine.md) — managed PaaS for simple APIs
- [Cloud IAM / Workload Identity](../auth/managed-identity.md) — how the credential chain works across clouds
