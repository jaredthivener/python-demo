---
sidebar_position: 1
description: Endpoint reference for the live Books API, including pagination, search, create, patch, delete, and error behavior.
keywords:
  - api reference
  - openapi
  - books api
  - fastapi
---

# Books API Reference

Full endpoint reference for the live demo Books API implemented in `main.py`.

**Base URL:** `http://localhost:8000/api/v1`

The API uses FastAPI request validation, UUID path parameters, and an in-memory store seeded with three books at startup. This is still a demo app, but the resource contract is intentionally realistic because it is used to illustrate the API concepts discussed throughout the docs.

## Endpoints

### `GET /books`

List all books with pagination.

| Parameter | Type    | Default | Description                 |
| --------- | ------- | ------- | --------------------------- |
| `skip`    | integer | `0`     | Number of items to skip     |
| `limit`   | integer | `20`    | Max items to return (1–100) |

```bash
curl "http://localhost:8000/api/v1/books?skip=0&limit=10"
```

**Response 200:**

```json
{
  "items": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "title": "Clean Code",
      "author": "Robert C. Martin",
      "year": 2008,
      "created_at": "2026-03-14T10:00:00Z"
    }
  ],
  "total": 3,
  "skip": 0,
  "limit": 10
}
```

---

### `POST /books`

Create a new book. Returns `201 Created`.

```bash
curl -X POST http://localhost:8000/api/v1/books \
  -H "Content-Type: application/json" \
  -d '{
    "title": "The Pragmatic Programmer",
    "author": "David Thomas, Andrew Hunt",
    "year": 2019
  }'
```

**Request body:**

```json
{
  "title": "string (required, 1–200 chars)",
  "author": "string (required, 1–100 chars)",
  "year": "integer (1900–2100)"
}
```

**Response 201:** Full `BookResponse` object with generated `id` and `created_at` values.

---

### `GET /books/{book_id}`

Get a single book by UUID.

```bash
curl http://localhost:8000/api/v1/books/3fa85f64-5717-4562-b3fc-2c963f66afa6
```

**Response 404** if not found:

```json
{ "detail": "Book not found" }
```

---

### `PATCH /books/{book_id}`

Partial update — only fields included in the request body are changed.

```bash
curl -X PATCH http://localhost:8000/api/v1/books/3fa85f64-5717-4562-b3fc-2c963f66afa6 \
  -H "Content-Type: application/json" \
  -d '{"year": 2022}'
```

Uses `model_dump(exclude_unset=True)` internally — fields omitted from the payload are untouched.

Empty payloads are valid and return the existing book unchanged.

---

### `DELETE /books/{book_id}`

Delete a book. Returns a confirmation message.

```bash
curl -X DELETE http://localhost:8000/api/v1/books/3fa85f64-5717-4562-b3fc-2c963f66afa6
```

**Response 200:**

```json
{ "message": "Book 3fa85f64-... deleted successfully" }
```

---

### `GET /books/search`

Search books by title or author substring (case-insensitive).

| Parameter | Type    | Required | Description               |
| --------- | ------- | -------- | ------------------------- |
| `q`       | string  | yes      | Search query (min 1 char) |
| `skip`    | integer | no       | Pagination offset         |
| `limit`   | integer | no       | Max results               |

```bash
curl "http://localhost:8000/api/v1/books/search?q=clean"
```

The search is case-insensitive and matches both title and author.

## Supporting endpoints

| Endpoint               | Purpose                                                |
| ---------------------- | ------------------------------------------------------ |
| `GET /`                | Root metadata payload with docs URL and traffic status |
| `GET /api/ps`          | Health payload with current book count                 |
| `HEAD /api/status`     | Header-only monitoring check                           |
| `OPTIONS /api/options` | Supported method list                                  |
| `GET /api/redirect`    | `307` redirect to a random seeded book                 |

## Error responses

| Status                     | Meaning                                                        |
| -------------------------- | -------------------------------------------------------------- |
| `422 Unprocessable Entity` | Validation error (Pydantic) — body contains field-level errors |
| `404 Not Found`            | Book UUID not in store                                         |
| `405 Method Not Allowed`   | Wrong HTTP verb                                                |
| `400 Bad Request`          | Invalid `X-Force-Error` header when chaos mode is enabled      |
| `500` / `503`              | Forced demo failures when chaos mode is enabled                |

Forced demo failures are disabled by default. To enable them locally:

```bash
ENABLE_CHAOS_HEADERS=true uvicorn main:app --reload --no-access-log
```

**Example 422:**

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "title"],
      "msg": "String should have at least 1 character",
      "input": ""
    }
  ]
}
```

## Data model

```python
class BookResponse(BaseModel):
    id: UUID
    title: str
    author: str
    year: int
    created_at: datetime
```

Internal fields (`id`, `created_at`) are never accepted in request bodies — separate `BookCreate` and `BookUpdate` models enforce this boundary.
