---
sidebar_position: 2
description: Quick local setup for the Python Demo API, including dependency install, running the FastAPI server, and verifying the Books API.
keywords:
  - quickstart
  - fastapi
  - uv
  - books api
---

# Getting Started

Get the demo Books API running locally in under two minutes. The live app is intentionally small and focuses on the core API concepts from the docs: validation, pagination, partial updates, monitoring, and request logging.

## Prerequisites

| Tool   | Version | Install                                            |
| ------ | ------- | -------------------------------------------------- |
| Python | 3.14+   | [python.org](https://www.python.org/downloads/)    |
| uv     | latest  | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Git    | any     | [git-scm.com](https://git-scm.com/)                |

## 1. Clone the repo

```bash
git clone https://github.com/jaredthivener/python-demo
cd python-demo
```

## 2. Install dependencies

```bash
uv sync --group dev
```

## 3. Run the server

```bash
uvicorn main:app --reload --no-access-log
```

You should see:

```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

## 4. Explore the API

| URL                                  | Description              |
| ------------------------------------ | ------------------------ |
| `http://localhost:8000/docs`         | Swagger UI (interactive) |
| `http://localhost:8000/redoc`        | ReDoc (readable)         |
| `http://localhost:8000/`             | Root metadata            |
| `http://localhost:8000/api/ps`       | Health payload           |
| `http://localhost:8000/api/status`   | HEAD status check        |
| `http://localhost:8000/api/v1/books` | Books collection         |

Background traffic is off by default. Enable it with `ENABLE_TRAFFIC_GENERATOR=true` if you want to watch the Rich logs fill with local demo traffic.

## Try it with curl

```bash
# Root check
curl http://localhost:8000/

# List books
curl "http://localhost:8000/api/v1/books?skip=0&limit=10"

# Create a book
curl -X POST http://localhost:8000/api/v1/books \
	-H "Content-Type: application/json" \
	-d '{"title": "Refactoring", "author": "Martin Fowler", "year": 2018}'

# Patch a seeded book
curl -X PATCH http://localhost:8000/api/v1/books/3fa85f64-5717-4562-b3fc-2c963f66afa6 \
	-H "Content-Type: application/json" \
	-d '{"year": 2022}'

# Simulate a forced error after starting the server with chaos headers enabled
curl http://localhost:8000/api/v1/books -H "X-Force-Error: 500"
```

To enable forced errors locally, start the server with:

```bash
ENABLE_CHAOS_HEADERS=true uvicorn main:app --reload --no-access-log
```

## Run the tests

```bash
uv run pytest
```

## Run the quality checks

```bash
uv run ruff check .
uv run ruff format --check .
cd website
npm run format:check
npm run typecheck
npm run build
```

## Next steps

- Read the [Auth Overview](./auth/overview.md) to understand the authentication patterns
- Check the [Deployment Guide](./deployment/index.md) when you're ready to ship
