---
sidebar_position: 2
---

# GKE (Google Kubernetes Engine)

GKE Workload Identity maps a Kubernetes service account to a Google Cloud service account, giving each pod its own IAM identity — no node-level credentials.

## When to choose GKE

- Complex microservices with per-pod IAM isolation
- Autopilot or standard Kubernetes with Workload Identity
- ~$100+/month for a running node pool

## Enable Workload Identity on the cluster

```bash
gcloud container clusters create fastapi-cluster \
  --workload-pool=my-project.svc.id.goog \
  --region us-central1

# Or enable on an existing cluster
gcloud container clusters update fastapi-cluster \
  --workload-pool=my-project.svc.id.goog \
  --region us-central1
```

## Create the IAM binding

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

## Kubernetes manifests

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

ADC inside the pod automatically uses the Workload Identity token — your Python code is identical to the [Cloud Run secrets pattern](./gcp-cloud-run.md#secrets-with-caching).

## Next steps

- [Cloud Run](./gcp-cloud-run.md) — simpler serverless containers
- [App Engine](./gcp-app-engine.md) — managed PaaS for simple APIs
- [Cloud IAM / Workload Identity](../auth/managed-identity.md) — how the credential chain works across clouds
