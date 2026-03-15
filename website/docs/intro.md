---
sidebar_position: 1
description: Overview of the Python Demo API, its live FastAPI surface, and the docs areas that expand on auth and cloud deployment patterns.
keywords:
  - fastapi
  - python
  - books api
  - auth
  - deployment
---

# Introduction

**Python Demo API** is a compact FastAPI demo that uses a realistic Books API to teach the API concepts discussed in the docs without turning the repository into a full production platform. The live app focuses on validation, pagination, PATCH behavior, monitoring, and request logging. The docs extend that foundation into auth and deployment guidance for AWS, GCP, and Azure.

## What you'll learn

- How to structure a small FastAPI service with Pydantic v2 models and clear API boundaries
- When to use JWT Bearer, Managed Identity, and Microsoft Entra ID — and how to combine them
- How to deploy a FastAPI app to AWS, GCP, and Azure with zero secrets in code
- Cloud-native observability: Lambda Powertools (AWS), Cloud Logging + OpenTelemetry (GCP), and Azure Monitor (Azure)

## What the live app actually covers

- CRUD and search on a simple Books resource
- Request validation and typed responses
- Partial updates with `PATCH`
- Health, status, and redirect endpoints
- Rich access logging and optional demo-only error injection

## What's included

| Component            | Description                                                                         |
| -------------------- | ----------------------------------------------------------------------------------- |
| `main.py`            | Books API, request logging middleware, lifespan hooks, and local demo configuration |
| `tests/test_main.py` | Behavioral coverage for the Books API and demo support endpoints                    |
| `website/docs/`      | Auth, API, and deployment guidance for AWS, GCP, and Azure                          |
| `website/src/`       | Docusaurus site shell and homepage components                                       |

## Project structure

```text
python-demo/
├── main.py
├── tests/
├── pyproject.toml
├── README.md
└── website/
```

## Quick navigation

- New here? Start with [Getting Started](./getting-started.md)
- Want to understand auth? Go to [Auth Overview](./auth/overview.md)
- Ready to deploy? See the [Deployment guide](./deployment/index.md)
