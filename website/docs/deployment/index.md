---
sidebar_position: 1
description: Multi-cloud deployment overview for the Python Demo API across AWS, GCP, and Azure hosting options.
keywords:
  - deployment
  - aws
  - gcp
  - azure
  - fastapi
---

# Deployment Overview

FastAPI deploys to all major cloud providers with **zero long-lived credentials** — your app authenticates using platform-native IAM instead of hard-coded secrets.

## Cloud comparison

### Serverless / scale-to-zero

|                       | AWS Lambda              | GCP Cloud Run         | Azure Functions       |
| --------------------- | ----------------------- | --------------------- | --------------------- |
| **Cost at idle**      | $0                      | $0                    | $0 (consumption)      |
| **Cold start?**       | Yes                     | Yes                   | Yes (mitigable)       |
| **IAM auth**          | Lambda execution role   | Bound service account | Managed Identity      |
| **Container support** | Yes (image up to 10 GB) | Native                | Yes                   |
| **Best for**          | Event-driven / spiky    | Stateless HTTP APIs   | Azure-native services |

### Container orchestration

|                           | AWS EKS + IRSA                 | GKE + Workload Identity | Azure AKS             |
| ------------------------- | ------------------------------ | ----------------------- | --------------------- |
| **Cost at idle**          | ~$100+/month+                  | ~$100+/month            | ~$150+/month          |
| **IAM auth**              | IAM Roles for Service Accounts | GKE Workload Identity   | AKS Workload Identity |
| **Managed control plane** | Yes                            | Yes                     | Yes                   |
| **Best for**              | Kubernetes on AWS              | Complex microservices   | Microsoft-stack apps  |

### PaaS web hosting

|                  | AWS Elastic Beanstalk | GCP App Engine     | Azure App Service   |
| ---------------- | --------------------- | ------------------ | ------------------- |
| **Cost at idle** | ~$20+/month           | ~$0 (F1 free tier) | ~$15+/month (B1)    |
| **IAM auth**     | Instance profile      | Default SA         | Managed Identity    |
| **Best for**     | Lift-and-shift        | Simple APIs        | Steady-traffic APIs |

## The credential pattern is the same everywhere

Regardless of cloud, the pattern is identical:

```
Your FastAPI app  →  Platform metadata endpoint  →  Cloud IAM
                  ←  Short-lived token (auto-refreshed)
                  →  Cloud service (DB, secrets, queues) with token
```

See [Cloud IAM / Workload Identity](../auth/managed-identity.md) for how each cloud implements this.

## Dockerfile (works on all clouds)

```dockerfile
FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:0.13.1 /uv /usr/local/bin/uv
ENV UV_PYTHON_DOWNLOADS=never PATH="/app/.venv/bin:$PATH"
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY main.py ./
USER nobody
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
```

This is the same `Dockerfile` checked in at the repo root, and CI builds it on every pull request so the docs cannot drift from it.

:::note Python 3.14
The app requires Python 3.14+. If a managed runtime on your platform does not offer 3.14 yet, deploy the container image above instead.
:::

:::warning State is per process
The Books store is an in-memory dict. Every worker process and every replica gets its own copy, so `--workers 4`, autoscaling, or more than one replica will return different data on different requests. Swap in a shared database before scaling out.
:::

Health checks and probes should point at `GET /api/ps`.

## Pick a guide

- [AWS](./aws.md) — Lambda + EKS + Elastic Beanstalk
- [GCP](./gcp.md) — Cloud Run + Workload Identity + GKE
- [Azure Functions](./azure-functions.md) — serverless, pay-per-invocation
- [AKS](./aks.md) — Kubernetes, full control
- [App Service](./app-service.md) — PaaS, simplest Azure setup
