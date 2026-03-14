---
sidebar_position: 3
---

# App Engine

App Engine Standard uses the default App Engine service account bound to your app. Useful for simple APIs that don't need custom networking.

## When to choose App Engine

- Simple web APIs without custom networking requirements
- ~$0 on the F1 free tier for low-traffic apps
- You prefer `gcloud app deploy` over container workflows

## `app.yaml`

```yaml
runtime: python313
entrypoint: uvicorn demo.main:app --host 0.0.0.0 --port $PORT

env_variables:
  GCP_PROJECT: "my-project"
```

## Deploy

```bash
gcloud app deploy
```

## Grant service account permissions

Grant the App Engine default service account the roles it needs:

```bash
gcloud projects add-iam-policy-binding my-project \
  --member "serviceAccount:my-project@appspot.gserviceaccount.com" \
  --role "roles/secretmanager.secretAccessor"
```

ADC automatically uses the App Engine default service account — no key files or `GOOGLE_APPLICATION_CREDENTIALS` needed. Your Python code is identical to the [Cloud Run secrets pattern](./gcp-cloud-run.md#secrets-with-caching).

## Next steps

- [Cloud Run](./gcp-cloud-run.md) — serverless containers with more control
- [GKE](./gcp-gke.md) — Kubernetes with Workload Identity
- [Cloud IAM / Workload Identity](../auth/managed-identity.md) — how the credential chain works across clouds
