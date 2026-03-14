---
sidebar_position: 2
---

# Getting Started

Get the demo Books API running locally in under two minutes.

## Prerequisites

| Tool | Version | Install |
|---|---|---|
| Python | 3.14+ | [python.org](https://www.python.org/downloads/) |
| uv | latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Git | any | [git-scm.com](https://git-scm.com/) |

## 1. Clone the repo

```bash
git clone https://github.com/jaredthivener/python-demo
cd python-demo
```

## 2. Install dependencies

```bash
uv sync
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

| URL | Description |
|---|---|
| `http://localhost:8000/docs` | Swagger UI (interactive) |
| `http://localhost:8000/redoc` | ReDoc (readable) |
| `http://localhost:8000/` | Root hello-world check |
| `http://localhost:8000/api/tags` | Example tags list |
| `http://localhost:8000/api/ps` | Process status |
| `http://localhost:8000/api/status` | HEAD status check |

Background traffic is generated automatically on startup — watch the colorful Rich logs in your terminal.

## Try it with curl

```bash
# Root check
curl http://localhost:8000/

# Tags
curl http://localhost:8000/api/tags

# POST pull
curl -X POST http://localhost:8000/api/pull

# PUT / PATCH / DELETE an item
curl -X PUT http://localhost:8000/api/items/42
curl -X PATCH http://localhost:8000/api/items/42
curl -X DELETE http://localhost:8000/api/items/42

# Simulate a forced error
curl -X PATCH http://localhost:8000/api/items/42 -H "X-Force-Error: 500"
```

## Next steps

- Read the [Auth Overview](./auth/overview.md) to understand the authentication patterns
- Check the [Deployment Guide](./deployment/index.md) when you're ready to ship
