# Python Demo API

[![CI](https://img.shields.io/github/actions/workflow/status/jaredthivener/python-demo/ci.yml?branch=main&label=CI)](https://github.com/jaredthivener/python-demo/actions/workflows/ci.yml)
[![Python 3.14+](https://img.shields.io/badge/python-3.14%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.135-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docs](https://img.shields.io/badge/docs-Docusaurus-2E8555?logo=docusaurus&logoColor=white)](https://docusaurus.io/)

A compact FastAPI demo app that covers the core API concepts discussed in the docs: validation, pagination, partial updates, rich logging, monitoring endpoints, and HTTP behavior. Authentication and multi-cloud deployment patterns remain in the documentation.

## What this repo is now

- A realistic in-memory resource API under `/api/v1/books`
- Rich request logging with latency, size, status, client, and request IDs
- Lightweight health, redirect, and method-demo endpoints for smoke testing and tooling demos
- Optional background traffic generation for local demos
- Optional forced-error headers for testing unhappy paths without creating fake routes

## Scope boundary

- The live app demonstrates API and observability concepts from the docs
- The docs cover broader topics like JWT, managed identity, enterprise SSO, and cloud deployment guidance
- The local demo does not provision cloud resources or implement full identity-provider integrations

## Prerequisites

- Python 3.14 or higher
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
uv sync --group dev
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

## Run the API

```bash
uvicorn main:app --reload --no-access-log
```

The API is available at `http://127.0.0.1:8000`.

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Optional demo switches

Enable background traffic generation:

```bash
ENABLE_TRAFFIC_GENERATOR=true uvicorn main:app --reload --no-access-log
```

Enable forced error responses through the `X-Force-Error` header:

```bash
ENABLE_CHAOS_HEADERS=true uvicorn main:app --reload --no-access-log
```

Allowed forced error codes are `400`, `404`, `409`, `500`, and `503`.

## API surface

### Core endpoints

- `GET /` returns API metadata and local docs links
- `GET /api/ps` returns a health payload and book count
- `HEAD /api/status` returns `X-System-Status: OK`
- `OPTIONS /api/options` returns supported methods
- `GET /api/redirect` returns a `307` to a seeded book

### Books API

Base URL: `http://127.0.0.1:8000/api/v1`

- `GET /books?skip=0&limit=20` lists books with pagination
- `GET /books/search?q=code` searches title and author fields
- `POST /books` creates a book
- `GET /books/{book_id}` fetches a single book
- `PATCH /books/{book_id}` applies a partial update
- `DELETE /books/{book_id}` deletes a book

## Example usage

```bash
# List books
curl "http://127.0.0.1:8000/api/v1/books?skip=0&limit=10"

# Create a book
curl -X POST http://127.0.0.1:8000/api/v1/books \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Refactoring",
    "author": "Martin Fowler",
    "year": 2018
  }'

# Partial update
curl -X PATCH http://127.0.0.1:8000/api/v1/books/3fa85f64-5717-4562-b3fc-2c963f66afa6 \
  -H "Content-Type: application/json" \
  -d '{"year": 2022}'

# Search
curl "http://127.0.0.1:8000/api/v1/books/search?q=martin"

# Forced error demo
curl http://127.0.0.1:8000/api/v1/books \
  -H "X-Force-Error: 503"
```

## Run tests

```bash
uv run pytest
```

## Quality checks

```bash
uv run ruff check .
uv run ruff format --check .
cd website && npm run format:check && npm run typecheck && npm run build
```

To apply formatting locally:

```bash
uv run ruff format .
cd website && npm run format
```

## Logging

Every request is logged with:

- Timestamp
- Status code
- Latency
- Response size
- Client IP
- HTTP method
- Request path
- `X-Request-ID`

## Project layout

```text
python-demo/
├── main.py
├── tests/
├── pyproject.toml
├── README.md
└── website/
```

## Next layer

The website under `website/` contains the broader auth and multi-cloud deployment guidance. The backend and README now define the local source of truth for the live demo API.

## MCP ingestion

If another team wants to build an MCP server or other machine-ingestion workflow from this repo, prefer these sources in this order:

1. `website/static/openapi.json` for the live API contract
2. `website/static/docs-index.json` for the curated docs manifest
3. `website/static/llms.txt` for the concise crawler entrypoint
4. `website/build/sitemap.xml` or the deployed `/sitemap.xml` for URL discovery
5. `website/docs/**/*.md` for the canonical prose source

The running API also exposes `GET /openapi.json` automatically through FastAPI, and `GET /` now returns `docs_url`, `redoc_url`, and `openapi_url` to make those entry points explicit.

These artifacts are generated from source, not meant to be hand-maintained.

To refresh the checked-in machine-readable artifacts after changing routes, models, or docs:

```bash
uv run python scripts/generate_machine_artifacts.py
```

For the full automation loop, use one of these entrypoints:

```bash
make fix    # auto-fix, regenerate, then validate everything
make check  # validate only, no file changes
```

The same loop is available without `make`:

```bash
uv run python scripts/repo_loop.py fix
uv run python scripts/repo_loop.py check
```

`fix` runs generation before and after formatting so the docs formatter cannot leave `docs-index.json` or `llms.txt` stale.

Workflow split:

- `CI` stays read-only and fails on drift.
- `Autofix Repo Standards` runs on pushes to `main`, applies `make fix`, and opens or updates an automation PR instead of pushing directly to `main`.

See `scripts/README.md` for the script-level details and how the loop fits into the repo.

CI also verifies that `website/static/openapi.json`, `website/static/docs-index.json`, and `website/static/llms.txt` are up to date.