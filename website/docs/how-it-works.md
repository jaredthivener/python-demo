---
sidebar_position: 3
description: A guided tour of main.py covering routers, dependency injection, validation, the request-ID middleware, lifespan hooks, and how the test suite protects each behavior.
keywords:
  - fastapi
  - dependency injection
  - apirouter
  - middleware
  - pytest
---

# How the Demo Works

A guided tour of `main.py`, in the order a request meets it. Each section ends with the test that protects the behavior.

## 1. Middleware: request IDs and access logs

`colorful_access_log` wraps every request. It reads `X-Request-ID` if the client sent one, stores it on `request.state.request_id`, times the call, prints the Rich access line, and echoes the ID on the response.

A client-supplied ID is only trusted when it matches `[A-Za-z0-9._-]{1,64}`. Anything else (spaces, markup, 10 KB of junk) is replaced with a fresh UUID, so a caller cannot inject text into your logs.

Each line has a level column right after the time: `INFO` below 400, `WARNING` for 4xx, `ERROR` for 5xx, in the same colors as the app's own log lines. The line goes through the `python-demo.access` logger, and a small handler prints the styled Rich line as-is, so the level is also on the log record for filtering or shipping to a log backend.

If a handler raises, the middleware logs the traceback with the request ID and returns a plain `500` instead of leaking internals.

Tests: `test_access_log_level_follows_status_class`, `test_access_output_shows_one_level_column_after_the_time`, `test_valid_incoming_request_id_is_echoed`, `test_unsafe_incoming_request_id_is_replaced`, `test_unhandled_exception_returns_500_with_request_id`.

## 2. Router-level dependencies

All Books routes live on one `APIRouter`:

```python
books_router = APIRouter(
    prefix="/api/v1/books",
    tags=["Books API"],
    dependencies=[Depends(maybe_force_error)],
)
```

`maybe_force_error` is a dependency, so it runs before every Books handler without being called in each one. It only acts when `ENABLE_CHAOS_HEADERS` is on and the `X-Force-Error` code is on the allow-list.

Tests: `test_every_books_route_honours_force_error`, `test_invalid_force_error_values_return_400`.

## 3. Annotated dependencies

Handlers declare what they need instead of reaching into `request.app.state`:

```python
BookStoreDep = Annotated[InMemoryBookStore, Depends(get_book_store)]
ExistingBook = Annotated[BookResponse, Depends(get_book_or_404)]


@books_router.get("/{book_id}", response_model=BookResponse)
async def get_book(book: ExistingBook) -> BookResponse:
    return book
```

`get_book_or_404` is shared by GET, PATCH, and DELETE, so the 404 logic exists once. The store itself knows nothing about HTTP: it returns `None`, and the dependency decides what that means.

Tests: `test_unknown_book_returns_404` (parametrized over all three verbs).

## 4. Validation as a contract

- `PageParams` and `SearchParams` are Pydantic models used as query parameters, so `skip` and `limit` are declared once. The OpenAPI schema is unchanged.
- `BookCreate` and `BookUpdate` use `extra="forbid"`. A body containing `id` or a typo like `titel` returns `422` instead of being silently dropped.
- `BookUpdate` rejects an explicit `null` for any field. Omitting a field leaves it alone; sending `null` would erase a required value.

Tests: `test_create_rejects_unknown_fields`, `test_patch_rejects_explicit_null_for_required_field`, `test_pagination_bounds_are_validated`.

## 5. PATCH done safely

```python
merged = {**book.model_dump(), **payload.model_dump(exclude_unset=True)}
updated = BookResponse.model_validate(merged)
```

`exclude_unset=True` means only the fields the client actually sent are applied. `model_validate` re-checks the merged result. `model_copy(update=...)` skips validation, which is how an invalid value used to slip into the store.

## 6. Lifespan and the traffic generator

`lifespan` starts `generate_traffic()` as a background task when `ENABLE_TRAFFIC_GENERATOR` is on and cancels it on shutdown. `generate_traffic` accepts an optional `httpx2` transport, which is how the tests drive it with `httpx2.MockTransport` instead of a real server.

Tests: `test_lifespan_starts_and_stops_traffic_generator`, `test_traffic_generator_survives_request_errors`.

## Running the tests

```bash
uv run pytest
```

The suite follows the project's test-first rule: write or update the test, watch it fail, then change `main.py`. `pyproject.toml` sets `pythonpath = ["."]`, so tests import `main` directly.

## State is per process

The store is an in-memory dict created at import time. It is not shared between uvicorn workers or replicas, and it resets on restart. That is deliberate for a demo; see the [deployment guide](./deployment/index.md) before scaling out.
