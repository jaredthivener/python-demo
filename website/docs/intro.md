---
sidebar_position: 1
---

# Introduction

**FastAPI Docs** is a reference implementation of production-grade FastAPI patterns for developers building cloud APIs. It covers three authentication strategies, a fully working CRUD API, and deployment guides for AWS, GCP, and Azure — each following the cloud provider's own best practices and official tooling.

## What you'll learn

- How to structure a FastAPI project with Pydantic v2 models and reusable dependencies
- When to use JWT Bearer, Managed Identity, and Microsoft Entra ID — and how to combine them
- How to deploy a containerised FastAPI app to AWS, GCP, and Azure with zero secrets in code
- Cloud-native observability: Lambda Powertools (AWS), Cloud Logging + OpenTelemetry (GCP), and Azure Monitor (Azure)

## What's included

| Component | Description |
|---|---|
| `demo/` | Books CRUD API — 6 endpoints, Pydantic v2, pagination, 422 validation |
| `demo/routers/books.py` | Full REST router with `PATCH` partial updates and typed responses |
| `demo/dependencies.py` | `PaginationParams` class dependency, `get_book_or_404` |
| `demo/models.py` | Pydantic v2 request/response models |

## Project structure

```
fastapi-docs/
├── demo/
│   ├── main.py          # App factory, lifespan, CORS, health check
│   ├── models.py        # Pydantic v2 request/response models
│   ├── database.py      # In-memory store (swap for real DB)
│   ├── dependencies.py  # Reusable Depends() callables
│   └── routers/
│       └── books.py     # CRUD + search endpoints
└── pyproject.toml
```

## Quick navigation

- New here? Start with [Getting Started](./getting-started.md)
- Want to understand auth? Go to [Auth Overview](./auth/overview.md)
- Ready to deploy? See the [Deployment guide](./deployment/index.md)
